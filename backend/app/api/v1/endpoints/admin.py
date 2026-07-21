"""
AutoWorth AI — Admin Endpoints

Admin-only model management: training trigger, version listing, activation.

Layer: API Layer
Auth: Admin role required (JWT + role check)

Security Note:
    The algorithm type (XGBoost, RandomForest, etc.) selected by the pipeline is
    intentionally excluded from all user-facing responses. It is visible only to
    admin users via the model version detail endpoints.
"""

from __future__ import annotations

import uuid
from pathlib import Path


from fastapi import APIRouter, HTTPException, status, BackgroundTasks, UploadFile, File, Form

from app.api.v1.dependencies import AdminUser, DBSession  # noqa: F401

from app.repositories.ml_model_repository import MLModelRepository
from app.schemas.common import APIResponse
from app.schemas.prediction import (
    MLModelResponse,
    ModelVersionResponse,
    TrainingRequest,
    TrainingResponse,
)
from app.services.ml_service import MLService

router = APIRouter(prefix="/admin", tags=["Admin — Model Management"])



# ──────────────────────────────────────────────
# POST /admin/models/train — Trigger Training
# ──────────────────────────────────────────────
async def background_training_task(
    dataset_path: Path,
    version_tag: str,
    dataset_id: uuid.UUID | None,
):
    from app.core.database import AsyncSessionLocal
    ml_service = MLService()
    async with AsyncSessionLocal() as db:
        try:
            await ml_service.run_training(
                dataset_path=dataset_path,
                version_tag=version_tag,
                db=db,
                dataset_id=dataset_id,
            )
        except Exception as e:
            # Error is logged in run_training and status is set to FAILED
            pass


@router.post(
    "/models/train",
    response_model=APIResponse[dict],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Offline Training Pipeline",
    description=(
        "Start an offline training run in the background using the specified dataset CSV. "
        "Trains LinearRegression, DecisionTree, RandomForest, and XGBoost — "
        "selects the best by 5-fold CV R² with Optuna hyperparameter tuning. "
        "The trained version is saved but NOT activated automatically."
    ),
)
async def trigger_training(
    data: TrainingRequest,
    current_user: AdminUser,
    background_tasks: BackgroundTasks,
) -> APIResponse[dict]:
    """
    Trigger the offline ML training pipeline (asynchronously).
    """
    dataset_path = Path(data.dataset_path)
    if not dataset_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": f"Dataset file not found: {data.dataset_path}",
                "error_code": "DATASET_NOT_FOUND",
            },
        )

    background_tasks.add_task(
        background_training_task,
        dataset_path=dataset_path,
        version_tag=data.version_tag,
        dataset_id=data.dataset_id,
    )

    return APIResponse(
        success=True,
        message="Training pipeline started in the background.",
        data={"version_tag": data.version_tag, "status": "training_started"},
    )


# ──────────────────────────────────────────────
# GET /admin/models — List All Models + Versions
# ──────────────────────────────────────────────
@router.get(
    "/models",
    response_model=APIResponse[list[MLModelResponse]],
    summary="List All ML Models",
    description=(
        "Return all MLModel records with their version history, "
        "including training metrics and status. Algorithm types are visible "
        "to admins only — never exposed to end users."
    ),
)
async def list_ml_models(
    current_user: AdminUser,
    db: DBSession,
) -> APIResponse[list[MLModelResponse]]:
    """List all MLModel records with their version history."""
    repo = MLModelRepository(db)
    ml_models = await repo.get_all_ml_models()

    result = []
    for ml_model in ml_models:
        versions = [
            ModelVersionResponse(
                id=v.id,
                version_tag=v.version_tag,
                status=v.status.value,
                r2_score=v.r2_score,
                rmse=v.rmse,
                mae=v.mae,
                cross_val_score=v.cross_val_score,
                training_time_seconds=v.training_time_seconds,
                training_samples=v.training_samples,
                model_artifact_path=v.model_artifact_path,
                preprocessor_path=v.preprocessor_path,
                notes=v.notes,
                created_at=v.created_at,
            )
            for v in sorted(ml_model.versions, key=lambda v: v.created_at, reverse=True)
        ]
        result.append(MLModelResponse(
            id=ml_model.id,
            name=ml_model.name,
            description=ml_model.description,
            is_active=ml_model.is_active,
            versions=versions,
            created_at=ml_model.created_at,
        ))

    return APIResponse(
        success=True,
        message=f"{len(result)} ML model(s) found.",
        data=result,
    )


# ──────────────────────────────────────────────
# POST /admin/models/{version_id}/activate
# ──────────────────────────────────────────────
@router.post(
    "/models/{version_id}/activate",
    response_model=APIResponse[ModelVersionResponse],
    summary="Activate a Model Version",
    description=(
        "Promote a TRAINED ModelVersion to ACTIVE status, making it the live "
        "model served for all new predictions. Any previously ACTIVE version for "
        "the same algorithm is automatically ARCHIVED. "
        "The in-memory model cache is invalidated so the next prediction reloads "
        "the newly activated artifacts."
    ),
)
async def activate_model_version(
    version_id: uuid.UUID,
    current_user: AdminUser,
    db: DBSession,
) -> APIResponse[ModelVersionResponse]:
    """
    Activate a trained model version.

    - Target version must be in TRAINED status.
    - Automatically archives the previous active version.
    - Invalidates the in-memory model cache.
    """
    repo = MLModelRepository(db)

    try:
        version = await repo.activate_version(version_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": str(exc),
                "error_code": "ACTIVATION_FAILED",
            },
        )

    await db.commit()

    # Invalidate the in-memory model cache so next prediction reloads
    MLService().invalidate_cache()

    return APIResponse(
        success=True,
        message=(
            f"Model version '{version.version_tag}' is now ACTIVE "
            "and will be used for all new predictions."
        ),
        data=ModelVersionResponse(
            id=version.id,
            version_tag=version.version_tag,
            status=version.status.value,
            r2_score=version.r2_score,
            rmse=version.rmse,
            mae=version.mae,
            cross_val_score=version.cross_val_score,
            training_time_seconds=version.training_time_seconds,
            training_samples=version.training_samples,
            model_artifact_path=version.model_artifact_path,
            preprocessor_path=version.preprocessor_path,
            notes=version.notes,
            created_at=version.created_at,
        ),
    )


# ──────────────────────────────────────────────
# GET /admin/models/{version_id} — Version Detail
# ──────────────────────────────────────────────
@router.get(
    "/models/{version_id}",
    response_model=APIResponse[ModelVersionResponse],
    summary="Get Model Version Detail",
    description="Return detailed metadata for a specific model version.",
)
async def get_model_version(
    version_id: uuid.UUID,
    current_user: AdminUser,
    db: DBSession,
) -> APIResponse[ModelVersionResponse]:
    """Return full metadata for a single ModelVersion."""
    repo = MLModelRepository(db)
    version = await repo.get_version_by_id(version_id)

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Model version not found.",
                "error_code": "VERSION_NOT_FOUND",
            },
        )

    return APIResponse(
        success=True,
        message="Model version retrieved.",
        data=ModelVersionResponse(
            id=version.id,
            version_tag=version.version_tag,
            status=version.status.value,
            r2_score=version.r2_score,
            rmse=version.rmse,
            mae=version.mae,
            cross_val_score=version.cross_val_score,
            training_time_seconds=version.training_time_seconds,
            training_samples=version.training_samples,
            model_artifact_path=version.model_artifact_path,
            preprocessor_path=version.preprocessor_path,
            notes=version.notes,
            created_at=version.created_at,
        ),
    )


# ──────────────────────────────────────────────
# GET /admin/analytics — Dashboard Analytics
# ──────────────────────────────────────────────
from app.schemas.admin import AnalyticsResponse, ActivityLogResponse, DatasetUploadResponse
from app.services.analytics_service import AnalyticsService

@router.get(
    "/analytics",
    response_model=APIResponse[AnalyticsResponse],
    summary="Get Dashboard Analytics",
    description="Fetch KPIs and system health for the admin dashboard."
)
async def get_analytics(
    current_user: AdminUser,
    db: DBSession,
) -> APIResponse[AnalyticsResponse]:
    service = AnalyticsService(db)
    data = await service.get_dashboard_data()
    return APIResponse(
        success=True,
        message="Analytics data retrieved.",
        data=data
    )


# ──────────────────────────────────────────────
# GET /admin/activity — Live Activity Feed
# ──────────────────────────────────────────────
from app.repositories.activity_log_repository import ActivityLogRepository

@router.get(
    "/activity",
    response_model=APIResponse[list[ActivityLogResponse]],
    summary="Get Recent Activity",
    description="Fetch recent activity logs for the dashboard."
)
async def get_activity(
    current_user: AdminUser,
    db: DBSession,
) -> APIResponse[list[ActivityLogResponse]]:
    repo = ActivityLogRepository(db)
    logs = await repo.get_recent_activities(limit=50)
    
    result = [
        ActivityLogResponse(
            id=log.id,
            action=log.action.value,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            ip_address=log.ip_address,
            extra_data=log.extra_data,
            user_id=log.user_id,
            created_at=log.created_at
        )
        for log in logs
    ]
    return APIResponse(
        success=True,
        message="Activity logs retrieved.",
        data=result
    )


# ──────────────────────────────────────────────
# POST /admin/datasets/upload — Upload CSV Dataset
# ──────────────────────────────────────────────
from app.services.dataset_service import DatasetService

@router.post(
    "/datasets/upload",
    response_model=APIResponse[DatasetUploadResponse],
    summary="Upload Dataset",
    description="Upload a CSV dataset for training. Mode can be 'replace' or 'merge'."
)
async def upload_dataset(
    current_user: AdminUser,
    db: DBSession,
    file: UploadFile = File(...),
    mode: str = Form("replace"),
    version: str = Form(...)
) -> APIResponse[DatasetUploadResponse]:
    if mode not in ["replace", "merge"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Mode must be 'replace' or 'merge'."}
        )
        
    service = DatasetService(db)
    try:
        result = await service.process_upload(file=file, mode=mode, version=version, user=current_user)
        # Note: the dataset upload should ideally be committed. 
        # Since service uses repository without commit, we must commit here:
        await db.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "message": str(exc)}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Upload failed: {exc}"}
        )
        
    return APIResponse(
        success=True,
        message="Dataset uploaded successfully.",
        data=DatasetUploadResponse(**result)
    )

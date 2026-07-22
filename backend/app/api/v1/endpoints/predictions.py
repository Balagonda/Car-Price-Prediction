"""
AutoWorth AI — Prediction Endpoints

User-facing API for vehicle price predictions and history.

Layer: API Layer
Auth: Verified users only (JWT)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response

from app.api.v1.dependencies import DBSession, VerifiedUser, ActiveUser
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.prediction import (
    PredictionListItem,
    PredictionRequest,
    PredictionResponse,
)
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


# ──────────────────────────────────────────────
# POST /predictions — Create Prediction
# ──────────────────────────────────────────────
@router.post(
    "",
    response_model=APIResponse[PredictionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Vehicle Price Prediction",
    description=(
        "Submit vehicle specifications and receive an AI-powered price estimate, "
        "SHAP feature explanations, 5 similar historical vehicles, and actionable "
        "recommendations. Response time target: < 3 seconds."
    ),
)
async def create_prediction(
    data: PredictionRequest,
    current_user: VerifiedUser,
    db: DBSession,
) -> APIResponse[PredictionResponse]:
    """
    Create a new prediction for the authenticated user.

    - Requires a verified user account.
    - Returns estimated price, confidence score (0–100%), SHAP breakdown,
      5 nearest comparable vehicles, and AI recommendations.
    - If confidence < 60%, a `confidence_warning` string is included.
    """
    service = PredictionService(db)

    try:
        result = await service.create_prediction(
            user_id=current_user.id,
            data=data,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": str(exc),
                "error_code": "MODEL_UNAVAILABLE",
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Prediction failed due to an internal error. Please try again.",
                "error_code": "PREDICTION_FAILED",
            },
        )

    return APIResponse(
        success=True,
        message="Vehicle price prediction generated successfully.",
        data=result,
    )


# ──────────────────────────────────────────────
# GET /predictions — User History
# ──────────────────────────────────────────────
@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[PredictionListItem]],
    summary="Get Prediction History",
    description="Return a paginated list of the authenticated user's past predictions.",
)
async def get_prediction_history(
    current_user: ActiveUser,
    db: DBSession,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=50, description="Items per page")] = 20,
) -> APIResponse[PaginatedResponse[PredictionListItem]]:
    """
    Retrieve paginated prediction history for the authenticated user.
    """
    skip = (page - 1) * page_size
    service = PredictionService(db)
    items = await service.get_user_history(
        user_id=current_user.id, skip=skip, limit=page_size
    )

    # Count total for pagination metadata
    from app.repositories.prediction_repository import PredictionRepository
    count = await PredictionRepository(db).count_by_user(current_user.id)
    total_pages = max(1, -(-count // page_size))  # Ceiling division

    return APIResponse(
        success=True,
        message="Prediction history retrieved.",
        data=PaginatedResponse(
            items=items,
            total=count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


# ──────────────────────────────────────────────
# GET /predictions/{prediction_id} — Detail
# ──────────────────────────────────────────────
@router.get(
    "/{prediction_id}",
    response_model=APIResponse[PredictionResponse],
    summary="Get Prediction Detail",
    description=(
        "Retrieve the full details of a specific prediction, including SHAP breakdown, "
        "similar vehicles, and recommendations."
    ),
)
async def get_prediction_detail(
    prediction_id: uuid.UUID,
    current_user: ActiveUser,
    db: DBSession,
) -> APIResponse[PredictionResponse]:
    """
    Retrieve full prediction details for the authenticated user.

    Returns 404 if the prediction does not belong to the requesting user.
    """
    service = PredictionService(db)
    result = await service.get_prediction_detail(prediction_id, current_user.id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Prediction not found.",
                "error_code": "PREDICTION_NOT_FOUND",
            },
        )

    return APIResponse(
        success=True,
        message="Prediction details retrieved.",
        data=result,
    )


# ──────────────────────────────────────────────
# GET /predictions/{prediction_id}/report — Download PDF
# ──────────────────────────────────────────────
@router.get(
    "/{prediction_id}/report",
    summary="Download PDF Report",
    description="Generates and returns a PDF valuation report for the prediction.",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the PDF file.",
        },
    },
)
async def download_prediction_report(
    prediction_id: uuid.UUID,
    current_user: ActiveUser,
    db: DBSession,
):
    from fastapi import Response
    from app.services.report_service import ReportService
    
    service = ReportService(db)
    pdf_bytes = await service.generate_prediction_report(prediction_id, current_user.id)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="autoworth_report_{prediction_id}.pdf"'
        }
    )


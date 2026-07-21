"""
AutoWorth AI — ML Service

Singleton-style service layer wrapping the MLPipeline, SHAPExplainer,
and SimilarityService. Caches the active model in memory to avoid
repeated disk I/O on every prediction request.

Layer: Service Layer
Dependencies: MLPipeline, SHAPExplainer, SimilarityService, MLModelRepository
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.ml.explainer import SHAPExplainer
from app.ml.pipeline import MLPipeline
from app.ml.similarity import SimilarityService
from app.models.ml_model import AlgorithmType, ModelStatus, ModelVersion

logger = logging.getLogger(__name__)


class MLService:
    """
    Manages the active ML model lifecycle:
    - Loading artifacts from disk into memory (cached after first load)
    - Running training pipelines triggered by admins
    - Serving predictions with SHAP explanations and similar vehicles

    This class is designed to be used as a per-request dependency via
    FastAPI's Depends(), while the model cache lives on the app state.
    """

    # Class-level cache shared across all instances (app lifetime)
    _cached_version_id: str | None = None
    _cached_pipeline: MLPipeline | None = None
    _cached_explainer: SHAPExplainer | None = None
    _cached_similarity: SimilarityService | None = None

    def __init__(self) -> None:
        self._settings = get_settings()
        self._artifacts_dir = Path(self._settings.MODEL_ARTIFACTS_DIR)

    # ──────────────────────────────────────────────
    # Model Loading / Cache
    # ──────────────────────────────────────────────
    async def load_active_model(self, db: AsyncSession) -> ModelVersion | None:
        """
        Load the active model version from the database and warm the artifact cache.

        Called at application startup (lifespan) and before any prediction
        if the cache is cold or has been invalidated (e.g., after activation).

        Returns:
            The active ModelVersion ORM object, or None if no active model exists.
        """
        from app.repositories.ml_model_repository import MLModelRepository

        repo = MLModelRepository(db)
        active_version = await repo.get_active_version()

        if active_version is None:
            logger.warning(
                "⚠️  [MLService] No active model version found. "
                "Train and activate a model via /api/v1/admin/models/train."
            )
            return None

        version_id = str(active_version.id)

        if MLService._cached_version_id == version_id:
            logger.debug("✅ [MLService] Model cache hit (version=%s)", version_id)
            return active_version

        # Load artifacts into cache
        await self._load_artifacts(active_version)
        MLService._cached_version_id = version_id
        logger.info("🔥 [MLService] Model cache warmed (version=%s)", version_id)
        return active_version

    async def _load_artifacts(self, version: ModelVersion) -> None:
        """Deserialize model + preprocessor + KNN artifacts from disk."""
        model_path = Path(version.model_artifact_path)
        preprocessor_path = Path(version.preprocessor_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found at: {model_path}. "
                "Re-train the model to regenerate artifacts."
            )

        # Pipeline (holds the fitted model)
        pipeline = MLPipeline(self._artifacts_dir)
        MLService._cached_pipeline = pipeline

        # SHAP Explainer
        explainer = SHAPExplainer(model_path, preprocessor_path)
        MLService._cached_explainer = explainer

        # KNN Similarity Service
        knn_path = model_path.parent / "knn_index.joblib"
        similarity = SimilarityService()
        if knn_path.exists():
            try:
                similarity.load(knn_path)
            except Exception as exc:
                logger.warning("[MLService] KNN index failed to load: %s", exc)
        MLService._cached_similarity = similarity

    def invalidate_cache(self) -> None:
        """Force-reload on next prediction (called after model activation)."""
        MLService._cached_version_id = None
        MLService._cached_pipeline = None
        MLService._cached_explainer = None
        MLService._cached_similarity = None
        logger.info("🔄 [MLService] Model cache invalidated.")

    # ──────────────────────────────────────────────
    # Training
    # ──────────────────────────────────────────────
    async def run_training(
        self,
        dataset_path: Path,
        version_tag: str,
        db: AsyncSession,
        algorithm_hint: AlgorithmType | None = None,
        dataset_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute the full offline training pipeline and persist metrics to the DB.

        Steps:
        1. Create MLModel + ModelVersion(status=TRAINING) records.
        2. Run MLPipeline.train().
        3. Update ModelVersion with final metrics + status=TRAINED.

        Note: Model activation is a separate admin action (POST /activate).

        Returns:
            Training metrics dict from MLPipeline.train().
        """
        from app.repositories.ml_model_repository import MLModelRepository

        repo = MLModelRepository(db)

        # Determine best algo from pipeline output (not known upfront)
        # Use a placeholder; updated after training completes.
        placeholder_algorithm = algorithm_hint or AlgorithmType.XGBOOST

        logger.info(
            "🏋️  [MLService] Starting training pipeline (version=%s)", version_tag
        )

        # Create DB records for this training run
        ml_model, model_version = await repo.create_model_and_version(
            algorithm=placeholder_algorithm,
            version_tag=version_tag,
            dataset_id=dataset_id,
        )
        await db.commit()

        try:
            pipeline = MLPipeline(self._artifacts_dir)
            metrics = await pipeline.train(dataset_path, version_tag)

            # Map the winning algorithm name to the enum
            algo_map = {
                "Linear Regression": AlgorithmType.LINEAR_REGRESSION,
                "Decision Tree": AlgorithmType.DECISION_TREE,
                "Random Forest": AlgorithmType.RANDOM_FOREST,
                "XGBoost": AlgorithmType.XGBOOST,
            }
            actual_algorithm = algo_map.get(
                metrics.get("algorithm", ""), AlgorithmType.XGBOOST
            )

            # Update the ML model with the actual winning algorithm
            ml_model.algorithm = actual_algorithm
            db.add(ml_model)

            # Update metrics on the ModelVersion
            await repo.update_version_metrics(
                version_id=model_version.id,
                metrics={
                    "r2_score": metrics["r2_score"],
                    "rmse": metrics["rmse"],
                    "mae": metrics["mae"],
                    "cross_val_score": metrics["cross_val_score"],
                    "training_time_seconds": metrics["training_time_seconds"],
                    "training_samples": metrics["training_samples"],
                    "model_artifact_path": metrics["model_artifact_path"],
                    "preprocessor_path": metrics["preprocessor_path"],
                    "status": ModelStatus.TRAINED,
                    "notes": (
                        "⚠️ R² below target threshold (0.90) — low confidence"
                        if metrics.get("low_confidence")
                        else None
                    ),
                },
            )
            await db.commit()

            logger.info(
                "✅ [MLService] Training complete — R²=%.4f, RMSE=%.0f",
                metrics["r2_score"],
                metrics["rmse"],
            )
            metrics["model_version_id"] = str(model_version.id)
            return metrics

        except Exception as exc:
            logger.exception("[MLService] Training failed: %s", exc)
            await repo.update_version_metrics(
                version_id=model_version.id,
                metrics={"status": ModelStatus.FAILED, "notes": str(exc)},
            )
            await db.commit()
            raise

    # ──────────────────────────────────────────────
    # Prediction
    # ──────────────────────────────────────────────
    async def run_prediction(
        self,
        features: dict[str, Any],
        active_version: ModelVersion,
    ) -> dict[str, Any]:
        """
        Run a full prediction: price estimate + SHAP explanation + similar vehicles.

        Args:
            features: Raw feature dict from PredictionRequest (resolved names).
            active_version: The active ModelVersion ORM object.

        Returns:
            dict with: estimated_price, confidence_score, confidence_warning,
                       price_range_min, price_range_max, shap_features,
                       similar_vehicles, base_value
        """
        if MLService._cached_pipeline is None:
            raise RuntimeError(
                "Model not loaded. Call load_active_model() first."
            )

        pipeline = MLService._cached_pipeline
        explainer = MLService._cached_explainer
        similarity = MLService._cached_similarity

        model_path = Path(active_version.model_artifact_path)
        preprocessor_path = Path(active_version.preprocessor_path)

        # Step 1: Price prediction
        pred_result = await pipeline.predict(features, model_path, preprocessor_path)
        estimated_price = pred_result["estimated_price"]
        preprocessed_input: np.ndarray = pred_result["preprocessed_input"]

        # Step 2: SHAP explanation
        shap_result: dict[str, Any] = {}
        if explainer is not None:
            try:
                shap_result = explainer.explain(preprocessed_input, estimated_price)
            except Exception as exc:
                logger.warning("[MLService] SHAP explanation failed: %s", exc)
                shap_result = {
                    "shap_features": [],
                    "confidence_score": 70.0,
                    "confidence_warning": "Explainability temporarily unavailable.",
                    "price_range_min": pred_result["price_range_min"],
                    "price_range_max": pred_result["price_range_max"],
                    "base_value": 0.0,
                }
        else:
            shap_result = {
                "shap_features": [],
                "confidence_score": pred_result["confidence_score"],
                "confidence_warning": None,
                "price_range_min": pred_result["price_range_min"],
                "price_range_max": pred_result["price_range_max"],
                "base_value": 0.0,
            }

        # Step 3: Similar vehicles
        similar_vehicles: list[dict[str, Any]] = []
        if similarity is not None and similarity.is_loaded:
            try:
                similar_vehicles = similarity.find_similar(preprocessed_input, n=5)
            except Exception as exc:
                logger.warning("[MLService] Similarity search failed: %s", exc)

        return {
            "estimated_price": estimated_price,
            "confidence_score": shap_result.get("confidence_score", 80.0),
            "confidence_warning": shap_result.get("confidence_warning"),
            "price_range_min": shap_result.get(
                "price_range_min", pred_result["price_range_min"]
            ),
            "price_range_max": shap_result.get(
                "price_range_max", pred_result["price_range_max"]
            ),
            "base_value": shap_result.get("base_value", 0.0),
            "shap_features": shap_result.get("shap_features", []),
            "similar_vehicles": similar_vehicles,
        }

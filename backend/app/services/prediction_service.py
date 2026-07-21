"""
AutoWorth AI — Prediction Service

Business logic for vehicle price predictions.
Orchestrates the end-to-end prediction workflow.

Layer: Business Logic Layer
Dependencies: VehicleRepository, PredictionRepository, MLService
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import FairPriceStatus, Prediction
from app.models.recommendation import Recommendation, RecommendationPriority
from app.models.shap_result import ShapResult
from app.models.vehicle import (
    FuelType,
    InsuranceStatus,
    OwnerType,
    SellerType,
    TransmissionType,
    Vehicle,
    VehicleCategory,
)
from app.repositories.ml_model_repository import MLModelRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.prediction import (
    PredictionListItem,
    PredictionRequest,
    PredictionResponse,
    RecommendationResponse,
    ShapFeatureResponse,
    SimilarVehicleResponse,
)
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)

# Depreciation lookup (rough %-per-year for Indian used car market)
_DEPRECIATION_RATES: dict[int, float] = {
    1: 15.0, 2: 20.0, 3: 25.0, 4: 30.0, 5: 35.0,
}
_MAX_DEPRECIATION = 50.0  # Cap at 50% for very old vehicles


class PredictionService:
    """
    Orchestrates the end-to-end prediction workflow.

    Responsibilities:
    1. Resolve Brand, CarModel, City names from FK IDs.
    2. Create and persist a Vehicle record.
    3. Load the active ModelVersion via MLModelRepository.
    4. Run MLService.run_prediction() → price + SHAP + similar vehicles.
    5. Compute FairPriceStatus (vs. median of similar vehicles).
    6. Generate rule-based Recommendations from SHAP top features.
    7. Persist Prediction, ShapResult[], Recommendation[] in one transaction.
    8. Return structured PredictionResponse.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._prediction_repo = PredictionRepository(db)
        self._vehicle_repo = VehicleRepository(db)
        self._ml_model_repo = MLModelRepository(db)
        self._ml_service = MLService()

    # ──────────────────────────────────────────────
    # Public: Create Prediction
    # ──────────────────────────────────────────────
    async def create_prediction(
        self,
        user_id: uuid.UUID,
        data: PredictionRequest,
    ) -> PredictionResponse:
        """
        Run the full prediction pipeline and persist all results.

        Raises:
            RuntimeError: If no active model is available.
        """
        start_time = time.perf_counter()

        # ── Step 1: Load active model ─────────────────────────
        active_version = await self._ml_service.load_active_model(self._db)
        if active_version is None:
            raise RuntimeError(
                "No active model is available for predictions. "
                "An administrator must train and activate a model first."
            )

        # ── Step 2: Resolve taxonomy names ───────────────────
        brand_name = await self._vehicle_repo.get_brand_name(data.brand_id)
        model_name = await self._vehicle_repo.get_model_name(data.car_model_id)
        city_name = await self._vehicle_repo.get_city_name(data.city_id)

        # ── Step 3: Create Vehicle record ─────────────────────
        vehicle = await self._vehicle_repo.create_vehicle(
            brand_id=data.brand_id,
            car_model_id=data.car_model_id,
            variant_id=data.variant_id,
            city_id=data.city_id,
            manufacturing_year=data.manufacturing_year,
            fuel_type=FuelType(data.fuel_type),
            transmission=TransmissionType(data.transmission),
            owner_type=OwnerType(data.owner_type),
            seller_type=SellerType(data.seller_type),
            category=VehicleCategory(data.category),
            kilometers_driven=data.kilometers_driven,
            engine_cc=data.engine_cc,
            mileage_kmpl=data.mileage_kmpl,
            seats=data.seats,
            max_power_bhp=data.max_power_bhp,
            insurance_status=InsuranceStatus(data.insurance_status),
        )

        # ── Step 4: Build feature dict for ML ────────────────
        features = {
            "brand": brand_name,
            "model": model_name,
            "city": city_name,
            "manufacturing_year": data.manufacturing_year,
            "fuel_type": data.fuel_type,
            "transmission": data.transmission,
            "owner_type": data.owner_type,
            "seller_type": data.seller_type,
            "category": data.category,
            "kilometers_driven": data.kilometers_driven,
            "engine_cc": data.engine_cc,
            "mileage_kmpl": data.mileage_kmpl,
            "seats": data.seats,
            "max_power_bhp": data.max_power_bhp,
        }

        # ── Step 5: Run ML prediction ─────────────────────────
        ml_result = await self._ml_service.run_prediction(features, active_version)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "⚡ [PredictionService] Inference completed in %.0fms", elapsed_ms
        )

        estimated_price = ml_result["estimated_price"]
        confidence_score = ml_result["confidence_score"]
        price_range_min = ml_result["price_range_min"]
        price_range_max = ml_result["price_range_max"]
        shap_features = ml_result["shap_features"]
        similar_vehicles = ml_result["similar_vehicles"]
        confidence_warning = ml_result.get("confidence_warning")

        # ── Step 6: Compute FairPriceStatus ──────────────────
        fair_price_status = self._compute_fair_price_status(
            estimated_price, similar_vehicles
        )

        # ── Step 7: Compute depreciation ─────────────────────
        import datetime
        vehicle_age = datetime.datetime.now().year - data.manufacturing_year
        depreciation_pct = min(
            _DEPRECIATION_RATES.get(vehicle_age, _MAX_DEPRECIATION),
            _MAX_DEPRECIATION,
        )

        # ── Step 8: Persist Prediction record ────────────────
        prediction_id = uuid.uuid4()
        prediction = Prediction(
            id=prediction_id,
            estimated_price=estimated_price,
            confidence_score=confidence_score / 100.0,  # Store as 0–1
            price_range_min=price_range_min,
            price_range_max=price_range_max,
            fair_price_status=fair_price_status,
            depreciation_percent=depreciation_pct,
            showroom_price=None,
            shap_values={
                "features": shap_features,
                "base_value": ml_result.get("base_value", 0.0),
            },
            similar_vehicles=similar_vehicles,
            user_id=user_id,
            vehicle_id=vehicle.id,
            model_version_id=active_version.id,
        )
        self._db.add(prediction)
        await self._db.flush()

        # ── Step 9: Persist ShapResult rows ──────────────────
        shap_orm_rows = self._build_shap_rows(shap_features, prediction_id)
        self._db.add_all(shap_orm_rows)

        # ── Step 10: Generate & persist Recommendations ───────
        recommendations = self._generate_recommendations(
            shap_features, fair_price_status, confidence_score
        )
        rec_orm_rows = self._build_recommendation_rows(recommendations, prediction_id)
        self._db.add_all(rec_orm_rows)

        # Update prediction-time metric on ModelVersion
        avg_ms = (
            active_version.avg_prediction_time_ms or elapsed_ms
        )
        active_version.avg_prediction_time_ms = round(
            (avg_ms + elapsed_ms) / 2, 1
        )
        self._db.add(active_version)

        await self._db.commit()

        logger.info(
            "✅ [PredictionService] Prediction %s created — ₹%.0f (%.1f%% confidence)",
            prediction_id,
            estimated_price,
            confidence_score,
        )

        # ── Build response ────────────────────────────────────
        return self._build_response(
            prediction=prediction,
            shap_features=shap_features,
            similar_vehicles=similar_vehicles,
            recommendations=recommendations,
            confidence_warning=confidence_warning,
        )

    # ──────────────────────────────────────────────
    # Public: History
    # ──────────────────────────────────────────────
    async def get_user_history(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[PredictionListItem]:
        """Return a lightweight paginated list of a user's past predictions."""
        predictions = await self._prediction_repo.get_by_user(
            user_id, skip=skip, limit=limit
        )
        return [
            PredictionListItem(
                id=p.id,
                estimated_price=float(p.estimated_price),
                confidence_score=float(p.confidence_score) * 100,
                fair_price_status=p.fair_price_status.value,
                created_at=p.created_at,
            )
            for p in predictions
        ]

    async def get_prediction_detail(
        self, prediction_id: uuid.UUID, user_id: uuid.UUID
    ) -> PredictionResponse | None:
        """Return full prediction details (verifies user ownership)."""
        prediction = await self._prediction_repo.get_with_full_details(prediction_id)
        if prediction is None or prediction.user_id != user_id:
            return None

        shap_features = (
            (prediction.shap_values or {}).get("features", [])
            if prediction.shap_values
            else []
        )
        similar_vehicles = prediction.similar_vehicles or []
        recommendations_raw = [
            {
                "title": r.title,
                "description": r.description,
                "priority": r.priority.value,
                "display_order": r.display_order,
            }
            for r in prediction.recommendations
        ]

        return self._build_response(
            prediction=prediction,
            shap_features=shap_features,
            similar_vehicles=similar_vehicles,
            recommendations=recommendations_raw,
            confidence_warning=None,
        )

    # ──────────────────────────────────────────────
    # Internal Helpers
    # ──────────────────────────────────────────────
    def _compute_fair_price_status(
        self,
        estimated_price: float,
        similar_vehicles: list[dict[str, Any]],
    ) -> FairPriceStatus:
        """
        Compare estimated price against the median price of similar vehicles.

        Thresholds:
            < -15%  → Below Market
            ±15%    → Fair
            > +15%  → Above Market
        """
        if not similar_vehicles:
            return FairPriceStatus.FAIR

        prices = [v.get("selling_price", 0.0) for v in similar_vehicles if v.get("selling_price", 0) > 0]
        if not prices:
            return FairPriceStatus.FAIR

        import statistics
        median_price = statistics.median(prices)
        deviation_pct = ((estimated_price - median_price) / median_price) * 100

        if deviation_pct < -15:
            return FairPriceStatus.BELOW_MARKET
        elif deviation_pct > 15:
            return FairPriceStatus.ABOVE_MARKET
        return FairPriceStatus.FAIR

    def _build_shap_rows(
        self,
        shap_features: list[dict[str, Any]],
        prediction_id: uuid.UUID,
    ) -> list[ShapResult]:
        """Convert SHAP feature dicts into ShapResult ORM rows."""
        rows = []
        for feat in shap_features:
            rows.append(ShapResult(
                feature_name=feat.get("feature_name", ""),
                feature_value=feat.get("feature_value"),
                shap_value=float(feat.get("shap_value", 0.0)),
                impact_direction=feat.get("impact_direction", "positive"),
                rank=int(feat.get("rank", 1)),
                human_readable_impact=feat.get("human_readable_impact"),
                prediction_id=prediction_id,
            ))
        return rows

    def _generate_recommendations(
        self,
        shap_features: list[dict[str, Any]],
        fair_price_status: FairPriceStatus,
        confidence_score: float,
    ) -> list[dict[str, Any]]:
        """
        Generate rule-based recommendations from SHAP insights.

        Rules:
        1. High mileage (negative SHAP) → suggest service records.
        2. Old vehicle (negative SHAP from age) → suggest refurbishment.
        3. Below market → good buying opportunity.
        4. Above market → negotiate hard.
        5. Low confidence → get professional assessment.
        """
        recs: list[dict[str, Any]] = []
        order = 1

        feature_map = {
            f.get("feature_name", "").lower(): f
            for f in shap_features
        }

        # Mileage recommendation
        km_feat = feature_map.get("kilometers driven")
        if km_feat and km_feat.get("impact_direction") == "negative":
            recs.append({
                "title": "High Mileage Impact",
                "description": (
                    "High kilometers driven has reduced this vehicle's value. "
                    "Providing full service history and recent maintenance records "
                    "can help justify the price to potential buyers."
                ),
                "priority": RecommendationPriority.HIGH.value,
                "display_order": order,
            })
            order += 1

        # Vehicle age recommendation
        age_feat = feature_map.get("vehicle age")
        if age_feat and age_feat.get("impact_direction") == "negative":
            recs.append({
                "title": "Age-Related Depreciation",
                "description": (
                    "The vehicle's age is contributing to a lower valuation. "
                    "A fresh paint job, interior refurbishment, or replaced tyres "
                    "can meaningfully improve perceived and actual resale value."
                ),
                "priority": RecommendationPriority.MEDIUM.value,
                "display_order": order,
            })
            order += 1

        # Fuel type insight
        fuel_feat = next(
            (f for k, f in feature_map.items() if "fuel type" in k), None
        )
        if fuel_feat and "diesel" in (fuel_feat.get("feature_name") or "").lower():
            recs.append({
                "title": "Diesel Premium",
                "description": (
                    "Diesel vehicles typically command a premium in the Indian market "
                    "due to better mileage. Highlight fuel efficiency figures in your listing."
                ),
                "priority": RecommendationPriority.LOW.value,
                "display_order": order,
            })
            order += 1

        # Market position recommendations
        if fair_price_status == FairPriceStatus.BELOW_MARKET:
            recs.append({
                "title": "Below Market Value — Buying Opportunity",
                "description": (
                    "This vehicle is priced below similar vehicles in the market. "
                    "This may indicate quick-sale motivation from the seller — "
                    "an excellent opportunity for buyers."
                ),
                "priority": RecommendationPriority.HIGH.value,
                "display_order": order,
            })
            order += 1
        elif fair_price_status == FairPriceStatus.ABOVE_MARKET:
            recs.append({
                "title": "Above Market Value — Negotiate",
                "description": (
                    "This vehicle is priced above similar market comparables. "
                    "Use the provided similar vehicles as negotiation benchmarks "
                    "to secure a better deal."
                ),
                "priority": RecommendationPriority.HIGH.value,
                "display_order": order,
            })
            order += 1

        # Confidence warning recommendation
        if confidence_score < 60.0:
            recs.append({
                "title": "Seek Professional Valuation",
                "description": (
                    "The AI confidence for this valuation is below our threshold. "
                    "This vehicle's specifications are uncommon in our training data. "
                    "We recommend a certified mechanic inspection and a dealer appraisal "
                    "for a more accurate price."
                ),
                "priority": RecommendationPriority.HIGH.value,
                "display_order": order,
            })

        return recs

    def _build_recommendation_rows(
        self,
        recommendations: list[dict[str, Any]],
        prediction_id: uuid.UUID,
    ) -> list[Recommendation]:
        """Convert recommendation dicts into Recommendation ORM rows."""
        rows = []
        for rec in recommendations:
            priority_val = rec.get("priority", "medium")
            try:
                priority = RecommendationPriority(priority_val)
            except ValueError:
                priority = RecommendationPriority.MEDIUM

            rows.append(Recommendation(
                title=rec["title"],
                description=rec["description"],
                priority=priority,
                display_order=rec.get("display_order", 1),
                prediction_id=prediction_id,
            ))
        return rows

    def _build_response(
        self,
        prediction: Prediction,
        shap_features: list[dict[str, Any]],
        similar_vehicles: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
        confidence_warning: str | None,
    ) -> PredictionResponse:
        """Assemble the final PredictionResponse from ORM + ML data."""
        shap_response = [
            ShapFeatureResponse(
                feature_name=f.get("feature_name", ""),
                raw_feature_name=f.get("raw_feature_name"),
                feature_value=f.get("feature_value"),
                shap_value=float(f.get("shap_value", 0.0)),
                impact_direction=f.get("impact_direction", "positive"),
                rank=int(f.get("rank", 1)),
                human_readable_impact=f.get("human_readable_impact"),
                impact_percentage=f.get("impact_percentage"),
            )
            for f in shap_features
        ]

        similar_response = [
            SimilarVehicleResponse(
                brand=v.get("brand", ""),
                model=v.get("model", ""),
                manufacturing_year=int(v.get("manufacturing_year", 0)),
                fuel_type=str(v.get("fuel_type", "")),
                transmission=str(v.get("transmission", "")),
                owner_type=str(v.get("owner_type", "")),
                kilometers_driven=int(v.get("kilometers_driven", 0)),
                selling_price=float(v.get("selling_price", 0.0)),
                similarity_score=float(v.get("similarity_score", 0.0)),
            )
            for v in similar_vehicles
        ]

        rec_response = [
            RecommendationResponse(
                title=r["title"],
                description=r["description"],
                priority=r.get("priority", "medium"),
                display_order=r.get("display_order", 1),
            )
            for r in recommendations
        ]

        # Confidence stored as 0–1 in DB; expose as 0–100 in API
        conf_score = float(prediction.confidence_score)
        if conf_score <= 1.0:
            conf_score = conf_score * 100.0

        return PredictionResponse(
            id=prediction.id,
            estimated_price=float(prediction.estimated_price),
            confidence_score=round(conf_score, 1),
            confidence_warning=confidence_warning,
            price_range_min=float(prediction.price_range_min),
            price_range_max=float(prediction.price_range_max),
            fair_price_status=prediction.fair_price_status.value,
            depreciation_percent=prediction.depreciation_percent,
            showroom_price=(
                float(prediction.showroom_price)
                if prediction.showroom_price
                else None
            ),
            shap_results=shap_response,
            similar_vehicles=similar_response,
            recommendations=rec_response,
            cv_damage_detected=prediction.cv_damage_detected,
            cv_damage_severity=prediction.cv_damage_severity,
            cv_repair_cost_estimate=prediction.cv_repair_cost_estimate,
            is_pdf_generated=prediction.is_pdf_generated,
            pdf_url=prediction.pdf_url,
            created_at=prediction.created_at,
        )

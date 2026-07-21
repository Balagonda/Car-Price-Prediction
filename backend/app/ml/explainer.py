"""
AutoWorth AI — SHAP Explainer

Generates human-readable feature contribution explanations for each prediction.
Uses TreeExplainer for tree-based models, KernelExplainer for linear ones.

Layer: ML Layer
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import shap

logger = logging.getLogger(__name__)

# Confidence threshold below which a warning is surfaced to the user
CONFIDENCE_WARNING_THRESHOLD = 60.0

# Human-readable display names for engineered / encoded feature prefixes
FEATURE_DISPLAY_MAP: dict[str, str] = {
    "vehicle_age": "Vehicle Age",
    "log_km_driven": "Kilometers Driven",
    "engine_cc": "Engine Displacement",
    "mileage_kmpl": "Fuel Efficiency",
    "max_power_bhp": "Engine Power",
    "seats": "Seating Capacity",
    "cat__brand_": "Brand",
    "cat__model_": "Model",
    "cat__fuel_type_": "Fuel Type",
    "cat__transmission_": "Transmission",
    "cat__owner_type_": "Owner History",
    "cat__seller_type_": "Seller Type",
    "cat__category_": "Vehicle Category",
    "cat__city_": "City",
    "num__": "",   # numeric transformer prefix — stripped
}

# Tree-based model class names that support TreeExplainer
TREE_BASED_TYPES = (
    "RandomForestRegressor",
    "XGBRegressor",
    "XGBClassifier",
    "DecisionTreeRegressor",
    "GradientBoostingRegressor",
    "LGBMRegressor",
)


class SHAPExplainer:
    """
    Generates SHAP feature importance explanations.

    For each prediction:
    1. Load the trained model and preprocessor from joblib artifacts.
    2. Compute SHAP values using TreeExplainer (for tree models)
       or LinearExplainer / KernelExplainer (for linear models).
    3. Rank features by absolute SHAP value.
    4. Generate human-readable impact strings:
       - "Mileage reduced vehicle value by ₹35,000"
       - "Automatic transmission increased value by ₹45,000"
    5. Compute a confidence score from SHAP value variance.
    6. Compute fair price range (±1σ of the SHAP distribution).
    """

    def __init__(self, model_artifact_path: Path, preprocessor_path: Path) -> None:
        self.model_artifact_path = model_artifact_path
        self.preprocessor_path = preprocessor_path
        self._model: Any = None
        self._preprocessor: Any = None
        self._explainer: Any = None
        self._feature_names: list[str] = []
        self._background_data: np.ndarray | None = None

    # ──────────────────────────────────────────────
    # Public
    # ──────────────────────────────────────────────
    def explain(
        self,
        preprocessed_input: np.ndarray,
        estimated_price: float,
        top_n: int = 10,
    ) -> dict[str, Any]:
        """
        Compute SHAP explanation for a single preprocessed feature vector.

        Args:
            preprocessed_input: 2D numpy array (1, n_features) from pipeline preprocessor.
            estimated_price: The predicted price in ₹ (used for % impact calculation).
            top_n: Number of top features to include in the response.

        Returns:
            dict with keys:
                - shap_features: list of feature contribution dicts
                - confidence_score: float (0–100)
                - confidence_warning: str | None
                - price_range_min: float
                - price_range_max: float
                - base_value: float (SHAP baseline / expected price)
        """
        self._ensure_loaded()

        shap_values = self._compute_shap_values(preprocessed_input)

        # shap_values shape: (1, n_features) — flatten to 1D
        if shap_values.ndim > 1:
            shap_values_1d = shap_values[0]
        else:
            shap_values_1d = shap_values

        base_value = self._get_base_value()

        # Build per-feature contribution list
        features = self._build_feature_contributions(
            shap_values_1d, estimated_price, top_n
        )

        # Confidence score
        confidence_score, confidence_warning = self._compute_confidence(
            shap_values_1d, base_value, estimated_price
        )

        # Fair price range: ±1σ of absolute SHAP values, scaled
        shap_std = float(np.std(np.abs(shap_values_1d)))
        price_range_min = max(estimated_price - shap_std, 0.0)
        price_range_max = estimated_price + shap_std

        # Clamp to ±30% of estimated price
        max_deviation = estimated_price * 0.30
        price_range_min = max(price_range_min, estimated_price - max_deviation)
        price_range_max = min(price_range_max, estimated_price + max_deviation)

        return {
            "shap_features": features,
            "confidence_score": round(confidence_score, 1),
            "confidence_warning": confidence_warning,
            "price_range_min": round(price_range_min, 2),
            "price_range_max": round(price_range_max, 2),
            "base_value": round(base_value, 2),
        }

    # ──────────────────────────────────────────────
    # Internal: Lazy Loading
    # ──────────────────────────────────────────────
    def _ensure_loaded(self) -> None:
        """Lazy-load model and preprocessor from disk on first call."""
        if self._model is None:
            logger.info("📂 [SHAP] Loading model artifact: %s", self.model_artifact_path)
            self._model = joblib.load(self.model_artifact_path)
            self._preprocessor = joblib.load(self.preprocessor_path)

            # Try to load feature names saved by pipeline
            feature_names_path = self.model_artifact_path.parent / "feature_names.joblib"
            if feature_names_path.exists():
                self._feature_names = joblib.load(feature_names_path)
            else:
                self._feature_names = []

            self._build_explainer()

    def _build_explainer(self) -> None:
        """Construct the appropriate SHAP explainer based on model type."""
        model_type = type(self._model).__name__
        logger.info("🔍 [SHAP] Building explainer for %s", model_type)

        if model_type in TREE_BASED_TYPES:
            # TreeExplainer: fast + exact for tree-based models
            self._explainer = shap.TreeExplainer(
                self._model,
                feature_perturbation="tree_path_dependent",
            )
        else:
            # LinearExplainer for linear regression
            try:
                self._explainer = shap.LinearExplainer(
                    self._model,
                    masker=shap.maskers.Independent(
                        np.zeros((1, self._get_n_features()))
                    ),
                )
            except Exception:
                logger.warning(
                    "[SHAP] LinearExplainer failed — falling back to KernelExplainer"
                )
                background = np.zeros((1, self._get_n_features()))
                self._explainer = shap.KernelExplainer(
                    self._model.predict, background
                )

    def _get_n_features(self) -> int:
        """Infer feature count from model or fallback."""
        if hasattr(self._model, "n_features_in_"):
            return int(self._model.n_features_in_)
        if self._feature_names:
            return len(self._feature_names)
        return 50  # safe fallback

    # ──────────────────────────────────────────────
    # Internal: SHAP Computation
    # ──────────────────────────────────────────────
    def _compute_shap_values(self, X: np.ndarray) -> np.ndarray:
        """Compute raw SHAP values for input X."""
        sv = self._explainer.shap_values(X)
        # XGBoost / some models return Explanation objects
        if hasattr(sv, "values"):
            sv = sv.values
        return np.array(sv)

    def _get_base_value(self) -> float:
        """Extract the SHAP base value (expected model output)."""
        ev = self._explainer.expected_value
        if isinstance(ev, (list, np.ndarray)):
            return float(ev[0])
        return float(ev)

    # ──────────────────────────────────────────────
    # Internal: Feature Contributions
    # ──────────────────────────────────────────────
    def _build_feature_contributions(
        self,
        shap_values: np.ndarray,
        estimated_price: float,
        top_n: int,
    ) -> list[dict[str, Any]]:
        """
        Sort features by absolute SHAP value and generate human-readable strings.
        """
        n = len(shap_values)
        feature_names = self._feature_names if self._feature_names else [
            f"feature_{i}" for i in range(n)
        ]

        # Pad or truncate feature names to match shap_values length
        if len(feature_names) < n:
            feature_names = feature_names + [
                f"feature_{i}" for i in range(len(feature_names), n)
            ]
        elif len(feature_names) > n:
            feature_names = feature_names[:n]

        pairs = list(zip(feature_names, shap_values.tolist()))

        # Sort by absolute SHAP value descending
        pairs.sort(key=lambda p: abs(p[1]), reverse=True)

        contributions: list[dict[str, Any]] = []
        for rank, (raw_name, sv) in enumerate(pairs[:top_n], start=1):
            direction = "positive" if sv >= 0 else "negative"
            display_name = self._humanize_feature_name(raw_name)
            impact_rupees = abs(sv)
            human_readable = self._format_impact_string(
                display_name, sv, impact_rupees, direction
            )

            contributions.append({
                "feature_name": display_name,
                "raw_feature_name": raw_name,
                "shap_value": round(sv, 2),
                "impact_direction": direction,
                "rank": rank,
                "human_readable_impact": human_readable,
                "impact_percentage": round(
                    (impact_rupees / max(abs(estimated_price), 1)) * 100, 2
                ),
            })

        return contributions

    def _humanize_feature_name(self, raw_name: str) -> str:
        """Convert an internal feature name to a human-readable label."""
        # Handle OHE features like "cat__fuel_type_Diesel" → "Fuel Type: Diesel"
        for prefix, label in FEATURE_DISPLAY_MAP.items():
            if raw_name.startswith(prefix):
                suffix = raw_name[len(prefix):]
                if label:
                    return f"{label}: {suffix.replace('_', ' ').title()}" if suffix else label
                else:
                    return suffix.replace("_", " ").title()
        return raw_name.replace("_", " ").title()

    def _format_impact_string(
        self,
        feature_name: str,
        shap_value: float,
        impact_rupees: float,
        direction: str,
    ) -> str:
        """Generate a ₹-denominated human-readable impact string."""
        amount = self._format_rupees(impact_rupees)
        if direction == "positive":
            return f"{feature_name} increased vehicle value by {amount}"
        else:
            return f"{feature_name} reduced vehicle value by {amount}"

    @staticmethod
    def _format_rupees(amount: float) -> str:
        """Format a value as Indian Rupees with lakh/crore notation."""
        if amount >= 10_000_000:
            return f"₹{amount / 10_000_000:.2f} Cr"
        elif amount >= 100_000:
            return f"₹{amount / 100_000:.2f} L"
        elif amount >= 1_000:
            return f"₹{amount / 1_000:.1f}K"
        else:
            return f"₹{amount:.0f}"

    # ──────────────────────────────────────────────
    # Internal: Confidence Score
    # ──────────────────────────────────────────────
    def _compute_confidence(
        self,
        shap_values: np.ndarray,
        base_value: float,
        estimated_price: float,
    ) -> tuple[float, str | None]:
        """
        Compute a confidence score (0–100%) based on SHAP value stability.

        Formula:
            confidence = 100 × (1 − std(|shap_values|) / max(|estimated_price|, 1))
        Clamped to [0, 100].
        A score below CONFIDENCE_WARNING_THRESHOLD triggers a warning.
        """
        shap_std = float(np.std(np.abs(shap_values)))
        denominator = max(abs(estimated_price), 1.0)
        raw = 100.0 * (1.0 - shap_std / denominator)
        confidence = float(np.clip(raw, 0.0, 100.0))

        # Secondary penalty: if SHAP values have very high max/std ratio
        shap_abs = np.abs(shap_values)
        if shap_abs.max() > 0:
            concentration = float(shap_abs.max() / (shap_abs.sum() + 1e-9))
            if concentration > 0.85:
                # Single dominant feature — reduce confidence
                confidence = min(confidence, 72.0)

        warning: str | None = None
        if confidence < CONFIDENCE_WARNING_THRESHOLD:
            warning = (
                "⚠️ Confidence is low for this valuation. "
                "The vehicle's specifications are unusual or outside typical market patterns. "
                "Treat this estimate as a broad range rather than a precise value."
            )

        return confidence, warning

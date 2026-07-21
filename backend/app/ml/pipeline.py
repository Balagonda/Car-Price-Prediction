"""
AutoWorth AI — ML Training Pipeline

Offline training pipeline for vehicle price prediction models.
Triggered by Admin → POST /api/v1/admin/models/train

Layer: ML Layer
"""

from __future__ import annotations

import logging
import time
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import optuna
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

warnings.filterwarnings("ignore", category=UserWarning)
optuna.logging.set_verbosity(optuna.logging.WARNING)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
TARGET_COLUMN = "selling_price"
REQUIRED_COLUMNS = {
    "brand", "model", "manufacturing_year", "fuel_type",
    "transmission", "owner_type", "seller_type", "kilometers_driven",
    TARGET_COLUMN,
}
OPTIONAL_COLUMNS = {
    "engine_cc", "mileage_kmpl", "max_power_bhp", "seats", "city", "category",
}

CATEGORICAL_FEATURES = [
    "brand", "model", "fuel_type", "transmission",
    "owner_type", "seller_type", "category", "city",
]
NUMERIC_FEATURES = [
    "vehicle_age", "log_km_driven", "engine_cc",
    "mileage_kmpl", "max_power_bhp", "seats",
]

OPTUNA_TRIALS = 30
CV_FOLDS = 5
R2_TARGET = 0.90


class MLPipeline:
    """
    Automated ML training and inference pipeline.

    Workflow:
    1.  Load and merge dataset CSV(s)
    2.  Validate schema and required columns
    3.  Clean: remove duplicates, handle missing values
    4.  Feature engineering: vehicle_age, log_km_driven, depreciation features
    5.  Encode categorical variables (Brand, Fuel, City, etc.)
    6.  Scale numerical features (KMs driven, Engine CC, Year)
    7.  Train all algorithms: LinearRegression, DecisionTree, RandomForest, XGBoost
    8.  Cross-validation and Optuna hyperparameter tuning (RF + XGB)
    9.  Evaluate: R², RMSE, MAE
    10. Select and save the best model artifact via joblib
    11. Persist preprocessor artifact separately for exact feature matching
    """

    def __init__(self, artifacts_dir: Path) -> None:
        self.artifacts_dir = artifacts_dir
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._preprocessor: ColumnTransformer | None = None
        self._model: Any = None
        self._knn: NearestNeighbors | None = None
        self._knn_records: list[dict[str, Any]] = []
        self._feature_names: list[str] = []

    # ──────────────────────────────────────────────
    # Public: Training
    # ──────────────────────────────────────────────
    async def train(self, dataset_path: Path, version_tag: str) -> dict[str, Any]:
        """
        Execute the full training pipeline and return evaluation metrics.

        Returns:
            dict with keys: r2_score, rmse, mae, cross_val_score,
                            training_time_seconds, training_samples,
                            model_artifact_path, preprocessor_path,
                            knn_artifact_path, low_confidence
        """
        start = time.perf_counter()
        version_dir = self.artifacts_dir / version_tag
        version_dir.mkdir(parents=True, exist_ok=True)

        logger.info("📦 [Pipeline] Loading dataset from %s", dataset_path)
        df = self._load_and_clean(dataset_path)
        logger.info("✅ [Pipeline] Cleaned dataset: %d rows", len(df))

        df = self._engineer_features(df)
        X, y = self._split_features_target(df)

        # Build preprocessor
        preprocessor = self._build_preprocessor(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.15, random_state=42
        )

        # Fit preprocessor on training data only
        X_train_proc = preprocessor.fit_transform(X_train)
        X_test_proc = preprocessor.transform(X_test)
        self._feature_names = self._get_feature_names(preprocessor, X)

        logger.info("🏋️  [Pipeline] Training all candidate models...")
        candidates = self._train_all_candidates(
            X_train_proc, y_train, X_test_proc, y_test
        )

        # Cross-validation scoring for top candidates
        best_algo, best_model, cv_mean = self._select_best_model(
            candidates, preprocessor, X, y
        )
        logger.info(
            "🏆 [Pipeline] Best model: %s  CV R²=%.4f", best_algo, cv_mean
        )

        # Final evaluation on held-out test set
        y_pred = best_model.predict(X_test_proc)
        final_r2 = float(r2_score(y_test, y_pred))
        final_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        final_mae = float(mean_absolute_error(y_test, y_pred))

        # Fit KNN similarity index on full processed dataset
        X_full_proc = preprocessor.transform(X)
        knn_records = self._build_knn_index(X_full_proc, df)

        # Persist artifacts
        model_path = version_dir / "model.joblib"
        preprocessor_path = version_dir / "preprocessor.joblib"
        knn_path = version_dir / "knn_index.joblib"
        feature_names_path = version_dir / "feature_names.joblib"

        joblib.dump(best_model, model_path)
        joblib.dump(preprocessor, preprocessor_path)
        joblib.dump({"knn": self._knn, "records": knn_records}, knn_path)
        joblib.dump(self._feature_names, feature_names_path)

        elapsed = time.perf_counter() - start
        logger.info("⏱️  [Pipeline] Training completed in %.1fs", elapsed)

        return {
            "algorithm": best_algo,
            "r2_score": final_r2,
            "rmse": final_rmse,
            "mae": final_mae,
            "cross_val_score": float(cv_mean),
            "training_time_seconds": round(elapsed, 2),
            "training_samples": len(df),
            "model_artifact_path": str(model_path),
            "preprocessor_path": str(preprocessor_path),
            "knn_artifact_path": str(knn_path),
            "low_confidence": cv_mean < R2_TARGET,
        }

    # ──────────────────────────────────────────────
    # Public: Inference
    # ──────────────────────────────────────────────
    async def predict(
        self,
        features: dict[str, Any],
        model_artifact_path: Path,
        preprocessor_path: Path,
    ) -> dict[str, Any]:
        """
        Run inference on a single vehicle feature vector.

        Returns:
            dict with keys: estimated_price, confidence_score (0–100),
                            price_range_min, price_range_max, raw_shap_input
        """
        if self._model is None or self._preprocessor is None:
            self._model = joblib.load(model_artifact_path)
            self._preprocessor = joblib.load(preprocessor_path)

        input_df = self._build_inference_df(features)
        X_proc = self._preprocessor.transform(input_df)

        estimated_price = float(self._model.predict(X_proc)[0])
        estimated_price = max(estimated_price, 10_000.0)  # Floor at ₹10k

        # Confidence derived from prediction interval heuristic
        # (full SHAP-based score computed in explainer.py)
        confidence_score = 85.0  # Placeholder; explainer refines this

        margin = estimated_price * 0.12  # ±12% base range
        price_range_min = max(estimated_price - margin, 0.0)
        price_range_max = estimated_price + margin

        return {
            "estimated_price": round(estimated_price, 2),
            "confidence_score": confidence_score,
            "price_range_min": round(price_range_min, 2),
            "price_range_max": round(price_range_max, 2),
            "preprocessed_input": X_proc,  # Passed to SHAPExplainer
        }

    # ──────────────────────────────────────────────
    # Internal: Data Loading & Cleaning
    # ──────────────────────────────────────────────
    def _load_and_clean(self, dataset_path: Path) -> pd.DataFrame:
        """Load CSV, validate schema, clean duplicates and missing values."""
        df = pd.read_csv(dataset_path, low_memory=False)

        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Map common alternative column names
        rename_map = {
            "name": "model",
            "year": "manufacturing_year",
            "km_driven": "kilometers_driven",
            "seller_type": "seller_type",
            "fuel": "fuel_type",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Validate required columns
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"Dataset is missing required columns: {missing_cols}. "
                f"Found: {list(df.columns)}"
            )

        # Remove duplicate rows
        initial_len = len(df)
        df = df.drop_duplicates()

        # Drop rows with missing target
        df = df.dropna(subset=[TARGET_COLUMN])

        # Remove obvious outliers (price < ₹10k or > ₹10 crore)
        df = df[df[TARGET_COLUMN].between(10_000, 100_000_000)]

        # Remove negative or zero KMs
        df = df[df["kilometers_driven"] > 0]
        df = df[df["manufacturing_year"].between(1980, 2026)]

        cleaned = initial_len - len(df)
        logger.info("🧹 [Pipeline] Removed %d invalid/duplicate rows", cleaned)

        # Fill optional numeric columns with medians
        for col in ["engine_cc", "mileage_kmpl", "max_power_bhp", "seats"]:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())

        # Fill optional categorical columns
        for col in ["city", "category"]:
            if col not in df.columns:
                df[col] = "Unknown"
            else:
                df[col] = df[col].fillna("Unknown")

        # Standardize categorical values
        for col in CATEGORICAL_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.title()

        return df.reset_index(drop=True)

    # ──────────────────────────────────────────────
    # Internal: Feature Engineering
    # ──────────────────────────────────────────────
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived features that improve model performance."""
        current_year = pd.Timestamp.now().year
        df["vehicle_age"] = current_year - df["manufacturing_year"]
        df["log_km_driven"] = np.log1p(df["kilometers_driven"])

        # Ensure numeric columns exist with sensible defaults
        for col, default in [
            ("engine_cc", 1200.0),
            ("mileage_kmpl", 15.0),
            ("max_power_bhp", 80.0),
            ("seats", 5.0),
        ]:
            if col not in df.columns:
                df[col] = default

        return df

    def _split_features_target(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Separate feature matrix from target vector."""
        feature_cols = CATEGORICAL_FEATURES + NUMERIC_FEATURES
        # Only keep features that exist in the dataframe
        available = [c for c in feature_cols if c in df.columns]
        return df[available].copy(), df[TARGET_COLUMN].copy()

    # ──────────────────────────────────────────────
    # Internal: Preprocessor
    # ──────────────────────────────────────────────
    def _build_preprocessor(self, X: pd.DataFrame) -> ColumnTransformer:
        """Build a ColumnTransformer with OHE + StandardScaler."""
        cat_cols = [c for c in CATEGORICAL_FEATURES if c in X.columns]
        num_cols = [c for c in NUMERIC_FEATURES if c in X.columns]

        transformers: list[Any] = []

        if cat_cols:
            transformers.append((
                "cat",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                    drop="if_binary",
                ),
                cat_cols,
            ))

        if num_cols:
            transformers.append(("num", StandardScaler(), num_cols))

        return ColumnTransformer(transformers=transformers, remainder="drop")

    def _get_feature_names(
        self, preprocessor: ColumnTransformer, X: pd.DataFrame
    ) -> list[str]:
        """Extract feature names after transformation for SHAP labelling."""
        names: list[str] = []
        for name, transformer, cols in preprocessor.transformers_:
            if name == "cat" and hasattr(transformer, "get_feature_names_out"):
                names.extend(transformer.get_feature_names_out(cols).tolist())
            elif name == "num":
                names.extend(cols if isinstance(cols, list) else list(cols))
        return names

    # ──────────────────────────────────────────────
    # Internal: Model Training
    # ──────────────────────────────────────────────
    def _train_all_candidates(
        self,
        X_train: np.ndarray,
        y_train: pd.Series,
        X_test: np.ndarray,
        y_test: pd.Series,
    ) -> dict[str, dict[str, Any]]:
        """Train all four candidate algorithms and return results."""
        candidates: dict[str, dict[str, Any]] = {}

        # 1. Linear Regression (baseline)
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        candidates["Linear Regression"] = {
            "model": lr,
            "test_r2": r2_score(y_test, lr.predict(X_test)),
        }

        # 2. Decision Tree
        dt = DecisionTreeRegressor(max_depth=12, min_samples_leaf=10, random_state=42)
        dt.fit(X_train, y_train)
        candidates["Decision Tree"] = {
            "model": dt,
            "test_r2": r2_score(y_test, dt.predict(X_test)),
        }

        # 3. Random Forest (Optuna tuned)
        logger.info("🔬 [Pipeline] Tuning RandomForest with Optuna (%d trials)...", OPTUNA_TRIALS)
        rf_model = self._tune_random_forest(X_train, y_train)
        candidates["Random Forest"] = {
            "model": rf_model,
            "test_r2": r2_score(y_test, rf_model.predict(X_test)),
        }

        # 4. XGBoost (Optuna tuned)
        logger.info("🔬 [Pipeline] Tuning XGBoost with Optuna (%d trials)...", OPTUNA_TRIALS)
        xgb_model = self._tune_xgboost(X_train, y_train)
        candidates["XGBoost"] = {
            "model": xgb_model,
            "test_r2": r2_score(y_test, xgb_model.predict(X_test)),
        }

        for algo, info in candidates.items():
            logger.info("  %-20s test R²=%.4f", algo, info["test_r2"])

        return candidates

    def _tune_random_forest(
        self, X_train: np.ndarray, y_train: pd.Series
    ) -> RandomForestRegressor:
        """Tune RandomForest hyperparameters with Optuna TPE sampler."""
        def objective(trial: optuna.Trial) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 100, 500),
                "max_depth": trial.suggest_int("max_depth", 5, 30),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                "max_features": trial.suggest_categorical(
                    "max_features", ["sqrt", "log2", 0.5, 0.8]
                ),
                "random_state": 42,
                "n_jobs": -1,
            }
            model = RandomForestRegressor(**params)
            scores = cross_val_score(
                model, X_train, y_train, cv=3, scoring="r2", n_jobs=-1
            )
            return float(scores.mean())

        study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        study.optimize(objective, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
        best = RandomForestRegressor(**study.best_params, random_state=42, n_jobs=-1)
        best.fit(X_train, y_train)
        return best

    def _tune_xgboost(
        self, X_train: np.ndarray, y_train: pd.Series
    ) -> XGBRegressor:
        """Tune XGBRegressor hyperparameters with Optuna TPE sampler."""
        def objective(trial: optuna.Trial) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 100, 600),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-5, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-5, 10.0, log=True),
                "random_state": 42,
                "n_jobs": -1,
                "verbosity": 0,
            }
            model = XGBRegressor(**params)
            scores = cross_val_score(
                model, X_train, y_train, cv=3, scoring="r2", n_jobs=-1
            )
            return float(scores.mean())

        study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        study.optimize(objective, n_trials=OPTUNA_TRIALS, show_progress_bar=False)
        best = XGBRegressor(**study.best_params, random_state=42, n_jobs=-1, verbosity=0)
        best.fit(X_train, y_train)
        return best

    # ──────────────────────────────────────────────
    # Internal: Model Selection
    # ──────────────────────────────────────────────
    def _select_best_model(
        self,
        candidates: dict[str, dict[str, Any]],
        preprocessor: ColumnTransformer,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> tuple[str, Any, float]:
        """
        Run 5-fold CV on all candidates and pick the highest mean R².
        Returns (algorithm_name, fitted_model, cv_mean_r2).
        """
        X_proc = preprocessor.transform(X)
        kfold = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=42)
        best_algo = ""
        best_model = None
        best_cv = -np.inf

        for algo, info in candidates.items():
            scores = cross_val_score(
                info["model"], X_proc, y, cv=kfold, scoring="r2", n_jobs=-1
            )
            cv_mean = float(scores.mean())
            logger.info("  CV R² %-20s mean=%.4f  std=%.4f", algo, cv_mean, scores.std())
            if cv_mean > best_cv:
                best_cv = cv_mean
                best_algo = algo
                best_model = info["model"]

        # Re-fit best model on full dataset
        assert best_model is not None
        best_model.fit(X_proc, y)
        self._model = best_model
        self._preprocessor = preprocessor
        return best_algo, best_model, best_cv

    # ──────────────────────────────────────────────
    # Internal: KNN Index
    # ──────────────────────────────────────────────
    def _build_knn_index(
        self, X_proc: np.ndarray, df: pd.DataFrame
    ) -> list[dict[str, Any]]:
        """Fit a cosine KNN index on the full processed dataset."""
        self._knn = NearestNeighbors(
            n_neighbors=6, metric="cosine", algorithm="brute", n_jobs=-1
        )
        self._knn.fit(X_proc)

        records: list[dict[str, Any]] = []
        for idx, row in df.iterrows():
            records.append({
                "idx": int(idx),
                "brand": str(row.get("brand", "Unknown")),
                "model": str(row.get("model", "Unknown")),
                "manufacturing_year": int(row.get("manufacturing_year", 0)),
                "fuel_type": str(row.get("fuel_type", "Unknown")),
                "kilometers_driven": int(row.get("kilometers_driven", 0)),
                "selling_price": float(row.get(TARGET_COLUMN, 0)),
                "transmission": str(row.get("transmission", "Unknown")),
                "owner_type": str(row.get("owner_type", "Unknown")),
            })

        self._knn_records = records
        return records

    # ──────────────────────────────────────────────
    # Internal: Inference Helper
    # ──────────────────────────────────────────────
    def _build_inference_df(self, features: dict[str, Any]) -> pd.DataFrame:
        """
        Convert a raw features dict into a properly engineered DataFrame
        that matches the training schema exactly.
        """
        import datetime
        current_year = datetime.datetime.now().year

        row = {
            "brand": str(features.get("brand", "Unknown")).strip().title(),
            "model": str(features.get("model", "Unknown")).strip().title(),
            "fuel_type": str(features.get("fuel_type", "Petrol")).strip().title(),
            "transmission": str(features.get("transmission", "Manual")).strip().title(),
            "owner_type": str(features.get("owner_type", "First Owner")).strip().title(),
            "seller_type": str(features.get("seller_type", "Individual")).strip().title(),
            "category": str(features.get("category", "Unknown")).strip().title(),
            "city": str(features.get("city", "Unknown")).strip().title(),
            # Engineered
            "vehicle_age": current_year - int(features.get("manufacturing_year", current_year - 5)),
            "log_km_driven": float(np.log1p(int(features.get("kilometers_driven", 30000)))),
            # Optional numerics
            "engine_cc": float(features.get("engine_cc") or 1200.0),
            "mileage_kmpl": float(features.get("mileage_kmpl") or 15.0),
            "max_power_bhp": float(features.get("max_power_bhp") or 80.0),
            "seats": float(features.get("seats") or 5.0),
        }

        return pd.DataFrame([row])

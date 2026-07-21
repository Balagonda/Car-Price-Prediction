"""
AutoWorth AI — KNN Similarity Service

Nearest-neighbour retrieval of historically similar vehicles.
Used to justify valuations with real comparable records.

Layer: ML Layer
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np

logger = logging.getLogger(__name__)

_NOT_LOADED = "KNN index not loaded. Call load() first."


class SimilarityService:
    """
    Cosine-distance K-Nearest Neighbours similarity retrieval.

    Given a preprocessed feature vector, returns the top-N most similar
    historical vehicles from the training dataset, along with a similarity
    score (0–100%) for each.

    The KNN index is built during training (MLPipeline) and persisted via
    joblib. This class loads and caches that artifact.
    """

    def __init__(self) -> None:
        self._knn: Any = None
        self._records: list[dict[str, Any]] = []
        self._artifact_path: Path | None = None

    # ──────────────────────────────────────────────
    # Loading
    # ──────────────────────────────────────────────
    def load(self, knn_artifact_path: Path) -> None:
        """
        Load the KNN index and vehicle record pool from a joblib artifact.

        The artifact is a dict with keys:
            - "knn": fitted sklearn NearestNeighbors instance
            - "records": list of historical vehicle dicts
        """
        logger.info("📂 [Similarity] Loading KNN artifact: %s", knn_artifact_path)
        data = joblib.load(knn_artifact_path)
        self._knn = data["knn"]
        self._records = data["records"]
        self._artifact_path = knn_artifact_path
        logger.info(
            "✅ [Similarity] KNN index loaded (%d records)", len(self._records)
        )

    # ──────────────────────────────────────────────
    # Public: Find Similar Vehicles
    # ──────────────────────────────────────────────
    def find_similar(
        self,
        preprocessed_input: np.ndarray,
        n: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find the N most similar historical vehicles to the given query vector.

        Args:
            preprocessed_input: 2D numpy array (1, n_features) from the pipeline
                                 ColumnTransformer — must match training schema.
            n: Number of similar vehicles to return (default 5).

        Returns:
            list of dicts, each containing:
                - brand, model, manufacturing_year, fuel_type
                - kilometers_driven, selling_price, transmission, owner_type
                - similarity_score (0–100 %)
        """
        if self._knn is None:
            raise RuntimeError(_NOT_LOADED)

        # Request n+1 to exclude the exact query itself if present
        n_query = min(n + 1, len(self._records))
        distances, indices = self._knn.kneighbors(
            preprocessed_input, n_neighbors=n_query
        )

        results: list[dict[str, Any]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if len(results) >= n:
                break
            # Cosine distance → similarity percentage
            # distance ∈ [0, 2]; 0 = identical, 2 = opposite
            similarity_pct = round(max(0.0, (1.0 - dist)) * 100, 1)
            record = self._records[idx].copy()
            record["similarity_score"] = similarity_pct
            record.pop("idx", None)  # Remove internal index
            results.append(record)

        return results

    # ──────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────
    @property
    def is_loaded(self) -> bool:
        """True if the KNN index has been loaded."""
        return self._knn is not None

    def __repr__(self) -> str:
        status = f"{len(self._records)} records" if self.is_loaded else "not loaded"
        return f"<SimilarityService [{status}]>"

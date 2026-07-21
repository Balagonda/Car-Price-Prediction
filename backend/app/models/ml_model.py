"""
AutoWorth AI — MLModel & ModelVersion Models

Tracks ML model registry (algorithms) and their versioned training runs.
Only ONE ModelVersion can be in 'active' status per MLModel at a time.
This invariant is enforced at the service layer, not here.
"""

import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AlgorithmType(str, enum.Enum):
    LINEAR_REGRESSION = "Linear Regression"
    DECISION_TREE = "Decision Tree"
    RANDOM_FOREST = "Random Forest"
    XGBOOST = "XGBoost"


class ModelStatus(str, enum.Enum):
    TRAINING = "training"
    TRAINED = "trained"
    ACTIVE = "active"       # Deployed in production — only one allowed per MLModel
    ARCHIVED = "archived"
    FAILED = "failed"


class MLModel(Base, TimestampMixin):
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    algorithm: Mapped[AlgorithmType] = mapped_column(
        Enum(AlgorithmType, name="algorithm_type_enum"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────
    versions: Mapped[list["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="ml_model", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MLModel id={self.id} name={self.name!r} algorithm={self.algorithm}>"


class ModelVersion(Base, TimestampMixin):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Version Info ──────────────────────────────────────────
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "v2.1"
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus, name="model_status_enum"),
        default=ModelStatus.TRAINING,
        nullable=False,
        index=True,
    )

    # ── Training Metrics ──────────────────────────────────────
    r2_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    cross_val_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_prediction_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Artifact Storage ──────────────────────────────────────
    model_artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    preprocessor_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Training Notes ────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Foreign Keys ──────────────────────────────────────────
    ml_model_id: Mapped[int] = mapped_column(
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    ml_model: Mapped["MLModel"] = relationship("MLModel", back_populates="versions")
    dataset: Mapped["Dataset | None"] = relationship("Dataset", back_populates="model_versions")  # noqa: F821
    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="model_version"
    )

    def __repr__(self) -> str:
        return (
            f"<ModelVersion id={self.id} "
            f"version={self.version_tag!r} "
            f"status={self.status}>"
        )

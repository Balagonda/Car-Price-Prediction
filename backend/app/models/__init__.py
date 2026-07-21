"""
AutoWorth AI — Models Package

IMPORTANT: Import ALL models here so Alembic's autogenerate can detect
every table when running `alembic revision --autogenerate`.
"""

from app.models.base import Base, TimestampMixin, UUIDMixin  # noqa: F401

# ── Core Auth ────────────────────────────────────────────────
from app.models.role import Role  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.session import UserSession  # noqa: F401

# ── Vehicle Taxonomy ─────────────────────────────────────────
from app.models.brand import Brand  # noqa: F401
from app.models.car_model import CarModel  # noqa: F401
from app.models.variant import Variant  # noqa: F401
from app.models.city import City  # noqa: F401
from app.models.vehicle import (  # noqa: F401
    Vehicle,
    FuelType,
    TransmissionType,
    OwnerType,
    SellerType,
    VehicleCategory,
    InsuranceStatus,
)

# ── ML & Dataset ─────────────────────────────────────────────
from app.models.dataset import Dataset  # noqa: F401
from app.models.ml_model import (  # noqa: F401
    MLModel,
    ModelVersion,
    AlgorithmType,
    ModelStatus,
)

# ── Predictions ───────────────────────────────────────────────
from app.models.prediction import Prediction, FairPriceStatus  # noqa: F401
from app.models.prediction_image import (  # noqa: F401
    PredictionImage,
    ImageAngle,
    DamageLevel,
)
from app.models.shap_result import ShapResult  # noqa: F401
from app.models.recommendation import Recommendation, RecommendationPriority  # noqa: F401

# ── User Features ─────────────────────────────────────────────
from app.models.favorite import Favorite  # noqa: F401
from app.models.feedback import Feedback, FeedbackStatus  # noqa: F401

# ── Logging ───────────────────────────────────────────────────
from app.models.activity_log import ActivityLog, ActionType  # noqa: F401
from app.models.error_log import ErrorLog, ErrorSeverity  # noqa: F401
from app.models.notification_log import (  # noqa: F401
    NotificationLog,
    NotificationType,
    NotificationStatus,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "Role",
    "User",
    "UserSession",
    "Brand",
    "CarModel",
    "Variant",
    "City",
    "Vehicle",
    "FuelType",
    "TransmissionType",
    "OwnerType",
    "SellerType",
    "VehicleCategory",
    "InsuranceStatus",
    "Dataset",
    "MLModel",
    "ModelVersion",
    "AlgorithmType",
    "ModelStatus",
    "Prediction",
    "FairPriceStatus",
    "PredictionImage",
    "ImageAngle",
    "DamageLevel",
    "ShapResult",
    "Recommendation",
    "RecommendationPriority",
    "Favorite",
    "Feedback",
    "FeedbackStatus",
    "ActivityLog",
    "ActionType",
    "ErrorLog",
    "ErrorSeverity",
    "NotificationLog",
    "NotificationType",
    "NotificationStatus",
]

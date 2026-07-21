"""
AutoWorth AI — Initial Database Migration

Creates all tables from scratch.
Includes CV Phase 4 enum types: image_angle_enum, damage_level_enum.

Revision ID: 0001
Revises: (none — initial migration)
Create Date: 2026-07-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ──────────────────────────────────────────────────────
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────────────
    # ENUM TYPES
    # ─────────────────────────────────────────────────────────────────────────

    # Auth / User
    op.execute(
        "CREATE TYPE user_status_enum AS ENUM ('active', 'inactive', 'banned')"
        " ON CONFLICT DO NOTHING"  # Not standard SQL; use checkfirst approach
    )

    # Use create_type with checkfirst for idempotency
    algorithm_type = postgresql.ENUM(
        "xgboost", "random_forest", "gradient_boost", "linear",
        name="algorithm_type_enum", create_type=False
    )
    algorithm_type.create(op.get_bind(), checkfirst=True)

    model_status = postgresql.ENUM(
        "training", "trained", "active", "archived", "failed",
        name="model_status_enum", create_type=False
    )
    model_status.create(op.get_bind(), checkfirst=True)

    fair_price_status = postgresql.ENUM(
        "Below Market", "Fair", "Above Market",
        name="fair_price_status_enum", create_type=False
    )
    fair_price_status.create(op.get_bind(), checkfirst=True)

    # ── Phase 4 CV enums ──────────────────────────────────────────────────────
    image_angle = postgresql.ENUM(
        "Front", "Rear", "Left Side", "Right Side", "Interior", "Other",
        name="image_angle_enum", create_type=False
    )
    image_angle.create(op.get_bind(), checkfirst=True)

    damage_level = postgresql.ENUM(
        "None", "Minor", "Moderate", "Severe",
        name="damage_level_enum", create_type=False
    )
    damage_level.create(op.get_bind(), checkfirst=True)

    recommendation_priority = postgresql.ENUM(
        "high", "medium", "low",
        name="recommendation_priority_enum", create_type=False
    )
    recommendation_priority.create(op.get_bind(), checkfirst=True)

    feedback_status = postgresql.ENUM(
        "pending", "reviewed", "actioned",
        name="feedback_status_enum", create_type=False
    )
    feedback_status.create(op.get_bind(), checkfirst=True)

    action_type = postgresql.ENUM(
        "login", "logout", "prediction_created", "model_trained",
        "model_activated", "user_registered", "password_changed",
        "profile_updated", "favorite_added", "favorite_removed",
        "feedback_submitted", "report_generated",
        name="action_type_enum", create_type=False
    )
    action_type.create(op.get_bind(), checkfirst=True)

    error_severity = postgresql.ENUM(
        "low", "medium", "high", "critical",
        name="error_severity_enum", create_type=False
    )
    error_severity.create(op.get_bind(), checkfirst=True)

    notification_type = postgresql.ENUM(
        "prediction_complete", "model_trained", "system_alert",
        "welcome", "password_reset", "email_verification",
        name="notification_type_enum", create_type=False
    )
    notification_type.create(op.get_bind(), checkfirst=True)

    notification_status = postgresql.ENUM(
        "pending", "sent", "failed", "skipped",
        name="notification_status_enum", create_type=False
    )
    notification_status.create(op.get_bind(), checkfirst=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TABLES
    # ─────────────────────────────────────────────────────────────────────────

    # roles
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.Text(), nullable=True),
        sa.Column("google_sub", sa.String(255), nullable=True, unique=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_verification_token", sa.String(255), nullable=True),
        sa.Column("password_reset_token", sa.String(255), nullable=True),
        sa.Column("password_reset_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # user_sessions
    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # brands
    op.create_table(
        "brands",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("country_of_origin", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # car_models
    op.create_table(
        "car_models",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # variants
    op.create_table(
        "variants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("car_model_id", sa.Integer(),
                  sa.ForeignKey("car_models.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # cities
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # vehicles
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("manufacturing_year", sa.Integer(), nullable=False),
        sa.Column("fuel_type", sa.String(50), nullable=False),
        sa.Column("transmission", sa.String(50), nullable=False),
        sa.Column("owner_type", sa.String(50), nullable=False),
        sa.Column("seller_type", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("kilometers_driven", sa.Integer(), nullable=False),
        sa.Column("engine_cc", sa.Integer(), nullable=True),
        sa.Column("mileage_kmpl", sa.Float(), nullable=True),
        sa.Column("seats", sa.Integer(), nullable=True),
        sa.Column("max_power_bhp", sa.Float(), nullable=True),
        sa.Column("insurance_status", sa.String(50), nullable=True),
        sa.Column("brand_id", sa.Integer(),
                  sa.ForeignKey("brands.id", ondelete="RESTRICT"), nullable=True, index=True),
        sa.Column("car_model_id", sa.Integer(),
                  sa.ForeignKey("car_models.id", ondelete="RESTRICT"), nullable=True, index=True),
        sa.Column("variant_id", sa.Integer(),
                  sa.ForeignKey("variants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("city_id", sa.Integer(),
                  sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # datasets
    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # ml_models
    op.create_table(
        "ml_models",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # model_versions
    op.create_table(
        "model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_tag", sa.String(50), nullable=False),
        sa.Column("status", sa.Enum(
            "training", "trained", "active", "archived", "failed",
            name="model_status_enum", create_type=False
        ), nullable=False, server_default="training"),
        sa.Column("algorithm", sa.Enum(
            "xgboost", "random_forest", "gradient_boost", "linear",
            name="algorithm_type_enum", create_type=False
        ), nullable=True),
        sa.Column("r2_score", sa.Float(), nullable=True),
        sa.Column("rmse", sa.Float(), nullable=True),
        sa.Column("mae", sa.Float(), nullable=True),
        sa.Column("cross_val_score", sa.Float(), nullable=True),
        sa.Column("training_time_seconds", sa.Float(), nullable=True),
        sa.Column("training_samples", sa.Integer(), nullable=True),
        sa.Column("model_artifact_path", sa.Text(), nullable=True),
        sa.Column("preprocessor_path", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("avg_prediction_time_ms", sa.Float(), nullable=True),
        sa.Column("ml_model_id", sa.Integer(),
                  sa.ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # predictions
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("estimated_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("price_range_min", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_range_max", sa.Numeric(12, 2), nullable=False),
        sa.Column("fair_price_status", sa.Enum(
            "Below Market", "Fair", "Above Market",
            name="fair_price_status_enum", create_type=False
        ), nullable=False),
        sa.Column("depreciation_percent", sa.Float(), nullable=True),
        sa.Column("showroom_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("shap_values", postgresql.JSON(), nullable=True),
        sa.Column("similar_vehicles", postgresql.JSON(), nullable=True),
        # ── CV columns (Phase 4) ──────────────────────────────
        sa.Column("cv_damage_detected", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("cv_damage_severity", sa.String(50), nullable=True),
        sa.Column("cv_repair_cost_estimate", sa.Float(), nullable=True),
        # ── Report (Phase 5) ──────────────────────────────────
        sa.Column("is_pdf_generated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("vehicle_id", sa.Integer(),
                  sa.ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("model_version_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("model_versions.id", ondelete="SET NULL"),
                  nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # prediction_images (Phase 4 — CV)
    op.create_table(
        "prediction_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("heatmap_url", sa.Text(), nullable=True),
        sa.Column("cloudinary_public_id", sa.String(255), nullable=True),
        sa.Column("image_angle", sa.Enum(
            "Front", "Rear", "Left Side", "Right Side", "Interior", "Other",
            name="image_angle_enum", create_type=False
        ), nullable=False, server_default="Front"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("damage_level", sa.Enum(
            "None", "Minor", "Moderate", "Severe",
            name="damage_level_enum", create_type=False
        ), nullable=False, server_default="None"),
        sa.Column("cv_analysis_result", postgresql.JSON(), nullable=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("predictions.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # shap_results
    op.create_table(
        "shap_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("feature_name", sa.String(100), nullable=False),
        sa.Column("feature_value", sa.String(255), nullable=True),
        sa.Column("shap_value", sa.Float(), nullable=False),
        sa.Column("impact_direction", sa.String(20), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("human_readable_impact", sa.Text(), nullable=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # recommendations
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.Enum(
            "high", "medium", "low",
            name="recommendation_priority_enum", create_type=False
        ), nullable=False, server_default="medium"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # favorites
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # feedback
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum(
            "pending", "reviewed", "actioned",
            name="feedback_status_enum", create_type=False
        ), nullable=False, server_default="pending"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # activity_logs
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("action", sa.Enum(
            "login", "logout", "prediction_created", "model_trained",
            "model_activated", "user_registered", "password_changed",
            "profile_updated", "favorite_added", "favorite_removed",
            "feedback_submitted", "report_generated",
            name="action_type_enum", create_type=False
        ), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # error_logs
    op.create_table(
        "error_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("severity", sa.Enum(
            "low", "medium", "high", "critical",
            name="error_severity_enum", create_type=False
        ), nullable=False, server_default="medium"),
        sa.Column("endpoint", sa.String(255), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # notification_logs
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("notification_type", sa.Enum(
            "prediction_complete", "model_trained", "system_alert",
            "welcome", "password_reset", "email_verification",
            name="notification_type_enum", create_type=False
        ), nullable=False),
        sa.Column("status", sa.Enum(
            "pending", "sent", "failed", "skipped",
            name="notification_status_enum", create_type=False
        ), nullable=False, server_default="pending"),
        sa.Column("channel", sa.String(50), nullable=True),
        sa.Column("recipient_email", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("body_snippet", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )


def downgrade() -> None:
    # Drop tables in reverse FK order
    op.drop_table("notification_logs")
    op.drop_table("error_logs")
    op.drop_table("activity_logs")
    op.drop_table("feedback")
    op.drop_table("favorites")
    op.drop_table("recommendations")
    op.drop_table("shap_results")
    op.drop_table("prediction_images")
    op.drop_table("predictions")
    op.drop_table("model_versions")
    op.drop_table("ml_models")
    op.drop_table("datasets")
    op.drop_table("vehicles")
    op.drop_table("cities")
    op.drop_table("variants")
    op.drop_table("car_models")
    op.drop_table("brands")
    op.drop_table("user_sessions")
    op.drop_table("users")
    op.drop_table("roles")

    # Drop enums
    for enum_name in [
        "notification_status_enum", "notification_type_enum",
        "error_severity_enum", "action_type_enum", "feedback_status_enum",
        "recommendation_priority_enum", "damage_level_enum", "image_angle_enum",
        "fair_price_status_enum", "model_status_enum", "algorithm_type_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

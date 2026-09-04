"""Part 2: add recommendations and alerts tables

Revision ID: 0002_part2_recommendations_alerts
Revises: 0001_initial_schema
Create Date: 2026-09-03

Hand-authored for the same reason as 0001 (no live PostgreSQL instance in
this sandbox to autogenerate against) - mirrors app/database/models.py's
Recommendation and Alert classes exactly. Does not touch any Part 1
table.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_part2_recommendations_alerts"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    recommendation_status = postgresql.ENUM(
        "NORMAL", "MONITOR", "IRRIGATION_RECOMMENDED", "HIGH_WATER_STRESS_RISK",
        name="recommendation_status",
    )
    recommendation_urgency = postgresql.ENUM("LOW", "MEDIUM", "HIGH", "CRITICAL", name="recommendation_urgency")
    alert_severity = postgresql.ENUM("INFO", "WARNING", "HIGH", "CRITICAL", name="alert_severity")
    alert_status = postgresql.ENUM("active", "acknowledged", "resolved", name="alert_status")

    recommendation_status.create(op.get_bind(), checkfirst=True)
    recommendation_urgency.create(op.get_bind(), checkfirst=True)
    alert_severity.create(op.get_bind(), checkfirst=True)
    alert_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("polyhouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("polyhouses.id", ondelete="CASCADE"), nullable=True),
        sa.Column("forecast_result_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("forecast_results.id", ondelete="SET NULL"), nullable=True),
        sa.Column("domain", sa.String(50), nullable=False, server_default="irrigation"),
        sa.Column("status", recommendation_status, nullable=False),
        sa.Column("urgency", recommendation_urgency, nullable=False),
        sa.Column("recommendation_text", sa.String(500), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("risk_factors", postgresql.JSONB, nullable=True),
        sa.Column("inputs_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("model_confidence", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recommendations_polyhouse_id", "recommendations", ["polyhouse_id"])
    op.create_index("ix_recommendations_polyhouse_created", "recommendations", ["polyhouse_id", "created_at"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("polyhouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("polyhouses.id", ondelete="CASCADE"), nullable=True),
        sa.Column("alert_type", sa.String(80), nullable=False),
        sa.Column("severity", alert_severity, nullable=False),
        sa.Column("status", alert_status, nullable=False, server_default="active"),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("source_reference", postgresql.JSONB, nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_alerts_polyhouse_id", "alerts", ["polyhouse_id"])
    op.create_index("ix_alerts_polyhouse_status", "alerts", ["polyhouse_id", "status"])
    op.create_index("ix_alerts_severity_status", "alerts", ["severity", "status"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("recommendations")

    sa.Enum(name="alert_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="alert_severity").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="recommendation_urgency").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="recommendation_status").drop(op.get_bind(), checkfirst=True)

"""Add container_metrics and observability_events tables.

Revision ID: 0006_observability
Revises: 0005_health_engine
Create Date: 2026-08-08
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision: str = "0006_observability"
down_revision = "0005_health_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. container_metrics table
    op.create_table(
        "container_metrics",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("deployment_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", sa.String(length=100), nullable=False),
        sa.Column("container_id", sa.String(length=255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("cpu_percent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("memory_usage_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("memory_limit_bytes", sa.BigInteger(), nullable=True),
        sa.Column("memory_percent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("network_rx_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("network_tx_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("network_rx_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("network_tx_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("block_read_bytes", sa.BigInteger(), nullable=True),
        sa.Column("block_write_bytes", sa.BigInteger(), nullable=True),
        sa.Column("restart_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("container_state", sa.String(length=50), nullable=False, server_default="running"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_container_metrics_service_time", "container_metrics", ["service_id", "timestamp"])
    op.create_index("ix_container_metrics_deployment_time", "container_metrics", ["deployment_id", "timestamp"])
    op.create_index("ix_container_metrics_project_time", "container_metrics", ["project_id", "timestamp"])

    # 2. observability_events table
    op.create_table(
        "observability_events",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("deployment_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON().with_variant(pg.JSONB, "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_observability_events_deployment_time", "observability_events", ["deployment_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_observability_events_deployment_time", "observability_events")
    op.drop_table("observability_events")
    op.drop_index("ix_container_metrics_project_time", "container_metrics")
    op.drop_index("ix_container_metrics_deployment_time", "container_metrics")
    op.drop_index("ix_container_metrics_service_time", "container_metrics")
    op.drop_table("container_metrics")

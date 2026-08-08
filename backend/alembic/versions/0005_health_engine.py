"""Add service_health, health_checks, and health_events tables.

Revision ID: 0005_health_engine
Revises: 0004_deployments
Create Date: 2026-08-08
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision: str = "0005_health_engine"
down_revision = "0004_deployments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. service_health table
    op.create_table(
        "service_health",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deployment_service_id", pg.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column(
            "status",
            sa.Enum("UNKNOWN", "STARTING", "HEALTHY", "DEGRADED", "UNHEALTHY", "FAILED", name="healthstatus"),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_successes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("last_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["deployment_service_id"], ["deployment_services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_health_service_id", "service_health", ["deployment_service_id"])

    # 2. health_checks table
    op.create_table(
        "health_checks",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deployment_service_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("check_type", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.Enum("UNKNOWN", "STARTING", "HEALTHY", "DEGRADED", "UNHEALTHY", "FAILED", name="healthcheckstatus"),
            nullable=False,
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["deployment_service_id"], ["deployment_services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_checks_service_id", "health_checks", ["deployment_service_id"])

    # 3. health_events table
    op.create_table(
        "health_events",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("deployment_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("previous_state", sa.String(length=50), nullable=True),
        sa.Column("new_state", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_events_deployment_id", "health_events", ["deployment_id"])
    op.create_index("ix_health_events_project_id", "health_events", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_health_events_project_id", "health_events")
    op.drop_index("ix_health_events_deployment_id", "health_events")
    op.drop_table("health_events")
    op.drop_index("ix_health_checks_service_id", "health_checks")
    op.drop_table("health_checks")
    op.drop_index("ix_service_health_service_id", "service_health")
    op.drop_table("service_health")
    op.execute("DROP TYPE IF EXISTS healthstatus")
    op.execute("DROP TYPE IF EXISTS healthcheckstatus")

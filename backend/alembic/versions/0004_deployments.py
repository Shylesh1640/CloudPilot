"""Add deployments and deployment_services tables.

Revision ID: 0004_deployments
Revises: 0003_infrastructure_plans
Create Date: 2026-08-08
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision: str = "0004_deployments"
down_revision = "0003_infrastructure_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. create deployments table
    op.create_table(
        "deployments",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("infrastructure_plan_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "PREPARING", "BUILDING", "CREATING_NETWORK", "CREATING_VOLUMES",
                "CREATING_SERVICES", "STARTING", "RUNNING", "FAILED", "STOPPED",
                name="deploymentstatus",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("logs", pg.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["infrastructure_plan_id"], ["infrastructure_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deployments_project_id", "deployments", ["project_id"])
    op.create_index("ix_deployments_plan_id", "deployments", ["infrastructure_plan_id"])

    # 2. create deployment_services table
    op.create_table(
        "deployment_services",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deployment_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", sa.String(length=100), nullable=False),
        sa.Column("container_id", sa.String(length=128), nullable=True),
        sa.Column("container_name", sa.String(length=200), nullable=False),
        sa.Column("image", sa.String(length=255), nullable=False),
        sa.Column(
            "desired_state",
            sa.Enum("RUNNING", "STOPPED", name="servicedesiredstate"),
            nullable=False,
            server_default="RUNNING",
        ),
        sa.Column(
            "actual_state",
            sa.Enum("RUNNING", "STARTING", "EXITED", "CREATED", "FAILED", "UNKNOWN", name="serviceactualstate"),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deployment_services_deployment_id", "deployment_services", ["deployment_id"])


def downgrade() -> None:
    op.drop_index("ix_deployment_services_deployment_id", "deployment_services")
    op.drop_table("deployment_services")
    op.drop_index("ix_deployments_plan_id", "deployments")
    op.drop_index("ix_deployments_project_id", "deployments")
    op.drop_table("deployments")
    op.execute("DROP TYPE IF EXISTS servicedesiredstate")
    op.execute("DROP TYPE IF EXISTS serviceactualstate")
    op.execute("DROP TYPE IF EXISTS deploymentstatus")

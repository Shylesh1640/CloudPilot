"""Add infrastructure_plans table.

Revision ID: 0003_infrastructure_plans
Revises: 0002_repository_analyses
Create Date: 2026-08-08
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision: str = "0003_infrastructure_plans"
down_revision = "0002_repository_analyses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "infrastructure_plans",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_analysis_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "GENERATING", "VALIDATING", "COMPLETED", "FAILED",
                name="planstatus",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("plan_data", pg.JSONB(), nullable=True),
        sa.Column("validation_result", pg.JSONB(), nullable=True),
        sa.Column("ai_provider", sa.String(length=100), nullable=True),
        sa.Column("ai_model", sa.String(length=100), nullable=True),
        sa.Column("generation_duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_analysis_id"], ["repository_analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_infrastructure_plans_project_id", "infrastructure_plans", ["project_id"])
    op.create_index("ix_infrastructure_plans_analysis_id", "infrastructure_plans", ["repository_analysis_id"])


def downgrade() -> None:
    op.drop_index("ix_infrastructure_plans_analysis_id", "infrastructure_plans")
    op.drop_index("ix_infrastructure_plans_project_id", "infrastructure_plans")
    op.drop_table("infrastructure_plans")
    op.execute("DROP TYPE IF EXISTS planstatus")

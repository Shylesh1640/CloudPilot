"""Add repository_analyses table.

Revision ID: 0002_repository_analyses
Revises: 0001_initial
Create Date: 2026-08-08
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
import sqlalchemy.dialects.postgresql as pg

revision: str = "0002_repository_analyses"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repository_analyses",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_url", sa.String(length=2048), nullable=False),
        sa.Column("repository_owner", sa.String(length=255), nullable=True),
        sa.Column("repository_name", sa.String(length=255), nullable=True),
        sa.Column("commit_sha", sa.String(length=40), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "CLONING", "SCANNING", "ANALYZING", "COMPLETED", "FAILED",
                name="analysisstatus",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_language", sa.String(length=100), nullable=True),
        sa.Column("analysis_result", pg.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repository_analyses_project_id", "repository_analyses", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_repository_analyses_project_id", "repository_analyses")
    op.drop_table("repository_analyses")
    op.execute("DROP TYPE IF EXISTS analysisstatus")

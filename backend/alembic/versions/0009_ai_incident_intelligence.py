"""Add Phase 9 incident memory and AI decision audit trail.

Revision ID: 0009_ai_incident_intelligence
Revises: 0008_self_healing
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = "0009_ai_incident_intelligence"
down_revision = "0008_self_healing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_col = sa.JSON().with_variant(pg.JSONB, "postgresql")
    op.create_table("incident_memory", sa.Column("id", pg.UUID(as_uuid=True), primary_key=True), sa.Column("incident_id", pg.UUID(as_uuid=True), nullable=False, unique=True), sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False), sa.Column("service_id", sa.String(100), nullable=False), sa.Column("incident_type", sa.String(100), nullable=False), sa.Column("root_cause", sa.String(100)), sa.Column("symptoms", json_col, nullable=False), sa.Column("evidence", json_col, nullable=False), sa.Column("successful_action", sa.String(50)), sa.Column("recovery_time_seconds", sa.Integer()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"))
    op.create_table("ai_decision_traces", sa.Column("id", pg.UUID(as_uuid=True), primary_key=True), sa.Column("incident_id", pg.UUID(as_uuid=True), nullable=False), sa.Column("provider", sa.String(50), nullable=False), sa.Column("model", sa.String(100), nullable=False), sa.Column("context_hash", sa.String(64), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("structured_result", json_col), sa.Column("validation_result", json_col), sa.Column("latency_ms", sa.Integer()), sa.Column("error_message", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"))
    op.create_index("ix_ai_trace_incident_context", "ai_decision_traces", ["incident_id", "context_hash"])


def downgrade() -> None:
    op.drop_table("ai_decision_traces")
    op.drop_table("incident_memory")

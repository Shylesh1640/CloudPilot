"""Add Phase 8 failure injection, incidents, recovery and audit tables.

Revision ID: 0008_self_healing
Revises: 0007_autoscaling
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = "0008_self_healing"
down_revision = "0007_autoscaling"
branch_labels = None
depends_on = None


def _id(name: str):
    return sa.Column(name, pg.UUID(as_uuid=True), nullable=False)


def _metadata():
    return sa.JSON().with_variant(pg.JSONB, "postgresql")


def upgrade() -> None:
    op.create_table("failure_injections", _id("id"), _id("project_id"), _id("deployment_id"), sa.Column("service_id", sa.String(100), nullable=False), sa.Column("target_container_id", sa.String(255)), sa.Column("scenario", sa.String(40), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("simulation", sa.Boolean(), nullable=False, server_default=sa.false()), _id("created_by"), sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.PrimaryKeyConstraint("id"), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"))
    op.create_table("incidents", _id("id"), _id("project_id"), _id("deployment_id"), sa.Column("service_id", sa.String(100), nullable=False), sa.Column("severity", sa.String(20), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("trigger", sa.String(100), nullable=False), sa.Column("root_cause_service_id", sa.String(100)), sa.Column("root_cause_type", sa.String(100)), sa.Column("diagnosis", _metadata()), sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("resolved_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.PrimaryKeyConstraint("id"), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"))
    op.create_table("recovery_policies", _id("id"), _id("project_id"), _id("deployment_id"), sa.Column("service_id", sa.String(100), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("simulation_mode", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("max_attempts", sa.Integer(), nullable=False), sa.Column("cooldown_seconds", sa.Integer(), nullable=False), sa.Column("verification_timeout_seconds", sa.Integer(), nullable=False), sa.Column("last_recovery_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.PrimaryKeyConstraint("id"), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"))
    op.create_table("recovery_attempts", _id("id"), _id("incident_id"), sa.Column("action", sa.String(50), nullable=False), sa.Column("target_service_id", sa.String(100), nullable=False), sa.Column("target_container_id", sa.String(255)), sa.Column("attempt_number", sa.Integer(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("error_message", sa.Text()), sa.PrimaryKeyConstraint("id"), sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"))
    op.create_table("recovery_events", _id("id"), _id("incident_id"), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("metadata_json", _metadata()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.PrimaryKeyConstraint("id"), sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"))
    op.create_table("audit_logs", _id("id"), sa.Column("user_id", pg.UUID(as_uuid=True)), _id("project_id"), sa.Column("deployment_id", pg.UUID(as_uuid=True)), sa.Column("service_id", sa.String(100)), sa.Column("action", sa.String(100), nullable=False), sa.Column("reason", sa.Text()), sa.Column("result", sa.String(30), nullable=False), sa.Column("metadata_json", _metadata()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.PrimaryKeyConstraint("id"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"))
    for table, columns in (("failure_injections", ["deployment_id", "created_at"]), ("incidents", ["deployment_id", "service_id", "status"]), ("recovery_attempts", ["incident_id", "attempt_number"]), ("recovery_events", ["incident_id", "created_at"])):
        op.create_index(f"ix_{table}_lookup", table, columns)
    op.create_index("uq_recovery_policy_service", "recovery_policies", ["deployment_id", "service_id"], unique=True)


def downgrade() -> None:
    for table in ("audit_logs", "recovery_events", "recovery_attempts", "recovery_policies", "incidents", "failure_injections"):
        op.drop_table(table)

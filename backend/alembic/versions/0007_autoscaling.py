"""Add Phase 7 autoscaling and traffic generator state.

Revision ID: 0007_autoscaling
Revises: 0006_observability
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = "0007_autoscaling"
down_revision = "0006_observability"
branch_labels = None
depends_on = None


def _json() -> sa.JSON:
    return sa.JSON().with_variant(pg.JSONB, "postgresql")


def upgrade() -> None:
    op.add_column("deployment_services", sa.Column("desired_replicas", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("deployment_services", sa.Column("replica_id", sa.Integer(), nullable=False, server_default="1"))
    op.create_table("scaling_policies", sa.Column("id", pg.UUID(as_uuid=True), primary_key=True), sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False), sa.Column("deployment_id", pg.UUID(as_uuid=True), nullable=False), sa.Column("service_id", sa.String(100), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("min_replicas", sa.Integer(), nullable=False), sa.Column("max_replicas", sa.Integer(), nullable=False), sa.Column("target_cpu", sa.Float()), sa.Column("target_memory", sa.Float()), sa.Column("target_request_rate", sa.Float()), sa.Column("target_latency", sa.Float()), sa.Column("scale_up_threshold", sa.Float()), sa.Column("scale_down_threshold", sa.Float()), sa.Column("scale_up_cooldown", sa.Integer(), nullable=False), sa.Column("scale_down_cooldown", sa.Integer(), nullable=False), sa.Column("stabilization_window", sa.Integer(), nullable=False), sa.Column("max_scale_up_step", sa.Integer(), nullable=False), sa.Column("max_scale_down_step", sa.Integer(), nullable=False), sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("simulation_mode", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("last_scale_up_at", sa.DateTime(timezone=True)), sa.Column("last_scale_down_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"))
    op.create_index("ix_scaling_policies_service", "scaling_policies", ["deployment_id", "service_id"], unique=True)
    for table in ("scaling_decisions", "scaling_events"):
        columns = [sa.Column("id", pg.UUID(as_uuid=True), primary_key=True), sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False), sa.Column("deployment_id", pg.UUID(as_uuid=True), nullable=False), sa.Column("service_id", sa.String(100), nullable=False)]
        if table == "scaling_decisions": columns += [sa.Column("current_replicas", sa.Integer(), nullable=False), sa.Column("recommended_replicas", sa.Integer(), nullable=False), sa.Column("action", sa.String(30), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("trigger_metric", sa.String(50)), sa.Column("metric_value", sa.Float()), sa.Column("target_value", sa.Float()), sa.Column("reason", sa.Text(), nullable=False), sa.Column("metrics_json", _json())]
        else: columns += [sa.Column("event_type", sa.String(50), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("metadata_json", _json())]
        columns += [sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE")]
        op.create_table(table, *columns)
        op.create_index(f"ix_{table}_deployment_time", table, ["deployment_id", "created_at"])
    op.create_table("traffic_runs", sa.Column("id", pg.UUID(as_uuid=True), primary_key=True), sa.Column("project_id", pg.UUID(as_uuid=True), nullable=False), sa.Column("deployment_id", pg.UUID(as_uuid=True), nullable=False), sa.Column("service_id", sa.String(100), nullable=False), sa.Column("scenario", sa.String(30), nullable=False), sa.Column("configuration", _json(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("current_rps", sa.Float(), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("created_by", pg.UUID(as_uuid=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"))


def downgrade() -> None:
    op.drop_table("traffic_runs")
    op.drop_table("scaling_events")
    op.drop_table("scaling_decisions")
    op.drop_table("scaling_policies")
    op.drop_column("deployment_services", "replica_id")
    op.drop_column("deployment_services", "desired_replicas")

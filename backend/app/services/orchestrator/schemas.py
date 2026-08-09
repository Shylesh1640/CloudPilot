"""Pydantic schemas for deployment API interaction."""
from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field
from app.models.deployment import DeploymentStatus, ServiceActualState, ServiceDesiredState


class DeploymentServiceRead(BaseModel):
    id: uuid.UUID
    deployment_id: uuid.UUID
    service_id: str
    container_id: str | None
    container_name: str
    image: str
    desired_state: ServiceDesiredState
    actual_state: ServiceActualState
    status: str
    port: int | None
    public: bool
    started_at: datetime | None
    stopped_at: datetime | None
    error_message: str | None
    desired_replicas: int = 1
    replica_id: int = 1

    model_config = {"from_attributes": True}


class DeploymentRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    infrastructure_plan_id: uuid.UUID
    version: int
    status: DeploymentStatus
    progress: int
    logs: list[dict[str, Any]] | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    services: list[DeploymentServiceRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ServiceLogsRead(BaseModel):
    service_id: str
    container_name: str
    logs: str

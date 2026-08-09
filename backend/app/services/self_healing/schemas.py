from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class FailureInjectionCreate(BaseModel):
    service_id: str = Field(min_length=1, max_length=100)
    scenario: Literal["CONTAINER_STOP", "CONTAINER_KILL", "SERVICE_FAILURE", "REPLICA_FAILURE", "HEALTH_CHECK_FAILURE"]
    replica_id: int | None = Field(default=None, ge=1)
    duration_seconds: int = Field(default=30, ge=1, le=120)
    simulation: bool = False


class FailureInjectionRead(BaseModel):
    id: UUID; project_id: UUID; deployment_id: UUID; service_id: str; target_container_id: str | None; scenario: str; status: str; simulation: bool; started_at: datetime | None; completed_at: datetime | None; created_at: datetime
    model_config = {"from_attributes": True}


class IncidentRead(BaseModel):
    id: UUID; project_id: UUID; deployment_id: UUID; service_id: str; severity: str; status: str; trigger: str; root_cause_service_id: str | None; root_cause_type: str | None; diagnosis: dict | None; opened_at: datetime; resolved_at: datetime | None; created_at: datetime
    model_config = {"from_attributes": True}


class RecoveryAttemptRead(BaseModel):
    id: UUID; incident_id: UUID; action: str; target_service_id: str; target_container_id: str | None; attempt_number: int; status: str; reason: str; started_at: datetime | None; completed_at: datetime | None; error_message: str | None
    model_config = {"from_attributes": True}


class RecoveryEventRead(BaseModel):
    id: UUID; incident_id: UUID; event_type: str; message: str; metadata_json: dict | None; created_at: datetime
    model_config = {"from_attributes": True}


class RecoverRequest(BaseModel):
    action: Literal["RESTART_CONTAINER", "REPLACE_REPLICA", "RESTART_SERVICE", "RECONCILE_SERVICE"] | None = None
    dry_run: bool = False


class RecoveryPolicyUpdate(BaseModel):
    enabled: bool = True
    dry_run: bool = False
    simulation_mode: bool = False
    max_attempts: int = Field(default=3, ge=1, le=10)
    cooldown_seconds: int = Field(default=60, ge=0, le=3600)
    verification_timeout_seconds: int = Field(default=120, ge=5, le=3600)


class RecoveryPolicyRead(RecoveryPolicyUpdate):
    id: UUID; project_id: UUID; deployment_id: UUID; service_id: str
    model_config = {"from_attributes": True}

"""Pydantic schemas defining the complete Infrastructure Plan contract."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ReplicasConfig(BaseModel):
    min: int = Field(default=1, ge=1, le=10)
    max: int = Field(default=1, ge=1, le=10)
    initial: int = Field(default=1, ge=1, le=10)


class ServiceDefinition(BaseModel):
    id: str
    name: str
    type: Literal["application", "worker", "database", "cache", "queue", "storage", "gateway"]
    runtime: str | None = None
    framework: str | None = None
    source_path: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    protocol: Literal["http", "https", "tcp", "udp"] = "http"
    public: bool = False
    replicas: ReplicasConfig = Field(default_factory=ReplicasConfig)
    scalable: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class ServiceDependency(BaseModel):
    source: str
    target: str
    dependency_type: Literal["database", "cache", "queue", "http", "other"] = "other"
    required: bool = True


class NetworkDefinition(BaseModel):
    name: str = "cloudpilot-internal"
    type: Literal["private", "public", "overlay"] = "private"


class VolumeDefinition(BaseModel):
    name: str
    service: str
    persistent: bool = True
    mount_path: str = "/data"


class EnvironmentVariable(BaseModel):
    name: str
    source: str | None = None
    secret: bool = False
    required: bool = True
    default: str | None = None


class ServiceEnvironment(BaseModel):
    service: str
    variables: list[EnvironmentVariable] = Field(default_factory=list)


class ScalingPolicy(BaseModel):
    service: str
    metric: Literal["cpu", "memory", "request_count", "p95_latency"] = "cpu"
    scale_up_threshold: int = Field(default=75, ge=1, le=100)
    scale_down_threshold: int = Field(default=30, ge=0, le=100)
    cooldown_seconds: int = Field(default=60, ge=10, le=600)


class ResourceProfile(BaseModel):
    service: str
    cpu: str = "0.5"        # e.g., "0.5" or "500m"
    memory: str = "512Mi"   # e.g., "512Mi" or "1Gi"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    reason: str = "Estimated baseline allocation"


class HealthCheck(BaseModel):
    service: str
    type: Literal["http", "tcp", "command"] = "http"
    path: str | None = "/health"
    port: int | None = Field(default=None, ge=1, le=65535)
    interval_seconds: int = Field(default=10, ge=1, le=300)
    timeout_seconds: int = Field(default=3, ge=1, le=60)
    failure_threshold: int = Field(default=3, ge=1, le=10)


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    runtime: str | None = None
    framework: str | None = None
    public: bool = False
    replicas: int = 1


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = "depends_on"
    dependency_type: str = "other"


class ArchitectureGraph(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class RiskItem(BaseModel):
    risk: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    description: str
    mitigation: str | None = None


class AIExplanation(BaseModel):
    summary: str
    architecture_choice: str
    scaling_reasoning: str
    security_notes: str


class ApplicationInfo(BaseModel):
    name: str
    architecture_type: Literal["single_service", "multi_service", "monorepo"] = "multi_service"


class InfrastructurePlan(BaseModel):
    plan_version: str = "1.0"
    generated_at: str | None = None
    analyzer_version: str = "2.0"
    planner_version: str = "1.0"
    application: ApplicationInfo
    services: list[ServiceDefinition] = Field(default_factory=list)
    networks: list[NetworkDefinition] = Field(default_factory=list)
    volumes: list[VolumeDefinition] = Field(default_factory=list)
    dependencies: list[ServiceDependency] = Field(default_factory=list)
    environment: list[ServiceEnvironment] = Field(default_factory=list)
    scaling: list[ScalingPolicy] = Field(default_factory=list)
    health_checks: list[HealthCheck] = Field(default_factory=list)
    resource_profiles: list[ResourceProfile] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    graph: ArchitectureGraph = Field(default_factory=ArchitectureGraph)
    explanation: AIExplanation
    deployment_order: list[str] = Field(default_factory=list)

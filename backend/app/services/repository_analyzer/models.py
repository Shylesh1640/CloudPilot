"""Normalized data models for repository profile output and detector results."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DetectionEvidence:
    description: str
    file_path: str | None = None
    snippet: str | None = None


@dataclass
class DetectionItem:
    name: str
    confidence: float  # 0.0 to 1.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class DatabaseDetection:
    name: str
    confidence: float
    certainty: str  # "Detected", "Likely", "Possible"
    evidence: list[str] = field(default_factory=list)


@dataclass
class PortInfo:
    port: int
    service: str
    port_type: str = "application_port"  # application_port, service_port, host_port
    source: str = ""


@dataclass
class EnvVarInfo:
    name: str
    sensitive: bool = False
    source: str = ""


@dataclass
class ServiceInfo:
    name: str
    type: str  # "application", "database", "cache", "queue", "worker"
    runtime: str | None = None
    framework: str | None = None
    port: int | None = None
    confidence: float = 1.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class DockerInfo:
    detected: bool = False
    has_dockerfile: bool = False
    has_compose: bool = False
    base_image: str | None = None
    exposed_ports: list[int] = field(default_factory=list)
    workdir: str | None = None
    compose_services: list[str] = field(default_factory=list)


@dataclass
class LanguageDistribution:
    primary: str
    distribution: dict[str, float] = field(default_factory=dict)  # Language name -> percentage


@dataclass
class RepositoryInfo:
    owner: str
    name: str
    url: str
    commit_sha: str | None = None


@dataclass
class RepositoryProfile:
    repository: RepositoryInfo
    languages: LanguageDistribution
    package_managers: list[str] = field(default_factory=list)
    frameworks: list[DetectionItem] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)  # manager -> list of packages
    databases: list[DatabaseDetection] = field(default_factory=list)
    caches: list[DetectionItem] = field(default_factory=list)
    queues: list[DetectionItem] = field(default_factory=list)
    containers: DockerInfo = field(default_factory=DockerInfo)
    ports: list[PortInfo] = field(default_factory=list)
    environment_variables: list[EnvVarInfo] = field(default_factory=list)
    services: list[ServiceInfo] = field(default_factory=list)
    is_monorepo: bool = False
    monorepo_apps: list[str] = field(default_factory=list)
    readme_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

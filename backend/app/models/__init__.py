"""Package marker — imports all models so SQLAlchemy metadata is populated."""
from app.models.user import User
from app.models.project import Project
from app.models.repository_analysis import RepositoryAnalysis
from app.models.infrastructure_plan import InfrastructurePlanModel
from app.models.deployment import DeploymentModel, DeploymentServiceModel
from app.models.health import ServiceHealthModel, HealthCheckRecordModel, HealthEventModel
from app.models.observability import ContainerMetricsModel, ObservabilityEventModel
from app.models.autoscaling import ScalingDecisionModel, ScalingEventModel, ScalingPolicyModel, TrafficRunModel
from app.models.self_healing import AuditLogModel, FailureInjectionModel, IncidentModel, RecoveryAttemptModel, RecoveryEventModel, RecoveryPolicyModel
from app.models.ai_incident import AIDecisionTraceModel, IncidentMemoryModel

__all__ = [
    "User",
    "Project",
    "RepositoryAnalysis",
    "InfrastructurePlanModel",
    "DeploymentModel",
    "DeploymentServiceModel",
    "ServiceHealthModel",
    "HealthCheckRecordModel",
    "HealthEventModel",
    "ContainerMetricsModel",
    "ObservabilityEventModel",
    "ScalingPolicyModel",
    "ScalingDecisionModel",
    "ScalingEventModel",
    "TrafficRunModel",
    "FailureInjectionModel", "IncidentModel", "RecoveryPolicyModel", "RecoveryAttemptModel", "RecoveryEventModel", "AuditLogModel",
    "IncidentMemoryModel", "AIDecisionTraceModel",
]

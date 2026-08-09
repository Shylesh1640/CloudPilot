from app.services.self_healing.classifier import FailureClassifier
from app.services.self_healing.models import RecoveryAction
from app.services.self_healing.policy_engine import RecoveryPolicyEngine
from app.services.self_healing.retry import backoff_seconds


def test_dependency_diagnosis_recovers_only_root_service():
    plan = {"dependencies": [{"source": "api", "target": "postgres", "required": True}, {"source": "frontend", "target": "api", "required": True}]}
    diagnosis = FailureClassifier.diagnose("api", "running", {"api": "UNHEALTHY", "postgres": "FAILED"}, plan)
    assert diagnosis.root_service_id == "postgres"
    assert diagnosis.impacted_services == ["api", "frontend"]


def test_single_failed_replica_uses_least_disruptive_restart():
    diagnosis = FailureClassifier.diagnose("api", "exited", {"api": "FAILED"}, {"dependencies": []})
    decision = RecoveryPolicyEngine.decide(diagnosis, "container-2", replica_count=2, desired_replicas=2)
    assert decision.action == RecoveryAction.RESTART_CONTAINER


def test_backoff_is_exponential_and_bounded_by_attempt_count():
    assert [backoff_seconds(attempt) for attempt in (1, 2, 3)] == [5, 10, 20]

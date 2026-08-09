"""Scaling remains owned by Phase 7 and is never an automatic Phase 8 action."""
from app.services.self_healing.models import RecoveryAction

ACTION = RecoveryAction.ESCALATE

"""Backward-compatible Phase 7 autoscaling exports.

New code should import from :mod:`app.services.autoscaling`; this module keeps
older callers from landing on the former Phase 7 stub.
"""
from app.services.autoscaling.evaluator import AutoscalingEvaluator
from app.services.autoscaling.scaler import Autoscaler

__all__ = ["Autoscaler", "AutoscalingEvaluator"]

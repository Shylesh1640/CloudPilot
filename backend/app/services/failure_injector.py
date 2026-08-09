"""Backward-compatible export for the bounded Phase 8 failure injector."""
from app.services.self_healing.injection.controller import FailureInjectionController as FailureInjector

__all__ = ["FailureInjector"]

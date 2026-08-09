from datetime import datetime, timezone


def cooldown_remaining(last_recovery_at, seconds: int) -> int:
    if not last_recovery_at:
        return 0
    return max(0, int(seconds - (datetime.now(timezone.utc) - last_recovery_at).total_seconds()))

from app.services.self_healing.retry import backoff_seconds


def attempts_exhausted(attempts: int, maximum: int) -> bool:
    return attempts >= maximum

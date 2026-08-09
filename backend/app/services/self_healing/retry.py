def backoff_seconds(attempt_number: int, base_delay_seconds: int = 5) -> int:
    return base_delay_seconds * (2 ** max(0, attempt_number - 1))

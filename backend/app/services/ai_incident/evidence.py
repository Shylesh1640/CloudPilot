from __future__ import annotations

import re

_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|secret|authorization|jwt)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]+"),
    re.compile(r"\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b"),
    re.compile(r"(?i)(postgres(?:ql)?|mysql|redis)://[^\s@]+@[^\s]+"),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----.*?-----END [A-Z ]+ PRIVATE KEY-----", re.S),
]


def redact(value: str) -> str:
    for pattern in _PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value


def redact_structure(value):
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [redact_structure(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_structure(item) for key, item in value.items() if key.lower() not in {"email", "user", "user_id", "created_by"}}
    return value

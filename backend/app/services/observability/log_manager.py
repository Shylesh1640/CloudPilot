"""LogManager — retrieves container logs and parses log levels."""
from __future__ import annotations

import datetime
import re
from typing import Any

from app.services.observability.schemas import LogEntriesRead, LogEntry
from app.services.orchestrator import ContainerRuntime, DockerRuntime


def parse_log_level(message: str) -> str:
    """Extracts log level (ERROR, WARN, INFO, DEBUG) from log line text."""
    msg_upper = message.upper()
    if "ERROR" in msg_upper or "EXCEPTION" in msg_upper or "FATAL" in msg_upper or "FAIL" in msg_upper:
        return "ERROR"
    elif "WARN" in msg_upper or "WARNING" in msg_upper:
        return "WARN"
    elif "DEBUG" in msg_upper:
        return "DEBUG"
    else:
        return "INFO"


class LogManager:
    def __init__(self, runtime: ContainerRuntime | None = None) -> None:
        self.runtime = runtime or DockerRuntime()

    def get_container_logs(
        self,
        service_id: str,
        container_name_or_id: str,
        tail: int = 100,
        level_filter: str | None = None,
        search_term: str | None = None,
    ) -> LogEntriesRead:
        raw_logs = self.runtime.get_container_logs(container_name_or_id, tail=tail * 2)
        entries: list[LogEntry] = []

        lines = raw_logs.splitlines() if raw_logs else []
        for line in lines:
            if not line.strip():
                continue

            # Parse ISO timestamp prefix if present
            match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+(.*)$", line)
            if match:
                ts = match.group(1)
                text = match.group(2)
            else:
                ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
                text = line

            level = parse_log_level(text)

            if level_filter and level_filter.upper() != "ALL" and level != level_filter.upper():
                continue

            if search_term and search_term.lower() not in text.lower():
                continue

            entries.append(LogEntry(timestamp=ts, level=level, message=text))

        # Enforce requested limit
        trimmed = entries[-tail:] if len(entries) > tail else entries
        return LogEntriesRead(
            service_id=service_id,
            lines=trimmed,
            logs=[l.message for l in trimmed],
        )

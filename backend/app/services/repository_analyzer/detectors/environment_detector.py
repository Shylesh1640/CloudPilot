"""Environment variable detector — extracts variable names from sample files without storing secrets."""
from __future__ import annotations

import re
from app.services.repository_analyzer.models import EnvVarInfo
from app.services.repository_analyzer.scanner import ScanResult

SENSITIVE_KEYWORDS = {
    "SECRET",
    "KEY",
    "PASSWORD",
    "PASS",
    "TOKEN",
    "PRIVATE",
    "CREDENTIAL",
    "AUTH",
    "JWT",
    "DATABASE_URL",
    "DB_URL",
    "REDIS_URL",
    "CONN_STR",
}


class EnvironmentDetector:
    def detect(self, scan_result: ScanResult) -> list[EnvVarInfo]:
        env_vars: list[EnvVarInfo] = []
        seen_names: set[str] = set()

        for f in scan_result.files:
            filename = f.relative_path.split("/")[-1].lower()
            if filename in (".env.example", ".env.sample", ".env.template", ".env.local.example"):
                text = f.read_text()
                if text:
                    for line in text.splitlines():
                        line_str = line.strip()
                        if not line_str or line_str.startswith("#"):
                            continue

                        # Match KEY=VALUE or KEY
                        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=", line_str)
                        if match:
                            var_name = match.group(1)
                            if var_name not in seen_names:
                                seen_names.add(var_name)
                                is_sensitive = any(
                                    kw in var_name.upper() for kw in SENSITIVE_KEYWORDS
                                )
                                env_vars.append(
                                    EnvVarInfo(
                                        name=var_name,
                                        sensitive=is_sensitive,
                                        source=f.relative_path,
                                    )
                                )

        return env_vars

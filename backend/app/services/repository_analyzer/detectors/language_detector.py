"""Language detector — calculates language distribution based on file extensions."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from app.services.repository_analyzer.models import LanguageDistribution
from app.services.repository_analyzer.scanner import ScanResult

# File extension → Language name
EXTENSION_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".java": "Java",
    ".rs": "Rust",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".md": "Markdown",
    ".dockerfile": "Dockerfile",
}


class LanguageDetector:
    def detect(self, scan_result: ScanResult) -> LanguageDistribution:
        lang_counts: Counter[str] = Counter()

        for scanned_file in scan_result.files:
            ext = Path(scanned_file.relative_path).suffix.lower()
            if ext in EXTENSION_MAP:
                lang = EXTENSION_MAP[ext]
                # Filter out pure markup/config from primary calculation if source files exist
                lang_counts[lang] += 1

        if not lang_counts:
            return LanguageDistribution(primary="Unknown", distribution={})

        total_files = sum(lang_counts.values())
        distribution: dict[str, float] = {
            lang: round((count / total_files) * 100, 1)
            for lang, count in lang_counts.most_common(10)
        }

        # Filter programming languages for primary language (ignore purely HTML/CSS/JSON/Markdown if code exists)
        code_langs = {
            lang: pct for lang, pct in distribution.items()
            if lang not in {"HTML", "CSS", "SCSS", "JSON", "YAML", "Markdown"}
        }

        primary = max(code_langs, key=code_langs.get) if code_langs else max(distribution, key=distribution.get)

        return LanguageDistribution(
            primary=primary,
            distribution=distribution,
        )

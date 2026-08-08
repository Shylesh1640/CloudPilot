"""Unit tests for repository analyzer engine and detectors using test fixtures."""
from __future__ import annotations

from pathlib import Path
import pytest

from app.services.repository_analyzer import RepositoryAnalyzer, parse_github_url, InvalidGitHubURL

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_github_url_valid():
    owner, repo = parse_github_url("https://github.com/fastapi/fastapi")
    assert owner == "fastapi"
    assert repo == "fastapi"

    owner, repo = parse_github_url("https://github.com/my-org/my-app.git/")
    assert owner == "my-org"
    assert repo == "my-app"


def test_parse_github_url_invalid():
    with pytest.raises(InvalidGitHubURL):
        parse_github_url("https://gitlab.com/user/repo")

    with pytest.raises(InvalidGitHubURL):
        parse_github_url("https://github.com/invalid")


def test_analyze_fastapi_react_fixture():
    fixture_dir = FIXTURES_DIR / "fastapi_react"
    analyzer = RepositoryAnalyzer()
    profile = analyzer.analyze(
        repo_dir=fixture_dir,
        repo_url="https://github.com/example/fastapi-react",
        owner="example",
        name="fastapi-react",
    )

    # Frameworks
    fw_names = [f.name for f in profile.frameworks]
    assert "FastAPI" in fw_names
    assert "React" in fw_names

    # Databases & Caches & Queues
    db_names = [d.name for d in profile.databases]
    assert "PostgreSQL" in db_names

    cache_names = [c.name for c in profile.caches]
    assert "Redis" in cache_names

    queue_names = [q.name for q in profile.queues]
    assert "Celery" in queue_names

    # Docker & Ports
    assert profile.containers.detected is True
    assert profile.containers.has_dockerfile is True
    assert profile.containers.has_compose is True

    port_numbers = [p.port for p in profile.ports]
    assert 8000 in port_numbers


def test_analyze_node_express_fixture():
    fixture_dir = FIXTURES_DIR / "node_express"
    analyzer = RepositoryAnalyzer()
    profile = analyzer.analyze(
        repo_dir=fixture_dir,
        repo_url="https://github.com/example/node-express",
        owner="example",
        name="node-express",
    )

    fw_names = [f.name for f in profile.frameworks]
    assert "Express" in fw_names

    db_names = [d.name for d in profile.databases]
    assert "MongoDB" in db_names


def test_analyze_django_fixture():
    fixture_dir = FIXTURES_DIR / "django_app"
    analyzer = RepositoryAnalyzer()
    profile = analyzer.analyze(
        repo_dir=fixture_dir,
        repo_url="https://github.com/example/django-app",
        owner="example",
        name="django-app",
    )

    fw_names = [f.name for f in profile.frameworks]
    assert "Django" in fw_names

    db_names = [d.name for d in profile.databases]
    assert "PostgreSQL" in db_names


def test_analyze_spring_boot_fixture():
    fixture_dir = FIXTURES_DIR / "spring_boot"
    analyzer = RepositoryAnalyzer()
    profile = analyzer.analyze(
        repo_dir=fixture_dir,
        repo_url="https://github.com/example/spring-boot-app",
        owner="example",
        name="spring-boot-app",
    )

    fw_names = [f.name for f in profile.frameworks]
    assert "Spring Boot" in fw_names


def test_analyze_go_service_fixture():
    fixture_dir = FIXTURES_DIR / "go_service"
    analyzer = RepositoryAnalyzer()
    profile = analyzer.analyze(
        repo_dir=fixture_dir,
        repo_url="https://github.com/example/go-service",
        owner="example",
        name="go-service",
    )

    fw_names = [f.name for f in profile.frameworks]
    assert "Gin" in fw_names

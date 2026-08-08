"""Integration tests for repository analysis API endpoints."""
from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fastapi_react"


@pytest.mark.asyncio
async def test_trigger_analysis_invalid_url(client: AsyncClient, auth_headers: dict[str, str]):
    # Create project first
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "test-proj-url-val"},
        headers=auth_headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Post invalid URL
    resp = await client.post(
        f"/api/v1/projects/{project_id}/repositories/analyze",
        json={"repository_url": "https://gitlab.com/user/repo"},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)
    err_str = str(resp.json())
    assert "GitHub" in err_str or "github" in err_str.lower()


@pytest.mark.asyncio
async def test_trigger_and_fetch_analysis(client: AsyncClient, auth_headers: dict[str, str]):
    # Create project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "test-proj-analysis"},
        headers=auth_headers,
    )
    project_id = proj_resp.json()["id"]

    # Trigger analysis
    # Patch clone_repository to use local fixture repo directory
    url = "https://github.com/example/fastapi-react"
    fixture_dir = str(FIXTURES_DIR)

    @contextmanager
    def mock_clone(url):
        yield fixture_dir, "abc12345"

    with patch("app.services.analysis_service.clone_repository", side_effect=mock_clone):
        resp = await client.post(
            f"/api/v1/projects/{project_id}/repositories/analyze",
            json={"repository_url": url},
            headers=auth_headers,
        )
        assert resp.status_code == 202
    analysis_data = resp.json()
    analysis_id = analysis_data["id"]
    assert analysis_data["status"] == "PENDING"
    assert analysis_data["repository_owner"] == "example"
    assert analysis_data["repository_name"] == "fastapi-react"

    # Fetch status
    status_resp = await client.get(
        f"/api/v1/repository-analyses/{analysis_id}",
        headers=auth_headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == analysis_id

    # Fetch result
    result_resp = await client.get(
        f"/api/v1/repository-analyses/{analysis_id}/result",
        headers=auth_headers,
    )
    assert result_resp.status_code == 200
    assert result_resp.json()["id"] == analysis_id

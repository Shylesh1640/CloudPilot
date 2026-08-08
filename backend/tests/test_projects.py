"""Tests for project CRUD endpoints — including authorization."""
import pytest
from httpx import AsyncClient


async def create_other_user_and_headers(client: AsyncClient) -> dict:
    """Helper: register a second user and return their auth headers."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Other User",
            "email": "other@example.com",
            "password": "otherpassword123",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "otherpassword123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── List ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_projects_empty(client: AsyncClient, auth_headers: dict):
    """A new user has no projects."""
    response = await client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_projects_unauthenticated(client: AsyncClient):
    """Listing projects without a token returns 401."""
    response = await client.get("/api/v1/projects")
    assert response.status_code == 401


# ── Create ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers: dict):
    """POST /api/v1/projects should create a project."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": "My App", "description": "A test project"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My App"
    assert data["description"] == "A test project"
    assert data["status"] == "CREATED"
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_create_project_unauthenticated(client: AsyncClient):
    """Creating a project without a token returns 401."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Hack"},
    )
    assert response.status_code == 401


# ── Get single ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, auth_headers: dict):
    """GET /api/v1/projects/{id} returns the project."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Specific Project"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == project_id


@pytest.mark.asyncio
async def test_get_nonexistent_project(client: AsyncClient, auth_headers: dict):
    """GET /api/v1/projects/{fake_id} returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/projects/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, auth_headers: dict):
    """PUT /api/v1/projects/{id} updates the project."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Old Name"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "New Name", "description": "Updated"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Updated"


# ── Delete ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, auth_headers: dict):
    """DELETE /api/v1/projects/{id} removes the project."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Deletable Project"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    get_resp = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert get_resp.status_code == 404


# ── Authorization ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_project_authorization(client: AsyncClient, auth_headers: dict):
    """User A cannot access User B's projects."""
    # User A creates a project
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Private Project"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    # User B tries to access it
    other_headers = await create_other_user_and_headers(client)
    response = await client.get(f"/api/v1/projects/{project_id}", headers=other_headers)
    assert response.status_code == 404  # Must not expose 403 to avoid info leakage


@pytest.mark.asyncio
async def test_user_cannot_delete_others_project(client: AsyncClient, auth_headers: dict):
    """User B cannot delete User A's project."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Protected Project"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    other_headers = await create_other_user_and_headers(client)
    response = await client.delete(f"/api/v1/projects/{project_id}", headers=other_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_projects_are_user_scoped(client: AsyncClient, auth_headers: dict):
    """User B's project list does not include User A's projects."""
    # User A creates a project
    await client.post(
        "/api/v1/projects",
        json={"name": "User A Project"},
        headers=auth_headers,
    )

    # User B lists their projects — should be empty
    other_headers = await create_other_user_and_headers(client)
    response = await client.get("/api/v1/projects", headers=other_headers)
    assert response.status_code == 200
    assert response.json() == []

"""Integration tests for storefront admin endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient


# ============================================================================
# Create Storefront Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_storefront_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test successfully creating a storefront."""
    response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["storefront_id"] == sample_storefront_data["storefront_id"]
    assert data["name"] == sample_storefront_data["name"]
    assert data["domain"] == sample_storefront_data["domain"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_storefront_without_optional_fields(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test creating storefront with only required fields."""
    data = {
        "storefront_id": "minimal-store",
        "name": "Minimal Store",
    }

    response = await client.post(
        "/admin/v1/storefronts",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    result = response.json()
    assert result["storefront_id"] == "minimal-store"
    assert result["domain"] is None
    assert result["description"] is None


@pytest.mark.asyncio
async def test_create_storefront_normalizes_id(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that storefront_id is normalized to lowercase."""
    data = {
        "storefront_id": "UPPER-CASE-STORE",
        "name": "Upper Case Store",
    }

    response = await client.post(
        "/admin/v1/storefronts",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    result = response.json()
    assert result["storefront_id"] == "upper-case-store"


@pytest.mark.asyncio
async def test_create_storefront_inactive(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test creating an inactive storefront."""
    data = {
        "storefront_id": "inactive-new",
        "name": "Inactive New Store",
        "is_active": False,
    }

    response = await client.post(
        "/admin/v1/storefronts",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    result = response.json()
    assert result["is_active"] is False


@pytest.mark.asyncio
async def test_create_duplicate_storefront_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test that creating duplicate storefront_id fails."""
    # Create first storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    # Try to create duplicate
    response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_storefront_invalid_id_fails(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that invalid storefront_id fails validation."""
    data = {
        "storefront_id": "invalid store!@#",
        "name": "Invalid Store",
    }

    response = await client.post(
        "/admin/v1/storefronts",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_storefront_missing_required_fields_fails(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that missing required fields fails validation."""
    response = await client.post(
        "/admin/v1/storefronts",
        json={"name": "Missing ID"},
        headers=auth_headers,
    )

    assert response.status_code == 422


# ============================================================================
# Get Storefront Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_storefront_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test getting a storefront by ID."""
    # Create storefront
    create_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = create_response.json()["id"]

    # Get storefront
    response = await client.get(
        f"/admin/v1/storefronts/{storefront_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == storefront_id
    assert data["storefront_id"] == sample_storefront_data["storefront_id"]
    assert data["name"] == sample_storefront_data["name"]


@pytest.mark.asyncio
async def test_get_storefront_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test getting non-existent storefront returns 404."""
    response = await client.get(
        "/admin/v1/storefronts/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# List Storefronts Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_storefronts_empty(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing storefronts when none exist."""
    response = await client.get(
        "/admin/v1/storefronts",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_storefronts_with_data(
    client: AsyncClient,
    auth_headers: dict,
    multiple_storefronts_data: list[dict[str, Any]],
):
    """Test listing storefronts with data."""
    # Create multiple storefronts
    for sf_data in multiple_storefronts_data:
        await client.post(
            "/admin/v1/storefronts",
            json=sf_data,
            headers=auth_headers,
        )

    # List storefronts
    response = await client.get(
        "/admin/v1/storefronts",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_storefronts_pagination(
    client: AsyncClient,
    auth_headers: dict,
    multiple_storefronts_data: list[dict[str, Any]],
):
    """Test listing storefronts with pagination."""
    # Create storefronts
    for sf_data in multiple_storefronts_data:
        await client.post(
            "/admin/v1/storefronts",
            json=sf_data,
            headers=auth_headers,
        )

    # List with limit
    response = await client.get(
        "/admin/v1/storefronts?skip=0&limit=2",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_list_storefronts_filter_active(
    client: AsyncClient,
    auth_headers: dict,
    multiple_storefronts_data: list[dict[str, Any]],
):
    """Test listing storefronts filtered by is_active."""
    # Create storefronts (includes one inactive)
    for sf_data in multiple_storefronts_data:
        await client.post(
            "/admin/v1/storefronts",
            json=sf_data,
            headers=auth_headers,
        )

    # List only active
    response = await client.get(
        "/admin/v1/storefronts?is_active=true",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # Only 2 active storefronts
    assert all(item["is_active"] is True for item in data["items"])


@pytest.mark.asyncio
async def test_list_storefronts_filter_inactive(
    client: AsyncClient,
    auth_headers: dict,
    multiple_storefronts_data: list[dict[str, Any]],
):
    """Test listing storefronts filtered by is_active=false."""
    # Create storefronts
    for sf_data in multiple_storefronts_data:
        await client.post(
            "/admin/v1/storefronts",
            json=sf_data,
            headers=auth_headers,
        )

    # List only inactive
    response = await client.get(
        "/admin/v1/storefronts?is_active=false",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1  # Only 1 inactive storefront
    assert all(item["is_active"] is False for item in data["items"])


# ============================================================================
# Update Storefront Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_storefront_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test updating a storefront."""
    # Create storefront
    create_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = create_response.json()["id"]

    # Update storefront
    response = await client.put(
        f"/admin/v1/storefronts/{storefront_id}",
        json={"name": "Updated Store Name", "is_active": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Store Name"
    assert data["is_active"] is False
    # Original storefront_id should be unchanged
    assert data["storefront_id"] == sample_storefront_data["storefront_id"]


@pytest.mark.asyncio
async def test_update_storefront_partial(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test partial update of storefront."""
    # Create storefront
    create_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = create_response.json()["id"]

    # Update only description
    response = await client.put(
        f"/admin/v1/storefronts/{storefront_id}",
        json={"description": "New description"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "New description"
    # Other fields unchanged
    assert data["name"] == sample_storefront_data["name"]
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_update_storefront_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test updating non-existent storefront returns 404."""
    response = await client.put(
        "/admin/v1/storefronts/99999",
        json={"name": "Updated"},
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Delete Storefront Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_storefront_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test deleting a storefront."""
    # Create storefront
    create_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = create_response.json()["id"]

    # Delete storefront
    response = await client.delete(
        f"/admin/v1/storefronts/{storefront_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/admin/v1/storefronts/{storefront_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_storefront_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test deleting non-existent storefront returns 404."""
    response = await client.delete(
        "/admin/v1/storefronts/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_storefront_unauthorized(
    client: AsyncClient,
    sample_storefront_data: dict,
):
    """Test that creating storefront without auth fails."""
    response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_storefront_unauthorized(
    client: AsyncClient,
):
    """Test that getting storefront without auth fails."""
    response = await client.get("/admin/v1/storefronts/1")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_storefronts_unauthorized(
    client: AsyncClient,
):
    """Test that listing storefronts without auth fails."""
    response = await client.get("/admin/v1/storefronts")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_storefront_unauthorized(
    client: AsyncClient,
):
    """Test that updating storefront without auth fails."""
    response = await client.put(
        "/admin/v1/storefronts/1",
        json={"name": "Updated"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_storefront_unauthorized(
    client: AsyncClient,
):
    """Test that deleting storefront without auth fails."""
    response = await client.delete("/admin/v1/storefronts/1")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_storefront_invalid_auth(
    client: AsyncClient,
    invalid_auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test that creating storefront with invalid auth fails."""
    response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=invalid_auth_headers,
    )

    assert response.status_code == 401

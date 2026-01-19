"""Integration tests for platform admin endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient


# ============================================================================
# Create Platform Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_platform_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_platform_data: dict,
):
    """Test successfully creating a platform."""
    response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["platform_code"] == sample_platform_data["platform_code"]
    assert data["name"] == sample_platform_data["name"]
    assert data["tier"] == sample_platform_data["tier"]
    assert data["category"] == sample_platform_data["category"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_platform_normalizes_code(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that platform_code is normalized to lowercase."""
    data = {
        "platform_code": "UPPER_CASE_PLATFORM",
        "name": "Upper Case Platform",
    }

    response = await client.post(
        "/admin/v1/platforms",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    result = response.json()
    assert result["platform_code"] == "upper_case_platform"


@pytest.mark.asyncio
async def test_create_platform_tier_1(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test creating tier 1 (critical) platform."""
    data = {
        "platform_code": "critical_platform",
        "name": "Critical Platform",
        "tier": 1,
    }

    response = await client.post(
        "/admin/v1/platforms",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    result = response.json()
    assert result["tier"] == 1


@pytest.mark.asyncio
async def test_create_platform_tier_3(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test creating tier 3 (standard) platform."""
    data = {
        "platform_code": "standard_platform",
        "name": "Standard Platform",
        "tier": 3,
    }

    response = await client.post(
        "/admin/v1/platforms",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    result = response.json()
    assert result["tier"] == 3


@pytest.mark.asyncio
async def test_create_duplicate_platform_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_platform_data: dict,
):
    """Test that creating duplicate platform_code fails."""
    # Create first platform
    await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )

    # Try to create duplicate
    response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_platform_invalid_code_fails(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that invalid platform_code fails validation."""
    data = {
        "platform_code": "invalid-platform-code!",  # Hyphens not allowed
        "name": "Invalid Platform",
    }

    response = await client.post(
        "/admin/v1/platforms",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_platform_invalid_tier_fails(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that invalid tier fails validation."""
    data = {
        "platform_code": "invalid_tier",
        "name": "Invalid Tier Platform",
        "tier": 5,  # Invalid tier
    }

    response = await client.post(
        "/admin/v1/platforms",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == 422


# ============================================================================
# Get Platform Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_platform_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_platform_data: dict,
):
    """Test getting a platform by ID."""
    # Create platform
    create_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = create_response.json()["id"]

    # Get platform
    response = await client.get(
        f"/admin/v1/platforms/{platform_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == platform_id
    assert data["platform_code"] == sample_platform_data["platform_code"]


@pytest.mark.asyncio
async def test_get_platform_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test getting non-existent platform returns 404."""
    response = await client.get(
        "/admin/v1/platforms/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# List Platforms Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_platforms_empty(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing platforms when none exist."""
    response = await client.get(
        "/admin/v1/platforms",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_platforms_with_data(
    client: AsyncClient,
    auth_headers: dict,
    multiple_platforms_data: list[dict[str, Any]],
):
    """Test listing platforms with data."""
    # Create platforms
    for pf_data in multiple_platforms_data:
        await client.post(
            "/admin/v1/platforms",
            json=pf_data,
            headers=auth_headers,
        )

    # List platforms
    response = await client.get(
        "/admin/v1/platforms",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["items"]) == 4


@pytest.mark.asyncio
async def test_list_platforms_filter_by_tier(
    client: AsyncClient,
    auth_headers: dict,
    multiple_platforms_data: list[dict[str, Any]],
):
    """Test listing platforms filtered by tier."""
    # Create platforms
    for pf_data in multiple_platforms_data:
        await client.post(
            "/admin/v1/platforms",
            json=pf_data,
            headers=auth_headers,
        )

    # List tier 1 platforms
    response = await client.get(
        "/admin/v1/platforms?tier=1",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # meta_capi and ga4 are tier 1
    assert all(item["tier"] == 1 for item in data["items"])


@pytest.mark.asyncio
async def test_list_platforms_filter_by_category(
    client: AsyncClient,
    auth_headers: dict,
    multiple_platforms_data: list[dict[str, Any]],
):
    """Test listing platforms filtered by category."""
    # Create platforms
    for pf_data in multiple_platforms_data:
        await client.post(
            "/admin/v1/platforms",
            json=pf_data,
            headers=auth_headers,
        )

    # List advertising platforms
    response = await client.get(
        "/admin/v1/platforms?category=advertising",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert all(item["category"] == "advertising" for item in data["items"])


@pytest.mark.asyncio
async def test_list_platforms_filter_active(
    client: AsyncClient,
    auth_headers: dict,
    multiple_platforms_data: list[dict[str, Any]],
):
    """Test listing platforms filtered by is_active."""
    # Create platforms
    for pf_data in multiple_platforms_data:
        await client.post(
            "/admin/v1/platforms",
            json=pf_data,
            headers=auth_headers,
        )

    # List only active
    response = await client.get(
        "/admin/v1/platforms?is_active=true",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # Only 3 active platforms
    assert all(item["is_active"] is True for item in data["items"])


@pytest.mark.asyncio
async def test_list_platforms_pagination(
    client: AsyncClient,
    auth_headers: dict,
    multiple_platforms_data: list[dict[str, Any]],
):
    """Test listing platforms with pagination."""
    # Create platforms
    for pf_data in multiple_platforms_data:
        await client.post(
            "/admin/v1/platforms",
            json=pf_data,
            headers=auth_headers,
        )

    # List with limit
    response = await client.get(
        "/admin/v1/platforms?skip=0&limit=2",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["items"]) == 2
    assert data["has_more"] is True


# ============================================================================
# Update Platform Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_platform_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_platform_data: dict,
):
    """Test updating a platform."""
    # Create platform
    create_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = create_response.json()["id"]

    # Update platform
    response = await client.put(
        f"/admin/v1/platforms/{platform_id}",
        json={"tier": 1, "is_active": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == 1
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_platform_partial(
    client: AsyncClient,
    auth_headers: dict,
    sample_platform_data: dict,
):
    """Test partial update of platform."""
    # Create platform
    create_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = create_response.json()["id"]

    # Update only name
    response = await client.put(
        f"/admin/v1/platforms/{platform_id}",
        json={"name": "New Platform Name"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Platform Name"
    # Other fields unchanged
    assert data["tier"] == sample_platform_data["tier"]


@pytest.mark.asyncio
async def test_update_platform_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test updating non-existent platform returns 404."""
    response = await client.put(
        "/admin/v1/platforms/99999",
        json={"name": "Updated"},
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Delete Platform Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_platform_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_platform_data: dict,
):
    """Test deleting a platform."""
    # Create platform
    create_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = create_response.json()["id"]

    # Delete platform
    response = await client.delete(
        f"/admin/v1/platforms/{platform_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/admin/v1/platforms/{platform_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_platform_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test deleting non-existent platform returns 404."""
    response = await client.delete(
        "/admin/v1/platforms/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_platform_unauthorized(
    client: AsyncClient,
    sample_platform_data: dict,
):
    """Test that creating platform without auth fails."""
    response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_platforms_unauthorized(
    client: AsyncClient,
):
    """Test that listing platforms without auth fails."""
    response = await client.get("/admin/v1/platforms")

    assert response.status_code == 401

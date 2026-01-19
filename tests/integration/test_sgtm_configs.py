"""Integration tests for sGTM config admin endpoints."""

import pytest
from httpx import AsyncClient


# ============================================================================
# Create sGTM Config Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_sgtm_config_ga4_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_sgtm_config_ga4: dict,
):
    """Test successfully creating a GA4 sGTM config."""
    # Create storefront first
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    # Create sGTM config
    config_data = {**sample_sgtm_config_ga4, "storefront_id": storefront_id}

    response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["storefront_id"] == storefront_id
    assert data["sgtm_url"] == sample_sgtm_config_ga4["sgtm_url"]
    assert data["client_type"] == "ga4"
    assert data["measurement_id"] == sample_sgtm_config_ga4["measurement_id"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_sgtm_config_custom_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_sgtm_config_custom: dict,
):
    """Test successfully creating a custom sGTM config."""
    # Create storefront first
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    # Create sGTM config
    config_data = {**sample_sgtm_config_custom, "storefront_id": storefront_id}

    response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["client_type"] == "custom"
    assert data["custom_endpoint_path"] == sample_sgtm_config_custom["custom_endpoint_path"]


@pytest.mark.asyncio
async def test_create_duplicate_sgtm_config_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_sgtm_config_custom: dict,
):
    """Test that creating duplicate sGTM config for same storefront fails."""
    # Create storefront
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    # Create first config
    config_data = {**sample_sgtm_config_custom, "storefront_id": storefront_id}
    await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )

    # Try to create duplicate
    response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_sgtm_config_invalid_storefront_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_sgtm_config_custom: dict,
):
    """Test that creating sGTM config with non-existent storefront fails."""
    config_data = {**sample_sgtm_config_custom, "storefront_id": 99999}

    response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_sgtm_config_invalid_url_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test that creating sGTM config with invalid URL fails."""
    # Create storefront
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    config_data = {
        "storefront_id": storefront_id,
        "sgtm_url": "not-a-valid-url",
        "client_type": "custom",
    }

    response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_ga4_config_without_measurement_id_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test that GA4 config without measurement_id fails."""
    # Create storefront
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    config_data = {
        "storefront_id": storefront_id,
        "sgtm_url": "https://tags.example.com",
        "client_type": "ga4",
        # Missing measurement_id
    }

    response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )

    assert response.status_code == 422


# ============================================================================
# Get sGTM Config Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_sgtm_config_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_sgtm_config_custom: dict,
):
    """Test getting a sGTM config by ID."""
    # Create storefront and config
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    config_data = {**sample_sgtm_config_custom, "storefront_id": storefront_id}
    create_response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )
    config_id = create_response.json()["id"]

    # Get config
    response = await client.get(
        f"/admin/v1/sgtm-configs/{config_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == config_id
    assert data["storefront_id"] == storefront_id


@pytest.mark.asyncio
async def test_get_sgtm_config_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test getting non-existent sGTM config returns 404."""
    response = await client.get(
        "/admin/v1/sgtm-configs/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# List sGTM Configs Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_sgtm_configs_empty(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing sGTM configs when none exist."""
    response = await client.get(
        "/admin/v1/sgtm-configs",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_sgtm_configs_filter_active(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_sgtm_config_custom: dict,
):
    """Test listing sGTM configs filtered by is_active."""
    # Create storefront and config
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    config_data = {**sample_sgtm_config_custom, "storefront_id": storefront_id}
    await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )

    # List only active
    response = await client.get(
        "/admin/v1/sgtm-configs?is_active=true",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert all(item["is_active"] is True for item in data["items"])


# ============================================================================
# Update sGTM Config Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_sgtm_config_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_sgtm_config_custom: dict,
):
    """Test updating a sGTM config."""
    # Create storefront and config
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    config_data = {**sample_sgtm_config_custom, "storefront_id": storefront_id}
    create_response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )
    config_id = create_response.json()["id"]

    # Update config
    response = await client.put(
        f"/admin/v1/sgtm-configs/{config_id}",
        json={
            "sgtm_url": "https://new-tags.example.com",
            "is_active": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sgtm_url"] == "https://new-tags.example.com"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_sgtm_config_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test updating non-existent sGTM config returns 404."""
    response = await client.put(
        "/admin/v1/sgtm-configs/99999",
        json={"is_active": False},
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Delete sGTM Config Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_sgtm_config_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_sgtm_config_custom: dict,
):
    """Test deleting a sGTM config."""
    # Create storefront and config
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    config_data = {**sample_sgtm_config_custom, "storefront_id": storefront_id}
    create_response = await client.post(
        "/admin/v1/sgtm-configs",
        json=config_data,
        headers=auth_headers,
    )
    config_id = create_response.json()["id"]

    # Delete config
    response = await client.delete(
        f"/admin/v1/sgtm-configs/{config_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/admin/v1/sgtm-configs/{config_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_sgtm_config_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test deleting non-existent sGTM config returns 404."""
    response = await client.delete(
        "/admin/v1/sgtm-configs/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_sgtm_config_unauthorized(
    client: AsyncClient,
):
    """Test that creating sGTM config without auth fails."""
    response = await client.post(
        "/admin/v1/sgtm-configs",
        json={
            "storefront_id": 1,
            "sgtm_url": "https://tags.example.com",
            "client_type": "custom",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_sgtm_configs_unauthorized(
    client: AsyncClient,
):
    """Test that listing sGTM configs without auth fails."""
    response = await client.get("/admin/v1/sgtm-configs")

    assert response.status_code == 401

"""Integration tests for credential admin endpoints."""

import pytest
from httpx import AsyncClient


# ============================================================================
# Create Credential Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_credential_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test successfully creating a credential."""
    # Create storefront and platform first
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    # Create credential
    credential_data = {
        "storefront_id": storefront_id,
        "platform_id": platform_id,
        "credentials": sample_credentials,
        "destination_type": "sgtm",
        "pixel_id": "pixel_123",
        "account_id": "account_456",
        "is_active": True,
    }

    response = await client.post(
        "/admin/v1/credentials",
        json=credential_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["storefront_id"] == storefront_id
    assert data["platform_id"] == platform_id
    assert data["destination_type"] == "sgtm"
    assert data["pixel_id"] == "pixel_123"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    # Credentials should NOT be returned in response
    assert "credentials" not in data or data.get("credentials") is None


@pytest.mark.asyncio
async def test_create_credential_direct_destination(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test creating credential with direct destination type."""
    # Create storefront and platform
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    # Create credential with direct destination
    credential_data = {
        "storefront_id": storefront_id,
        "platform_id": platform_id,
        "credentials": sample_credentials,
        "destination_type": "direct",
    }

    response = await client.post(
        "/admin/v1/credentials",
        json=credential_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["destination_type"] == "direct"


@pytest.mark.asyncio
async def test_create_duplicate_credential_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test that creating duplicate credential (same storefront + platform) fails."""
    # Create storefront and platform
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    # Create first credential
    credential_data = {
        "storefront_id": storefront_id,
        "platform_id": platform_id,
        "credentials": sample_credentials,
    }

    await client.post(
        "/admin/v1/credentials",
        json=credential_data,
        headers=auth_headers,
    )

    # Try to create duplicate
    response = await client.post(
        "/admin/v1/credentials",
        json=credential_data,
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_credential_invalid_storefront_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test that creating credential with non-existent storefront fails."""
    # Create platform only
    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    credential_data = {
        "storefront_id": 99999,  # Non-existent
        "platform_id": platform_id,
        "credentials": sample_credentials,
    }

    response = await client.post(
        "/admin/v1/credentials",
        json=credential_data,
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_credential_invalid_platform_fails(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_credentials: dict,
):
    """Test that creating credential with non-existent platform fails."""
    # Create storefront only
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    credential_data = {
        "storefront_id": storefront_id,
        "platform_id": 99999,  # Non-existent
        "credentials": sample_credentials,
    }

    response = await client.post(
        "/admin/v1/credentials",
        json=credential_data,
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Get Credential Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_credential_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test getting a credential by ID."""
    # Create storefront, platform, and credential
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    create_response = await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": storefront_id,
            "platform_id": platform_id,
            "credentials": sample_credentials,
        },
        headers=auth_headers,
    )
    credential_id = create_response.json()["id"]

    # Get credential
    response = await client.get(
        f"/admin/v1/credentials/{credential_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == credential_id
    # Credentials should NOT be returned without decrypt param
    assert "credentials" not in data or data.get("credentials") is None


@pytest.mark.asyncio
async def test_get_credential_with_decrypt(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test getting a credential with decrypted credentials."""
    # Create storefront, platform, and credential
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    create_response = await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": storefront_id,
            "platform_id": platform_id,
            "credentials": sample_credentials,
        },
        headers=auth_headers,
    )
    credential_id = create_response.json()["id"]

    # Get credential with decrypt
    response = await client.get(
        f"/admin/v1/credentials/{credential_id}?decrypt=true",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == credential_id
    # Credentials should be returned
    assert "credentials" in data
    assert data["credentials"]["access_token"] == sample_credentials["access_token"]
    assert data["credentials"]["pixel_id"] == sample_credentials["pixel_id"]


@pytest.mark.asyncio
async def test_get_credential_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test getting non-existent credential returns 404."""
    response = await client.get(
        "/admin/v1/credentials/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# List Credentials Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_credentials_empty(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing credentials when none exist."""
    response = await client.get(
        "/admin/v1/credentials",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_credentials_filter_by_storefront(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test listing credentials filtered by storefront_id."""
    # Create storefront, platform, and credential
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": storefront_id,
            "platform_id": platform_id,
            "credentials": sample_credentials,
        },
        headers=auth_headers,
    )

    # List credentials for storefront
    response = await client.get(
        f"/admin/v1/credentials?storefront_id={storefront_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert all(item["storefront_id"] == storefront_id for item in data["items"])


@pytest.mark.asyncio
async def test_list_credentials_filter_active(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test listing credentials filtered by is_active."""
    # Create storefront and platform
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    # Create active credential
    await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": storefront_id,
            "platform_id": platform_id,
            "credentials": sample_credentials,
            "is_active": True,
        },
        headers=auth_headers,
    )

    # Create another platform for inactive credential
    pf_response2 = await client.post(
        "/admin/v1/platforms",
        json={
            "platform_code": "another_platform",
            "name": "Another Platform",
        },
        headers=auth_headers,
    )
    platform_id2 = pf_response2.json()["id"]

    # Create inactive credential
    await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": storefront_id,
            "platform_id": platform_id2,
            "credentials": sample_credentials,
            "is_active": False,
        },
        headers=auth_headers,
    )

    # List only active
    response = await client.get(
        "/admin/v1/credentials?is_active=true",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert all(item["is_active"] is True for item in data["items"])


# ============================================================================
# Update Credential Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_credential_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test updating a credential."""
    # Create storefront, platform, and credential
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    create_response = await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": storefront_id,
            "platform_id": platform_id,
            "credentials": sample_credentials,
        },
        headers=auth_headers,
    )
    credential_id = create_response.json()["id"]

    # Update credential
    response = await client.put(
        f"/admin/v1/credentials/{credential_id}",
        json={"pixel_id": "new_pixel_789", "is_active": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["pixel_id"] == "new_pixel_789"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_credential_with_new_credentials(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test updating credential with new encrypted credentials."""
    # Create storefront, platform, and credential
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    create_response = await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": storefront_id,
            "platform_id": platform_id,
            "credentials": sample_credentials,
        },
        headers=auth_headers,
    )
    credential_id = create_response.json()["id"]

    # Update with new credentials
    new_credentials = {"access_token": "new_token_xyz_789"}
    response = await client.put(
        f"/admin/v1/credentials/{credential_id}",
        json={"credentials": new_credentials},
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Verify new credentials
    get_response = await client.get(
        f"/admin/v1/credentials/{credential_id}?decrypt=true",
        headers=auth_headers,
    )

    data = get_response.json()
    assert data["credentials"]["access_token"] == "new_token_xyz_789"


@pytest.mark.asyncio
async def test_update_credential_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test updating non-existent credential returns 404."""
    response = await client.put(
        "/admin/v1/credentials/99999",
        json={"is_active": False},
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Delete Credential Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_credential_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_platform_data: dict,
    sample_credentials: dict,
):
    """Test deleting a credential."""
    # Create storefront, platform, and credential
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    storefront_id = sf_response.json()["id"]

    pf_response = await client.post(
        "/admin/v1/platforms",
        json=sample_platform_data,
        headers=auth_headers,
    )
    platform_id = pf_response.json()["id"]

    create_response = await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": storefront_id,
            "platform_id": platform_id,
            "credentials": sample_credentials,
        },
        headers=auth_headers,
    )
    credential_id = create_response.json()["id"]

    # Delete credential
    response = await client.delete(
        f"/admin/v1/credentials/{credential_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/admin/v1/credentials/{credential_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_credential_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test deleting non-existent credential returns 404."""
    response = await client.delete(
        "/admin/v1/credentials/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_credential_unauthorized(
    client: AsyncClient,
):
    """Test that creating credential without auth fails."""
    response = await client.post(
        "/admin/v1/credentials",
        json={
            "storefront_id": 1,
            "platform_id": 1,
            "credentials": {"access_token": "test"},
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_credentials_unauthorized(
    client: AsyncClient,
):
    """Test that listing credentials without auth fails."""
    response = await client.get("/admin/v1/credentials")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_credential_with_decrypt_unauthorized(
    client: AsyncClient,
):
    """Test that getting credential with decrypt without auth fails."""
    response = await client.get("/admin/v1/credentials/1?decrypt=true")

    assert response.status_code == 401

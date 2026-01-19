"""Integration tests for health check endpoints."""

import pytest
from httpx import AsyncClient


# ============================================================================
# Liveness Health Check Tests
# ============================================================================


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    """Test liveness health check returns 200 OK."""
    response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_returns_healthy_status(client: AsyncClient):
    """Test liveness health check returns healthy status."""
    response = await client.get("/health")

    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_endpoint_includes_version(client: AsyncClient):
    """Test liveness health check includes version."""
    response = await client.get("/health")

    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)


@pytest.mark.asyncio
async def test_health_endpoint_includes_environment(client: AsyncClient):
    """Test liveness health check includes environment."""
    response = await client.get("/health")

    data = response.json()
    assert "environment" in data
    assert isinstance(data["environment"], str)


@pytest.mark.asyncio
async def test_health_endpoint_no_auth_required(client: AsyncClient):
    """Test liveness health check does not require authentication."""
    # No auth headers provided
    response = await client.get("/health")

    assert response.status_code == 200


# ============================================================================
# Readiness Health Check Tests
# ============================================================================


@pytest.mark.asyncio
async def test_readiness_endpoint_returns_200(client: AsyncClient):
    """Test readiness health check returns 200 when healthy."""
    response = await client.get("/health/ready")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_readiness_endpoint_returns_ready_status(client: AsyncClient):
    """Test readiness health check returns ready status."""
    response = await client.get("/health/ready")

    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_readiness_endpoint_includes_database_status(client: AsyncClient):
    """Test readiness health check includes database status."""
    response = await client.get("/health/ready")

    data = response.json()
    assert "database" in data
    assert data["database"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_endpoint_no_auth_required(client: AsyncClient):
    """Test readiness health check does not require authentication."""
    # No auth headers provided
    response = await client.get("/health/ready")

    assert response.status_code == 200


# ============================================================================
# Response Format Tests
# ============================================================================


@pytest.mark.asyncio
async def test_health_endpoint_content_type(client: AsyncClient):
    """Test health endpoint returns JSON content type."""
    response = await client.get("/health")

    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_readiness_endpoint_content_type(client: AsyncClient):
    """Test readiness endpoint returns JSON content type."""
    response = await client.get("/health/ready")

    assert "application/json" in response.headers["content-type"]

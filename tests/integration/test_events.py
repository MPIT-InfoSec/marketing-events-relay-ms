"""Integration tests for event ingestion endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient


# ============================================================================
# Event Batch Ingestion Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ingest_event_batch_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
    sample_event_batch_single_storefront: dict,
):
    """Test successfully ingesting a batch of events."""
    # Create storefront first
    sf_response = await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )
    assert sf_response.status_code == 201

    # Ingest events
    response = await client.post(
        "/v1/events",
        json=sample_event_batch_single_storefront,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 2
    assert data["rejected"] == 0
    assert len(data["event_ids"]) == 2
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_ingest_event_batch_multiple_storefronts(
    client: AsyncClient,
    auth_headers: dict,
    sample_event_batch: dict,
):
    """Test ingesting events for multiple storefronts."""
    # Create storefronts for the batch (bosley and pfizer)
    await client.post(
        "/admin/v1/storefronts",
        json={"storefront_id": "bosley", "name": "Bosley Store"},
        headers=auth_headers,
    )
    await client.post(
        "/admin/v1/storefronts",
        json={"storefront_id": "pfizer", "name": "Pfizer Store"},
        headers=auth_headers,
    )

    # Ingest events
    response = await client.post(
        "/v1/events",
        json=sample_event_batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 3
    assert data["rejected"] == 0


@pytest.mark.asyncio
async def test_ingest_event_batch_unknown_storefront_rejected(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that events for unknown storefront are rejected."""
    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": "nonexistent-store",
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "order_unknown_001",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 0
    assert data["rejected"] == 1
    assert len(data["errors"]) == 1
    assert "storefront" in data["errors"][0]["error"].lower()


@pytest.mark.asyncio
async def test_ingest_event_batch_inactive_storefront_rejected(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that events for inactive storefront are rejected."""
    # Create inactive storefront
    await client.post(
        "/admin/v1/storefronts",
        json={
            "storefront_id": "inactive-store",
            "name": "Inactive Store",
            "is_active": False,
        },
        headers=auth_headers,
    )

    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": "inactive-store",
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "order_inactive_001",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 0
    assert data["rejected"] == 1
    # Error should mention kill switch or inactive
    assert len(data["errors"]) == 1


@pytest.mark.asyncio
async def test_ingest_event_batch_duplicate_order_id_rejected(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test that duplicate order_id is rejected."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    # First batch with order_001
    batch1 = {
        "count": 1,
        "data": [
            {
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "duplicate_order_001",
            }
        ],
        "error": "",
    }

    response1 = await client.post(
        "/v1/events",
        json=batch1,
        headers=auth_headers,
    )
    assert response1.status_code == 202
    assert response1.json()["accepted"] == 1

    # Second batch with same order_id (should be rejected)
    batch2 = {
        "count": 1,
        "data": [
            {
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "purchase",
                "event_time": "2026-01-15T11:00:00Z",
                "order_id": "duplicate_order_001",  # Duplicate
            }
        ],
        "error": "",
    }

    response2 = await client.post(
        "/v1/events",
        json=batch2,
        headers=auth_headers,
    )

    assert response2.status_code == 202
    data = response2.json()
    assert data["accepted"] == 0
    assert data["rejected"] == 1
    assert "already exists" in data["errors"][0]["error"].lower() or "duplicate" in data["errors"][0]["error"].lower()


@pytest.mark.asyncio
async def test_ingest_event_batch_partial_success(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test batch with mix of valid and invalid events."""
    # Create only one storefront
    await client.post(
        "/admin/v1/storefronts",
        json={"storefront_id": "valid-store", "name": "Valid Store"},
        headers=auth_headers,
    )

    batch = {
        "count": 3,
        "data": [
            {
                "storefront_id": "valid-store",
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "valid_order_001",
            },
            {
                "storefront_id": "invalid-store",  # Does not exist
                "event_name": "purchase",
                "event_time": "2026-01-15T10:05:00Z",
                "order_id": "invalid_order_001",
            },
            {
                "storefront_id": "valid-store",
                "event_name": "add_to_cart",
                "event_time": "2026-01-15T10:10:00Z",
                "order_id": "valid_order_002",
            },
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 2
    assert data["rejected"] == 1
    assert len(data["event_ids"]) == 2
    assert len(data["errors"]) == 1


@pytest.mark.asyncio
async def test_ingest_event_batch_with_revenue(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test ingesting events with order revenue."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "purchase_completed",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "revenue_order_001",
                "order_revenue": 149.99,
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1


@pytest.mark.asyncio
async def test_ingest_event_batch_with_utm_params(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test ingesting events with UTM parameters."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "utm_order_001",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "spring_2026",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1


@pytest.mark.asyncio
async def test_ingest_event_batch_empty_with_error(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that empty batch with error is accepted."""
    batch = {
        "count": 0,
        "data": [],
        "error": "OMS database connection failed",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    # Should return 202 even with empty data when error is present
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 0
    assert data["rejected"] == 0


@pytest.mark.asyncio
async def test_ingest_event_batch_empty_without_error_fails(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that empty batch without error fails validation."""
    batch = {
        "count": 0,
        "data": [],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 422


# ============================================================================
# Event Ingestion with T-Value Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ingest_event_with_t_value(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test ingesting events with t-value field."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    batch = {
        "count": 1,
        "data": [
            {
                "t-value": "affiliate_tracking_123",
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "tvalue_order_001",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1


# ============================================================================
# Full OMS Batch Format Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ingest_full_oms_batch_format(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test ingesting events using the exact OMS batch format with all fields."""
    # Create storefronts for the batch (bosley and pfizer)
    await client.post(
        "/admin/v1/storefronts",
        json={"storefront_id": "bosley", "name": "Bosley Store"},
        headers=auth_headers,
    )
    await client.post(
        "/admin/v1/storefronts",
        json={"storefront_id": "pfizer", "name": "Pfizer Store"},
        headers=auth_headers,
    )

    # Exact OMS batch format with all fields
    batch = {
        "count": 3,
        "data": [
            {
                "t-value": "bosleyaffiliate_0123",
                "storefront_id": "bosley",
                "event_name": "consult_started",
                "event_time": "2026-01-15T10:15:00Z",
                "order_id": "2025010100001111",
                "session_id": "sess_123",
                "utm_source": "facebook",
                "utm_medium": "cpc",
                "utm_campaign": "bosley_q1",
            },
            {
                "t-value": "pfizeraffiliate_0123",
                "storefront_id": "pfizer",
                "event_name": "rx_issued",
                "event_time": "2026-01-15T10:20:30Z",
                "order_id": "2025010100002222",
                "session_id": "sess_789",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "pfizer_q1",
            },
            {
                "t-value": "bosleyaffiliate_0123",
                "storefront_id": "bosley",
                "event_name": "purchase_completed",
                "event_time": "2026-01-15T10:25:00Z",
                "order_id": "2025020100003333",
                "order_created_date": "2026-01-15T10:25:00Z",
                "order_ship_date": "2026-01-15T10:25:00Z",
                "order_revenue": 80.79,
                "session_id": "sess_456",
                "utm_source": "google",
                "utm_medium": "organic",
                "utm_campaign": "bosley_q1",
            },
        ],
        "error": "",
        "next_index": 1000,
        "next_url": "https://oms.example.com/events?offset=1000",
        "previous_index": "",
        "previous_url": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 3
    assert data["rejected"] == 0
    assert len(data["event_ids"]) == 3
    assert "2025010100001111" in data["event_ids"]
    assert "2025010100002222" in data["event_ids"]
    assert "2025020100003333" in data["event_ids"]


@pytest.mark.asyncio
async def test_ingest_oms_batch_with_all_optional_fields(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test that all optional fields in OMS batch are accepted."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    batch = {
        "count": 1,
        "data": [
            {
                "t-value": "affiliate_full_test",
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "purchase_completed",
                "event_time": "2026-01-15T14:30:00Z",
                "order_id": "full_fields_order_001",
                "order_created_date": "2026-01-15T14:00:00Z",
                "order_ship_date": "2026-01-16T09:00:00Z",
                "order_revenue": 149.99,
                "session_id": "sess_full_test",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "winter_sale_2026",
            }
        ],
        "error": "",
        "next_index": 100,
        "next_url": "https://oms.example.com/events?offset=100",
        "previous_index": "",
        "previous_url": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1
    assert data["rejected"] == 0


@pytest.mark.asyncio
async def test_ingest_oms_batch_minimal_fields(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test OMS batch with only required fields (no optional fields)."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    # Minimal batch - only required fields
    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "page_view",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "minimal_order_001",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1


@pytest.mark.asyncio
async def test_ingest_large_oms_batch(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test ingesting a larger batch similar to production loads."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    # Generate 50 events (simulate subset of 4000 event batch)
    events = []
    for i in range(50):
        event = {
            "t-value": f"affiliate_batch_{i:04d}",
            "storefront_id": sample_storefront_data["storefront_id"],
            "event_name": "purchase" if i % 2 == 0 else "add_to_cart",
            "event_time": f"2026-01-15T{10 + (i // 60):02d}:{i % 60:02d}:00Z",
            "order_id": f"batch_order_{i:06d}",
            "session_id": f"sess_{i:04d}",
            "utm_source": "google" if i % 3 == 0 else "facebook",
            "utm_medium": "cpc",
            "utm_campaign": "batch_test",
        }
        if i % 2 == 0:  # Add revenue for purchase events
            event["order_revenue"] = 25.00 + (i * 1.5)
        events.append(event)

    batch = {
        "count": 50,
        "data": events,
        "error": "",
        "next_index": 50,
        "next_url": "https://oms.example.com/events?offset=50",
        "previous_index": "",
        "previous_url": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 50
    assert data["rejected"] == 0
    assert len(data["event_ids"]) == 50


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ingest_events_unauthorized(
    client: AsyncClient,
):
    """Test that ingesting events without auth fails."""
    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": "test-store",
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "unauth_order_001",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ingest_events_invalid_auth(
    client: AsyncClient,
    invalid_auth_headers: dict,
):
    """Test that ingesting events with invalid auth fails."""
    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": "test-store",
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "invalid_auth_order_001",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=invalid_auth_headers,
    )

    assert response.status_code == 401


# ============================================================================
# Response Format Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ingest_events_response_format(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test the response format of event ingestion."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "format_order_001",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()

    # Verify response structure
    assert "accepted" in data
    assert "rejected" in data
    assert "event_ids" in data
    assert "errors" in data
    assert isinstance(data["accepted"], int)
    assert isinstance(data["rejected"], int)
    assert isinstance(data["event_ids"], list)
    assert isinstance(data["errors"], list)


@pytest.mark.asyncio
async def test_ingest_events_content_type(
    client: AsyncClient,
    auth_headers: dict,
    sample_storefront_data: dict,
):
    """Test that event ingestion returns JSON content type."""
    # Create storefront
    await client.post(
        "/admin/v1/storefronts",
        json=sample_storefront_data,
        headers=auth_headers,
    )

    batch = {
        "count": 1,
        "data": [
            {
                "storefront_id": sample_storefront_data["storefront_id"],
                "event_name": "purchase",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "content_type_order_001",
            }
        ],
        "error": "",
    }

    response = await client.post(
        "/v1/events",
        json=batch,
        headers=auth_headers,
    )

    assert "application/json" in response.headers["content-type"]

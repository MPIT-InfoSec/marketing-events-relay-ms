# Marketing Events Relay Microservice

## Project Overview

A Python/FastAPI microservice that receives marketing events from OMS (Order Management System) and forwards them to server-side Google Tag Manager (sGTM) or direct platform APIs.

**Primary Use Case**: The OMS Marketing Analytics Event Generator polls the OMS database and sends batched events to this service. Events are then routed to sGTM (primary) or directly to ad/analytics platforms (fallback).

**Architecture Note**: For new Upscript tenants, there is **NO web GTM and NO client-side tracking** in storefront portals. All marketing analytics is 100% server-side via this microservice.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI (async)
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy 2.0 (async with `AsyncSession`)
- **Migrations**: Alembic
- **Encryption**: Fernet (from `cryptography` library)
- **Testing**: pytest with pytest-asyncio

## Architecture

```
app/
├── api/                    # API routes (FastAPI routers)
│   ├── v1/                 # Event ingestion endpoints
│   │   └── routes/
│   │       ├── events.py   # POST /v1/events
│   │       └── health.py   # Health checks
│   └── admin/v1/           # Admin CRUD endpoints
│       └── routes/
│           ├── storefronts.py
│           ├── sgtm_configs.py
│           ├── platforms.py
│           └── credentials.py
├── core/                   # Core infrastructure
│   ├── config.py           # Pydantic Settings (env vars)
│   ├── database.py         # SQLAlchemy async engine/session
│   ├── security.py         # Basic Auth + Fernet encryption
│   └── exceptions.py       # Custom exception classes
├── models/                 # SQLAlchemy ORM models
│   ├── storefront.py       # Storefront entity
│   ├── sgtm_config.py      # sGTM config per storefront
│   ├── platform.py         # Ad analytics platform master data
│   ├── credential.py       # Encrypted platform credentials
│   ├── event.py            # Marketing events inbox
│   └── event_attempt.py    # Delivery attempt audit log
├── schemas/                # Pydantic request/response schemas
├── repositories/           # Data access layer (CRUD operations)
├── services/               # Business logic layer
├── adapters/               # Platform-specific API adapters
│   ├── sgtm.py             # Server-side GTM adapter (primary)
│   ├── meta_capi.py        # Meta Conversions API
│   ├── ga4.py              # Google Analytics 4
│   ├── tiktok.py           # TikTok Events API
│   ├── snapchat.py         # Snapchat Conversions API
│   └── pinterest.py        # Pinterest Conversions API
└── workers/
    └── retry_worker.py     # Background retry worker
```

## Key Design Patterns

### 1. Layered Architecture
```
Request → API Route → Schema (validation) → Service (business logic) → Repository (data access) → Model (ORM)
```

### 2. Generic Repository Pattern
`BaseRepository[T]` provides common CRUD operations. Entity-specific repositories extend it.

### 3. Adapter Pattern
Each platform has an adapter implementing a common interface for event forwarding.

### 4. Kill Switch Hierarchy
Events can be disabled at multiple levels:
1. `storefronts.is_active` - Entire storefront disabled
2. `storefront_sgtm_config.is_active` - sGTM forwarding disabled
3. `ad_analytics_platforms.is_active` - Platform globally disabled
4. `platform_credentials.is_active` - Platform disabled for specific storefront

## Database Schema (6 Tables)

| Table | Purpose |
|-------|---------|
| `storefronts` | Core storefront info with kill switch |
| `storefront_sgtm_config` | sGTM config per storefront |
| `ad_analytics_platforms` | Master data for 53+ platforms |
| `platform_credentials` | Encrypted credentials per storefront/platform |
| `marketing_events` | Event inbox with status tracking |
| `event_attempts` | Delivery attempt audit log |

## Event Ingestion - Dual Path Support

The system supports two ingestion paths for flexibility:

### Path 1: API Ingestion (POST /v1/events)

OMS Marketing Analytics Event Generator calls the API with batched events:

```json
{
  "count": 4000,
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
      "utm_campaign": "bosley_q1"
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
      "utm_campaign": "pfizer_q1"
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
      "utm_campaign": "bosley_q1"
    }
  ],
  "error": "",
  "next_index": 1000,
  "next_url": "...",
  "previous_index": "",
  "previous_url": ""
}
```

Key fields per event:
- `storefront_id` (string): Matches `storefronts.storefront_id` code
- `order_id` (string): Unique event identifier
- `event_name` (string): Event type (e.g., `purchase_completed`, `rx_issued`)
- `event_time` (datetime): When the event occurred
- Optional: `t-value`, `utm_*`, `order_revenue`, `session_id`

The API resolves `storefront_id` (string code) to integer FK and writes to `marketing_events`.

### Path 2: Direct Database Write

OMS can write directly to `marketing_events` table, bypassing the API.

**Option A - Using integer storefront_id (recommended if OMS has same IDs):**
```sql
INSERT INTO marketing_events (
    event_id,
    storefront_id,      -- Integer FK (same as OMS storefronts.id)
    event_type,
    event_payload,
    source_system,
    status
) VALUES (
    '2025020100003333',
    5,                  -- Integer storefront ID
    'purchase_completed',
    '{"order_id": "2025020100003333", "order_revenue": 80.79, "utm_source": "google"}',
    'oms_direct',
    'pending'
);
```

**Option B - Using storefront_code (worker resolves):**
```sql
INSERT INTO marketing_events (
    event_id,
    storefront_code,    -- String code, worker resolves to storefront_id
    event_type,
    event_payload,
    source_system,
    status
) VALUES (
    '2025020100003333',
    'bosley',           -- String storefront code
    'purchase_completed',
    '{"order_id": "2025020100003333", "order_revenue": 80.79, "utm_source": "google"}',
    'oms_direct',
    'pending'
);
```

### marketing_events Table Contract

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `event_id` | VARCHAR(100) | Yes | Unique event identifier (order_id) |
| `storefront_id` | INT | One of these | FK to storefronts.id |
| `storefront_code` | VARCHAR(50) | required | Storefront code (worker resolves) |
| `event_type` | VARCHAR(50) | Yes | Event type (lowercase) |
| `event_payload` | TEXT | Yes | JSON string with event data |
| `source_system` | VARCHAR(50) | Yes | `oms` (API) or `oms_direct` (DB write) |
| `status` | VARCHAR(20) | Yes | Must be `pending` for new events |

**Constraint**: At least one of `storefront_id` or `storefront_code` must be provided.

## Common Commands

```bash
# Docker (recommended for development)
docker-compose up -d              # Start all services
docker-compose logs -f api        # View API logs
docker-compose down               # Stop services

# Database migrations
alembic upgrade head              # Run all migrations
alembic revision -m "description" # Create new migration
alembic downgrade -1              # Rollback one migration

# Local development
uvicorn app.main:app --reload     # Start API server
python -m app.workers.retry_worker # Start background worker

# Testing
pytest tests/ -v                  # Run all tests
pytest tests/unit/ -v             # Unit tests only
pytest tests/integration/ -v      # Integration tests only

# Linting
black app/ tests/                 # Format code
isort app/ tests/                 # Sort imports
mypy app/                         # Type checking
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | MySQL async URL: `mysql+aiomysql://user:pass@host/db` | Yes |
| `BASIC_AUTH_USERNAME` | API authentication username | Yes |
| `BASIC_AUTH_PASSWORD` | API authentication password | Yes |
| `ENCRYPTION_KEY` | Fernet key for credential encryption | Yes |
| `MAX_RETRY_ATTEMPTS` | Max delivery retry attempts | No (default: 5) |
| `RETRY_BACKOFF_BASE` | Base seconds for exponential backoff | No (default: 60) |
| `DEBUG` | Enable debug mode | No (default: false) |

Generate encryption key:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## API Authentication

- **Event ingestion** (`/v1/events`): HTTP Basic Auth
- **Admin APIs** (`/admin/v1/*`): HTTP Basic Auth
- **Health endpoints** (`/health`, `/health/ready`): No auth

## Important Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application entry point |
| `app/core/config.py` | All settings from environment |
| `app/core/database.py` | SQLAlchemy async session setup |
| `app/core/security.py` | `CredentialEncryption` class, `verify_basic_auth` |
| `app/schemas/event.py` | `EventDataItem`, `EventBatchRequest` schemas |
| `app/services/event_service.py` | Event ingestion business logic |
| `app/services/forwarding_service.py` | Event routing and delivery |
| `app/adapters/sgtm.py` | sGTM HTTP forwarding |

## Coding Conventions

1. **Async everywhere**: All database operations and HTTP calls use async/await
2. **Type hints**: All functions have type annotations
3. **Pydantic for validation**: Request/response schemas use Pydantic v2
4. **Repository pattern**: Never access models directly from services; use repositories
5. **Dependency injection**: Use FastAPI's `Depends()` for session and auth
6. **Error handling**: Custom exceptions in `app/core/exceptions.py`

## sGTM Integration

The primary forwarding destination is server-side GTM. The adapter supports **two client types**:

### Client Type: GA4 (Default)

Uses GA4 Measurement Protocol format. Configure in `storefront_sgtm_config`:

```json
{
  "sgtm_url": "https://tags.upscript.com",
  "client_type": "ga4",
  "measurement_id": "G-XXXXXX",
  "api_secret": "your_api_secret"
}
```

**Request sent to sGTM:**
```
POST https://tags.upscript.com/mp/collect?measurement_id=G-XXXXXX&api_secret=XXX

{
  "client_id": "session_123",
  "events": [{
    "name": "purchase",
    "params": {
      "transaction_id": "order_123",
      "value": 80.79,
      "currency": "USD",
      "storefront_id": "bosley",
      "utm_source": "google"
    }
  }]
}
```

### Client Type: Custom

Uses flexible JSON format for custom sGTM clients. Configure:

```json
{
  "sgtm_url": "https://tags.upscript.com",
  "client_type": "custom",
  "custom_endpoint_path": "/collect",
  "custom_headers": {"X-Api-Key": "your-key"}
}
```

**Request sent to sGTM:**
```
POST https://tags.upscript.com/collect

{
  "event_name": "purchase_completed",
  "storefront_id": "bosley",
  "order_id": "123",
  "order_revenue": 80.79,
  "utm_source": "google",
  ...all payload fields pass through...
}
```

### sGTM Configuration Table

| Field | GA4 Client | Custom Client |
|-------|------------|---------------|
| `sgtm_url` | Required | Required |
| `client_type` | `"ga4"` | `"custom"` |
| `measurement_id` | Required | Not used |
| `api_secret` | Recommended | Not used |
| `custom_endpoint_path` | Not used | Default: `/collect` |
| `custom_headers` | Not used | Optional JSON |

sGTM then routes to configured platforms (Meta CAPI, TikTok, etc.) via custom tags.

## Retry Logic

Failed events use exponential backoff:
- Attempt 1: Immediate
- Attempt 2: After `RETRY_BACKOFF_BASE` seconds (default 60)
- Attempt 3: After `RETRY_BACKOFF_BASE * 2` seconds
- Attempt N: After `RETRY_BACKOFF_BASE * 2^(N-1)` seconds

Max attempts controlled by `MAX_RETRY_ATTEMPTS` (default 5).

## Current Status

- Core infrastructure: Complete
- Database models and migrations: Complete
- Admin CRUD APIs: Complete
- Event ingestion endpoint: Complete (updated to OMS batch format)
- sGTM adapter: Implemented (may need refinement based on actual sGTM setup)
- Direct platform adapters: Implemented for Tier 1 platforms
- Retry worker: Complete
- Tests: Basic structure in place

## Related Documentation

- `docs/TECHNICAL-DESIGN.md` - Full technical specification
- `docs/AD-ANALYTICS-PLATFORMS.md` - Platform details and credential structures
- `docs/SGTM-SETUP-GUIDE.md` - Server-side GTM setup guide for the team
- `README.md` - Quick start guide

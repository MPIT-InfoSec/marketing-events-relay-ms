# GitHub Copilot Instructions

## Project Overview

This is a **Python/FastAPI microservice** for marketing event routing. It receives events from an OMS (Order Management System) and forwards them to server-side Google Tag Manager (sGTM) or direct platform APIs.

## Tech Stack

- Python 3.11+
- FastAPI (async)
- MySQL 8.0 with SQLAlchemy 2.0 async
- Alembic for migrations
- Pydantic v2 for validation
- Fernet for credential encryption

## Code Style

### Always Use Async

```python
# CORRECT
async def get_item(self, id: int) -> Model:
    result = await self.session.execute(select(Model).where(Model.id == id))
    return result.scalar_one_or_none()

# WRONG - sync patterns
def get_item(self, id: int) -> Model:
    return self.session.query(Model).filter_by(id=id).first()
```

### Type Hints Required

```python
# CORRECT
async def process_event(self, event_id: str, payload: dict[str, Any]) -> EventResponse:
    ...

# WRONG - missing types
async def process_event(self, event_id, payload):
    ...
```

### Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, verify_basic_auth

@router.get("/")
async def endpoint(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_basic_auth),
):
    ...
```

### Layered Architecture

Follow this pattern:
```
API Route → Pydantic Schema → Service → Repository → SQLAlchemy Model
```

- Routes handle HTTP concerns only
- Services contain business logic
- Repositories handle database operations
- Never skip layers

## Project Structure

```
app/
├── api/v1/routes/     # Event ingestion endpoints
├── api/admin/v1/      # Admin CRUD endpoints
├── core/              # config, database, security, exceptions
├── models/            # SQLAlchemy models
├── schemas/           # Pydantic schemas
├── repositories/      # Data access
├── services/          # Business logic
├── adapters/          # Platform API adapters
└── workers/           # Background workers
```

## Key Patterns

### Creating Services

```python
class MyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = MyRepository(session)
```

### Creating Repositories

Extend `BaseRepository[T]`:
```python
class MyRepository(BaseRepository[MyModel]):
    def __init__(self, session):
        super().__init__(MyModel, session)
```

### Pydantic Schemas

Use Pydantic v2 with `from_attributes = True`:
```python
class MyResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
```

## Database

6 tables: `storefronts`, `storefront_sgtm_config`, `ad_analytics_platforms`, `platform_credentials`, `marketing_events`, `event_attempts`

Use async SQLAlchemy 2.0 patterns:
```python
from sqlalchemy import select
result = await session.execute(select(Model).where(Model.id == id))
```

## Event Ingestion - Dual Path Support

### Path 1: API (POST /v1/events)
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
- `order_id` is the unique event identifier
- `storefront_id` is a string code (API resolves to integer FK)

### Path 2: Direct Database Write
```sql
-- Using integer storefront_id
INSERT INTO marketing_events (event_id, storefront_id, event_type, event_payload, source_system, status)
VALUES ('123', 5, 'purchase_completed', '{"order_revenue": 80.79}', 'oms_direct', 'pending');

-- Or using storefront_code (worker resolves)
INSERT INTO marketing_events (event_id, storefront_code, event_type, event_payload, source_system, status)
VALUES ('123', 'bosley', 'purchase_completed', '{"order_revenue": 80.79}', 'oms_direct', 'pending');
```

At least one of `storefront_id` or `storefront_code` must be provided.

## Testing

```bash
pytest tests/ -v
```

Tests are in `tests/unit/` and `tests/integration/`.

## Important Files

- `app/core/config.py` - Settings from environment
- `app/core/database.py` - Async session factory
- `app/core/security.py` - Auth and encryption
- `app/services/event_service.py` - Event processing logic
- `app/adapters/sgtm.py` - sGTM forwarding

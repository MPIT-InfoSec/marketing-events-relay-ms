# Agent Instructions: Marketing Events Relay Microservice

This document provides context for AI coding assistants (OpenAI Codex, GitHub Copilot, etc.) working on this project.

## Project Summary

**What**: Python/FastAPI microservice for marketing event routing
**Purpose**: Receives marketing events from OMS, forwards to sGTM or direct platform APIs
**Tech**: Python 3.11+, FastAPI, MySQL 8.0, SQLAlchemy 2.0 (async), Alembic, Fernet encryption

**Important**: For new Upscript tenants, there is NO web GTM and NO client-side tracking. All marketing analytics is 100% server-side via this microservice.

## Quick Reference

### Project Structure
```
app/
├── api/           # FastAPI routes
│   ├── v1/        # Event ingestion (POST /v1/events)
│   └── admin/v1/  # CRUD for storefronts, configs, credentials
├── core/          # Config, database, security, exceptions
├── models/        # SQLAlchemy ORM models (6 tables)
├── schemas/       # Pydantic request/response schemas
├── repositories/  # Data access layer
├── services/      # Business logic
├── adapters/      # Platform API adapters (sGTM, Meta, etc.)
└── workers/       # Background retry worker
```

### Key Technologies
- **Async/Await**: All DB and HTTP operations are async
- **SQLAlchemy 2.0**: Using `AsyncSession`, `async_sessionmaker`
- **Pydantic v2**: With `model_validator`, `field_validator`
- **Fernet Encryption**: For credential storage

## Architecture Guidelines

### 1. Layered Architecture
```
API Route → Pydantic Schema → Service → Repository → SQLAlchemy Model
```

Do NOT skip layers. Services should never directly access models without going through repositories.

### 2. Dependency Injection Pattern
```python
from app.api.deps import get_db, verify_basic_auth
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/")
async def endpoint(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_basic_auth),
):
    service = SomeService(db)
    return await service.do_something()
```

### 3. Repository Pattern
```python
# In services, always use repositories
class MyService:
    def __init__(self, session: AsyncSession):
        self.repository = MyRepository(session)

    async def get_item(self, id: int):
        return await self.repository.get_by_id(id)
```

### 4. Async Database Operations
```python
# CORRECT - using async session
async with AsyncSessionLocal() as session:
    result = await session.execute(select(Model).where(...))

# WRONG - don't use sync operations
session.query(Model).filter(...)  # This is sync SQLAlchemy 1.x style
```

## Code Patterns

### Creating a New Endpoint

```python
# app/api/v1/routes/my_route.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_basic_auth
from app.schemas.my_schema import MyRequest, MyResponse
from app.services.my_service import MyService

router = APIRouter(prefix="/my-resource", tags=["my-resource"])

@router.post("/", response_model=MyResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    request: MyRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_basic_auth),
):
    service = MyService(db)
    return await service.create(request)
```

### Creating a New Service

```python
# app/services/my_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.my_repository import MyRepository
from app.core.exceptions import NotFoundError

class MyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = MyRepository(session)

    async def get_by_id(self, id: int) -> MyModel:
        item = await self.repository.get_by_id(id)
        if not item:
            raise NotFoundError("Resource", id)
        return item
```

### Creating a New Repository

```python
# app/repositories/my_repository.py
from app.repositories.base import BaseRepository
from app.models.my_model import MyModel

class MyRepository(BaseRepository[MyModel]):
    def __init__(self, session):
        super().__init__(MyModel, session)

    # Add custom methods as needed
    async def get_by_code(self, code: str) -> MyModel | None:
        result = await self.session.execute(
            select(self.model).where(self.model.code == code)
        )
        return result.scalar_one_or_none()
```

### Creating a New Schema

```python
# app/schemas/my_schema.py
from pydantic import BaseModel, Field
from datetime import datetime

class MyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)

class MyUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None

class MyResponse(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 for ORM mode
```

## Database Schema

| Table | Key Fields |
|-------|------------|
| `storefronts` | id, storefront_id (code), name, is_active |
| `storefront_sgtm_config` | id, storefront_id, sgtm_url, is_active |
| `ad_analytics_platforms` | id, platform_code, name, auth_type |
| `platform_credentials` | id, storefront_id, platform_id, credentials_encrypted |
| `marketing_events` | id, event_id, storefront_id, storefront_code, status |
| `event_attempts` | id, event_id, destination_type, status |

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

OMS can write directly to `marketing_events` table:

```sql
-- Option A: Using integer storefront_id (if OMS has same IDs)
INSERT INTO marketing_events (event_id, storefront_id, event_type, event_payload, source_system, status)
VALUES ('order123', 5, 'purchase_completed', '{"order_revenue": 80.79}', 'oms_direct', 'pending');

-- Option B: Using storefront_code (worker resolves)
INSERT INTO marketing_events (event_id, storefront_code, event_type, event_payload, source_system, status)
VALUES ('order123', 'bosley', 'purchase_completed', '{"order_revenue": 80.79}', 'oms_direct', 'pending');
```

**Constraint**: At least one of `storefront_id` or `storefront_code` must be provided.

## Encryption

Credentials are encrypted using Fernet:
```python
from app.core.security import CredentialEncryption

encryption = CredentialEncryption()
encrypted = encryption.encrypt({"api_key": "secret"})
decrypted = encryption.decrypt(encrypted)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_services.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

Test structure:
- `tests/unit/` - Unit tests with mocked dependencies
- `tests/integration/` - Integration tests with test database
- `tests/conftest.py` - Shared pytest fixtures

## Common Mistakes to Avoid

1. **Don't use sync SQLAlchemy patterns**
   ```python
   # WRONG
   session.query(Model).filter_by(id=1).first()

   # CORRECT
   result = await session.execute(select(Model).where(Model.id == 1))
   return result.scalar_one_or_none()
   ```

2. **Don't forget `await` on async operations**
   ```python
   # WRONG
   item = repository.get_by_id(id)

   # CORRECT
   item = await repository.get_by_id(id)
   ```

3. **Don't access models directly from API routes**
   ```python
   # WRONG (in route)
   result = await db.execute(select(Storefront))

   # CORRECT (use service)
   service = StorefrontService(db)
   result = await service.get_all()
   ```

4. **Don't mix storefront code (string) with storefront id (int)**
   ```python
   # Event data has storefront_id as string "bosley"
   # Database uses integer foreign keys
   # Service layer handles the lookup/mapping
   ```

## File Locations

| Purpose | Location |
|---------|----------|
| Environment config | `app/core/config.py` |
| Database session | `app/core/database.py` |
| Auth & encryption | `app/core/security.py` |
| Custom exceptions | `app/core/exceptions.py` |
| Event ingestion schema | `app/schemas/event.py` |
| Event business logic | `app/services/event_service.py` |
| Platform adapters | `app/adapters/*.py` |
| Migrations | `alembic/versions/*.py` |

## Related Documentation

- `README.md` - Quick start and setup
- `docs/TECHNICAL-DESIGN.md` - Full technical specification
- `docs/AD-ANALYTICS-PLATFORMS.md` - Platform credential structures
- `CLAUDE.md` - Extended context for Claude

# Marketing Events Relay Microservice

A Python/FastAPI microservice that receives marketing events from OMS (Order Management System) and forwards them to server-side Google Tag Manager (sGTM) or direct platform APIs.

## Features

- **Event Ingestion**: Batch event ingestion API with deduplication
- **Multi-Platform Support**: 53+ ad analytics platforms (Meta, Google, TikTok, etc.)
- **Dual Delivery**: Support for sGTM routing or direct API calls
- **Encrypted Credentials**: Fernet-based encryption for sensitive data
- **Kill Switches**: Hierarchical disable at storefront, sGTM, platform, or credential level
- **Retry Logic**: Exponential backoff for failed deliveries
- **Admin APIs**: Full CRUD for all entities

## Tech Stack

- Python 3.11+
- FastAPI
- MySQL 8.0
- SQLAlchemy 2.0 (async)
- Alembic
- Fernet (cryptography)

## Quick Start

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose run --rm migrate

# View logs
docker-compose logs -f api
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload

# In another terminal, start the worker
python -m app.workers.retry_worker
```

## API Endpoints

### Health Checks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks DB) |

### Event Ingestion

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/events` | Basic | Batch event ingestion |

### Admin APIs (`/admin/v1/`)

| Resource | Endpoints |
|----------|-----------|
| Storefronts | `GET`, `GET/{id}`, `POST`, `PUT/{id}`, `DELETE/{id}` |
| sGTM Configs | `GET`, `GET/{id}`, `POST`, `PUT/{id}`, `DELETE/{id}` |
| Platforms | `GET`, `GET/{id}`, `POST`, `PUT/{id}`, `DELETE/{id}` |
| Credentials | `GET`, `GET/{id}?decrypt=true`, `POST`, `PUT/{id}`, `DELETE/{id}` |

## Event Ingestion Example

```bash
curl -X POST http://localhost:8000/v1/events \
  -H "Content-Type: application/json" \
  -u admin:changeme123 \
  -d '{
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
}'
```

## Project Structure

```
marketing-events-relay-ms/
├── alembic/                 # Database migrations
├── app/
│   ├── api/                 # API routes
│   │   ├── v1/              # Event ingestion
│   │   └── admin/v1/        # Admin CRUD
│   ├── core/                # Config, DB, security
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic
│   ├── adapters/            # Platform adapters
│   └── workers/             # Background workers
├── tests/                   # Test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection URL | Required |
| `BASIC_AUTH_USERNAME` | API auth username | `admin` |
| `BASIC_AUTH_PASSWORD` | API auth password | `changeme` |
| `ENCRYPTION_KEY` | Fernet key for credentials | Auto-generated |
| `MAX_RETRY_ATTEMPTS` | Max delivery retries | `5` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Supported Platforms

### Tier 1 (Critical)
- Meta Conversions API (Facebook/Instagram)
- Google Ads
- Google Analytics 4
- TikTok Events API
- Snapchat Conversions API
- Pinterest Conversions API
- Twitter/X Conversions API
- LinkedIn Conversions API
- Microsoft Ads

### Tier 2 (Important)
- Amazon Ads, Criteo, Reddit, Quora, Taboola, Outbrain, The Trade Desk, DV360, Adobe Analytics, Mixpanel, Amplitude, Segment, Klaviyo, Braze

### Tier 3 (Standard)
- 30+ additional platforms for analytics, attribution, marketing, and CDP

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_services.py -v
```

## License

Proprietary - All rights reserved.

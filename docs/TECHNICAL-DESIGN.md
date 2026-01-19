# Marketing Events Relay - Technical Design

## 1. Overview

An internal analytics gateway built with Python, FastAPI, and MySQL that receives marketing events from the OMS Marketing Analytics Event Generator and forwards them to Server-side GTM (sGTM) or directly to ad/analytics platforms.

### 100% Server-side Architecture (New Tenants)

**For all new Upscript tenants, there is NO web GTM and NO client-side tracking tags in storefront portals.** All marketing analytics is measured server-side via this microservice.

| Aspect | Approach |
|--------|----------|
| Page Views | Not tracked (focus on conversions) |
| Conversion Events | All from OMS via this microservice |
| Attribution | UTM params captured at conversion time |
| User Matching | Email/phone from order data |
| Consent | Handled at OMS level |

Benefits: No ad blockers, better data quality, simpler compliance, faster page loads.

See `docs/SGTM-SETUP-GUIDE.md` for detailed setup instructions.

### Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Testing**: pytest + testcontainers

---

## 2. Architecture

### Event Flow

```
SERVER EVENTS (OMS)
-------------------
OMS (AWS RDS / MySQL)
      |
      v
OMS Marketing Analytics Event Generator
      |
      v
marketing-events-relay.upscript.com   <-- This Service
      |
      v
+---------------------+
| Routing Decision    |
+---------------------+
      |
      +--[sGTM configured]--> tags.upscript.com (Server-side GTM)
      |                              |
      |                              +--> GA4
      |                              +--> Meta CAPI
      |                              +--> Google Ads
      |                              +--> TikTok
      |
      +--[Direct connection]--> Platform API directly
                                     |
                                     +--> Meta CAPI
                                     +--> GA4
                                     +--> Google Ads
                                     +--> TikTok
                                     +--> Snapchat
                                     +--> Pinterest
                                     +--> etc.
```

### Routing Strategy

**Primary**: Forward to sGTM (handles platform fan-out)
**Fallback**: Direct platform connection (when sGTM doesn't support a platform)

```
Per Storefront Configuration:
┌─────────────────────────────────────────────────────────┐
│ Storefront: pfizer                                      │
├─────────────────────────────────────────────────────────┤
│ sGTM Config:                                            │
│   - sgtm_url: https://tags.upscript.com/pfizer          │
│   - is_active: true                                     │
├─────────────────────────────────────────────────────────┤
│ Direct Platform Credentials (fallback):                 │
│   - META_CAPI: (not configured - uses sGTM)             │
│   - GA4: (not configured - uses sGTM)                   │
│   - SNAPCHAT: pixel_id=xxx, token=xxx (direct - sGTM    │
│               doesn't support)                          │
└─────────────────────────────────────────────────────────┘
```

### Request Flow (Internal)

```
Request In (Batch from OMS)
    |
    v
+-------------------+
| Authentication    |  --> Basic Auth (OMS credentials)
+-------------------+
    |
    v
+-------------------+
| Validation        |  --> Required fields: storefront_id, event_name, event_time
+-------------------+
    |
    v
+-------------------+
| Storefront Lookup |  --> Verify storefront exists and is active
+-------------------+
    |
    v
+-------------------+
| Persist Events    |  --> Save to marketing_events (status=PENDING)
+-------------------+
    |
    v
+-------------------+
| Return 202        |  --> Accepted for processing
+-------------------+

Background Worker
    |
    v
+-------------------+
| Route & Forward   |  --> sGTM (primary) or Direct Platform (fallback)
+-------------------+
    |
    +--> Success --> status=COMPLETED
    |
    +--> Failure --> Retry (max 3, 2 min interval)
                     |
                     +--> After 3 failures --> status=FAILED
```

---

## 3. Database Schema

### 3.1 `storefronts`
Core storefront information with kill switch.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PK, AUTO_INCREMENT | Primary key |
| code | VARCHAR(50) | UNIQUE, NOT NULL | Unique identifier (e.g., `pfizer`, `bosley`) |
| name | VARCHAR(255) | NOT NULL | Display name |
| is_active | BOOLEAN | DEFAULT true | Kill switch - disable all event processing |
| created_at | DATETIME | NOT NULL | Creation timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

**Indexes**: `idx_storefronts_code` (code), `idx_storefronts_is_active` (is_active)

---

### 3.2 `storefront_sgtm_config`
Server-side GTM configuration per storefront. Supports two client types:
- **GA4**: Uses GA4 Measurement Protocol format (`/mp/collect`)
- **Custom**: Uses flexible JSON format to custom endpoint path

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PK, AUTO_INCREMENT | Primary key |
| storefront_id | INT | FK, UNIQUE, NOT NULL | Reference to storefronts |
| sgtm_url | VARCHAR(500) | NOT NULL | sGTM container base URL |
| client_type | VARCHAR(20) | NOT NULL, DEFAULT 'ga4' | Client type: `ga4` or `custom` |
| container_id | VARCHAR(50) | NULL | GTM container ID (GTM-XXXXXX) |
| measurement_id | VARCHAR(50) | NULL | GA4 Measurement ID (G-XXXXXX) - required for GA4 |
| api_secret | TEXT | NULL | Encrypted API secret for GA4 Measurement Protocol |
| custom_endpoint_path | VARCHAR(100) | NULL, DEFAULT '/collect' | Endpoint path for custom client |
| custom_headers | TEXT | NULL | JSON string of custom headers |
| is_active | BOOLEAN | DEFAULT true | Enable/disable sGTM forwarding |
| created_at | DATETIME | NOT NULL | Creation timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

**Foreign Keys**: `storefront_id` -> `storefronts(id)` ON DELETE CASCADE

**Client Type Configuration:**

| Field | GA4 Client | Custom Client |
|-------|------------|---------------|
| `measurement_id` | Required | Not used |
| `api_secret` | Recommended | Not used |
| `custom_endpoint_path` | Not used | Default: `/collect` |
| `custom_headers` | Not used | Optional |

---

### 3.3 `ad_analytics_platforms`
Master data for ad/analytics platforms (for direct connections).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PK, AUTO_INCREMENT | Primary key |
| code | VARCHAR(50) | UNIQUE, NOT NULL | Platform code (e.g., `META_CAPI`, `GA4`) |
| name | VARCHAR(255) | NOT NULL | Display name |
| default_base_url | VARCHAR(500) | NULL | Default API endpoint |
| default_auth_type | ENUM | NOT NULL | AUTH_TYPE: API_KEY, OAUTH2, ACCESS_TOKEN, BASIC_AUTH |
| is_active | BOOLEAN | DEFAULT true | Global kill switch for platform |
| created_at | DATETIME | NOT NULL | Creation timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

**Indexes**: `idx_platforms_code` (code), `idx_platforms_is_active` (is_active)

---

### 3.4 `platform_credentials`
Storefront-specific platform credentials (for direct connections when sGTM doesn't support).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PK, AUTO_INCREMENT | Primary key |
| storefront_id | INT | FK, NOT NULL | Reference to storefronts |
| platform_id | INT | FK, NOT NULL | Reference to ad_analytics_platforms |
| auth_type | ENUM | NULL | Override auth type (uses platform default if null) |
| credentials_encrypted | TEXT | NOT NULL | Encrypted JSON credentials |
| base_url | VARCHAR(500) | NULL | Override base URL (uses platform default if null) |
| is_active | BOOLEAN | DEFAULT true | Enable/disable this platform for storefront |
| created_at | DATETIME | NOT NULL | Creation timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

**Foreign Keys**:
- `storefront_id` -> `storefronts(id)` ON DELETE CASCADE
- `platform_id` -> `ad_analytics_platforms(id)` ON DELETE CASCADE

**Unique Constraint**: `uq_storefront_platform` (storefront_id, platform_id)
**Indexes**: `idx_credentials_is_active` (is_active)

---

### 3.5 `marketing_events`
Event inbox with delivery status. Supports dual ingestion: API or direct database write.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| event_id | VARCHAR(100) | UNIQUE, NOT NULL | Unique event identifier (order_id from OMS) |
| storefront_id | INT | FK, NULL | Reference to storefronts (set by API or direct write) |
| storefront_code | VARCHAR(50) | NULL | Storefront code for direct writes (worker resolves) |
| event_type | VARCHAR(50) | NOT NULL | Event type (e.g., `purchase_completed`) |
| event_payload | TEXT | NOT NULL | JSON event payload |
| source_system | VARCHAR(50) | NOT NULL | Source: `oms` (API) or `oms_direct` (DB write) |
| status | VARCHAR(20) | NOT NULL | pending, processing, delivered, retrying, failed |
| retry_count | INT | DEFAULT 0 | Current retry count |
| next_retry_at | DATETIME | NULL | Next retry timestamp |
| processed_at | DATETIME | NULL | When fully processed |
| error_message | TEXT | NULL | Last error message |
| created_at | DATETIME | NOT NULL | Event received time |
| updated_at | DATETIME | NOT NULL | Last status change |

**Foreign Keys**: `storefront_id` -> `storefronts(id)` ON DELETE CASCADE

**Check Constraint**: `storefront_id IS NOT NULL OR storefront_code IS NOT NULL`

**Indexes**:
- `ix_marketing_events_event_id` (event_id) UNIQUE
- `ix_marketing_events_storefront_id` (storefront_id)
- `ix_marketing_events_storefront_code` (storefront_code)
- `ix_marketing_events_event_type` (event_type)
- `ix_marketing_events_status` (status)
- `ix_marketing_events_next_retry_at` (next_retry_at)

---

### 3.6 `event_attempts`
Audit log of delivery attempts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| event_id | BIGINT | FK, NOT NULL | Reference to marketing_events |
| attempt_number | INT | NOT NULL | Attempt number (1, 2, 3) |
| destination_type | ENUM | NOT NULL | SGTM, DIRECT_PLATFORM |
| platform_code | VARCHAR(50) | NULL | Platform code if direct (e.g., `META_CAPI`) |
| status | ENUM | NOT NULL | SUCCESS, FAILED |
| response_code | INT | NULL | HTTP response code |
| response_body | TEXT | NULL | Response body (truncated) |
| error_message | TEXT | NULL | Error details |
| attempted_at | DATETIME | NOT NULL | Attempt timestamp |

**Foreign Keys**: `event_id` -> `marketing_events(id)` ON DELETE CASCADE
**Indexes**: `idx_attempts_event` (event_id), `idx_attempts_attempted_at` (attempted_at)

---

## 4. API Endpoints

### 4.1 Event Ingestion - Dual Path Support

The system supports two ingestion paths for maximum flexibility:

#### Path 1: API Ingestion (POST /v1/events)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/events` | Basic Auth | Receive batch events from OMS |

- OMS Marketing Analytics Event Generator calls the API
- `storefront_id` is sent as a string code (e.g., "bosley")
- API resolves to integer FK and validates storefront exists/active
- Sets `source_system = 'oms'`

#### Path 2: Direct Database Write

OMS can write directly to `marketing_events` table, bypassing the API.

**Option A - Using integer storefront_id (recommended):**
```sql
INSERT INTO marketing_events (
    event_id, storefront_id, event_type, event_payload, source_system, status
) VALUES (
    '2025020100003333', 5, 'purchase_completed',
    '{"order_id": "2025020100003333", "order_revenue": 80.79}',
    'oms_direct', 'pending'
);
```

**Option B - Using storefront_code (worker resolves):**
```sql
INSERT INTO marketing_events (
    event_id, storefront_code, event_type, event_payload, source_system, status
) VALUES (
    '2025020100003333', 'bosley', 'purchase_completed',
    '{"order_id": "2025020100003333", "order_revenue": 80.79}',
    'oms_direct', 'pending'
);
```

**Direct Write Requirements:**
- At least one of `storefront_id` (integer) or `storefront_code` (string) must be provided
- `status` must be `'pending'` for new events
- `event_id` must be unique (order_id from OMS)
- `event_payload` must be valid JSON string
- If using `storefront_code`, the worker will resolve it to `storefront_id` before processing

### 4.2 Health & Monitoring

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | None | Liveness probe |
| GET | `/health/ready` | None | Readiness probe (includes DB check) |

---

### 4.3 Batch Event Request (from OMS Marketing Analytics Event Generator)

The OMS Marketing Analytics Event Generator polls the OMS database and sends events as a batch. The batch is **multi-tenant** (contains events from multiple storefronts) and **multi-event-type** (contains different event types).

**Request**:
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

**Key Characteristics**:
- **Multi-tenant**: Each record has its own `storefront_id`
- **Multi-event-type**: Each record has its own `event_name`
- **Dynamic fields**: Records can have any number of key-value pairs
- **Required fields per record**: `storefront_id`, `event_name`, `event_time`

**Response (202 Accepted)**:
```json
{
  "status": "accepted",
  "batch_id": "batch_12345",
  "events_received": 3,
  "message": "Batch queued for processing"
}
```

**Error Response (400 Bad Request)** - Validation failures:
```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": [
    {"index": 0, "field": "storefront_id", "error": "required field missing"},
    {"index": 2, "field": "event_time", "error": "invalid datetime format"}
  ]
}
```

---

### 4.4 Batch Size Limits

| Limit | Value | Reason |
|-------|-------|--------|
| Max records per batch | 500 | Memory efficiency |
| Max payload size | 5 MB | HTTP request limits |
| Recommended batch size | 100-200 | Optimal processing |

If limits are exceeded, the API returns `413 Payload Too Large`.

---

## 5. Configuration (.env)

```bash
# ===========================================
# Application
# ===========================================
APP_NAME=marketing-events-relay-ms
APP_ENV=development                          # development, staging, production
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# ===========================================
# Database
# ===========================================
DB_HOST=localhost
DB_PORT=3306
DB_NAME=marketing_events_relay
DB_USERNAME=app_user
DB_PASSWORD=change_me_in_production
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=false                                # Log SQL queries (dev only)

# ===========================================
# Server-side Auth (OMS Event Generator)
# ===========================================
SERVER_AUTH_USERNAME=oms_event_generator
SERVER_AUTH_PASSWORD=change_me_in_production

# ===========================================
# Retry Configuration
# ===========================================
RETRY_MAX_ATTEMPTS=3
RETRY_INTERVAL_SECONDS=120

# ===========================================
# Batch Configuration
# ===========================================
BATCH_MAX_RECORDS=500
BATCH_MAX_PAYLOAD_SIZE_MB=5

# ===========================================
# Security
# ===========================================
ENCRYPTION_KEY=change_me_32_char_secret_key  # For credential encryption

# ===========================================
# Logging
# ===========================================
LOG_LEVEL=INFO                               # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                              # json, text
```

---

## 6. Project Structure

```
marketing-events-relay-ms/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   └── 002_seed_data.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
│
├── app/
│   ├── __init__.py
│   ├── main.py                              # FastAPI app entry point
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py                    # API router aggregation
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── events.py                # POST /v1/events
│   │           └── health.py                # Health endpoints
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── event_service.py                 # Event processing orchestration
│   │   ├── storefront_service.py            # Storefront lookup and validation
│   │   └── forwarding_service.py            # Routing & forwarding orchestration
│   │
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base_adapter.py                  # Abstract base adapter
│   │   ├── adapter_factory.py               # Factory for platform adapters
│   │   ├── sgtm_adapter.py                  # Server-side GTM adapter (primary)
│   │   ├── meta_capi_adapter.py             # Meta Conversions API adapter
│   │   ├── ga4_adapter.py                   # Google Analytics 4 adapter
│   │   ├── google_ads_adapter.py            # Google Ads adapter
│   │   ├── tiktok_adapter.py                # TikTok Events API adapter
│   │   ├── snapchat_adapter.py              # Snapchat Conversions API adapter
│   │   └── pinterest_adapter.py             # Pinterest Conversions API adapter
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base_repository.py               # Base repository class
│   │   ├── event_repository.py              # marketing_events, event_attempts
│   │   ├── storefront_repository.py         # storefronts, storefront_sgtm_config
│   │   └── platform_repository.py           # ad_analytics_platforms, platform_credentials
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                          # SQLAlchemy base
│   │   ├── storefront.py                    # Storefront, StorefrontSgtmConfig
│   │   ├── platform.py                      # AdAnalyticsPlatform, PlatformCredentials
│   │   └── event.py                         # MarketingEvent, EventAttempt
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── event_schema.py                  # Event request/response schemas
│   │   └── common.py                        # Common schemas (errors)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                        # Settings from .env (pydantic)
│   │   ├── database.py                      # Database connection & session
│   │   ├── security.py                      # Auth & encryption utilities
│   │   └── exceptions.py                    # Custom exception classes
│   │
│   └── workers/
│       ├── __init__.py
│       └── retry_worker.py                  # Background retry worker
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                          # Shared fixtures
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── test_event_service.py
│   │   │   └── test_storefront_service.py
│   │   └── adapters/
│   │       ├── __init__.py
│   │       └── test_adapters.py
│   │
│   └── integration/
│       ├── __init__.py
│       ├── conftest.py                      # Test containers setup
│       └── api/
│           ├── __init__.py
│           ├── test_events.py
│           └── test_health.py
│
├── docs/
│   ├── HIPAA-PRIVACY-MS.md                  # Original requirements
│   └── TECHNICAL-DESIGN.md                  # This document
│
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 7. Seed Data

> **Note**: For detailed platform information including credential structures, rate limits, and documentation links, see [AD-ANALYTICS-PLATFORMS.md](./AD-ANALYTICS-PLATFORMS.md).

### 7.1 Ad Analytics Platforms - Tier 1 (Critical)

Must-have platforms used by 90%+ of e-commerce businesses.

| code | name | default_base_url | default_auth_type | is_active |
|------|------|------------------|-------------------|-----------|
| SGTM | Server-side GTM | (from storefront config) | API_KEY | true |
| META_CAPI | Meta Conversions API | https://graph.facebook.com/v18.0 | ACCESS_TOKEN | true |
| GA4 | Google Analytics 4 | https://www.google-analytics.com/mp/collect | API_KEY | true |
| GOOGLE_ADS | Google Ads | https://googleads.googleapis.com | OAUTH2 | true |
| TIKTOK | TikTok Events API | https://business-api.tiktok.com/open_api/v1.3/pixel/track | ACCESS_TOKEN | true |
| MICROSOFT_ADS | Microsoft Advertising | https://bat.bing.com/action/0 | OAUTH2 | true |
| SNAPCHAT | Snapchat Conversions API | https://tr.snapchat.com/v2/conversion | ACCESS_TOKEN | true |
| PINTEREST | Pinterest Conversions API | https://api.pinterest.com/v5/ad_accounts | ACCESS_TOKEN | true |

### 7.2 Ad Analytics Platforms - Tier 2 (High Priority)

High-priority platforms used by 50%+ of e-commerce businesses.

| code | name | default_base_url | default_auth_type | is_active |
|------|------|------------------|-------------------|-----------|
| AMAZON_ADS | Amazon Advertising | https://advertising-api.amazon.com | OAUTH2 | true |
| AMAZON_ATTRIBUTION | Amazon Attribution | https://advertising-api.amazon.com/attribution | OAUTH2 | true |
| CRITEO | Criteo Events API | https://api.criteo.com/2022-01/events | OAUTH2 | true |
| TWITTER | Twitter/X Conversions | https://ads-api.twitter.com/12/measurement/conversions | OAUTH2 | true |
| LINKEDIN | LinkedIn Conversions | https://api.linkedin.com/rest/conversionEvents | OAUTH2 | true |
| REDDIT | Reddit Conversions | https://ads-api.reddit.com/api/v2.0/conversions/events | ACCESS_TOKEN | true |
| KLAVIYO | Klaviyo Events | https://a.klaviyo.com/api | API_KEY | true |
| ATTENTIVE | Attentive Events | https://api.attentivemobile.com/v1/events | API_KEY | true |
| BRAZE | Braze User Track | https://rest.iad-01.braze.com | API_KEY | true |
| IMPACT | Impact.com | https://api.impact.com | BASIC_AUTH | true |
| CJ_AFFILIATE | CJ Affiliate | https://commissions.api.cj.com | API_KEY | true |
| SHAREASALE | ShareASale | https://api.shareasale.com | API_KEY | true |
| RAKUTEN | Rakuten Advertising | https://api.rakutenmarketing.com | ACCESS_TOKEN | true |
| TABOOLA | Taboola Conversions | https://backstage.taboola.com/backstage/api/1.0 | ACCESS_TOKEN | true |
| OUTBRAIN | Outbrain Conversions | https://api.outbrain.com/amplify/v0.1 | ACCESS_TOKEN | true |

### 7.3 Ad Analytics Platforms - Tier 3 (Standard)

Common platforms used by 20%+ of e-commerce businesses.

| code | name | default_base_url | default_auth_type | is_active |
|------|------|------------------|-------------------|-----------|
| QUORA | Quora Conversions | https://ads-api.quora.com | API_KEY | true |
| WALMART_CONNECT | Walmart Connect | https://advertising.walmart.com/api | OAUTH2 | true |
| EBAY_ADS | eBay Promoted Listings | https://api.ebay.com/sell/marketing/v1 | OAUTH2 | true |
| INSTACART_ADS | Instacart Ads | https://ads.instacart.com/api/v1 | ACCESS_TOKEN | true |
| TARGET_ROUNDEL | Target Roundel | https://api.roundel.com | ACCESS_TOKEN | true |
| KROGER | Kroger Precision Marketing | https://api.kroger.com/v1 | OAUTH2 | true |
| THE_TRADE_DESK | The Trade Desk | https://api.thetradedesk.com/v3 | ACCESS_TOKEN | true |
| DV360 | Google Display & Video 360 | https://displayvideo.googleapis.com/v2 | OAUTH2 | true |
| AMAZON_DSP | Amazon DSP | https://advertising-api.amazon.com/dsp | OAUTH2 | true |
| ADROLL | AdRoll | https://services.adroll.com/api/v1 | OAUTH2 | true |
| RTB_HOUSE | RTB House | https://api.rtbhouse.com | API_KEY | true |
| SEGMENT | Segment | https://api.segment.io/v1 | API_KEY | true |
| MPARTICLE | mParticle | https://s2s.mparticle.com/v2 | BASIC_AUTH | true |
| APPSFLYER | AppsFlyer | https://api2.appsflyer.com/inappevent | API_KEY | true |
| ADJUST | Adjust | https://s2s.adjust.com/event | API_KEY | true |
| BRANCH | Branch | https://api2.branch.io/v2/event/custom | API_KEY | true |
| KOCHAVA | Kochava | https://control.kochava.com/track/event | API_KEY | true |
| ITERABLE | Iterable | https://api.iterable.com/api | API_KEY | true |
| CUSTOMERIO | Customer.io | https://track.customer.io/api/v1 | BASIC_AUTH | true |
| POSTSCRIPT | Postscript | https://api.postscript.io/v1 | API_KEY | true |
| OMNISEND | Omnisend | https://api.omnisend.com/v3 | API_KEY | true |
| MIXPANEL | Mixpanel | https://api.mixpanel.com | API_KEY | true |
| AMPLITUDE | Amplitude | https://api2.amplitude.com/2/httpapi | API_KEY | true |
| HEAP | Heap | https://heapanalytics.com/api | API_KEY | true |
| FULLSTORY | FullStory | https://api.fullstory.com | API_KEY | true |
| SPOTIFY_ADS | Spotify Advertising | https://ads.spotify.com/api | OAUTH2 | true |
| ROKU_ADS | Roku Ads | https://ads.roku.com/api | ACCESS_TOKEN | true |
| YOTPO | Yotpo | https://api.yotpo.com | API_KEY | true |
| TRIPLE_WHALE | Triple Whale | https://api.triplewhale.com | API_KEY | true |
| NORTHBEAM | Northbeam | https://api.northbeam.io | API_KEY | true |

### 7.4 Ad Analytics Platforms - Tier 4 (Extended)

Niche and emerging platforms. Set `is_active=false` by default, enable as needed.

| code | name | category | default_auth_type | is_active |
|------|------|----------|-------------------|-----------|
| HOME_DEPOT | Home Depot Retail Media | Retail Media | ACCESS_TOKEN | false |
| LOWES | Lowe's One Roof Media | Retail Media | ACCESS_TOKEN | false |
| BEST_BUY | Best Buy Ads | Retail Media | ACCESS_TOKEN | false |
| CVS_MEDIA | CVS Media Exchange | Retail Media | ACCESS_TOKEN | false |
| WALGREENS | Walgreens Advertising | Retail Media | ACCESS_TOKEN | false |
| ALBERTSONS | Albertsons Media Collective | Retail Media | ACCESS_TOKEN | false |
| ULTA | Ulta Beauty Media | Retail Media | ACCESS_TOKEN | false |
| SEPHORA | Sephora Media | Retail Media | ACCESS_TOKEN | false |
| CHEWY | Chewy Ads | Retail Media | ACCESS_TOKEN | false |
| WAYFAIR | Wayfair Advertising | Retail Media | ACCESS_TOKEN | false |
| COSTCO | Costco Advertising | Retail Media | ACCESS_TOKEN | false |
| SAMS_CLUB | Sam's Club MAP | Retail Media | ACCESS_TOKEN | false |
| DOLLAR_GENERAL | DG Media Network | Retail Media | ACCESS_TOKEN | false |
| GOPUFF | Gopuff Ads | Retail Media | ACCESS_TOKEN | false |
| DOORDASH | DoorDash Ads | Retail Media | ACCESS_TOKEN | false |
| UBER_EATS | Uber Ads | Retail Media | ACCESS_TOKEN | false |
| MEDIAMATH | MediaMath | DSP | OAUTH2 | false |
| XANDR | Xandr (Microsoft) | DSP | OAUTH2 | false |
| VIANT | Viant Adelphic | DSP | ACCESS_TOKEN | false |
| STACKADAPT | StackAdapt | DSP | API_KEY | false |
| BASIS | Basis (Centro) | DSP | OAUTH2 | false |
| SIMPLIFI | Simpli.fi | DSP | API_KEY | false |
| QUANTCAST | Quantcast | DSP | API_KEY | false |
| LOTAME | Lotame | DMP | API_KEY | false |
| LIVERAMP | LiveRamp | Identity | API_KEY | false |
| ADFORM | Adform | DSP | API_KEY | false |
| MOLOCO | Moloco | DSP | API_KEY | false |
| ROKT | Rokt | Transaction Ads | API_KEY | false |
| ZETA | Zeta Global | DSP | API_KEY | false |
| YAHOO_DSP | Yahoo DSP | DSP | OAUTH2 | false |
| MGID | MGID | Native | API_KEY | false |
| REVCONTENT | Revcontent | Native | API_KEY | false |
| NATIVO | Nativo | Native | ACCESS_TOKEN | false |
| TRIPLELIFT | TripleLift | Native | API_KEY | false |
| SHARETHROUGH | Sharethrough | Native | API_KEY | false |
| SAMSUNG_ADS | Samsung Ads | CTV | ACCESS_TOKEN | false |
| LG_ADS | LG Ads | CTV | ACCESS_TOKEN | false |
| VIZIO_ADS | Vizio Ads | CTV | ACCESS_TOKEN | false |
| HULU | Hulu Ads | CTV | OAUTH2 | false |
| PEACOCK | Peacock Ads | CTV | ACCESS_TOKEN | false |
| PARAMOUNT | Paramount+ Ads | CTV | ACCESS_TOKEN | false |
| DISNEY_PLUS | Disney+ Ads | CTV | OAUTH2 | false |
| NETFLIX | Netflix Ads | CTV | OAUTH2 | false |
| AMAZON_FIRE | Amazon Fire TV | CTV | OAUTH2 | false |
| TUBI | Tubi Ads | CTV | API_KEY | false |
| PLUTO | Pluto TV | CTV | ACCESS_TOKEN | false |
| FUBO | FuboTV Ads | CTV | ACCESS_TOKEN | false |
| MNTN | MNTN Performance TV | CTV | API_KEY | false |
| INNOVID | Innovid | CTV/Video | API_KEY | false |
| MAGNITE | Magnite (SpotX) | Video SSP | API_KEY | false |
| NEXXEN | Nexxen (Tremor) | CTV/Video | API_KEY | false |
| PANDORA | Pandora (SiriusXM) | Audio | OAUTH2 | false |
| IHEARTRADIO | iHeartRadio | Audio | API_KEY | false |
| AMAZON_MUSIC | Amazon Music Ads | Audio | OAUTH2 | false |
| PODCORN | Podcorn | Podcast | API_KEY | false |
| PODSCRIBE | Podscribe | Podcast | API_KEY | false |
| PODSIGHTS | Podsights | Podcast | API_KEY | false |
| CHARTABLE | Chartable | Podcast | API_KEY | false |
| ACAST | Acast | Podcast | API_KEY | false |
| MEGAPHONE | Megaphone | Podcast | API_KEY | false |
| AWIN | Awin | Affiliate | API_KEY | false |
| PARTNERIZE | Partnerize | Affiliate | ACCESS_TOKEN | false |
| PARTNERSTACK | PartnerStack | B2B Affiliate | API_KEY | false |
| REFERSION | Refersion | Affiliate | API_KEY | false |
| EVERFLOW | Everflow | Affiliate | API_KEY | false |
| TUNE | Tune (HasOffers) | Affiliate | API_KEY | false |
| TAPFILIATE | Tapfiliate | Affiliate | API_KEY | false |
| LEADDYNO | LeadDyno | Affiliate | API_KEY | false |
| CREATORIQ | CreatorIQ | Influencer | OAUTH2 | false |
| GRIN | Grin | Influencer | API_KEY | false |
| ASPIRE | Aspire | Influencer | API_KEY | false |
| UPFLUENCE | Upfluence | Influencer | API_KEY | false |
| TRAACKR | Traackr | Influencer | API_KEY | false |
| MAVRCK | Mavrck | Influencer | API_KEY | false |
| SHOPIFY_COLLABS | Shopify Collabs | Influencer | API_KEY | false |
| LTK | LTK (LikeToKnowIt) | Influencer | API_KEY | false |
| SHOPMY | ShopMy | Influencer | API_KEY | false |
| TEALIUM | Tealium | CDP | API_KEY | false |
| RUDDERSTACK | Rudderstack | CDP | API_KEY | false |
| TREASURE_DATA | Treasure Data | CDP | API_KEY | false |
| BLOOMREACH | Bloomreach | CDP | API_KEY | false |
| AMPERITY | Amperity | CDP | API_KEY | false |
| ACTIONIQ | ActionIQ | CDP | API_KEY | false |
| HIGHTOUCH | Hightouch | Reverse ETL | API_KEY | false |
| CENSUS | Census | Reverse ETL | API_KEY | false |
| LYTICS | Lytics | CDP | API_KEY | false |
| BLUECONIC | BlueConic | CDP | API_KEY | false |
| MAILCHIMP | Mailchimp | Email | API_KEY | false |
| SENDGRID | SendGrid | Email | API_KEY | false |
| SAILTHRU | Sailthru | Email | API_KEY | false |
| CORDIAL | Cordial | Email | API_KEY | false |
| LISTRAK | Listrak | Email | API_KEY | false |
| DRIP | Drip | Email | API_KEY | false |
| ACTIVECAMPAIGN | ActiveCampaign | Email | API_KEY | false |
| ADOBE_ANALYTICS | Adobe Analytics | Analytics | OAUTH2 | false |
| PENDO | Pendo | Product Analytics | API_KEY | false |
| HOTJAR | Hotjar | Heatmaps | API_KEY | false |
| CONTENTSQUARE | Contentsquare | Experience Analytics | API_KEY | false |
| QUANTUM_METRIC | Quantum Metric | Experience Analytics | API_KEY | false |
| LOGROCKET | LogRocket | Session Replay | API_KEY | false |
| SINGULAR | Singular | Marketing Analytics | API_KEY | false |
| ROCKERBOX | Rockerbox | Attribution | API_KEY | false |
| MEASURED | Measured | Incrementality | API_KEY | false |
| FOSPHA | Fospha | Attribution | API_KEY | false |
| OPTIMIZELY | Optimizely | A/B Testing | API_KEY | false |
| VWO | VWO | Testing | API_KEY | false |
| DYNAMIC_YIELD | Dynamic Yield | Personalization | API_KEY | false |
| MONETATE | Monetate | Personalization | API_KEY | false |
| NOSTO | Nosto | E-commerce Personalization | API_KEY | false |
| ALGOLIA | Algolia | Search | API_KEY | false |
| BAZAARVOICE | Bazaarvoice | Reviews/UGC | API_KEY | false |
| POWERREVIEWS | PowerReviews | Reviews | API_KEY | false |
| TRUSTPILOT | Trustpilot | Reviews | API_KEY | false |
| SMILE | Smile.io | Loyalty | API_KEY | false |
| LOYALTYLION | LoyaltyLion | Loyalty | API_KEY | false |
| FRIENDBUY | Friendbuy | Referrals | API_KEY | false |
| EXTOLE | Extole | Referrals | API_KEY | false |

**Platform Summary:**
- Tier 1 (Critical): 8 platforms
- Tier 2 (High Priority): 15 platforms
- Tier 3 (Standard): 30 platforms
- Tier 4 (Extended): 110+ platforms
- **Total: 163+ platforms**

### 7.5 Sample Storefronts

| code | name | is_active |
|------|------|-----------|
| pfizer | Pfizer Store | true |
| bosley | Bosley | true |
| hims | Hims | true |
| roman | Roman | true |

### 7.6 Sample sGTM Configs

| storefront | sgtm_url | is_active |
|------------|----------|-----------|
| pfizer | https://tags.upscript.com/pfizer | true |
| bosley | https://tags.upscript.com/bosley | true |
| hims | https://tags.upscript.com/hims | true |
| roman | https://tags.upscript.com/roman | true |

---

## 8. Kill Switch Hierarchy

Three-level hierarchy for disabling event processing:

```
Level 1: storefronts.is_active = false
         → Storefront disabled entirely (reject all events)

Level 2: storefront_sgtm_config.is_active = false
         → sGTM forwarding disabled (fall back to direct platform)

Level 3: ad_analytics_platforms.is_active = false
         → Platform disabled globally

Level 4: platform_credentials.is_active = false
         → Platform disabled for specific storefront

Evaluation Order:
1. Check storefronts.is_active → if false, reject with 400
2. Check storefront_sgtm_config.is_active → if true, forward to sGTM
3. If no sGTM or sGTM disabled, check platform_credentials for direct forwarding
4. Check ad_analytics_platforms.is_active and platform_credentials.is_active
```

---

## 10. Forwarding Logic

```python
def forward_event(event, storefront):
    # 1. Check if sGTM is configured and active
    sgtm_config = get_sgtm_config(storefront.id)

    if sgtm_config and sgtm_config.is_active:
        # Primary: Forward to sGTM
        return forward_to_sgtm(event, sgtm_config)

    # 2. Fallback: Forward to direct platform connections
    platform_credentials = get_active_platform_credentials(storefront.id)

    results = []
    for cred in platform_credentials:
        if cred.platform.is_active and cred.is_active:
            adapter = get_adapter(cred.platform.code)
            result = adapter.forward(event, cred)
            results.append(result)

    return results
```

---

## 11. sGTM Payload Formats

The sGTM adapter supports two client types with different payload formats:

### GA4 Client Type (Default)

Uses GA4 Measurement Protocol format. Sent to `{sgtm_url}/mp/collect`:

```
POST https://tags.upscript.com/mp/collect?measurement_id=G-XXXXXX&api_secret=XXX
Content-Type: application/json

{
  "client_id": "session_123",
  "user_id": "user_456",
  "events": [
    {
      "name": "purchase",
      "params": {
        "transaction_id": "ORD-123",
        "value": 50.00,
        "currency": "USD",
        "storefront_id": "pfizer",
        "utm_source": "facebook",
        "utm_medium": "cpc",
        "utm_campaign": "pfizer_q1",
        "t_value": "affiliate_123"
      }
    }
  ]
}
```

**Event name mapping:**
- `purchase_completed` → `purchase`
- `complete_registration` → `sign_up`
- `lead` → `generate_lead`
- Custom events (e.g., `rx_issued`) pass through as-is

### Custom Client Type

Flexible JSON format for custom sGTM clients. Sent to `{sgtm_url}{custom_endpoint_path}`:

```
POST https://tags.upscript.com/collect
Content-Type: application/json
X-Api-Key: your-api-key  (if custom_headers configured)

{
  "event_name": "purchase_completed",
  "storefront_id": "pfizer",
  "order_id": "ORD-123",
  "order_revenue": 50.00,
  "t_value": "affiliate_123",
  "utm_source": "facebook",
  "utm_medium": "cpc",
  "utm_campaign": "pfizer_q1",
  "session_id": "session_123",
  ...all payload fields pass through...
}
```

The custom format passes through all event payload fields with minimal transformation, allowing the sGTM custom client to parse and route as needed.

---

## 12. Retry Logic

```
Configuration:
  RETRY_MAX_ATTEMPTS=3
  RETRY_INTERVAL_SECONDS=120

Flow:
  Attempt 1 (immediate) → Fail → next_retry_at = now + 120s
  Attempt 2 (after 2 min) → Fail → next_retry_at = now + 120s
  Attempt 3 (after 2 min) → Fail → status = FAILED (no more retries)

Worker Query:
  SELECT * FROM marketing_events
  WHERE status IN ('PENDING', 'PROCESSING')
  AND (next_retry_at IS NULL OR next_retry_at <= NOW())
  ORDER BY created_at ASC
  LIMIT 100
```

---

## 13. Dependencies

### requirements.txt
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.25
pymysql>=1.1.0
cryptography>=42.0.0
alembic>=1.13.1
pydantic>=2.6.0
pydantic-settings>=2.1.0
httpx>=0.26.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
```

### requirements-dev.txt
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
testcontainers[mysql]>=3.7.1
httpx>=0.26.0
black>=24.1.0
isort>=5.13.0
flake8>=7.0.0
mypy>=1.8.0
```

---

## 14. Next Steps

1. Set up project structure
2. Implement database models and migrations
3. Implement core services (event, storefront, forwarding)
4. Implement sGTM adapter (primary)
5. Implement platform adapters (fallback)
6. Implement API endpoint
7. Implement background retry worker
8. Write unit tests
9. Write integration tests
10. Dockerize application

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-15 | Claude | Initial design |
| 1.1 | 2026-01-15 | Claude | Updated server events to batch format |
| 2.0 | 2026-01-18 | Claude | Simplified to server events + sGTM only |
| 2.1 | 2026-01-18 | Claude | Renamed to marketing-events-relay-ms. Added platform tables and adapters for direct platform fallback |
| 2.2 | 2026-01-18 | Claude | Added comprehensive platform list (163+ platforms) with 4-tier prioritization. Created AD-ANALYTICS-PLATFORMS.md reference document |

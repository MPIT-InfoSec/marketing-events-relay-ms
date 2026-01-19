# Marketing Events Relay API - Postman Collection

This directory contains a comprehensive Postman collection for testing and interacting with the Marketing Events Relay Microservice API.

## Files

| File | Description |
|------|-------------|
| `Marketing_Events_Relay_API.postman_collection.json` | Main API collection with all endpoints and tests |
| `Local.postman_environment.json` | Environment variables for local development |
| `README.md` | This documentation file |

## Quick Start

### 1. Import into Postman

1. Open Postman
2. Click **Import** button (top-left)
3. Drag and drop both JSON files, or click **Upload Files**
4. Select both `Marketing_Events_Relay_API.postman_collection.json` and `Local.postman_environment.json`
5. Click **Import**

### 2. Select Environment

1. In the top-right corner, click the environment dropdown
2. Select **"Marketing Events Relay - Local"**

### 3. Update Credentials (if needed)

If your local server uses different credentials:

1. Click the **eye icon** next to the environment dropdown
2. Click **Edit** on the "Marketing Events Relay - Local" environment
3. Update `username` and `password` values to match your `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` environment variables
4. Click **Save**

### 4. Start Testing

1. Ensure your local server is running (`uvicorn app.main:app --reload`)
2. Expand the collection in the sidebar
3. Start with **Health Checks** folder to verify connectivity
4. Run **Admin API - Storefronts** > **Create Storefront - Bosley** to set up sample data
5. Continue with other endpoints

## Collection Structure

```
Marketing Events Relay API/
├── Health Checks/
│   ├── Liveness Check (GET /health)
│   └── Readiness Check (GET /health/ready)
│
├── Admin API - Storefronts/
│   ├── Create Storefront
│   ├── Create Storefront - Bosley (Sample)
│   ├── Create Storefront - Pfizer (Sample)
│   ├── List Storefronts
│   ├── List Active Storefronts Only
│   ├── Get Storefront by ID
│   ├── Update Storefront
│   ├── Disable Storefront (Kill Switch)
│   ├── Enable Storefront
│   ├── Delete Storefront
│   └── Get Non-Existent Storefront (404)
│
├── Admin API - Platforms/
│   ├── Create Platform - Meta CAPI
│   ├── Create Platform - GA4
│   ├── Create Platform - TikTok
│   ├── List All Platforms
│   ├── List Tier 1 Platforms
│   ├── List Advertising Platforms
│   ├── Get Platform by ID
│   ├── Update Platform
│   └── Disable Platform (Kill Switch)
│
├── Admin API - Credentials/
│   ├── Create Credential
│   ├── Get Credential (Without Decrypt)
│   ├── Get Credential (With Decrypt)
│   ├── List Credentials
│   ├── List Credentials by Storefront
│   ├── Update Credential
│   ├── Disable Credential (Kill Switch)
│   └── Delete Credential
│
├── Admin API - sGTM Configs/
│   ├── Create sGTM Config (GA4)
│   ├── Create sGTM Config (Custom)
│   ├── List sGTM Configs
│   ├── List Active sGTM Configs
│   ├── Get sGTM Config by ID
│   ├── Update sGTM Config
│   ├── Disable sGTM Config (Kill Switch)
│   └── Delete sGTM Config
│
├── Event Ingestion/
│   ├── Ingest Full OMS Batch (Sample)
│   ├── Ingest Single Event
│   ├── Ingest Event with All Fields
│   ├── Ingest Events - Unknown Storefront
│   ├── Ingest Events - Duplicate Order ID
│   ├── Ingest Events - Partial Success
│   ├── Ingest Events - Empty Batch with Error
│   ├── Ingest Events - Empty Batch without Error (422)
│   └── Ingest Events - Large Batch (50 events)
│
└── Error Scenarios/
    ├── 401 - No Authentication
    ├── 401 - Invalid Credentials
    ├── 404 - Resource Not Found
    ├── 409 - Duplicate Storefront
    ├── 422 - Invalid Storefront ID Format
    ├── 422 - Missing Required Field
    ├── 422 - Invalid sGTM URL
    ├── 422 - GA4 Config Missing measurement_id
    └── 401 - Event Ingestion Without Auth
```

## Running Tests

### Run Individual Request

1. Select a request from the collection
2. Click **Send**
3. View response and test results in the **Tests** tab

### Run Folder

1. Right-click on a folder
2. Select **Run folder**
3. Configure run options (iterations, delay, etc.)
4. Click **Run**

### Run Entire Collection

1. Click the **three dots** menu on the collection
2. Select **Run collection**
3. Choose folders to include
4. Configure options
5. Click **Run Marketing Events Relay API**

## Recommended Test Order

For best results, run tests in this order:

1. **Health Checks** - Verify server is running
2. **Admin API - Storefronts** - Create Bosley and Pfizer storefronts
3. **Admin API - Platforms** - Create Meta, GA4, TikTok platforms
4. **Admin API - sGTM Configs** - Configure sGTM for storefronts
5. **Admin API - Credentials** - Add platform credentials
6. **Event Ingestion** - Test event batch processing
7. **Error Scenarios** - Verify error handling

## Environment Variables

### Configurable Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |
| `username` | `admin` | Basic auth username |
| `password` | `admin` | Basic auth password |

### Auto-Populated Variables

These are automatically set by test scripts:

| Variable | Description |
|----------|-------------|
| `storefront_db_id` | Database ID of created test storefront |
| `bosley_storefront_id` | Database ID of Bosley storefront |
| `pfizer_storefront_id` | Database ID of Pfizer storefront |
| `meta_platform_id` | Database ID of Meta CAPI platform |
| `ga4_platform_id` | Database ID of GA4 platform |
| `credential_id` | Database ID of created credential |
| `sgtm_config_id` | Database ID of created sGTM config |
| `order_id_*` | Generated unique order IDs for testing |

## Test Scripts

Each request includes test scripts that verify:

- **Status Codes**: Correct HTTP status codes
- **Response Structure**: Required fields are present
- **Data Validation**: Values match expected results
- **Variable Storage**: IDs saved for subsequent requests

### Example Test Script

```javascript
// Test: Status code is 200
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test: Response has required fields
pm.test("Response has storefront details", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('storefront_id');
});

// Save ID for later use
if (pm.response.code === 201) {
    const jsonData = pm.response.json();
    pm.collectionVariables.set('storefront_db_id', jsonData.id);
}
```

## OMS Event Batch Format

The Event Ingestion endpoints accept batches in this format:

```json
{
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
            "storefront_id": "bosley",
            "event_name": "purchase_completed",
            "event_time": "2026-01-15T10:25:00Z",
            "order_id": "2025020100003333",
            "order_revenue": 80.79,
            "utm_source": "google",
            "utm_medium": "organic"
        }
    ],
    "error": "",
    "next_index": 1000,
    "next_url": "https://oms.example.com/events?offset=1000",
    "previous_index": "",
    "previous_url": ""
}
```

## Troubleshooting

### Connection Refused

- Ensure the server is running: `uvicorn app.main:app --reload`
- Verify `base_url` is correct in environment variables

### 401 Unauthorized

- Check `username` and `password` in environment match server config
- Verify `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` env vars on server

### 404 Not Found

- Resource may have been deleted or never created
- Run the setup requests to create required data

### Tests Failing

- Check if required variables are populated (run parent requests first)
- Verify database has required data

## Creating Additional Environments

To create environments for staging/production:

1. Right-click the "Local" environment
2. Select **Duplicate**
3. Rename to "Staging" or "Production"
4. Update `base_url` to the deployment URL
5. Update credentials as needed

## Support

For issues with the API, check:
- Server logs for error details
- API documentation in collection descriptions
- `CLAUDE.md` in the project root for architecture overview

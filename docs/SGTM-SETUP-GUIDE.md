# Server-side Google Tag Manager (sGTM) Setup Guide

This guide explains how to set up sGTM to receive events from the Marketing Events Relay microservice and forward them to GA4, Meta CAPI, TikTok, and other platforms.

---

## Architecture: 100% Server-side for New Tenants

**For all new Upscript tenants, there is NO web GTM and NO client-side tracking tags in storefront portals.** All marketing analytics is measured server-side.

### Why Server-side Only?

| Benefit | Description |
|---------|-------------|
| **No Ad Blockers** | Server-side requests bypass browser ad blockers |
| **Better Data Quality** | Data comes from OMS (source of truth), not browser |
| **Higher Match Rates** | Meta CAPI gets better user matching with server data |
| **Simplified Compliance** | No client-side cookies = simpler privacy compliance |
| **Consistent Tracking** | Works regardless of browser, device, or user settings |
| **No Tag Management in Storefronts** | Cleaner frontend, faster page loads |

### The Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STOREFRONT PORTAL (BROWSER)                          │
│                                                                             │
│                    ┌─────────────────────────────────────┐                  │
│                    │  NO tracking tags                   │                  │
│                    │  NO web GTM                         │                  │
│                    │  NO pixels (Meta, TikTok, etc.)     │                  │
│                    │  Just clean application code        │                  │
│                    └─────────────────────────────────────┘                  │
│                                                                             │
│                    User actions generate orders/events                      │
│                                     │                                       │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND SYSTEMS                                 │
│                                                                             │
│  ┌─────────────┐      ┌─────────────────────┐      ┌─────────────────────┐ │
│  │    OMS      │      │ Marketing Events    │      │      sGTM           │ │
│  │  Database   │ ───► │ Relay Microservice  │ ───► │ (tags.upscript.com) │ │
│  │             │      │                     │      │                     │ │
│  │ • Orders    │      │ • Validates events  │      │ • GA4 Client        │ │
│  │ • Consults  │      │ • Routes to sGTM    │      │ • Routes to tags    │ │
│  │ • RX Events │      │ • Retry on failure  │      │                     │ │
│  └─────────────┘      └─────────────────────┘      └──────────┬──────────┘ │
│                                                               │             │
│                    All events from backend:                   │             │
│                    • purchase_completed                       │             │
│                    • consult_started                          │             │
│                    • consult_completed                        │             │
│                    • rx_issued                                │             │
│                    • lead / signup                            ▼             │
│                                                                             │
│                                              ┌────────────────────────────┐ │
│                                              │  Platform APIs:            │ │
│                                              │  • GA4 Measurement Protocol│ │
│                                              │  • Meta Conversions API    │ │
│                                              │  • TikTok Events API       │ │
│                                              │  • Google Ads Conversions  │ │
│                                              │  • Snapchat CAPI           │ │
│                                              │  • Pinterest CAPI          │ │
│                                              └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What This Means

| Aspect | Server-side Only Approach |
|--------|---------------------------|
| **Page Views** | Not tracked (or tracked via OMS session data) |
| **Remarketing Audiences** | Built from conversion data, not browsing |
| **Consent Management** | Handled at OMS level, not browser |
| **User Identification** | Via order data (email, phone) not cookies |
| **Attribution** | Based on UTM params captured at conversion |

### Events Tracked (All from OMS)

| Event | Description | Platforms |
|-------|-------------|-----------|
| `purchase_completed` | Order completed | GA4, Meta, TikTok, Google Ads |
| `consult_started` | Consultation began | GA4, Meta, TikTok |
| `consult_completed` | Consultation finished | GA4, Meta, TikTok |
| `rx_issued` | Prescription issued | GA4, Meta, TikTok |
| `lead` | Lead captured | GA4, Meta, Google Ads |
| `signup` | User registered | GA4, Meta |

---

## Legacy Tenants: Hybrid Architecture (Optional Reference)

> **Note:** This section is for reference only. It documents the hybrid approach used by existing/legacy tenants who have web GTM in place. **New tenants should skip to the Overview section.**

<details>
<summary>Click to expand legacy hybrid architecture details</summary>

For legacy tenants with existing web GTM, the architecture is hybrid:

### Client-side (Web GTM) - Existing Setup

| Component | Purpose |
|-----------|---------|
| GA4 Page Views | Track page visits |
| Meta Pixel (fbq) | Page views, remarketing |
| Google Ads Base Tag | Remarketing audiences |
| Cookiebot/Consent | GDPR consent management |
| Salesforce Chat Widget | Customer support (UI, not analytics) |

### Server-side (sGTM) - Conversions

| Event Type | Source |
|------------|--------|
| Purchases | OMS |
| Leads/Signups | OMS |
| RX Issued | OMS |
| Consult Events | OMS |

### Components That Stay Client-side Only

| Component | ID/Config | Reason |
|-----------|-----------|--------|
| Salesforce Chat | Org: `00D5e000002GWZE` | UI widget |
| Cookiebot | ID: `d604caed-d533-46da-ae69-ab7ac8a89971` | Consent |
| Google Ads Base | `AW-801363001` | Remarketing |

</details>

---

## Overview

```
                                           sGTM Container
                                    ┌─────────────────────────────┐
Marketing Events Relay              │                             │
        │                           │  ┌─────────────────────┐    │
        │  POST /mp/collect         │  │    GA4 Client       │    │
        │  (GA4 Measurement         │  │    (parses HTTP     │    │
        │   Protocol format)        │  │     requests)       │    │
        └──────────────────────────►│  └──────────┬──────────┘    │
                                    │             │               │
                                    │    Event Data Object        │
                                    │             │               │
                                    │  ┌──────────┴──────────┐    │
                                    │  │      Triggers       │    │
                                    │  │  (event_name =      │    │
                                    │  │   purchase, etc.)   │    │
                                    │  └──────────┬──────────┘    │
                                    │             │               │
                    ┌───────────────┼─────────────┼───────────────┼───────────────┐
                    │               │             │               │               │
                    ▼               ▼             ▼               ▼               ▼
             ┌──────────┐    ┌──────────┐  ┌──────────┐   ┌──────────┐    ┌──────────┐
             │  GA4     │    │  Meta    │  │ TikTok   │   │  Google  │    │  Custom  │
             │  Tag     │    │  CAPI    │  │ Events   │   │  Ads     │    │   Tag    │
             │          │    │  Tag     │  │  API     │   │  Tag     │    │          │
             └────┬─────┘    └────┬─────┘  └────┬─────┘   └────┬─────┘    └────┬─────┘
                  │               │             │               │               │
                  ▼               ▼             ▼               ▼               ▼
             Google          Facebook       TikTok          Google          Any
             Analytics       Graph API      API             Ads             Endpoint
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create sGTM Container

### 1.1 Create Container in GTM

1. Go to [tagmanager.google.com](https://tagmanager.google.com)
2. Click **Admin** → **Create Container**
3. Enter container name: `tags.upscript.com` (or your domain)
4. Select **Server** as container type
5. Click **Create**

### 1.2 Deploy sGTM Server

**Option A: Google Cloud (Recommended)**
1. In the container, go to **Admin** → **Container Settings**
2. Click **Manually provision tagging server**
3. Copy the Container Config string
4. Deploy to Google Cloud Run or App Engine:
   - Follow: https://developers.google.com/tag-platform/tag-manager/server-side/deployment

**Option B: Custom Server**
- Use the official Docker image: `gcr.io/cloud-tagging-10302018/gtm-cloud-image`
- Set environment variable `CONTAINER_CONFIG` with your config string

### 1.3 Configure Custom Domain

1. Point `tags.upscript.com` to your sGTM server
2. Set up SSL certificate
3. Verify the domain in container settings

---

## Step 2: Configure GA4 Client

The GA4 Client receives requests in GA4 Measurement Protocol format from our microservice.

### 2.1 Add GA4 Client

1. Go to **Clients** in your sGTM container
2. Click **New** → **GA4**
3. Configure:
   - **Client name**: `GA4 Client`
   - **Default GA4 paths**: Leave enabled (`/g/collect`, `/mp/collect`)

4. Click **Save**

### 2.2 Client Behavior

The GA4 Client will:
- Accept POST requests to `/mp/collect`
- Parse the GA4 Measurement Protocol JSON
- Create an **Event Data Object** with:
  - `event_name`: The event name (e.g., "purchase")
  - `client_id`: From the payload
  - All event parameters (value, currency, transaction_id, etc.)

---

## Step 3: Create Triggers

### 3.1 All Events Trigger

1. Go to **Triggers** → **New**
2. Name: `All Events`
3. Trigger Type: **Custom**
4. Fire on: **All Events**
5. Save

### 3.2 Purchase Event Trigger

1. Go to **Triggers** → **New**
2. Name: `Purchase Event`
3. Trigger Type: **Custom**
4. Fire on: **Some Events**
5. Condition: `Event Name` equals `purchase`
6. Save

### 3.3 Custom Event Triggers (Healthcare/Pharma)

Create triggers for your custom events:

| Trigger Name | Condition |
|--------------|-----------|
| `RX Issued` | `Event Name` equals `rx_issued` |
| `Consult Started` | `Event Name` equals `consult_started` |
| `Consult Completed` | `Event Name` equals `consult_completed` |

---

## Step 4: Set Up GA4 Tag

Forward events to Google Analytics 4.

### 4.1 Create GA4 Tag

1. Go to **Tags** → **New**
2. Name: `GA4 - All Events`
3. Tag Type: **Google Analytics: GA4**
4. Configuration:
   - **Measurement ID**: `G-XXXXXXXXX` (your GA4 property)
   - **Event Name**: `{{Event Name}}` (use built-in variable)
   - **Event Parameters**: (Auto-populated from event data)

5. Triggering: Select `All Events` trigger
6. Save

---

## Step 5: Set Up Meta Conversions API (CAPI) Tag

### 5.1 Install Meta CAPI Template

1. Go to **Templates** → **Tag Templates** → **Search Gallery**
2. Search for "Facebook Conversions API"
3. Add the official Meta template to your workspace

### 5.2 Create Meta CAPI Tag

1. Go to **Tags** → **New**
2. Name: `Meta CAPI - Purchase`
3. Tag Type: **Facebook Conversions API** (from template)
4. Configuration:

```
Pixel ID:           1248630053164112  (from your web GTM)
Access Token:       [Get from Meta Events Manager]
Event Name:         Purchase
Action Source:      website

Event Parameters:
- value:            {{Event Data - value}}
- currency:         {{Event Data - currency}}
- content_type:     product
- order_id:         {{Event Data - transaction_id}}

User Data (for matching):
- client_ip_address: {{Client IP Address}}
- client_user_agent: {{User Agent}}
- em (email hash):   {{Event Data - user_data.em}}
- ph (phone hash):   {{Event Data - user_data.ph}}
```

5. Triggering: Select `Purchase Event` trigger
6. Save

### 5.3 Meta Event Mapping

Create tags for each event type:

| Web GTM Event | sGTM Tag | Meta Event |
|---------------|----------|------------|
| `add_to_cart` | Meta CAPI - Add to Cart | `AddToCart` |
| `purchase` | Meta CAPI - Purchase | `Purchase` |
| `lead` | Meta CAPI - Lead | `Lead` |
| `complete_registration` | Meta CAPI - CompleteRegistration | `CompleteRegistration` |

### 5.4 Get Meta Access Token

1. Go to [Meta Events Manager](https://business.facebook.com/events_manager)
2. Select your Pixel
3. Go to **Settings** → **Conversions API**
4. Generate Access Token
5. Store securely (use sGTM's built-in secret manager)

---

## Step 6: Set Up TikTok Events API Tag

### 6.1 Install TikTok Template

1. Go to **Templates** → **Tag Templates** → **Search Gallery**
2. Search for "TikTok Events API"
3. Add the template

### 6.2 Create TikTok Tag

1. Go to **Tags** → **New**
2. Name: `TikTok - Purchase`
3. Tag Type: **TikTok Events API**
4. Configuration:

```
Pixel ID:           [Your TikTok Pixel ID]
Access Token:       [From TikTok Ads Manager]
Event:              CompletePayment

Parameters:
- value:            {{Event Data - value}}
- currency:         {{Event Data - currency}}
- content_type:     product
- order_id:         {{Event Data - transaction_id}}
```

5. Triggering: Select `Purchase Event` trigger
6. Save

---

## Step 7: Set Up Google Ads Conversion Tag

For server-side conversion tracking with Google Ads.

### Understanding Web GTM vs sGTM for Google Ads

**Your existing web GTM has:**
```
Tag Type: Google Tag
Tag ID: AW-801363001
Fires on: cookieConsentUpdated (after Cookiebot consent)
```

This is the **base Google Ads tag** for remarketing/audiences. It stays in web GTM.

**In sGTM, you need:** A **Conversion Tracking** tag that fires on purchase events from OMS.

### 7.1 Get Conversion Label from Google Ads

1. Go to [Google Ads](https://ads.google.com)
2. Navigate to **Tools & Settings** → **Conversions**
3. Find or create your "Purchase" conversion
4. Click on it and find the **Conversion ID** and **Conversion Label**
   - Conversion ID: `801363001` (same as AW-801363001)
   - Conversion Label: Something like `AbCdEfGhIjKlMnOp` (unique per conversion)

### 7.2 Create Google Ads Conversion Tag in sGTM

1. Go to **Tags** → **New**
2. Name: `Google Ads - Purchase Conversion`
3. Tag Type: **Google Ads Conversion Tracking**
4. Configuration:
   - **Conversion ID**: `801363001`
   - **Conversion Label**: `[Your label from step 7.1]`
   - **Conversion Value**: `{{Event Data - value}}`
   - **Currency Code**: `{{Event Data - currency}}`
   - **Order ID**: `{{Event Data - transaction_id}}`

5. Triggering: Select `Purchase Event` trigger
6. Save

### 7.3 Google Ads Event Types

Create separate conversion tags for different conversion types:

| Conversion Action | sGTM Trigger | Notes |
|-------------------|--------------|-------|
| Purchase | `event_name = purchase` | Primary conversion |
| Lead | `event_name = generate_lead` | For lead gen campaigns |
| Sign Up | `event_name = sign_up` | Registration conversions |

**Note:** Each conversion action in Google Ads has a unique Conversion Label. Create separate tags for each.

---

## Step 8: Create Variables

### 8.1 Event Data Variables

Create variables to extract data from the event:

| Variable Name | Type | Path |
|---------------|------|------|
| `Event Data - value` | Event Data | `value` |
| `Event Data - currency` | Event Data | `currency` |
| `Event Data - transaction_id` | Event Data | `transaction_id` |
| `Event Data - storefront_id` | Event Data | `storefront_id` |
| `Event Data - t_value` | Event Data | `t_value` |
| `Event Data - user_data.em` | Event Data | `user_data.em` |
| `Event Data - user_data.ph` | Event Data | `user_data.ph` |

### 8.2 Built-in Variables

Enable these built-in variables:
- `Event Name`
- `Client ID`
- `User Agent`
- `IP Address`

---

## Step 9: Test Configuration

### 9.1 Use Preview Mode

1. Click **Preview** in sGTM
2. Open Preview Debugger

### 9.2 Send Test Request

```bash
curl -X POST "https://tags.upscript.com/mp/collect?measurement_id=G-XXXXXXXXX&api_secret=YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test_client_123",
    "events": [{
      "name": "purchase",
      "params": {
        "transaction_id": "TEST-001",
        "value": 99.99,
        "currency": "USD",
        "storefront_id": "bosley",
        "t_value": "affiliate_123"
      }
    }]
  }'
```

### 9.3 Verify in Preview

Check that:
1. GA4 Client received the request
2. Triggers fired correctly
3. Tags executed (GA4, Meta CAPI, TikTok)

---

## Step 10: Production Checklist

### Configuration Checklist

- [ ] sGTM server deployed and accessible at `tags.upscript.com`
- [ ] SSL certificate configured
- [ ] GA4 Client enabled
- [ ] GA4 Tag configured with correct Measurement ID
- [ ] Meta CAPI Tag configured with Pixel ID and Access Token
- [ ] TikTok Tag configured with Pixel ID and Access Token
- [ ] All triggers created for event types
- [ ] Variables created for event data extraction
- [ ] Preview mode tested successfully

### Security Checklist

- [ ] Access tokens stored in sGTM Secret Manager
- [ ] API secrets not hardcoded
- [ ] Server firewall configured (only accept from known IPs)

---

## Event Mapping Reference

### Events from Marketing Events Relay

| Event Type | GA4 Event Name | Meta Event | TikTok Event |
|------------|---------------|------------|--------------|
| `purchase_completed` | `purchase` | `Purchase` | `CompletePayment` |
| `add_to_cart` | `add_to_cart` | `AddToCart` | `AddToCart` |
| `begin_checkout` | `begin_checkout` | `InitiateCheckout` | `InitiateCheckout` |
| `lead` | `generate_lead` | `Lead` | `SubmitForm` |
| `complete_registration` | `sign_up` | `CompleteRegistration` | `CompleteRegistration` |
| `rx_issued` | `rx_issued` | `Lead` (custom) | Custom Event |
| `consult_started` | `consult_started` | Custom Event | Custom Event |
| `consult_completed` | `consult_completed` | `Lead` | `SubmitForm` |

---

## Your Existing Credentials Reference

Based on your web GTM configuration, here are the IDs you'll need for sGTM:

### Known IDs (from web GTM)

| Platform | ID Type | Value | Where to Use |
|----------|---------|-------|--------------|
| **Meta/Facebook** | Pixel ID | `1248630053164112` | Meta CAPI Tag |
| **Google Ads** | Conversion ID | `801363001` | Google Ads Conversion Tag |
| **Cookiebot** | Cookiebot ID | `d604caed-d533-46da-ae69-ab7ac8a89971` | Not needed in sGTM |

### IDs You Need to Obtain

| Platform | What to Get | Where to Get It |
|----------|-------------|-----------------|
| **GA4** | Measurement ID (`G-XXXXXX`) | GA4 Admin → Property → Data Streams |
| **GA4** | API Secret | GA4 Admin → Data Streams → Measurement Protocol API secrets |
| **Meta** | Access Token | Meta Events Manager → Settings → Conversions API |
| **Google Ads** | Conversion Label | Google Ads → Tools → Conversions → [Your conversion] |
| **TikTok** | Pixel ID | TikTok Ads Manager → Assets → Events |
| **TikTok** | Access Token | TikTok Ads Manager → Assets → Events → Settings |

### Components That Stay in Web GTM Only

These are NOT migrated to sGTM:

| Component | ID/Config | Reason |
|-----------|-----------|--------|
| **Salesforce Chat** | Org: `00D5e000002GWZE`, Deployment: `MIAW_Channel_V1` | UI widget, not analytics |
| **Cookiebot** | ID: `d604caed-d533-46da-ae69-ab7ac8a89971` | Consent must be client-side |
| **Google Ads Base Tag** | `AW-801363001` | Remarketing needs client cookies |

---

## Microservice Configuration

Once sGTM is set up, configure the microservice's sGTM connection:

```json
{
  "storefront_id": 1,
  "sgtm_url": "https://tags.upscript.com",
  "client_type": "ga4",
  "measurement_id": "G-XXXXXXXXX",
  "api_secret": "your_api_secret_here",
  "is_active": true
}
```

The microservice will send requests in GA4 Measurement Protocol format, and sGTM will route to all configured platforms.

### Per-Storefront Configuration

Each storefront can have different sGTM configurations:

| Storefront | sGTM URL | Measurement ID | Notes |
|------------|----------|----------------|-------|
| bosley | `https://tags.upscript.com` | `G-BOSLEY123` | Main storefront |
| pfizer | `https://tags.upscript.com` | `G-PFIZER456` | Different GA4 property |
| hims | `https://tags-hims.example.com` | `G-HIMS789` | Separate sGTM instance |

The sGTM container can route events to different platform accounts based on the `storefront_id` parameter in the event data.

---

## Troubleshooting

### Events not appearing in GA4
- Check Measurement ID is correct
- Verify api_secret is valid
- Check sGTM Preview for errors

### Meta CAPI events not tracking
- Verify Pixel ID and Access Token
- Check Event Match Quality in Meta Events Manager
- Ensure user data (em, ph) is being passed for deduplication

### TikTok events not tracking
- Verify Pixel ID and Access Token
- Check TikTok Events Manager for errors
- Ensure event names match TikTok's expected format

---

## Frequently Asked Questions

### Q: Do new tenants need web GTM?

**A: No.** New Upscript tenants use 100% server-side tracking. There are no tracking tags in storefront portals. Benefits:
- Cleaner frontend code
- Faster page loads
- No ad blocker issues
- Simpler privacy compliance
- Data from source of truth (OMS)

### Q: What about page view tracking?

**A: Page views are not tracked for new tenants.** The focus is on conversion events (purchases, leads, consults) which are the metrics that matter for marketing attribution and ROAS. If page view data is needed, it can be derived from OMS session data.

### Q: How does attribution work without client-side tracking?

**A: Attribution is based on UTM parameters captured at conversion time.** When a user completes an action (purchase, lead, etc.), the OMS captures:
- `utm_source`, `utm_medium`, `utm_campaign`
- `t-value` (affiliate tracking)
- `session_id`

These are sent with the event to sGTM and forwarded to platforms for attribution.

### Q: What about remarketing audiences?

**A: Remarketing audiences are built from conversion data.** Instead of tracking all browsing behavior:
- Upload customer lists (email/phone hashes) to platforms
- Use conversion events to build "purchasers" audiences
- Create lookalike audiences from converters

This is often more effective than cookie-based remarketing.

### Q: Will we have duplicate events?

**A: No, for new tenants.** Since there's no client-side tracking, all events come from server-side only. No deduplication needed.

For **legacy tenants** with hybrid tracking: Use `transaction_id` / `event_id` for deduplication.

### Q: What about consent management (GDPR/CCPA)?

**A: Simplified for server-side only.**
- No client-side cookies means fewer consent requirements
- Consent can be captured at account creation in OMS
- Meta CAPI supports `data_processing_options` for Limited Data Use (LDU)
- Pass consent status in event payload if needed

### Q: Can sGTM handle multiple storefronts?

**A: Yes.** The microservice sends `storefront_id` in every event. sGTM can:
- Route to different GA4 properties per storefront
- Use different Meta Pixels per storefront
- Create lookup tables in sGTM to map storefront → platform credentials

### Q: Do we need separate sGTM containers per storefront?

**A: Usually not.** A single sGTM container can handle multiple storefronts by:
- Using the `storefront_id` parameter to route events
- Creating lookup tables for storefront-specific credentials
- Using conditional logic in tags

However, if storefronts have completely different platform setups or compliance requirements, separate containers may make sense.

### Q: What platforms are supported?

**A: All major ad/analytics platforms via their server-side APIs:**
- Google Analytics 4 (Measurement Protocol)
- Meta/Facebook (Conversions API)
- TikTok (Events API)
- Google Ads (Enhanced Conversions)
- Snapchat (Conversions API)
- Pinterest (Conversions API)
- And 50+ more platforms

### Q: What about legacy tenants with existing web GTM?

**A: Legacy tenants can keep their web GTM.** The sGTM setup is additive - server-side tracking runs alongside client-side. See the "Legacy Tenants" section for hybrid architecture details.

---

## Quick Start Checklist

For the team setting up sGTM:

- [ ] **Step 1**: Create sGTM container in Google Tag Manager
- [ ] **Step 2**: Deploy sGTM server (Cloud Run recommended)
- [ ] **Step 3**: Configure custom domain (`tags.upscript.com`)
- [ ] **Step 4**: Enable GA4 Client in sGTM
- [ ] **Step 5**: Get credentials:
  - [ ] GA4 Measurement ID and API Secret
  - [ ] Meta Access Token (Pixel ID already known: `1248630053164112`)
  - [ ] Google Ads Conversion Label (Conversion ID already known: `801363001`)
  - [ ] TikTok Pixel ID and Access Token
- [ ] **Step 6**: Create sGTM tags (GA4, Meta CAPI, TikTok, Google Ads)
- [ ] **Step 7**: Test with Preview mode
- [ ] **Step 8**: Share GA4 Measurement ID + API Secret with microservice team

---

## Resources

- [sGTM Documentation](https://developers.google.com/tag-platform/tag-manager/server-side)
- [GA4 Measurement Protocol](https://developers.google.com/analytics/devguides/collection/protocol/ga4)
- [Meta Conversions API](https://developers.facebook.com/docs/marketing-api/conversions-api)
- [TikTok Events API](https://business-api.tiktok.com/portal/docs?id=1741601162187777)
- [Google Ads Server-side Tagging](https://developers.google.com/tag-platform/tag-manager/server-side/ads-setup)

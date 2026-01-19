# Ad & Analytics Platforms Reference

Comprehensive reference of all ad and analytics platforms for the Marketing Events Relay microservice.

---

## Table of Contents

1. [Platform Tiers](#platform-tiers)
2. [Tier 1 - Critical Platforms](#tier-1---critical-platforms)
3. [Tier 2 - High Priority Platforms](#tier-2---high-priority-platforms)
4. [Tier 3 - Standard Platforms](#tier-3---standard-platforms)
5. [Tier 4 - Extended Platforms](#tier-4---extended-platforms)
6. [Platform Categories Summary](#platform-categories-summary)
7. [Authentication Types](#authentication-types)
8. [Credential Structures](#credential-structures)

---

## Platform Tiers

| Tier | Priority | Description | Count |
|------|----------|-------------|-------|
| **Tier 1** | Critical | Must-have platforms used by 90%+ e-commerce | 7 |
| **Tier 2** | High | High-priority platforms used by 50%+ e-commerce | 15 |
| **Tier 3** | Standard | Common platforms used by 20%+ e-commerce | 30 |
| **Tier 4** | Extended | Niche/emerging platforms for specific use cases | 100+ |

---

## Tier 1 - Critical Platforms

These platforms are essential for any e-commerce business in the USA.

### 1.1 META_CAPI - Meta Conversions API

| Attribute | Value |
|-----------|-------|
| **Code** | `META_CAPI` |
| **Name** | Meta Conversions API |
| **Category** | Paid Social |
| **Purpose** | Facebook & Instagram ad optimization, retargeting, lookalike audiences |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://graph.facebook.com/v18.0` |
| **Rate Limits** | 1000 events/second per pixel |
| **Documentation** | https://developers.facebook.com/docs/marketing-api/conversions-api |

**Credential Structure:**
```json
{
  "pixel_id": "123456789012345",
  "access_token": "EAAxxxxxxxxxx",
  "test_event_code": "TEST12345"
}
```

**Event Mapping:**
| Standard Event | E-commerce Event |
|----------------|------------------|
| `Purchase` | purchase_completed |
| `InitiateCheckout` | checkout_started |
| `AddToCart` | add_to_cart |
| `Lead` | consult_started |
| `CompleteRegistration` | rx_issued |

---

### 1.2 GA4 - Google Analytics 4

| Attribute | Value |
|-----------|-------|
| **Code** | `GA4` |
| **Name** | Google Analytics 4 |
| **Category** | Analytics |
| **Purpose** | Web/app analytics, conversion tracking, audience building |
| **Connectivity** | Measurement Protocol (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://www.google-analytics.com/mp/collect` |
| **Rate Limits** | 1M hits/day free tier |
| **Documentation** | https://developers.google.com/analytics/devguides/collection/protocol/ga4 |

**Credential Structure:**
```json
{
  "measurement_id": "G-XXXXXXXXXX",
  "api_secret": "xxxxxxxxxxxxxxxxxxxx"
}
```

**Event Mapping:**
| Standard Event | E-commerce Event |
|----------------|------------------|
| `purchase` | purchase_completed |
| `begin_checkout` | checkout_started |
| `add_to_cart` | add_to_cart |
| `generate_lead` | consult_started |

---

### 1.3 GOOGLE_ADS - Google Ads

| Attribute | Value |
|-----------|-------|
| **Code** | `GOOGLE_ADS` |
| **Name** | Google Ads Conversions |
| **Category** | Paid Search |
| **Purpose** | Search/display/shopping ad optimization, conversion tracking |
| **Connectivity** | Google Ads API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://googleads.googleapis.com` |
| **Rate Limits** | 15,000 operations/day |
| **Documentation** | https://developers.google.com/google-ads/api/docs/conversions/upload-clicks |

**Credential Structure:**
```json
{
  "client_id": "xxxxx.apps.googleusercontent.com",
  "client_secret": "xxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxx",
  "developer_token": "xxxxxxxxxxxxxxx",
  "customer_id": "123-456-7890",
  "conversion_action_id": "123456789"
}
```

---

### 1.4 TIKTOK - TikTok Events API

| Attribute | Value |
|-----------|-------|
| **Code** | `TIKTOK` |
| **Name** | TikTok Events API |
| **Category** | Paid Social |
| **Purpose** | TikTok ad optimization, short-form video advertising |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://business-api.tiktok.com/open_api/v1.3/pixel/track` |
| **Rate Limits** | 1000 requests/minute |
| **Documentation** | https://ads.tiktok.com/marketing_api/docs?id=1701890979375106 |

**Credential Structure:**
```json
{
  "pixel_code": "XXXXXXXXXXXXXXXXX",
  "access_token": "xxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Event Mapping:**
| Standard Event | E-commerce Event |
|----------------|------------------|
| `CompletePayment` | purchase_completed |
| `InitiateCheckout` | checkout_started |
| `AddToCart` | add_to_cart |
| `SubmitForm` | consult_started |

---

### 1.5 MICROSOFT_ADS - Microsoft Advertising

| Attribute | Value |
|-----------|-------|
| **Code** | `MICROSOFT_ADS` |
| **Name** | Microsoft Advertising (Bing Ads) |
| **Category** | Paid Search |
| **Purpose** | Bing/Yahoo/DuckDuckGo search ads, conversion tracking |
| **Connectivity** | UET API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://bat.bing.com/action/0` |
| **Rate Limits** | 10,000 conversions/day |
| **Documentation** | https://docs.microsoft.com/en-us/advertising/guides/universal-event-tracking |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxx",
  "customer_id": "123456789",
  "account_id": "987654321",
  "tag_id": "12345678"
}
```

---

### 1.6 SNAPCHAT - Snapchat Conversions API

| Attribute | Value |
|-----------|-------|
| **Code** | `SNAPCHAT` |
| **Name** | Snapchat Conversions API |
| **Category** | Paid Social |
| **Purpose** | Snapchat ad optimization, Gen Z targeting |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://tr.snapchat.com/v2/conversion` |
| **Rate Limits** | 1000 events/second |
| **Documentation** | https://marketingapi.snapchat.com/docs/conversion.html |

**Credential Structure:**
```json
{
  "pixel_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "access_token": "xxxxxxxxxxxxxxxxxxxxxxx"
}
```

---

### 1.7 PINTEREST - Pinterest Conversions API

| Attribute | Value |
|-----------|-------|
| **Code** | `PINTEREST` |
| **Name** | Pinterest Conversions API |
| **Category** | Paid Social |
| **Purpose** | Pinterest ad optimization, visual discovery shopping |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://api.pinterest.com/v5/ad_accounts/{ad_account_id}/events` |
| **Rate Limits** | 1000 events/request |
| **Documentation** | https://developers.pinterest.com/docs/conversions/conversions/ |

**Credential Structure:**
```json
{
  "ad_account_id": "123456789012345678",
  "access_token": "xxxxxxxxxxxxxxxxxxxxxxx"
}
```

---

## Tier 2 - High Priority Platforms

High-priority platforms used by 50%+ of e-commerce businesses.

### 2.1 AMAZON_ADS - Amazon Advertising

| Attribute | Value |
|-----------|-------|
| **Code** | `AMAZON_ADS` |
| **Name** | Amazon Advertising API |
| **Category** | Retail Media |
| **Purpose** | Amazon marketplace ads, sponsored products |
| **Connectivity** | Amazon Ads API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://advertising-api.amazon.com` |
| **Rate Limits** | Variable by endpoint |
| **Documentation** | https://advertising.amazon.com/API/docs/en-us |

**Credential Structure:**
```json
{
  "client_id": "amzn1.application-oa2-client.xxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxx",
  "profile_id": "1234567890",
  "region": "NA"
}
```

---

### 2.2 AMAZON_ATTRIBUTION - Amazon Attribution

| Attribute | Value |
|-----------|-------|
| **Code** | `AMAZON_ATTRIBUTION` |
| **Name** | Amazon Attribution |
| **Category** | Attribution |
| **Purpose** | Off-Amazon traffic attribution to Amazon sales |
| **Connectivity** | Attribution API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://advertising-api.amazon.com/attribution` |
| **Rate Limits** | 1000 requests/day |
| **Documentation** | https://advertising.amazon.com/API/docs/en-us/amazon-attribution |

**Credential Structure:**
```json
{
  "client_id": "amzn1.application-oa2-client.xxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxx",
  "profile_id": "1234567890"
}
```

---

### 2.3 CRITEO - Criteo Events API

| Attribute | Value |
|-----------|-------|
| **Code** | `CRITEO` |
| **Name** | Criteo Events API |
| **Category** | Retargeting |
| **Purpose** | Dynamic retargeting, display advertising |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://api.criteo.com/2022-01/events` |
| **Rate Limits** | 1000 requests/minute |
| **Documentation** | https://developers.criteo.com/marketing-solutions/docs/events-api |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "partner_id": "12345"
}
```

---

### 2.4 TWITTER - Twitter/X Conversions API

| Attribute | Value |
|-----------|-------|
| **Code** | `TWITTER` |
| **Name** | Twitter/X Conversions API |
| **Category** | Paid Social |
| **Purpose** | Twitter ad optimization, brand awareness |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://ads-api.twitter.com/12/measurement/conversions` |
| **Rate Limits** | 1500 requests/15 min |
| **Documentation** | https://developer.twitter.com/en/docs/twitter-ads-api/measurement |

**Credential Structure:**
```json
{
  "consumer_key": "xxxxxxxxxxxxxxx",
  "consumer_secret": "xxxxxxxxxxxxxxx",
  "access_token": "xxxxxxxxxxxxxxx",
  "access_token_secret": "xxxxxxxxxxxxxxx",
  "pixel_id": "xxxxx"
}
```

---

### 2.5 LINKEDIN - LinkedIn Conversions API

| Attribute | Value |
|-----------|-------|
| **Code** | `LINKEDIN` |
| **Name** | LinkedIn Conversions API |
| **Category** | Paid Social |
| **Purpose** | B2B advertising, professional targeting |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://api.linkedin.com/rest/conversionEvents` |
| **Rate Limits** | 100 requests/day |
| **Documentation** | https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/conversions |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "access_token": "xxxxxxxxxxxxxxx",
  "account_id": "123456789"
}
```

---

### 2.6 REDDIT - Reddit Conversions API

| Attribute | Value |
|-----------|-------|
| **Code** | `REDDIT` |
| **Name** | Reddit Conversions API |
| **Category** | Paid Social |
| **Purpose** | Community-based advertising, niche targeting |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://ads-api.reddit.com/api/v2.0/conversions/events` |
| **Rate Limits** | 60 requests/minute |
| **Documentation** | https://ads-api.reddit.com/docs/v2/#tag/Conversions |

**Credential Structure:**
```json
{
  "pixel_id": "t2_xxxxxx",
  "access_token": "xxxxxxxxxxxxxxx"
}
```

---

### 2.7 KLAVIYO - Klaviyo Events API

| Attribute | Value |
|-----------|-------|
| **Code** | `KLAVIYO` |
| **Name** | Klaviyo Events API |
| **Category** | Email/SMS Marketing |
| **Purpose** | E-commerce email/SMS marketing, customer data |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://a.klaviyo.com/api` |
| **Rate Limits** | 75 requests/second |
| **Documentation** | https://developers.klaviyo.com/en/reference/api-overview |

**Credential Structure:**
```json
{
  "private_api_key": "pk_xxxxxxxxxxxxxxx",
  "public_api_key": "xxxxxxx"
}
```

---

### 2.8 ATTENTIVE - Attentive Events API

| Attribute | Value |
|-----------|-------|
| **Code** | `ATTENTIVE` |
| **Name** | Attentive Events API |
| **Category** | SMS Marketing |
| **Purpose** | SMS marketing automation, personalization |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.attentivemobile.com/v1/events` |
| **Rate Limits** | 1000 requests/minute |
| **Documentation** | https://docs.attentivemobile.com/openapi/reference/tag/Custom-Events |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx"
}
```

---

### 2.9 BRAZE - Braze Events API

| Attribute | Value |
|-----------|-------|
| **Code** | `BRAZE` |
| **Name** | Braze User Track API |
| **Category** | Customer Engagement |
| **Purpose** | Cross-channel customer engagement, messaging |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://rest.iad-01.braze.com` |
| **Rate Limits** | 250,000 requests/hour |
| **Documentation** | https://www.braze.com/docs/api/endpoints/user_data/post_user_track |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "app_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "instance_url": "rest.iad-01.braze.com"
}
```

---

### 2.10 IMPACT - Impact.com Conversions

| Attribute | Value |
|-----------|-------|
| **Code** | `IMPACT` |
| **Name** | Impact.com Conversions API |
| **Category** | Affiliate Marketing |
| **Purpose** | Affiliate tracking, partner marketing |
| **Connectivity** | Server-to-Server Postback |
| **Auth Type** | BASIC_AUTH |
| **Base URL** | `https://api.impact.com/Advertisers/{AccountSID}` |
| **Rate Limits** | 1000 requests/minute |
| **Documentation** | https://integrations.impact.com/impact-brand/docs |

**Credential Structure:**
```json
{
  "account_sid": "IRxxxxxxxxxxxxxxx",
  "auth_token": "xxxxxxxxxxxxxxx",
  "campaign_id": "12345"
}
```

---

### 2.11 CJ_AFFILIATE - CJ Affiliate

| Attribute | Value |
|-----------|-------|
| **Code** | `CJ_AFFILIATE` |
| **Name** | CJ Affiliate (Commission Junction) |
| **Category** | Affiliate Marketing |
| **Purpose** | Affiliate network, publisher partnerships |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://commissions.api.cj.com` |
| **Rate Limits** | 25 requests/second |
| **Documentation** | https://developers.cj.com/ |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx",
  "company_id": "1234567",
  "website_id": "7654321"
}
```

---

### 2.12 SHAREASALE - ShareASale

| Attribute | Value |
|-----------|-------|
| **Code** | `SHAREASALE` |
| **Name** | ShareASale (Awin) |
| **Category** | Affiliate Marketing |
| **Purpose** | Affiliate network, conversion tracking |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.shareasale.com/x.cfm` |
| **Rate Limits** | 200 requests/day |
| **Documentation** | https://www.shareasale.com/info/api/ |

**Credential Structure:**
```json
{
  "api_token": "xxxxxxxxxxxxxxx",
  "api_secret": "xxxxxxxxxxxxxxx",
  "merchant_id": "12345"
}
```

---

### 2.13 RAKUTEN - Rakuten Advertising

| Attribute | Value |
|-----------|-------|
| **Code** | `RAKUTEN` |
| **Name** | Rakuten Advertising |
| **Category** | Affiliate Marketing |
| **Purpose** | Global affiliate network, conversion tracking |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://api.rakutenmarketing.com` |
| **Rate Limits** | 1000 requests/hour |
| **Documentation** | https://developers.rakutenadvertising.com/ |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "account_id": "12345",
  "site_id": "67890"
}
```

---

### 2.14 TABOOLA - Taboola Conversions

| Attribute | Value |
|-----------|-------|
| **Code** | `TABOOLA` |
| **Name** | Taboola Conversions API |
| **Category** | Native Advertising |
| **Purpose** | Native content discovery, conversion tracking |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://backstage.taboola.com/backstage/api/1.0` |
| **Rate Limits** | 1000 requests/minute |
| **Documentation** | https://developers.taboola.com/backstage-api/reference |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "account_id": "your-account-name"
}
```

---

### 2.15 OUTBRAIN - Outbrain Conversions

| Attribute | Value |
|-----------|-------|
| **Code** | `OUTBRAIN` |
| **Name** | Outbrain Conversions API |
| **Category** | Native Advertising |
| **Purpose** | Native content recommendation, conversion tracking |
| **Connectivity** | Server-to-Server (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://api.outbrain.com/amplify/v0.1` |
| **Rate Limits** | 100 requests/minute |
| **Documentation** | https://www.outbrain.com/developers/ |

**Credential Structure:**
```json
{
  "access_token": "xxxxxxxxxxxxxxx",
  "marketer_id": "xxxxxxxx"
}
```

---

## Tier 3 - Standard Platforms

Common platforms used by 20%+ of e-commerce businesses.

### 3.1 QUORA - Quora Conversions

| Attribute | Value |
|-----------|-------|
| **Code** | `QUORA` |
| **Name** | Quora Conversions API |
| **Category** | Paid Social |
| **Purpose** | Q&A platform advertising |
| **Connectivity** | Pixel/S2S |
| **Auth Type** | API_KEY |
| **Base URL** | `https://ads-api.quora.com` |
| **Documentation** | https://quoraadsupport.zendesk.com/hc/en-us |

**Credential Structure:**
```json
{
  "pixel_id": "xxxxxxxxxxxxxxx",
  "api_key": "xxxxxxxxxxxxxxx"
}
```

---

### 3.2 WALMART_CONNECT - Walmart Connect

| Attribute | Value |
|-----------|-------|
| **Code** | `WALMART_CONNECT` |
| **Name** | Walmart Connect |
| **Category** | Retail Media |
| **Purpose** | Walmart marketplace advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://advertising.walmart.com/api` |
| **Documentation** | https://developer.walmart.com/doc/us/ads/ |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "advertiser_id": "12345"
}
```

---

### 3.3 EBAY_ADS - eBay Advertising

| Attribute | Value |
|-----------|-------|
| **Code** | `EBAY_ADS` |
| **Name** | eBay Promoted Listings |
| **Category** | Retail Media |
| **Purpose** | eBay marketplace advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://api.ebay.com/sell/marketing/v1` |
| **Documentation** | https://developer.ebay.com/api-docs/sell/marketing/overview.html |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxx"
}
```

---

### 3.4 INSTACART_ADS - Instacart Ads

| Attribute | Value |
|-----------|-------|
| **Code** | `INSTACART_ADS` |
| **Name** | Instacart Ads |
| **Category** | Retail Media |
| **Purpose** | Grocery delivery advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://ads.instacart.com/api/v1` |
| **Documentation** | https://developers.instacart.com/docs |

**Credential Structure:**
```json
{
  "access_token": "xxxxxxxxxxxxxxx",
  "advertiser_id": "12345"
}
```

---

### 3.5 TARGET_ROUNDEL - Target Roundel

| Attribute | Value |
|-----------|-------|
| **Code** | `TARGET_ROUNDEL` |
| **Name** | Target Roundel |
| **Category** | Retail Media |
| **Purpose** | Target marketplace advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://api.roundel.com` |
| **Documentation** | Contact Target for API access |

**Credential Structure:**
```json
{
  "access_token": "xxxxxxxxxxxxxxx",
  "advertiser_id": "12345"
}
```

---

### 3.6 KROGER - Kroger Precision Marketing

| Attribute | Value |
|-----------|-------|
| **Code** | `KROGER` |
| **Name** | Kroger Precision Marketing |
| **Category** | Retail Media |
| **Purpose** | Grocery retail media |
| **Connectivity** | API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://api.kroger.com/v1` |
| **Documentation** | https://developer.kroger.com/ |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "account_id": "12345"
}
```

---

### 3.7 THE_TRADE_DESK - The Trade Desk

| Attribute | Value |
|-----------|-------|
| **Code** | `THE_TRADE_DESK` |
| **Name** | The Trade Desk |
| **Category** | Programmatic/DSP |
| **Purpose** | Programmatic advertising, DSP |
| **Connectivity** | Real-time API (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://api.thetradedesk.com/v3` |
| **Rate Limits** | 100 requests/second |
| **Documentation** | https://partner.thetradedesk.com/v3/portal/api/doc |

**Credential Structure:**
```json
{
  "partner_id": "xxxxxxxx",
  "access_token": "xxxxxxxxxxxxxxx",
  "advertiser_id": "xxxxxxxx"
}
```

---

### 3.8 DV360 - Google Display & Video 360

| Attribute | Value |
|-----------|-------|
| **Code** | `DV360` |
| **Name** | Google Display & Video 360 |
| **Category** | Programmatic/DSP |
| **Purpose** | Programmatic display/video advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://displayvideo.googleapis.com/v2` |
| **Documentation** | https://developers.google.com/display-video/api/guides |

**Credential Structure:**
```json
{
  "client_id": "xxxxx.apps.googleusercontent.com",
  "client_secret": "xxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxx",
  "partner_id": "12345"
}
```

---

### 3.9 AMAZON_DSP - Amazon DSP

| Attribute | Value |
|-----------|-------|
| **Code** | `AMAZON_DSP` |
| **Name** | Amazon DSP |
| **Category** | Programmatic/DSP |
| **Purpose** | Programmatic display advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://advertising-api.amazon.com/dsp` |
| **Documentation** | https://advertising.amazon.com/API/docs/en-us/dsp |

**Credential Structure:**
```json
{
  "client_id": "amzn1.application-oa2-client.xxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxx",
  "profile_id": "1234567890"
}
```

---

### 3.10 ADROLL - AdRoll

| Attribute | Value |
|-----------|-------|
| **Code** | `ADROLL` |
| **Name** | AdRoll |
| **Category** | Retargeting |
| **Purpose** | Retargeting, display advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://services.adroll.com/api/v1` |
| **Documentation** | https://developers.adroll.com/ |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "access_token": "xxxxxxxxxxxxxxx",
  "advertisable_eid": "xxxxxxxx"
}
```

---

### 3.11 RTB_HOUSE - RTB House

| Attribute | Value |
|-----------|-------|
| **Code** | `RTB_HOUSE` |
| **Name** | RTB House |
| **Category** | Retargeting |
| **Purpose** | Deep learning retargeting |
| **Connectivity** | API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.rtbhouse.com` |
| **Documentation** | https://docs.rtbhouse.com/ |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx",
  "account_hash": "xxxxxxxx"
}
```

---

### 3.12 SEGMENT - Segment CDP

| Attribute | Value |
|-----------|-------|
| **Code** | `SEGMENT` |
| **Name** | Segment |
| **Category** | CDP |
| **Purpose** | Customer data platform, event routing |
| **Connectivity** | Tracking API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.segment.io/v1` |
| **Rate Limits** | 500 requests/second |
| **Documentation** | https://segment.com/docs/connections/sources/catalog/libraries/server/http-api/ |

**Credential Structure:**
```json
{
  "write_key": "xxxxxxxxxxxxxxx"
}
```

---

### 3.13 MPARTICLE - mParticle CDP

| Attribute | Value |
|-----------|-------|
| **Code** | `MPARTICLE` |
| **Name** | mParticle |
| **Category** | CDP |
| **Purpose** | Customer data platform, event routing |
| **Connectivity** | Events API (S2S) |
| **Auth Type** | BASIC_AUTH |
| **Base URL** | `https://s2s.mparticle.com/v2` |
| **Documentation** | https://docs.mparticle.com/developers/server/http/ |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx",
  "api_secret": "xxxxxxxxxxxxxxx"
}
```

---

### 3.14 APPSFLYER - AppsFlyer

| Attribute | Value |
|-----------|-------|
| **Code** | `APPSFLYER` |
| **Name** | AppsFlyer S2S |
| **Category** | Mobile Attribution |
| **Purpose** | Mobile app attribution, analytics |
| **Connectivity** | S2S Events API |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api2.appsflyer.com/inappevent` |
| **Documentation** | https://dev.appsflyer.com/hc/docs/s2s-events-api |

**Credential Structure:**
```json
{
  "dev_key": "xxxxxxxxxxxxxxx",
  "app_id": "com.example.app"
}
```

---

### 3.15 ADJUST - Adjust

| Attribute | Value |
|-----------|-------|
| **Code** | `ADJUST` |
| **Name** | Adjust S2S |
| **Category** | Mobile Attribution |
| **Purpose** | Mobile app attribution, analytics |
| **Connectivity** | S2S Events API |
| **Auth Type** | API_KEY |
| **Base URL** | `https://s2s.adjust.com/event` |
| **Documentation** | https://help.adjust.com/en/article/server-to-server-events |

**Credential Structure:**
```json
{
  "app_token": "xxxxxxxxxxxxxxx",
  "event_token": "xxxxxx"
}
```

---

### 3.16 BRANCH - Branch

| Attribute | Value |
|-----------|-------|
| **Code** | `BRANCH` |
| **Name** | Branch |
| **Category** | Mobile Attribution |
| **Purpose** | Deep linking, mobile attribution |
| **Connectivity** | S2S Events API |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api2.branch.io/v2/event/custom` |
| **Documentation** | https://help.branch.io/developers-hub/docs/server-to-server |

**Credential Structure:**
```json
{
  "branch_key": "key_live_xxxxxxx",
  "branch_secret": "secret_live_xxxxxxx"
}
```

---

### 3.17 KOCHAVA - Kochava

| Attribute | Value |
|-----------|-------|
| **Code** | `KOCHAVA` |
| **Name** | Kochava |
| **Category** | Mobile Attribution |
| **Purpose** | Mobile attribution, analytics |
| **Connectivity** | S2S Events API |
| **Auth Type** | API_KEY |
| **Base URL** | `https://control.kochava.com/track/event` |
| **Documentation** | https://support.kochava.com/server-to-server-integration/ |

**Credential Structure:**
```json
{
  "app_guid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "api_key": "xxxxxxxxxxxxxxx"
}
```

---

### 3.18 ITERABLE - Iterable

| Attribute | Value |
|-----------|-------|
| **Code** | `ITERABLE` |
| **Name** | Iterable |
| **Category** | Customer Engagement |
| **Purpose** | Cross-channel marketing automation |
| **Connectivity** | Events API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.iterable.com/api` |
| **Documentation** | https://api.iterable.com/api/docs |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx"
}
```

---

### 3.19 CUSTOMERIO - Customer.io

| Attribute | Value |
|-----------|-------|
| **Code** | `CUSTOMERIO` |
| **Name** | Customer.io |
| **Category** | Customer Engagement |
| **Purpose** | Messaging automation |
| **Connectivity** | Track API (S2S) |
| **Auth Type** | BASIC_AUTH |
| **Base URL** | `https://track.customer.io/api/v1` |
| **Documentation** | https://customer.io/docs/api/ |

**Credential Structure:**
```json
{
  "site_id": "xxxxxxxxxxxxxxx",
  "api_key": "xxxxxxxxxxxxxxx"
}
```

---

### 3.20 POSTSCRIPT - Postscript

| Attribute | Value |
|-----------|-------|
| **Code** | `POSTSCRIPT` |
| **Name** | Postscript |
| **Category** | SMS Marketing |
| **Purpose** | SMS marketing for Shopify |
| **Connectivity** | API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.postscript.io/v1` |
| **Documentation** | https://developers.postscript.io/ |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx",
  "shop_id": "12345"
}
```

---

### 3.21 OMNISEND - Omnisend

| Attribute | Value |
|-----------|-------|
| **Code** | `OMNISEND` |
| **Name** | Omnisend |
| **Category** | Email/SMS Marketing |
| **Purpose** | E-commerce marketing automation |
| **Connectivity** | API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.omnisend.com/v3` |
| **Documentation** | https://api-docs.omnisend.com/ |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx"
}
```

---

### 3.22 MIXPANEL - Mixpanel

| Attribute | Value |
|-----------|-------|
| **Code** | `MIXPANEL` |
| **Name** | Mixpanel |
| **Category** | Product Analytics |
| **Purpose** | Product analytics, event tracking |
| **Connectivity** | Track API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.mixpanel.com` |
| **Documentation** | https://developer.mixpanel.com/docs |

**Credential Structure:**
```json
{
  "project_token": "xxxxxxxxxxxxxxx",
  "api_secret": "xxxxxxxxxxxxxxx"
}
```

---

### 3.23 AMPLITUDE - Amplitude

| Attribute | Value |
|-----------|-------|
| **Code** | `AMPLITUDE` |
| **Name** | Amplitude |
| **Category** | Product Analytics |
| **Purpose** | Product analytics, behavioral data |
| **Connectivity** | HTTP V2 API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api2.amplitude.com/2/httpapi` |
| **Documentation** | https://developers.amplitude.com/docs/http-api-v2 |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx"
}
```

---

### 3.24 HEAP - Heap

| Attribute | Value |
|-----------|-------|
| **Code** | `HEAP` |
| **Name** | Heap |
| **Category** | Product Analytics |
| **Purpose** | Auto-capture analytics |
| **Connectivity** | Server-side API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://heapanalytics.com/api` |
| **Documentation** | https://developers.heap.io/reference/server-side-apis-overview |

**Credential Structure:**
```json
{
  "app_id": "xxxxxxxxxxxxxxx"
}
```

---

### 3.25 FULLSTORY - FullStory

| Attribute | Value |
|-----------|-------|
| **Code** | `FULLSTORY` |
| **Name** | FullStory |
| **Category** | Product Analytics |
| **Purpose** | Session replay, digital experience |
| **Connectivity** | Server API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.fullstory.com` |
| **Documentation** | https://developer.fullstory.com/ |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx",
  "org_id": "xxxxxxx"
}
```

---

### 3.26 SPOTIFY_ADS - Spotify Ads

| Attribute | Value |
|-----------|-------|
| **Code** | `SPOTIFY_ADS` |
| **Name** | Spotify Advertising |
| **Category** | Audio Advertising |
| **Purpose** | Audio/podcast advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | OAUTH2 |
| **Base URL** | `https://ads.spotify.com/api` |
| **Documentation** | https://ads.spotify.com/en-US/help/ |

**Credential Structure:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "account_id": "12345"
}
```

---

### 3.27 ROKU_ADS - Roku Ads

| Attribute | Value |
|-----------|-------|
| **Code** | `ROKU_ADS` |
| **Name** | Roku Ads (OneView) |
| **Category** | CTV/OTT |
| **Purpose** | Connected TV advertising |
| **Connectivity** | API (S2S) |
| **Auth Type** | ACCESS_TOKEN |
| **Base URL** | `https://ads.roku.com/api` |
| **Documentation** | https://developer.roku.com/docs/developer-program/advertising/ |

**Credential Structure:**
```json
{
  "access_token": "xxxxxxxxxxxxxxx",
  "advertiser_id": "12345"
}
```

---

### 3.28 YOTPO - Yotpo

| Attribute | Value |
|-----------|-------|
| **Code** | `YOTPO` |
| **Name** | Yotpo |
| **Category** | Reviews/UGC |
| **Purpose** | Reviews, loyalty, UGC |
| **Connectivity** | API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.yotpo.com` |
| **Documentation** | https://apidocs.yotpo.com/ |

**Credential Structure:**
```json
{
  "app_key": "xxxxxxxxxxxxxxx",
  "secret_key": "xxxxxxxxxxxxxxx"
}
```

---

### 3.29 TRIPLE_WHALE - Triple Whale

| Attribute | Value |
|-----------|-------|
| **Code** | `TRIPLE_WHALE` |
| **Name** | Triple Whale |
| **Category** | Attribution |
| **Purpose** | E-commerce attribution, analytics |
| **Connectivity** | API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.triplewhale.com` |
| **Documentation** | https://developers.triplewhale.com/ |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx",
  "shop_id": "myshop.myshopify.com"
}
```

---

### 3.30 NORTHBEAM - Northbeam

| Attribute | Value |
|-----------|-------|
| **Code** | `NORTHBEAM` |
| **Name** | Northbeam |
| **Category** | Attribution |
| **Purpose** | Marketing attribution, analytics |
| **Connectivity** | API (S2S) |
| **Auth Type** | API_KEY |
| **Base URL** | `https://api.northbeam.io` |
| **Documentation** | https://docs.northbeam.io/ |

**Credential Structure:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx"
}
```

---

## Tier 4 - Extended Platforms

Niche and emerging platforms for specific use cases.

### Retail Media Networks

| Code | Name | Category | Base URL |
|------|------|----------|----------|
| `HOME_DEPOT` | Home Depot Retail Media | Retail Media | Contact for access |
| `LOWES` | Lowe's One Roof Media | Retail Media | Contact for access |
| `BEST_BUY` | Best Buy Ads | Retail Media | Contact for access |
| `CVS_MEDIA` | CVS Media Exchange | Retail Media | Contact for access |
| `WALGREENS` | Walgreens Advertising | Retail Media | Contact for access |
| `ALBERTSONS` | Albertsons Media Collective | Retail Media | Contact for access |
| `ULTA` | Ulta Beauty Media | Retail Media | Contact for access |
| `SEPHORA` | Sephora Media | Retail Media | Contact for access |
| `CHEWY` | Chewy Ads | Retail Media | Contact for access |
| `WAYFAIR` | Wayfair Advertising | Retail Media | Contact for access |
| `COSTCO` | Costco Advertising | Retail Media | Contact for access |
| `SAMS_CLUB` | Sam's Club MAP | Retail Media | Contact for access |
| `DOLLAR_GENERAL` | DG Media Network | Retail Media | Contact for access |
| `GOPUFF` | Gopuff Ads | Retail Media | Contact for access |
| `DOORDASH` | DoorDash Ads | Retail Media | Contact for access |
| `UBER_EATS` | Uber Ads | Retail Media | Contact for access |
| `SHIPT` | Shipt Ads | Retail Media | Contact for access |

### Additional Programmatic Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `MEDIAMATH` | MediaMath | DSP | OAUTH2 |
| `XANDR` | Xandr (Microsoft) | DSP | OAUTH2 |
| `VIANT` | Viant Adelphic | DSP | ACCESS_TOKEN |
| `STACKADAPT` | StackAdapt | DSP | API_KEY |
| `BASIS` | Basis (Centro) | DSP | OAUTH2 |
| `SIMPLIFI` | Simpli.fi | DSP | API_KEY |
| `QUANTCAST` | Quantcast | DSP | API_KEY |
| `LOTAME` | Lotame | DMP | API_KEY |
| `LIVERAMP` | LiveRamp | Identity | API_KEY |
| `ADFORM` | Adform | DSP | API_KEY |
| `MOLOCO` | Moloco | DSP | API_KEY |
| `ROKT` | Rokt | Transaction Ads | API_KEY |
| `ZETA` | Zeta Global | DSP | API_KEY |
| `YAHOO_DSP` | Yahoo DSP | DSP | OAUTH2 |

### Additional Native Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `MGID` | MGID | Native | API_KEY |
| `REVCONTENT` | Revcontent | Native | API_KEY |
| `NATIVO` | Nativo | Native | ACCESS_TOKEN |
| `TRIPLELIFT` | TripleLift | Native | API_KEY |
| `SHARETHROUGH` | Sharethrough | Native | API_KEY |

### CTV/OTT Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `SAMSUNG_ADS` | Samsung Ads | CTV | ACCESS_TOKEN |
| `LG_ADS` | LG Ads | CTV | ACCESS_TOKEN |
| `VIZIO_ADS` | Vizio Ads (Inscape) | CTV | ACCESS_TOKEN |
| `HULU` | Hulu Ads (Disney) | CTV | OAUTH2 |
| `PEACOCK` | Peacock Ads | CTV | ACCESS_TOKEN |
| `PARAMOUNT` | Paramount+ Ads | CTV | ACCESS_TOKEN |
| `DISNEY_PLUS` | Disney+ Ads | CTV | OAUTH2 |
| `NETFLIX` | Netflix Ads (Microsoft) | CTV | OAUTH2 |
| `AMAZON_FIRE` | Amazon Fire TV | CTV | OAUTH2 |
| `TUBI` | Tubi Ads | CTV | API_KEY |
| `PLUTO` | Pluto TV | CTV | ACCESS_TOKEN |
| `FUBO` | FuboTV Ads | CTV | ACCESS_TOKEN |
| `MNTN` | MNTN Performance TV | CTV | API_KEY |
| `INNOVID` | Innovid | CTV/Video | API_KEY |
| `MAGNITE` | Magnite (SpotX) | Video SSP | API_KEY |
| `NEXXEN` | Nexxen (Tremor) | CTV/Video | API_KEY |

### Audio/Podcast Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `PANDORA` | Pandora (SiriusXM) | Audio | OAUTH2 |
| `IHEARTRADIO` | iHeartRadio | Audio | API_KEY |
| `AMAZON_MUSIC` | Amazon Music Ads | Audio | OAUTH2 |
| `PODCORN` | Podcorn | Podcast | API_KEY |
| `PODSCRIBE` | Podscribe | Podcast Attribution | API_KEY |
| `PODSIGHTS` | Podsights (Spotify) | Podcast | API_KEY |
| `CHARTABLE` | Chartable (Spotify) | Podcast | API_KEY |
| `ACAST` | Acast | Podcast | API_KEY |
| `MEGAPHONE` | Megaphone (Spotify) | Podcast | API_KEY |
| `ADVERTISECAST` | AdvertiseCast | Podcast | API_KEY |
| `REDCIRCLE` | RedCircle | Podcast | API_KEY |
| `AUDIOGO` | AudioGO | Audio | API_KEY |

### Additional Affiliate Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `AWIN` | Awin | Affiliate | API_KEY |
| `PARTNERIZE` | Partnerize | Affiliate | ACCESS_TOKEN |
| `PARTNERSTACK` | PartnerStack | B2B Affiliate | API_KEY |
| `REFERSION` | Refersion | Affiliate | API_KEY |
| `EVERFLOW` | Everflow | Affiliate | API_KEY |
| `TUNE` | Tune (HasOffers) | Affiliate | API_KEY |
| `TAPFILIATE` | Tapfiliate | Affiliate | API_KEY |
| `LEADDYNO` | LeadDyno | Affiliate | API_KEY |
| `AFFILIATLY` | Affiliatly | Affiliate | API_KEY |
| `UPPROMOTE` | UpPromote | Affiliate | API_KEY |
| `LEVANTA` | Levanta | Amazon Affiliate | API_KEY |

### Influencer Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `CREATORIQ` | CreatorIQ | Influencer | OAUTH2 |
| `GRIN` | Grin | Influencer | API_KEY |
| `ASPIRE` | Aspire (AspireIQ) | Influencer | API_KEY |
| `UPFLUENCE` | Upfluence | Influencer | API_KEY |
| `TRAACKR` | Traackr | Influencer | API_KEY |
| `MAVRCK` | Mavrck | Influencer | API_KEY |
| `KLEAR` | Klear | Influencer | API_KEY |
| `HEEPSY` | Heepsy | Influencer | API_KEY |
| `MODASH` | Modash | Influencer | API_KEY |
| `SHOPIFY_COLLABS` | Shopify Collabs | Influencer | API_KEY |
| `LTK` | LTK (LikeToKnowIt) | Influencer | API_KEY |
| `SHOPMY` | ShopMy | Influencer | API_KEY |

### Additional CDP Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `TEALIUM` | Tealium | CDP/Tag Mgmt | API_KEY |
| `RUDDERSTACK` | Rudderstack | CDP | API_KEY |
| `TREASURE_DATA` | Treasure Data | CDP | API_KEY |
| `BLOOMREACH` | Bloomreach | Commerce CDP | API_KEY |
| `AMPERITY` | Amperity | CDP | API_KEY |
| `ACTIONIQ` | ActionIQ | CDP | API_KEY |
| `HIGHTOUCH` | Hightouch | Reverse ETL | API_KEY |
| `CENSUS` | Census | Reverse ETL | API_KEY |
| `LYTICS` | Lytics | CDP | API_KEY |
| `BLUECONIC` | BlueConic | CDP | API_KEY |
| `SIMON_DATA` | Simon Data | CDP | API_KEY |

### Email/SMS Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `MAILCHIMP` | Mailchimp | Email | API_KEY |
| `SENDGRID` | SendGrid | Email | API_KEY |
| `SAILTHRU` | Sailthru | Email | API_KEY |
| `CORDIAL` | Cordial | Email | API_KEY |
| `LISTRAK` | Listrak | Email | API_KEY |
| `DRIP` | Drip | Email | API_KEY |
| `ACTIVECAMPAIGN` | ActiveCampaign | Email | API_KEY |
| `SENDLANE` | Sendlane | Email | API_KEY |
| `YOTPO_SMS` | Yotpo SMS | SMS | API_KEY |

### Additional Analytics Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `ADOBE_ANALYTICS` | Adobe Analytics | Analytics | OAUTH2 |
| `PENDO` | Pendo | Product Analytics | API_KEY |
| `HOTJAR` | Hotjar | Heatmaps | API_KEY |
| `CRAZYEGG` | Crazy Egg | Heatmaps | API_KEY |
| `LUCKYORANGE` | Lucky Orange | Session Recording | API_KEY |
| `MOUSEFLOW` | Mouseflow | Session Recording | API_KEY |
| `CONTENTSQUARE` | Contentsquare | Experience Analytics | API_KEY |
| `QUANTUM_METRIC` | Quantum Metric | Experience Analytics | API_KEY |
| `GLASSBOX` | Glassbox | Experience Analytics | API_KEY |
| `LOGROCKET` | LogRocket | Session Replay | API_KEY |
| `INDICATIVE` | Indicative | Customer Analytics | API_KEY |
| `WOOPRA` | Woopra | Customer Journey | API_KEY |
| `KISSMETRICS` | Kissmetrics | Behavioral Analytics | API_KEY |
| `SINGULAR` | Singular | Marketing Analytics | API_KEY |
| `AIRBRIDGE` | Airbridge | Mobile Analytics | API_KEY |
| `ROCKERBOX` | Rockerbox | Attribution | API_KEY |
| `MEASURED` | Measured | Incrementality | API_KEY |
| `FOSPHA` | Fospha | Attribution | API_KEY |

### Personalization/Testing Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `OPTIMIZELY` | Optimizely | A/B Testing | API_KEY |
| `VWO` | VWO | Testing | API_KEY |
| `DYNAMIC_YIELD` | Dynamic Yield | Personalization | API_KEY |
| `MONETATE` | Monetate | Personalization | API_KEY |
| `AB_TASTY` | AB Tasty | Testing | API_KEY |
| `KAMELEOON` | Kameleoon | Testing | API_KEY |
| `CONVERT` | Convert | A/B Testing | API_KEY |
| `NOSTO` | Nosto | E-commerce Personalization | API_KEY |
| `CLERK` | Clerk.io | E-commerce Search | API_KEY |
| `ALGOLIA` | Algolia | Search | API_KEY |
| `CONSTRUCTOR` | Constructor.io | E-commerce Search | API_KEY |
| `SEARCHSPRING` | Searchspring | E-commerce Search | API_KEY |
| `KLEVU` | Klevu | AI Search | API_KEY |

### Reviews/UGC Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `BAZAARVOICE` | Bazaarvoice | Reviews/UGC | API_KEY |
| `POWERREVIEWS` | PowerReviews | Reviews | API_KEY |
| `TRUSTPILOT` | Trustpilot | Reviews | API_KEY |
| `STAMPED` | Stamped.io | Reviews | API_KEY |
| `JUDGEME` | Judge.me | Reviews | API_KEY |
| `LOOX` | Loox | Photo Reviews | API_KEY |
| `OKENDO` | Okendo | Reviews | API_KEY |
| `REVIEWSIO` | Reviews.io | Reviews | API_KEY |
| `FERA` | Fera.ai | Reviews | API_KEY |

### Loyalty Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `YOTPO_LOYALTY` | Yotpo Loyalty | Loyalty | API_KEY |
| `SMILE` | Smile.io | Loyalty | API_KEY |
| `LOYALTYLION` | LoyaltyLion | Loyalty | API_KEY |
| `ANNEX_CLOUD` | Annex Cloud | Loyalty | API_KEY |
| `ANTAVO` | Antavo | Loyalty | API_KEY |
| `FRIENDBUY` | Friendbuy | Referrals | API_KEY |
| `REFERRALCANDY` | ReferralCandy | Referrals | API_KEY |
| `EXTOLE` | Extole | Referrals | API_KEY |
| `MENTION_ME` | Mention Me | Referrals | API_KEY |
| `TALKABLE` | Talkable | Referrals | API_KEY |

### Messaging Platforms

| Code | Name | Category | Auth Type |
|------|------|----------|-----------|
| `WHATSAPP` | WhatsApp Business | Messaging | ACCESS_TOKEN |
| `TELEGRAM` | Telegram Bot | Messaging | API_KEY |

### International Platforms

| Code | Name | Category | Region | Auth Type |
|------|------|----------|--------|-----------|
| `YANDEX` | Yandex Metrica | Analytics | Russia | API_KEY |
| `BAIDU` | Baidu Analytics | Analytics | China | API_KEY |
| `NAVER` | Naver Ads | Search | Korea | API_KEY |
| `KAKAO` | Kakao Ads | Social | Korea | API_KEY |
| `LINE` | LINE Ads | Messaging | Japan | API_KEY |
| `WECHAT` | WeChat Ads | Social | China | API_KEY |

---

## Platform Categories Summary

| Category | Count | Examples |
|----------|-------|----------|
| Paid Social | 15+ | Meta, TikTok, Snapchat, Pinterest, Twitter, LinkedIn, Reddit |
| Paid Search | 5+ | Google Ads, Microsoft Ads, Yahoo, Yandex, Baidu |
| Analytics | 20+ | GA4, Adobe Analytics, Mixpanel, Amplitude, Heap |
| Retail Media | 20+ | Amazon, Walmart, Target, Kroger, Instacart |
| Programmatic/DSP | 15+ | The Trade Desk, DV360, Amazon DSP, Criteo |
| Native Advertising | 7+ | Taboola, Outbrain, MGID, TripleLift |
| CTV/OTT | 15+ | Roku, Samsung, LG, Vizio, Hulu, Peacock |
| Audio/Podcast | 12+ | Spotify, Pandora, iHeart, Podcorn |
| Affiliate | 15+ | Impact, CJ, ShareASale, Rakuten, Awin |
| Influencer | 12+ | CreatorIQ, Grin, Aspire, LTK |
| CDP | 12+ | Segment, mParticle, Tealium, Bloomreach |
| Mobile Attribution | 6+ | AppsFlyer, Adjust, Branch, Kochava |
| Email/SMS | 15+ | Klaviyo, Attentive, Braze, Iterable |
| Reviews/UGC | 10+ | Yotpo, Bazaarvoice, Trustpilot |
| Loyalty | 10+ | Smile.io, LoyaltyLion, Friendbuy |
| Attribution | 5+ | Triple Whale, Northbeam, Rockerbox |
| Personalization | 15+ | Optimizely, Dynamic Yield, Nosto |

**Total Platforms: 200+**

---

## Authentication Types

| Type | Description | Usage |
|------|-------------|-------|
| `API_KEY` | Simple API key in header or query param | Most common, simple integrations |
| `ACCESS_TOKEN` | Bearer token in Authorization header | Social platforms, modern APIs |
| `OAUTH2` | OAuth 2.0 flow with refresh tokens | Google, Microsoft, enterprise APIs |
| `BASIC_AUTH` | Username:password base64 encoded | Legacy APIs, some affiliates |

---

## Credential Structures

All credentials are stored encrypted in `platform_credentials.credentials_encrypted` as JSON.

### Standard Structure Template

```json
{
  "required_field_1": "value",
  "required_field_2": "value",
  "optional_field": "value"
}
```

### Common Fields by Auth Type

**API_KEY:**
```json
{
  "api_key": "xxxxxxxxxxxxxxx"
}
```

**ACCESS_TOKEN:**
```json
{
  "access_token": "xxxxxxxxxxxxxxx",
  "pixel_id": "xxxxxxxxxxxxxxx"
}
```

**OAUTH2:**
```json
{
  "client_id": "xxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxx",
  "account_id": "12345"
}
```

**BASIC_AUTH:**
```json
{
  "username": "xxxxxxxxxxxxxxx",
  "password": "xxxxxxxxxxxxxxx"
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-18 | Claude | Initial comprehensive platform list |

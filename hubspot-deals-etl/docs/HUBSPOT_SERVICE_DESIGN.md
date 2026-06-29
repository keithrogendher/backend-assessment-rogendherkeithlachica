# HubSpot Service — Technical Design & Deployment Guide
**Version:** 1.0 **Date:** 2026-06-07 **Applies To:** Black Diamond Platform — HubSpot Integration Service **Author:** Glynac Engineering

---

## Table of Contents

1. Overview
2. Architecture
3. HubSpot API Deep Dive
4. Service Design
5. API Endpoints
6. Environment Variables & Vault Secrets
7. Nomad HCL — Development
8. Nomad HCL — Staging
9. Nomad HCL — Production
10. Data Flow
11. Kafka Topic Design
12. Integration with Existing Stack
13. Deployment Checklist
14. Troubleshooting

---

## 1. Overview

### What This Service Does
The Black Diamond HubSpot Service extracts data from HubSpot CRM using the HubSpot REST API (with cursor-based pagination) and feeds it into the Glynac data pipeline. It acts as the dedicated extraction engine for HubSpot, following the same architectural pattern as other BD extraction services.

### Why HubSpot API (vs. Batch/Export)
HubSpot does not offer a true bulk export API for large-scale reads. Instead, it provides:

- **CRM Objects API** — paginated REST endpoints for Contacts, Companies, Deals, Tickets, etc.
- **Cursor-based pagination** — using `after` cursor tokens for reliable large-scale reads
- **Search API** — for filtered/incremental extraction using `lastmodifieddate` filters
- **Associations API** — for fetching relationships between objects (e.g., Contact → Company)
For large orgs (100k+ records), the extraction pattern is:

1. Use the Search API with `lastmodifieddate >= <timestamp>` filter for incremental runs
2. Page through results using the `paging.next.after` cursor
3. Fetch associations separately per object batch
This page-and-cursor pattern fits naturally into the same BD pipeline infrastructure used by other extraction services.

### Relationship to Existing Services

```
[black-diamond-core-service]         <- Orchestrator (creates/tracks/monitors scan jobs)
         |
         | HTTP + HMAC (internal)
         v
[black-diamond-hubspot-service]      <- NEW: This service (HubSpot extractor)
         |
         | OAuth 2.0 (Private App Token)
         v
[HubSpot CRM API v3]                 <- External data source
         |
         | (results)
         v
[MinIO / Kafka / ClickHouse]         <- Storage and streaming pipeline
```

---

## 2. Architecture

### Component Diagram

```
+---------------------------+        +--------------------------------+
|  BD Core Service          |        |  BD HubSpot Service            |
|  (Orchestrator)           |        |  (Extraction Engine)           |
|                           |        |                                |
|  POST /scans  ----------->| HMAC   |  POST /api/scan/start          |
|                           +------->|                                |
|  GET  /scans/status <-----+        |  GET  /api/scan/{id}/status    |
|                           |        |  GET  /api/scan/list           |
|  PUT  /scans/{id}/cancel ->        |  POST /api/scan/{id}/cancel    |
|                           |        |  POST /api/maintenance/cleanup |
+---------------------------+        |  GET  /api/health              |
                                     |  GET  /api/key/verify          |
                                     +----------------+---------------+
                                                      |
                                        Private App Token (Bearer)
                                                      |
                                     +----------------v---------------+
                                     |  HubSpot CRM API v3            |
                                     |                                |
                                     |  POST /crm/v3/objects/search   |
                                     |  GET  /crm/v3/objects/{type}   |
                                     |  GET  /crm/v3/associations/    |
                                     |        {from}/{to}/batch/read  |
                                     +--------------------------------+
                                                      |
                                              (JSON result pages)
                                                      |
                          +-----------+--------------++--------------+
                          |           |                              |
                    +-----v---+  +----v----+                  +-----v------+
                    | MinIO   |  | Kafka   |                  | ClickHouse |
                    | (raw    |  | (stream |                  | (analytics |
                    |  files) |  |  ingest)|                  |  store)    |
                    +---------+  +---------+                  +------------+
```

### Technology Stack
LayerTechnologyReasonService frameworkFlask-RESTXConsistent with other BD extraction servicesHubSpot clienthubspot-api-client + custom pagination wrapperOfficial Python SDK; custom cursor handler for Search APIAuth to HubSpotPrivate App Token (Bearer)Recommended for server-to-server; no user session requiredData serializationJSON → Parquet (via pandas/pyarrow)HubSpot API returns JSON; normalize to Parquet for pipelineObject storageMinIO (S3-compatible)Same pattern as other BD extraction servicesStreamingKafkaSame topics pattern as existing servicesSecretsHashiCorp Vault via Nomad templateConsistent with rest of platformAuth (internal)HMAC (dual-key: core-key + engineer-key)Consistent with CLAUDE.md security standards
---

## 3. HubSpot API Deep Dive

### 3.1 Authentication — Private App Token
HubSpot Private Apps are the recommended method for server-to-server integrations. Unlike OAuth 2.0 flows that require user interaction, a Private App Token is a long-lived Bearer token scoped to specific CRM permissions.

**Step 1 — Create a Private App in HubSpot:**

- Go to HubSpot Settings → Integrations → Private Apps
- Create app with required scopes (see Section 3.4)
- Copy the generated access token
**Step 2 — Use token in all API requests:**

```
Authorization: Bearer <private_app_token>
```
**Token lifetime:** Private App tokens do not expire unless manually rotated or the app is deleted. The service should handle `401 Unauthorized` responses by logging an alert (the token needs manual rotation in HubSpot and Vault update).

**Vault secret path for credentials:**

```
secrets/data/blackdiamond/blackdiamond-hubspot-service-prod
  HUBSPOT_ACCESS_TOKEN    = <Private App Token>
  HUBSPOT_PORTAL_ID       = <HubSpot Account/Portal ID>
```

### 3.2 HubSpot CRM API — Pagination Pattern
HubSpot uses **cursor-based pagination** via the `paging.next.after` field. All list/search endpoints return up to 100 records per page.

#### Full Object List (no filter)

```
GET /crm/v3/objects/contacts?limit=100&properties=email,firstname,lastname,...
Authorization: Bearer <token>
```
Response:

```
{
  "results": [ { "id": "...", "properties": {...}, "createdAt": "...", "updatedAt": "..." } ],
  "paging": {
    "next": {
      "after": "NTI1Cg%3D%3D",
      "link": "https://api.hubapi.com/crm/v3/objects/contacts?after=NTI1Cg%3D%3D&..."
    }
  }
}
```
When `paging.next` is absent, all pages have been consumed.

#### Filtered / Incremental Extraction (Search API)
For incremental runs, use the Search API to filter by `lastmodifieddate`:

```
POST /crm/v3/objects/contacts/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "filterGroups": [{
    "filters": [{
      "propertyName": "lastmodifieddate",
      "operator": "GTE",
      "value": "1704067200000"
    }]
  }],
  "sorts": [{ "propertyName": "lastmodifieddate", "direction": "ASCENDING" }],
  "properties": ["email", "firstname", "lastname", "phone", "company", "hs_object_id"],
  "limit": 100,
  "after": 0
}
```
Response structure is identical to the GET endpoint. Use `paging.next.after` to paginate.

**Important:** HubSpot Search API uses **millisecond Unix timestamps**, not ISO8601 strings.

#### Associations (e.g., Contact → Company)

```
POST /crm/v3/associations/contacts/companies/batch/read
Authorization: Bearer <token>
Content-Type: application/json

{
  "inputs": [
    { "id": "101" },
    { "id": "102" }
  ]
}
```
Response:

```
{
  "status": "COMPLETE",
  "results": [
    {
      "from": { "id": "101" },
      "to": [ { "id": "55", "type": "contact_to_company" } ]
    }
  ]
}
```
Fetch associations in batches of 100 (HubSpot batch read limit).

### 3.3 Rate Limits and Quotas
LimitValueMitigationAPI requests per 10 seconds100 (default) / 150 (Enterprise)Exponential backoff on 429Search API requests per minute4 requests/second sustainedRate-limit wrapper with token bucketMax records per search page100Always paginateAssociation batch read limit100 inputs per requestChunk contact IDs into batches of 100Private App token lifetimeDoes not expireRotate manually; handle 401 alertsDaily API call limit500,000 (varies by tier)Monitor via `/account-info/v3/api-usage/daily`
### 3.4 Required HubSpot Scopes
When creating the Private App, request these scopes:

ScopePurpose`crm.objects.contacts.read`Read Contacts`crm.objects.companies.read`Read Companies`crm.objects.deals.read`Read Deals`crm.objects.tickets.read`Read Tickets`crm.objects.leads.read`Read Leads`crm.objects.owners.read`Read Owners (user mapping)`crm.associations.read`Read associations between objects`sales-email-read`Read email engagement data
### 3.5 Supported HubSpot Objects for Extraction
ObjectAPI endpointEstimated volumeNotesContact`/crm/v3/objects/contacts`LargeCore CRM entity; includes email, phoneCompany`/crm/v3/objects/companies`MediumFirm/org dataDeal`/crm/v3/objects/deals`LargePipeline/revenue dataTicket`/crm/v3/objects/tickets`MediumSupport/service dataLead`/crm/v3/objects/leads`MediumPre-contact lead dataOwner`/crm/v3/owners/v2/owners`SmallFor user/rep mappingEmail Engagement`/engagements/v1/engagements/paged`LargeEmail send/open/click historyContact-Company Assoc.`/crm/v3/associations/contacts/companies/batch/read`MediumRelationship mapping
---

## 4. Service Design

### 4.1 Directory Structure

```
black-diamond-hubspot-service/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Flask app factory, startup validation
│   ├── config.py                   # Settings class with Pydantic validation
│   ├── routes.py                   # API route definitions
│   ├── auth/
│   │   ├── __init__.py
│   │   └── hubspot_auth.py         # Private App token manager
│   ├── clients/
│   │   ├── __init__.py
│   │   └── hubspot_client.py       # HubSpot API wrapper with pagination + rate limiting
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extraction_service.py   # Orchestrates object extraction lifecycle
│   │   ├── pagination_service.py   # Cursor-based pagination handler
│   │   ├── association_service.py  # Fetches and maps object associations
│   │   ├── normalization_service.py # JSON -> Parquet conversion
│   │   ├── deduplication_service.py # Remove duplicate records by hs_object_id
│   │   └── maintenance_service.py  # Cleanup old scans
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── minio_client.py         # MinIO upload helper
│   │   └── kafka_producer.py       # Kafka message publisher
│   └── models/
│       ├── __init__.py
│       ├── scan.py                 # Scan state model
│       └── extraction.py           # HubSpot extraction job model
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── Dockerfile
│  ... (file content continues)
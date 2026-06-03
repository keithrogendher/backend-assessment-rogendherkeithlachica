# 📋 HubSpot Deal Extraction Service - Integration with HubSpot CRM API v3

This document explains the HubSpot CRM REST API endpoints required by the HubSpot Deal Extraction Service to extract deal data from HubSpot instances.

---

## 📋 Overview

The HubSpot Deal Extraction Service integrates with HubSpot CRM API v3 endpoints to extract deal object information. Below are the required and optional endpoints:

### ✅ **Required Endpoint (Essential)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals`    | Search and list all deals           | v3 | crm.objects.deals.read     | **Required** |

### 🔧 **Optional Endpoints (Advanced Features)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/[api_path]/[endpoint_1]`         | Get detailed [object] information   | [API_VERSION] | [Permission_Name]      | Optional     |
| `/[api_path]/[endpoint_2]`         | Get [object] [related_data]         | [API_VERSION] | [Permission_Name]      | Optional     |
| `/[api_path]/[endpoint_3]`         | Get [object] [configuration]        | [API_VERSION] | [Permission_Name]      | Optional     |
| `/[api_path]/[endpoint_4]`         | Get [object] [additional_data]      | [API_VERSION] | [Permission_Name]      | Optional     |

### 🎯 **Recommendation**
**Start with only the required endpoint.** The `/crm/v3/objects/deals` endpoint provides all essential deal data needed for basic deal  analytics and extraction.

---

## 🔐 Authentication Requirements

### **[Authentication Method] Authentication**
```http
Authorization: Bearer pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Content-Type: application/json
```

### **Required Permissions**
- **crm.objects.deals.read**: Read all deal objects, properties, and metadata (required)
- **crm.schemas.deals.read**: Read deal property schema and field definitions (required)

---

## 🌐 HubSpot CRM API Endpoints 

### 🎯 **PRIMARY ENDPOINT (Required for Basic Deal Extraction))**

### 1. ** List Deals** - `/crm/v3/objects/deals` ✅ **REQUIRED**

**Purpose**: Get paginated list of all deals - **THIS IS ALL YOU NEED FOR BASIC DEAL EXTRACTION**

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals`

**Query Parameters**:
```
?limit=100&after=<cursor>&properties=dealname,amount,dealstage&archived=false
```

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=dealname,amount,dealstage,pipeline,closedate,createdate,hubspot_owner_id,hs_deal_stage_probability
Authorization: Bearer pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Content-Type: application/json
```

**Response Structure** (Contains ALL essential [object] data):
```json
{
  "results": [
    {
      "id": "123456789",
      "properties": {
        "dealname": "Acme Corp - Enterprise License",
        "amount": "50000",
        "dealstage": "closedwon",
        "pipeline": "default",
        "closedate": "2024-03-31T00:00:00.000Z",
        "createdate": "2024-01-10T09:15:22.123Z",
        "hs_lastmodifieddate": "2024-03-31T14:22:00.000Z",
        "hubspot_owner_id": "98765",
        "hs_deal_stage_probability": "1.0"
      },
      "createdAt": "2024-01-10T09:15:22.123Z",
      "updatedAt": "2024-03-31T14:22:00.000Z",
      "archived": false
    },
    {
      "id": "987654321",
      "properties": {
        "dealname": "Beta Inc - Starter Plan",
        "amount": "12500",
        "dealstage": "contractsent",
        "pipeline": "default",
        "closedate": "2024-06-30T00:00:00.000Z",
        "createdate": "2024-02-05T11:00:00.000Z",
        "hs_lastmodifieddate": "2024-02-20T09:00:00.000Z",
        "hubspot_owner_id": "98765",
        "hs_deal_stage_probability": "0.9"
      },
      "createdAt": "2024-02-05T11:00:00.000Z",
      "updatedAt": "2024-02-20T09:00:00.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "NTI1Cg%3D%3D",
      "link": "https://api.hubapi.com/crm/v3/objects/deals?after=NTI1Cg%3D%3D"
    }
  }
}
```

**✅ This endpoint provides ALL the default deal fields:**
- id, dealname, amount, dealstage, pipeline
- closedate, createdate, hs_lastmodifieddate
- hubspot_owner_id for owner reference
- hs_deal_stage_probability and win/loss metadata
- archived status and full createdAt / updatedAt timestamps

## Core Deal Fields
  Property  |  Type | Description
- hs_object_id | string | HubSpot internal deal ID
- dealname | string | Name of the deal
- amount | number| Deal value
- dealstage | enumeration | Current pipeline stage of the deal
- pipeline | enumeration | Pipeline the deal belongs to
- closedate | datetime | Expected or actual close date
- createdate | datetime | Date the deal was created
- hs_lastmodifieddate | datetime | Date the deal was last modified
- dealtype | enumeration | Type of deal (e.g., newbusiness, existingbusiness)description | string | Deal description

## Deal Stage & Forecast
  Property | Type | Description
- hs_deal_stage_probability| number | Win probability (0.0–1.0) based on stage
- hs_forecast_amount | number | Forecasted revenue amount
- hs_forecast_probability |numberManual forecast probability override
- hs_manual_forecast_category |enumeration |Forecast category: OMIT, PIPELINE, BEST_CASE, COMMIT, CLOSED
- hs_next_step | string | Configured next step for the deal
- hs_is_closed | boolean | Whether the deal is in a closed stage
- hs_is_closed_won | boolean | Whether the deal is closed-won
- closed_lost_reason | string | Reason the deal was lost
- hs_priority | enumeration | Deal priority: low, medium, high

## Ownership
  Property | Type | Description
- hubspot_owner_id | enumeration | ID of the deal owner (HubSpot user)
- hubspot_team_id | enumeration | Primary team ID for the deal
- hubspot_owner_assigneddate | datetime | Date the current owner was assigned

## Financial & Currency
- Property |Type | Description |
- amount_in_home_currency | number | Deal amount in portal home currency
- deal_currency_code | enumeration | ISO currency code (e.g., USD, EUR)
- hs_acv | number | Annual contract value
- hs_arr | number | Annual recurring revenue
- hs_mrr | number | Monthly recurring revenue
- hs_tcv | number | Total contract value

## Activity & Engagement
  Property | Type | Description |
- notes_last_contacted | datetime | Date of last contact
- activitynotes_last_updated | datetime | Date notes were last 
- updatednotes_next_activity_date |datetime | Date of next scheduled
- activitynum_contacted_notes | number | Number of times 
- contactednum_notes | number | Total number of notes
- hs_num_associated_contacts | number |Number of associated

## Source & Attribution
  Property | Type | Description
- hs_analytics_source | enumeration | Original traffic source
- hs_analytics_source_data_1 | string | Source detail 1
- hs_analytics_source_data_2 | string | Source detail 2
- hs_campaign | string | Associated marketing campaign

## Metadata
  Property | Type | Description
- hs_created_by_user_id | number | HubSpot user ID who created the deal
- hs_updated_by_user_id | number | HubSpot user ID who last updated the deal

**Rate Limit**: 100 requests per 10 seconds per Private App token

---

## 🔧 **OPTIONAL ENDPOINTS (Advanced Features Only)**

> **⚠️ Note**: These endpoints are NOT required for basic [object] extraction. Only implement if you need advanced [object] analytics like [feature 1], [feature 2], or [feature 3].

### 2. **Get [Object] Details** - `/[api_path]/[endpoint_1]/{objectId}` 🔧 **OPTIONAL**

**Purpose**: Get detailed information for a specific [object]

**When to use**: Only if you need additional [object] metadata not available in search

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_1]/{objectId}`

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_1]/[sample_id]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[field_id]": "[sample_id]",
  "[field_url]": "https://[your_instance].[platform_domain]/[api_path]/[endpoint_1]/[sample_id]",
  "[field_name]": "[Sample Object Name]",
  "[field_type]": "[object_type]",
  "[additional_field_1]": {
    "[sub_field_1]": [
      {
        "[property_1]": "[value_1]",
        "[property_2]": "[value_2]",
        "[property_3]": true
      }
    ],
    "[sub_field_2]": [
      {
        "[property_4]": "[value_4]",
        "[property_5]": "[value_5]"
      }
    ]
  },
  "[nested_object]": {
    "[nested_field_1]": "[value_1]",
    "[nested_field_2]": "[value_2]",
    "[nested_field_3]": "[value_3]",
    "[nested_field_4]": "[value_4]",
    "[nested_field_5]": "[value_5]"
  },
  "[boolean_field_1]": true,
  "[boolean_field_2]": false,
  "[boolean_field_3]": false
}
```

---

### 3. **Get [Object] [Related Data]** - `/[api_path]/[endpoint_2]/{objectId}/[related_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [related data] associated with a [object]

**When to use**: Only if you need [related data] analysis and [specific metrics]

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_2]/{objectId}/[related_endpoint]`

**Query Parameters**:
```
?[param1]=[value]&[param2]=[value]&[filter_param]=[filter_value]
```

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_2]/[sample_id]/[related_endpoint]?[param2]=[value]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[pagination_start]": 0,
  "[pagination_size]": 50,
  "[pagination_total]": 25,
  "[pagination_last]": false,
  "[data_array]": [
    {
      "[related_id]": 1,
      "[related_url]": "https://[your_instance].[platform_domain]/[api_path]/[related_endpoint]/1",
      "[related_status]": "[status_1]",
      "[related_name]": "[Related Item 1]",
      "[date_start]": "[date_format]",
      "[date_end]": "[date_format]",
      "[date_complete]": "[date_format]",
      "[date_created]": "[date_format]",
      "[origin_field]": "[sample_id]",
      "[description_field]": "[Description text]"
    },
    {
      "[related_id]": 2,
      "[related_url]": "https://[your_instance].[platform_domain]/[api_path]/[related_endpoint]/2",
      "[related_status]": "[status_2]", 
      "[related_name]": "[Related Item 2]",
      "[date_start]": "[date_format]",
      "[date_end]": "[date_format]",
      "[date_created]": "[date_format]",
      "[origin_field]": "[sample_id]",
      "[description_field]": "[Description text]"
    }
  ]
}
```

---

### 4. **Get [Object] Configuration** - `/[api_path]/[endpoint_3]/{objectId}/[config_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [object] configuration details ([config_type_1], [config_type_2], [config_type_3])

**When to use**: Only if you need [workflow type] and [object] setup analysis

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_3]/{objectId}/[config_endpoint]`

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_3]/[sample_id]/[config_endpoint]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[field_id]": "[sample_id]",
  "[field_name]": "[Sample Object Name]",
  "[field_type]": "[object_type]",
  "[field_url]": "https://[your_instance].[platform_domain]/[api_path]/[endpoint_3]/[sample_id]/[config_endpoint]",
  "[location_field]": {
    "[location_type]": "[location_value]",
    "[location_identifier]": "[identifier]"
  },
  "[filter_field]": {
    "[filter_id]": "[filter_value]",
    "[filter_url]": "https://[your_instance].[platform_domain]/[api_path]/[filter_endpoint]/[filter_value]"
  },
  "[config_object]": {
    "[config_array]": [
      {
        "[config_name]": "[Config Item 1]",
        "[config_values]": [
          {
            "[config_id]": "[id_1]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_1]"
          }
        ]
      },
      {
        "[config_name]": "[Config Item 2]",
        "[config_values]": [
          {
            "[config_id]": "[id_2]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_2]"
          }
        ]
      },
      {
        "[config_name]": "[Config Item 3]",
        "[config_values]": [
          {
            "[config_id]": "[id_3]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_3]"
          }
        ]
      }
    ],
    "[constraint_type]": "[constraint_value]"
  },
  "[estimation_field]": {
    "[estimation_type]": "[estimation_value]",
    "[estimation_details]": {
      "[detail_id]": "[detail_value]",
      "[detail_name]": "[Detail Display Name]"
    }
  }
}
```

---

### 5. **Get [Object] [Additional Data]** - `/[api_path]/[endpoint_4]/{objectId}/[additional_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [additional data] for a [object]

**When to use**: Only if you need [additional data] analysis and [specific functionality]

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_4]/{objectId}/[additional_endpoint]`

**Query Parameters**:
```
?[param1]=[value]&[param2]=[value]&[query_param]=[query_value]&[validation_param]=[validation_value]&[fields_param]=[field1],[field2],[field3],[field4]
```

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_4]/[sample_id]/[additional_endpoint]?[param2]=[value]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[pagination_start]": 0,
  "[pagination_size]": 50,
  "[pagination_total]": 120,
  "[data_key]": [
    {
      "[item_id]": "[item_id_value]",
      "[item_key]": "[ITEM-123]",
      "[item_url]": "https://[your_instance].[platform_domain]/[api_path]/[item_endpoint]/[item_id_value]",
      "[item_fields]": {
        "[summary_field]": "[Item summary text]",
        "[status_field]": {
          "[status_id]": "[status_id_value]",
          "[status_name]": "[Status Name]",
          "[status_category]": {
            "[category_id]": 2,
            "[category_key]": "[category_key]",
            "[category_color]": "[color-name]"
          }
        },
        "[assignee_field]": {
          "[assignee_id]": "[assignee_account_id]",
          "[assignee_name]": "[Assignee Name]"
        },
        "[priority_field]": {
          "[priority_id]": "[priority_id_value]",
          "[priority_name]": "[Priority Level]"
        }
      }
    }
  ]
}
```

---

## 📊 Data Extraction Flow

### 🎯 **SIMPLE FLOW (Recommended - Using Only Required Endpoint)**

### **Single Endpoint Approach - `/crm/v3/objects/deals` Only**
```python
mport requests

def extract_all_deals(access_token):
    """Extract all deals using only the /crm/v3/objects/deals endpoint"""
    base_url = "https://api.hubapi.com/crm/v3/objects/deals"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "limit": 100,
        "properties": "dealname,amount,dealstage,pipeline,closedate,createdate,hubspot_owner_id,hs_deal_stage_probability,dealtype,description,hs_priority,hs_is_closed_won,closed_lost_reason"
    }
    all_deals = []

    while True:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        all_deals.extend(data.get("results", []))

        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break

        params["after"] = after

    return all_deals

# This gives you ALL essential deal data:
# - id, dealname, amount, dealstage, pipeline
# - closedate, createdate, hs_lastmodifieddate
# - hubspot_owner_id for owner reference
# - hs_deal_stage_probability, hs_is_closed_won, closed_lost_reason
```

---

### 🔧 **ADVANCED FLOW (Optional - Multiple Endpoints)**

> **⚠️ Only use this if you need [related_data], [configuration], or [additional_data] data**

### **Step 1: Batch [Object] Retrieval**
```python
# Get [objects] in batches of 50
for start_at in range(0, total_objects, 50):
    response = requests.get(
        f"{base_url}/[api_path]/[primary_endpoint]",
        params={
            "[pagination_param]": start_at,
            "[size_param]": 50
        },
        headers=auth_headers
    )
    objects_data = response.json()
    objects = objects_data.get("[data_array]", [])
```

### **Step 2: Enhanced [Object] Details (Optional)**
```python
# Get detailed information for each [object]
for obj in objects:
    response = requests.get(
        f"{base_url}/[api_path]/[endpoint_1]/{obj['[field_id]']}",
        headers=auth_headers
    )
    detailed_object = response.json()
```

### **Step 3: [Object] [Related Data] (Optional)**
```python
# Get [related data] for each [specific type] [object]
for obj in objects:
    if obj['[field_type]'] == '[specific_type]':
        response = requests.get(
            f"{base_url}/[api_path]/[endpoint_2]/{obj['[field_id]']}/[related_endpoint]",
            params={"[param2]": 50},
            headers=auth_headers
        )
        object_related_data = response.json()
```

### **Step 4: [Object] Configuration (Optional)**
```python
# Get configuration for each [object]
for obj in objects:
    response = requests.get(
        f"{base_url}/[api_path]/[endpoint_3]/{obj['[field_id]']}/[config_endpoint]",
        headers=auth_headers
    )
    object_config = response.json()
```

---

## ⚡ Performance Considerations

### **Rate Limiting**
- **Default Limit**: 100 requests per 10 seconds per Private App token
- **Burst Limit**:  250,000 requests per day (Enterprise: 1,000,000/day)
- **Best Practice**: Implement exponential backoff on 429 responses; respect Retry-After header

### **Batch Processing**
- **Recommended Batch Size**:  100 deals per request (HubSpot maximum)
- **Concurrent Requests**: Max 3 parallel requests to stay safely under rate limits
- **Request Interval**: 150ms between sequential requests for sustained extraction

### **Error Handling**
```http
# Rate limit exceeded
HTTP/1.1 429 Too Many Requests
Retry-After: 10

# Authentication failed
HTTP/1.1 401 Unauthorized

# Insufficient permissions
HTTP/1.1 403 Forbidden

# Deal not found
HTTP/1.1 404 Not Found
```

---

## 🔒 Security Requirements

### **API Token Permissions**

#### ✅ **Required (Minimum Permissions)**
```
Required Scopes:
- crm.objects.deals.read    (read and list all deal objects)
- crm.schemas.deals.read   (read deal property definitions)
```

#### 🔧 **Optional (Advanced Features)**
```
Additional Scopes (only if using optional endpoints):
- [scope_2] (for [related data] information)
- [scope_3] (for [object] configuration)
```

### **User Permissions**

#### ✅ **Required (Minimum)**
The Private App token user must have:
- **CRM: Deals **  View permission (read access to all deals across all owners)
- **Super Admin** deal visibility across the portal

#### 🔧 **Optional (Advanced Features)**
Additional permissions (only if using optional endpoints):
- **[Permission_3]** permission (for [object] configuration details)
- **[Permission_4]** (for [additional data] access)

---

## 📈 Monitoring & Debugging

### **Request Headers for Debugging**
```http
Authorization: Bearer pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Content-Type: application/json
User-Agent: DealExtractionService/1.0
X-Request-ID: deal-scan-001-batch-1
```

### **Response Validation**
```python
def validate_deal_response(deal):
    required_fields = ["id", "properties", "createdAt", "updatedAt"]
    for field in required_fields:
        if field not in deal:
            raise ValueError(f"Missing required field: {field}")

    props = deal["properties"]
    if not props.get("dealname"):
        raise ValueError("Deal is missing dealname")
    if not props.get("dealstage"):
        raise ValueError("Deal is missing dealstage")
```

### **API Usage Metrics**
- Track requests per 10-second window vs. the 100-request limit
- Monitor response times for latency spikes
- Log X-HubSpot-RateLimit-Remaining response header
- Track 401 and 403 authentication failures

---

## 🧪 Testing API Integration

### **Test Authentication**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  -H "Content-Type: application/json"
```

### **Test Deal List**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=5&properties=dealname,amount,dealstage" \
  -H "Authorization: Bearer pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  -H "Content-Type: application/json"
```

### **Test [Object] Details**
```bash
curl -X GET \
  "https://[your_instance].[platform_domain]/[api_path]/[endpoint_1]/{objectId}" \
  -H "[AUTH_HEADER]: [AUTH_VALUE]" \
  -H "Content-Type: application/json"
```

---

## 🚨 Common Issues & Solutions

### **Issue**: 401 Unauthorized
**Solution**: Verify the Private App token is valid and not expired. Regenerate from HubSpot → Settings → Private Apps.
```bash
curl -X GET "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Issue**: 403 Forbidden
**Solution**: Check the Private App has crm.objects.deals.read scope and the token user has View permission on Deals in HubSpot.

### **Issue**:  429 Rate Limited
**Solution**: Implement retry with exponential backoff
```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

### **Issue**: Empty Deal List
**Solution**:Check if the token user has access to deals in HubSpot. Confirm the portal has deals created and the Private App scopes are saved correctly.

### **Issue**: Missing Properties in Response**
**Solution**:  Explicitly pass the desired property names via the properties parameter. HubSpot only returns a default subset unless requested.

---

## 💡 **Implementation Recommendations**

### 🎯 **Phase 1: Start Simple (Recommended)**
1. Implement only `/[api_path]/[primary_endpoint]`
2. Extract basic [object] data ([field_id], [field_name], [field_type], [nested_object] info)
3. This covers 90% of [object type] analytics needs

### 🔧 **Phase 2: Add Advanced Features (If Needed)**
1. Add `/[api_path]/[endpoint_1]/{objectId}` for detailed [object] info
2. Add `/[api_path]/[endpoint_2]/{objectId}/[related_endpoint]` for [related data] analysis  
3. Add `/[api_path]/[endpoint_3]/{objectId}/[config_endpoint]` for [workflow type] analysis
4. Add `/[api_path]/[endpoint_4]/{objectId}/[additional_endpoint]` for [additional functionality]

### ⚡ **Performance Tip**
- **Simple approach**: 1 API call per [batch_size] [objects]
- **Advanced approach**: 1 + N API calls (N = number of [objects] for details)
- Start simple to minimize API usage and complexity!

---

## 📞 Support Resources

- **HubSpot Deals API Documentation**: [(https://developers.hubspot.com/docs/api/crm/deals)]
- **Rate Limiting Guide**: [https://developers.hubspot.com/docs/api/usage-details]
- **Authentication Guide**: [https://developers.hubspot.com/docs/api/private-apps]
- **Deal Properties Reference**: [https://developers.hubspot.com/docs/api/crm/properties]
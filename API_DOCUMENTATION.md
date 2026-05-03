# ProcureIQ API Documentation

## Overview

ProcureIQ API provides enterprise-grade REST endpoints for integrating procurement decision support with enterprise systems (SAP, Coupa, Ariba, data warehouses).

**Base URL:** `http://localhost:8501/api`  
**Authentication:** JWT Bearer tokens via query parameter `token` or Authorization header  
**Format:** JSON  
**API Version:** 1.0.0

---

## Authentication

### Get Access Token (Login)

```
POST /login
Content-Type: application/json

{
  "username": "user@company.com",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "session_id": "sess_abc123xyz"
}
```

### Use Token

Include token in any request:
- Query parameter: `GET /market-data/MSFT?token=eyJ0eXAi...`
- Header: `Authorization: Bearer eyJ0eXAi...`

### Logout

```
POST /logout?token={access_token}
```

---

## API Endpoints

### Spend Management

#### Import Spend Line Items
```
POST /import-spend
```

Import PO, invoice, or spend data for auto-classification.

**Request:**
```json
{
  "category": "IT Services",
  "spend": 150000,
  "supplier": "Accenture",
  "date": "2024-01-15"
}
```

**Response (200):**
```json
{
  "message": "Spend data imported successfully",
  "data": {
    "category": "IT Services",
    "spend": 150000,
    "supplier": "Accenture",
    "date": "2024-01-15"
  }
}
```

### Evaluation Management

#### Export Decision
```
GET /export-decision/{event_id}
```

Export supplier scorecard, recommendation, and 90-day plan.

**Parameters:**
- `event_id` (path): Evaluation event UUID
- `token` (query): Auth token

**Response (200):**
```json
{
  "event_id": "eval_abc123",
  "recommendation": "Award to Vendor A",
  "scores": {
    "Price / TCO": 92,
    "SLA Strength": 88,
    "Execution Risk": 85
  },
  "created_at": "2024-01-20T14:30:00Z"
}
```

### Market Intelligence

#### Get Real-Time Market Data
```
GET /market-data/{ticker}
```

Fetch supplier financial signals, news, and peer comparison.

**Parameters:**
- `ticker` (path): Stock ticker symbol (e.g., "MSFT", "ORCL")
- `token` (query): Auth token

**Response (200):**
```json
{
  "ticker": "MSFT",
  "data": {
    "price": 380.50,
    "market_cap": "2.8T",
    "pe_ratio": 34.2,
    "latest_news": ["Microsoft achieves carbon negative milestone..."],
    "recent_filings": ["10-K Annual Report", "8-K Current Report"]
  },
  "cached": false
}
```

#### Get Real-Time Quote
```
GET /realtime/quote/{symbol}
```

Latest price, volume, and market data for a public company.

**Response (200):**
```json
{
  "symbol": "MSFT",
  "price": 380.50,
  "volume": 15200000,
  "change": "+2.15%",
  "timestamp": "2024-01-20T15:45:02Z"
}
```

#### Get Company Overview
```
GET /realtime/company/{symbol}
```

Company profile, financials, business description.

**Response (200):**
```json
{
  "symbol": "MSFT",
  "name": "Microsoft Corporation",
  "sector": "Information Technology",
  "description": "...",
  "employees": 221000,
  "founded": 1975
}
```

#### Get Market Trends
```
GET /realtime/trends
```

Procurement industry trends, commodity indices, market outlook.

**Response (200):**
```json
{
  "trends": [
    {"category": "Cloud Infrastructure", "outlook": "rising", "confidence": 0.92},
    {"category": "Logistics", "outlook": "stable", "confidence": 0.78}
  ],
  "bls_ppi_changes": {"IT Services": -1.2, "Logistics": 2.1}
}
```

#### Get Procurement News
```
GET /realtime/news?query=procurement+supply+chain
```

News articles filtered by topic.

**Response (200):**
```json
{
  "news": [
    {
      "title": "Global supply chain resilience improves",
      "source": "Reuters",
      "date": "2024-01-20",
      "url": "..."
    }
  ]
}
```

### Validation & Compliance

####  Validate RFP Data
```
POST /validate-rfp
```

Validate that RFP or evaluation event has required fields.

**Request:**
```json
{
  "event_name": "HRIS Platform Sourcing",
  "category": "HR Systems",
  "suppliers": [
    {"name": "Workday", "price": 500000},
    {"name": "SAP SuccessFactors", "price": 450000}
  ]
}
```

**Response (200):**
```json
{
  "valid": true,
  "errors": []
}
```

**Response (422) - Validation Failed:**
```json
{
  "valid": false,
  "errors": [
    "Missing supplier #1 pricing",
    "Category 'HR Systems' not in taxonomy"
  ]
}
```

### Audit & Compliance

#### Retrieve Audit Log
```
GET /audit-log?limit=50
```

View action history (who did what, when).

**Response (200):**
```json
{
  "audit_log": [
    {
      "timestamp": "2024-01-20T14:22:15Z",
      "user": "alice@company.com",
      "action": "create_evaluation",
      "resource": "eval_abc123",
      "details": {"category": "IT Services", "suppliers": 3}
    }
  ]
}
```

#### Protected Endpoint (Verify Auth)
```
GET /protected-endpoint
```

Verify that your token is valid and active.

**Response (200):**
```json
{
  "message": "Access granted",
  "user": "alice@company.com"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Resource not found |
| 422 | Validation error |
| 500 | Server error |
| 503 | Service unavailable (market data down) |

### Example Error Responses

**401 - Missing Token:**
```json
{"detail": "Token required"}
```

**400 - Invalid Category:**
```json
{"detail": "Invalid category: 'Xyz Services'"}
```

**503 - Market Data Unavailable:**
```json
{"detail": "Market data service unavailable"}
```

---

## Integration Scenarios

### SAP Integration

Import spend from SAP FI/CO GL accounts:

```python
# Extract spend by cost object from SAP
for line in sap_export:
    requests.post(
        "http://procureiq/api/import-spend",
        json={
            "category": map_to_procureiq(line.cost_object),
            "spend": float(line.amount),
            "supplier": line.vendor_name,
            "date": line.posting_date.isoformat()
        },
        params={"token": access_token}
    )
```

### Coupa Integration

Push sourcing event decisions back to Coupa RFx:

```python
# After evaluation completes in ProcureIQ
decision = requests.get(
    f"http://procureiq/api/export-decision/{event_id}",
    params={"token": access_token}
).json()

# POST back to Coupa RFx module
coupa_client.update_rfx(
    event_id=decision["event_id"],
    winner=decision["recommendation"],
    scores=decision["scores"]
)
```

### Data Warehouse Integration

Fetch market trends for BI dashboard:

```python
trends = requests.get(
    "http://procureiq/api/realtime/trends",
    params={"token": access_token}
).json()

# Load into data warehouse
dw_client.load_table("procurement_trends", trends)
```

---

## Rate Limiting & Quotas

- **Default:** 100 requests/minute per user
- **Batch imports:** 1000 line items/request
- **Real-time data:** Cached for 5 minutes to avoid overload

---

## Webhook Support (Future)

**Planned for v1.1:**
- POST notifications when evaluations complete
- Alerts for contract renewal dates
- Market trend updates

---

## SDK & Samples

### Python Client

```python
from procureiq_sdk import ProcureIQClient

client = ProcureIQClient(
    base_url="http://localhost:8501/api",
    username="user@company.com",
    password="secure_password"
)

# Import spend
client.import_spend(
    category="IT Services",
    spend=150000,
    supplier="Accenture",
    date="2024-01-20"
)

# Get market data
msft = client.get_market_data("MSFT")
print(f"Microsoft price: ${msft['price']}")

# Export decision
decision = client.export_decision("eval_abc123")
print(f"Recommendation: {decision['recommendation']}")
```

### REST Examples

```bash
# Login
curl -X POST http://localhost:8501/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@company.com","password":"pwd"}'

# Import spend
curl -X POST http://localhost:8501/api/import-spend \
  -H "Content-Type: application/json" \
  -d '{"category":"IT","spend":150000,"supplier":"Accenture","date":"2024-01-20"}' \
  -G --data-urlencode "token=eyJ0eX..."

# Get market data
curl http://localhost:8501/api/market-data/MSFT \
  -G --data-urlencode "token=eyJ0eX..."
```

---

## Support & Changelog

**Documentation Version:** 1.0  
**Last Updated:** 2024-01-20

For questions or issues, contact: support@procureiq.dev

### API Versioning

-  `v1.0.0` - Current stable version
- Breaking changes will increment major version
- New features increment minor version

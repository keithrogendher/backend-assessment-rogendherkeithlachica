# HubSpot Service Deployment Checklist

**Version:** 1.0  
**Date:** 2026-06-29  
**Status:** ✅ Ready for Staging/Testing

## Pre-Deployment Verification

- [x] Core HubSpot API client implemented (search, validate token, associations)
- [x] Data source integration wired (DLT + HubSpot search API)
- [x] API routes exposed (`/scan/start`, `/scan/list`, `/scan/{id}/cancel`, `/key/verify`, `/maintenance/cleanup`, etc.)
- [x] Regression test suite passing (4/4 tests)
- [x] Health check endpoint operational
- [x] Cleanup/maintenance endpoints functional
- [x] Token validation working via `GET /api/key/verify`

## Test Results

```
4 tests passed, 0 failures
- test_search_payload_uses_cursor_and_last_modified_filter ✅
- test_get_associations_posts_batch_read_request ✅
- test_key_verify_endpoint_returns_valid_status ✅
- test_cleanup_endpoint_returns_deleted_count ✅
```

## Environment Setup

### Required Environment Variables
```bash
HUBSPOT_ACCESS_TOKEN=<your-private-app-token>
HUBSPOT_OBJECT_TYPE=deals  # or contacts, companies, etc.
DB_HOST=localhost
DB_PORT=5432
DB_NAME=extracted_data
DB_USER=postgres
DB_PASSWORD=<password>
FLASK_ENV=development
LOG_LEVEL=INFO
```

### Optional Environment Variables
```bash
HUBSPOT_PORTAL_ID=<your-portal-id>
MAX_CONCURRENT_SCANS=5
CLEANUP_DAYS=7
API_RATE_LIMIT=100
```

## Staging Deployment Steps

1. **Clone and install**
   ```bash
   git clone <repo>
   cd hubspot-deals-etl
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with credentials
   ```

3. **Start database** (if not in Docker)
   ```bash
   docker run -d --name hubspot_postgres \
     -e POSTGRES_PASSWORD=<pwd> \
     -p 5432:5432 postgres:15-alpine
   ```

4. **Run migrations** (if any)
   ```bash
   # Database is auto-initialized on first run
   ```

5. **Start service**
   ```bash
   python app.py
   ```

6. **Verify health**
   ```bash
   curl http://localhost:5200/api/health
   ```

## Docker Deployment

```bash
# Build image
docker build -f Dockerfile.stage -t hubspot-service:1.0 .

# Run container
docker run -d \
  -e HUBSPOT_ACCESS_TOKEN=<token> \
  -e DB_HOST=postgres_host \
  -p 5200:5000 \
  hubspot-service:1.0
```

## API Quick Test

### 1. Validate Token
```bash
curl "http://localhost:5200/api/key/verify?accessToken=YOUR_TOKEN"
```

Expected response:
```json
{
  "success": true,
  "data": {
    "valid": true,
    "message": "HubSpot access token is valid"
  }
}
```

### 2. Start a Scan
```bash
curl -X POST http://localhost:5200/api/scan/start \
  -H "Content-Type: application/json" \
  -d '{
    "scanId": "test-001",
    "organizationId": "org-123",
    "type": "hubspot",
    "auth": {"accessToken": "YOUR_TOKEN"},
    "filters": {
      "objectType": "deals",
      "properties": ["id", "dealname", "pipeline"]
    }
  }'
```

### 3. Check Status
```bash
curl http://localhost:5200/api/scan/test-001/status
```

### 4. List Scans
```bash
curl "http://localhost:5200/api/scan/list?limit=10"
```

### 5. Cleanup Old Data
```bash
curl -X POST http://localhost:5200/api/maintenance/cleanup \
  -H "Content-Type: application/json" \
  -d '{"daysOld": 7}'
```

## Known Limitations

1. **Single-threaded extraction** — Uses DLT sequential mode; for parallel extraction, implement batch requests
2. **No request signing** — HMAC auth not implemented for core-service integration (see design Section 6)
3. **No Kafka streaming** — Currently stores to PostgreSQL only (see design Section 11)
4. **No MinIO integration** — Raw extracts not archived to object storage (see design Section 12)

## Next Steps for Production

1. **Add HMAC authentication** for internal core-service calls
2. **Implement Kafka producer** for real-time event streaming
3. **Add MinIO S3 uploads** for raw JSON backup
4. **Deploy to Nomad** using HCL templates from design
5. **Set up monitoring** with Prometheus + Grafana
6. **Add distributed tracing** with Jaeger
7. **Configure log aggregation** with Loki

## Support & Documentation

- **Design Spec**: See [HUBSPOT_SERVICE_DESIGN.md](HUBSPOT_SERVICE_DESIGN.md)
- **Implementation Notes**: See [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md)
- **API Reference**: See [APi-DOCS.md](APi-DOCS.md)
- **Database Schema**: See [DATABASE-DESIGN-DOCS.md](DATABASE-DESIGN-DOCS.md)
- **Deployment Guide**: See [INTEGRATION-DOCS.md](INTEGRATION-DOCS.md)

## Rollback Plan

If issues arise in staging:

1. Stop the service
2. Revert to previous Docker image
3. Run cleanup to remove incomplete scans:
   ```bash
   curl -X POST http://localhost:5200/api/maintenance/cleanup -d '{"daysOld": 0}'
   ```
4. Review logs in `logs/app.log`

## Contacts

- **Engineering Lead**: Glynac Engineering
- **Design Reference**: See `docs/HUBSPOT_SERVICE_DESIGN.md`

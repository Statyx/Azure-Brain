# Monitoring Agent — Known Issues & Workarounds

## Common Issues

### 1. Admin API Returns 403
**Symptom**: Any `/v1/admin/*` endpoint returns 403 Forbidden.  
**Cause**: User/SP is not a Fabric Admin or Global Admin.  
**Fix**: 
- Add user to "Fabric administrators" role in Microsoft 365 Admin Center
- Or use a service principal with Power BI Service Admin role
- Tenant setting must also allow the SP to use admin APIs

### 2. Activity Events Have 30-Minute Delay
**Symptom**: Recent user actions don't appear in activity events.  
**Cause**: Audit log pipeline has ~30 minute buffering delay.  
**Fix**: This is by design. Don't use activity events for real-time monitoring. For near-real-time, use KQL dashboards querying EventStream data.

### 3. Activity Events Limited to 24-Hour Windows
**Symptom**: API returns error when requesting more than 24 hours of activity.  
**Cause**: Maximum time range per request is 24 hours.  
**Fix**: Split requests into daily batches:
```python
from datetime import datetime, timedelta

def get_weekly_events(token: str):
    all_events = []
    for i in range(7):
        start = (datetime.utcnow() - timedelta(days=i+1)).strftime("%Y-%m-%dT00:00:00Z")
        end = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%dT00:00:00Z")
        events = get_all_activity_events(start, end, token)
        all_events.extend(events)
    return all_events
```

### 4. Job Status Returns "Unknown" or No Details
**Symptom**: Polling a job returns status "Unknown" indefinitely.  
**Cause**: 
- (a) Job was triggered but didn't start (capacity issue)
- (b) Using wrong Location URL
- (c) Job type incorrect (e.g., `runNotebook` instead of `RunNotebook`)  
**Fix**: 
- Verify the Location header URL from the 202 response
- Verify `jobType=RunNotebook` (exact casing)
- Check capacity is Active and has available CUs

### 5. Rate Limiting on Admin APIs
**Symptom**: 429 Too Many Requests after ~30 calls.  
**Cause**: Admin API rate limit is ~30 requests/minute.  
**Fix**: Add delays between calls:
```python
import time
for ws in workspaces:
    process(ws)
    time.sleep(2)  # 2 seconds between calls ≈ 30/min
```

### 6. Continuation Token Expires
**Symptom**: Pagination stops working mid-way through large result sets.  
**Cause**: Continuation tokens have a limited lifespan (~5 minutes).  
**Fix**: Process pages quickly. Don't pause between pages. If token expires, restart from the beginning with more specific filters.

### 7. KQL Dashboard Shows No Data
**Symptom**: Dashboard tiles are empty even though data exists.  
**Cause**: 
- (a) Wrong database/table selected
- (b) Time range filter too narrow
- (c) Dashboard parameter not set
- (d) KQL query syntax error  
**Fix**: 
- Test queries directly in KQL Queryset first
- Use `SensorReading | count` to verify data exists
- Check `ago()` time ranges match when data was ingested

### 8. Cannot Access capacity metrics via API
**Symptom**: Capacity-level metrics endpoints return 404 or empty data.  
**Cause**: Capacity metrics API is being consolidated; some endpoints are in transition.  
**Fix**: 
- Use ARM API for basic capacity status (Active/Paused/SKU)
- Use Fabric Capacity Metrics App (installable from AppSource) for detailed utilization
- Use Admin API for workspace-level item counts

---

## What Works and What Doesn't

| Operation | Status | Notes |
|-----------|--------|-------|
| List workspaces (admin) | ✅ Works | Requires Fabric Admin role |
| Get activity events | ✅ Works | 24h max window, ~30 min delay |
| List capacities (admin) | ✅ Works | Basic info (SKU, state) |
| Capacity utilization metrics | ⚠️ Limited | Use Capacity Metrics App for detailed |
| Job status polling | ✅ Works | Use Location header from 202 |
| Refresh history (datasets) | ✅ Works | Via Power BI API |
| Real-time ingestion monitoring | ✅ Works | Via KQL dashboards |
| User access audit | ✅ Works | Via activity events |
| Item-level usage stats | ⚠️ Limited | Some item types don't report usage |
| Cross-workspace monitoring | ✅ Works | Admin API required |

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────┐
│              Monitoring Layer                     │
│                                                   │
│  ┌───────────────┐  ┌──────────────────────────┐ │
│  │ Admin REST API │  │ KQL Dashboard            │ │
│  │ (audit, users) │  │ (real-time ops metrics)  │ │
│  └───────┬───────┘  └─────────┬────────────────┘ │
│          │                     │                   │
│  ┌───────▼───────┐  ┌────────▼─────────────────┐ │
│  │ Activity Events│  │ Eventhouse               │ │
│  │ (~30 min delay)│  │ (SensorReading, Alerts)  │ │
│  └───────────────┘  └──────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ Job Polling (real-time per execution)        │ │
│  │ GET /items/{id}/jobs/instances/{jobId}       │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

- **Real-time ops** → KQL Dashboard (sub-second data)
- **Job tracking** → REST API polling (per-execution)
- **Audit/compliance** → Activity Events (30 min delay, comprehensive)
- **Capacity health** → ARM API + Capacity Metrics App

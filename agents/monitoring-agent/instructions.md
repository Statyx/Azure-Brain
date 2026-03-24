# Monitoring Agent — Instructions

## System Prompt

You are an expert at monitoring and troubleshooting Microsoft Fabric environments. You use Admin REST APIs, job tracking patterns, audit logs, and KQL dashboards to provide operational visibility. You detect failures, track performance, and help teams maintain healthy Fabric workspaces.

**Before monitoring work**, load `admin_apis.md` for API reference and `kql_dashboards.md` for query patterns.

---

## Mandatory Rules

### Rule 1: Use the Correct API for Each Monitoring Need

| Need | API | Base URL | Token Scope |
|------|-----|----------|-------------|
| Job status (individual) | Fabric REST | `api.fabric.microsoft.com/v1` | `api.fabric.microsoft.com` |
| Workspace-wide activity | Admin API | `api.fabric.microsoft.com/v1/admin` | `api.fabric.microsoft.com` |
| Capacity metrics | ARM API | `management.azure.com` | `management.azure.com` |
| Audit events | Admin API | `api.fabric.microsoft.com/v1/admin` | `api.fabric.microsoft.com` |

### Rule 2: Always Use Async Polling for Long-Running Operations
All Fabric job executions (notebooks, pipelines, dataflows) return `202 Accepted` with a `Location` header. Poll until terminal state:

> **Proven pattern** from `Fabric RTI Demo/src/helpers.py` — battle-tested with 5s interval / 120s timeout

```python
import time, requests

def poll_operation(location_url: str, token: str, interval: int = 5, timeout: int = 120) -> dict:
    """Poll a long-running Fabric operation until completion.
    
    This is the proven pattern from helpers.py used across all deploy scripts.
    """
    headers = {"Authorization": f"Bearer {token}"}
    elapsed = 0
    
    while elapsed < timeout:
        resp = requests.get(location_url, headers=headers)
        
        if resp.status_code == 200:
            result = resp.json()
            status = result.get("status", "Unknown")
            
            if status in ("Completed", "Succeeded"):
                print(f"✅ Operation completed in {elapsed}s")
                return result
            elif status in ("Failed", "Cancelled", "Deduped"):
                print(f"❌ Operation {status}: {result.get('failureReason', 'No details')}")
                return result
            
            print(f"  ⏳ {status} ({elapsed}s)")
        
        time.sleep(interval)
        elapsed += interval
    
    raise TimeoutError(f"Operation timed out after {timeout}s")
```

**Non-standard polling patterns from user's codebase**:
- **SQL Endpoint readiness**: Poll `GET /items?type=SQLEndpoint` until name match (20×10s = 200s max)
- **KQL Database readiness**: Poll `GET /items?type=KQLDatabase` until name match (20×10s = 200s max)  
- **Streaming ingestion enable**: Wait 15s after `.alter table policy streamingingestion enable`

### Rule 3: Categorize Errors Before Troubleshooting
When a job fails, classify the error category first:

| Category | Symptoms | Root Cause | Fix |
|----------|----------|-----------|-----|
| **Auth** | 401, 403 | Token expired, wrong scope, no permissions | Refresh token, check roles |
| **Capacity** | Throttled, queued, slow | CU limits exceeded | Scale up or stagger jobs |
| **Configuration** | 400, ItemNotFound | Wrong IDs, missing items | Verify IDs, check dependencies |
| **Runtime** | Job Failed | Code error, data issue | Check job logs, fix code |
| **Transient** | 429, 500, 503 | Service temporary issue | Retry with backoff |

### Rule 4: Log Everything in Structured Format
When building monitoring scripts, always produce structured output:

```python
import json
from datetime import datetime

def log_event(event_type: str, item_name: str, status: str, details: dict = None):
    """Output structured monitoring event."""
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "item_name": item_name,
        "status": status,
        "details": details or {}
    }
    print(json.dumps(event))
```

### Rule 5: Rate Limit Awareness
Fabric REST APIs have rate limits. Monitor and respect them:

| Endpoint | Limit | Backoff |
|----------|-------|---------|
| Standard Fabric API | ~100 req/min | Exponential backoff on 429 |
| Admin API | ~30 req/min | 60s wait on 429 |
| OneLake DFS | ~1000 req/min | Retry on 503 |

### Rule 6: Token Acquisition — Never Use `az rest` from Python
> **Critical lesson** from `Github_Brain/known_issues.md`: `az rest` from Python subprocess **hangs indefinitely**. Always use `az account get-access-token` instead.

**Three token scopes in Fabric**:

| API | Scope | Usage |
|-----|-------|-------|
| Fabric REST | `https://api.fabric.microsoft.com` | Items, workspaces, jobs |
| OneLake DFS | `https://storage.azure.com` | File upload/download |
| Kusto Management | `{queryServiceUri}/.default` | KQL commands (with fallback scopes) |

```python
import subprocess, json

def get_fabric_token():
    result = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com"],
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)["accessToken"]
```

---

## Decision Trees

### "Something failed — how do I diagnose it?"
```
├── What type of job failed?
│   ├── Notebook → Check job status via GET /items/{id}/jobs/instances/{jobId}
│   ├── Pipeline → Check pipeline run details
│   ├── EventStream → Check EventStream API + KQL ingestion tables
│   └── Dataflow → Check Dataflow refresh history
├── Get the error details
│   ├── Check status response for "failureReason"
│   ├── Check job output/logs if available
│   └── Check audit log for the operation
├── Classify the error (Rule 3)
│   ├── Auth → Fix token/permissions
│   ├── Capacity → Scale or wait
│   ├── Config → Fix IDs/parameters
│   ├── Runtime → Fix code/data
│   └── Transient → Retry
└── After fix → Re-run and monitor
```

### "I need to monitor an end-to-end deployment"
```
├── Track each step sequentially
│   ├── Workspace creation → Poll GET /workspaces/{id}
│   ├── Lakehouse creation → Confirm via GET /items
│   ├── File upload → Verify via OneLake DFS list
│   ├── Notebook execution → Poll job instance
│   ├── EventStream creation → Confirm active status
│   └── Report creation → Confirm via GET /items
├── Aggregate results
│   ├── Log each step: timestamp, duration, status
│   └── Produce summary report
└── Alert on failures
    └── Report first failure with context
```

### "I need ongoing capacity monitoring"
```
├── Schedule periodic checks (every 5-15 min)
│   ├── Get capacity utilization via Admin API
│   ├── Count active/queued jobs per workspace
│   ├── Check KQL ingestion lag
│   └── Monitor throttling events
├── Define thresholds
│   ├── CU > 80% → Warning
│   ├── CU > 95% → Critical
│   ├── Queued jobs > 5 → Warning
│   └── Ingestion lag > 30s → Alert
└── Alert via output / webhook / email
```

---

## Job Tracking Patterns

### Track Notebook Execution
```python
def run_and_monitor_notebook(ws_id: str, notebook_id: str, token: str) -> dict:
    """Run a notebook and monitor until completion."""
    API = "https://api.fabric.microsoft.com/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Trigger notebook
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/items/{notebook_id}/jobs/instances?jobType=RunNotebook",
        headers=headers
    )
    
    if resp.status_code != 202:
        raise RuntimeError(f"Failed to trigger notebook: {resp.status_code} {resp.text}")
    
    location = resp.headers.get("Location")
    log_event("notebook_triggered", notebook_id, "Running")
    
    # Poll for completion
    result = poll_job(location, token)
    log_event("notebook_completed", notebook_id, result.get("status", "Unknown"))
    
    return result
```

### Track Multiple Jobs
```python
def run_jobs_sequentially(jobs: list, ws_id: str, token: str):
    """
    Run multiple jobs in sequence, tracking each.
    
    Args:
        jobs: List of {"item_id": "...", "type": "Notebook|Pipeline", "name": "..."}
    """
    results = []
    for job in jobs:
        print(f"\n{'='*50}")
        print(f"Running: {job['name']} ({job['type']})")
        
        start = time.time()
        try:
            result = run_and_monitor_notebook(ws_id, job["item_id"], token)
            duration = time.time() - start
            results.append({
                "name": job["name"],
                "status": result.get("status"),
                "duration_seconds": round(duration),
                "error": None
            })
        except Exception as e:
            duration = time.time() - start
            results.append({
                "name": job["name"],
                "status": "Failed",
                "duration_seconds": round(duration),
                "error": str(e)
            })
            print(f"❌ Job failed: {e}")
            break  # Stop on first failure
    
    # Summary
    print(f"\n{'='*50}")
    print("EXECUTION SUMMARY")
    for r in results:
        icon = "✅" if r["status"] in ("Completed", "Succeeded") else "❌"
        print(f"  {icon} {r['name']}: {r['status']} ({r['duration_seconds']}s)")
    
    return results
```

---

## Retry Pattern with Exponential Backoff

```python
def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 2.0):
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited — use Retry-After header if available
                retry_after = int(e.response.headers.get("Retry-After", base_delay * (2 ** attempt)))
                print(f"  Rate limited. Waiting {retry_after}s (attempt {attempt+1}/{max_retries+1})")
                time.sleep(retry_after)
            elif e.response.status_code >= 500:
                # Server error — retry with backoff
                delay = base_delay * (2 ** attempt)
                print(f"  Server error {e.response.status_code}. Waiting {delay}s")
                time.sleep(delay)
            else:
                raise  # Don't retry 4xx errors (except 429)
    raise RuntimeError(f"Max retries ({max_retries}) exceeded")
```

---

## Health Check Script

```python
def workspace_health_check(ws_id: str, token: str):
    """Run a comprehensive health check on a workspace."""
    API = "https://api.fabric.microsoft.com/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Workspace Health Check\n")
    
    # 1. Workspace exists and accessible
    ws = requests.get(f"{API}/workspaces/{ws_id}", headers=headers)
    if ws.status_code != 200:
        print(f"❌ Workspace not accessible: {ws.status_code}")
        return
    ws_data = ws.json()
    print(f"✅ Workspace: {ws_data['displayName']}")
    print(f"   Capacity: {ws_data.get('capacityId', 'NONE')}")
    
    if not ws_data.get("capacityId"):
        print("❌ No capacity assigned — items will not function")
        return
    
    # 2. List all items
    items = requests.get(f"{API}/workspaces/{ws_id}/items", headers=headers).json()["value"]
    type_counts = {}
    for item in items:
        t = item["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print(f"\n📦 Items ({len(items)} total):")
    for t, c in sorted(type_counts.items()):
        print(f"   {t}: {c}")
    
    # 3. Check Lakehouses for SQL Endpoints
    lakehouses = [i for i in items if i["type"] == "Lakehouse"]
    sql_endpoints = [i for i in items if i["type"] == "SQLEndpoint"]
    
    if lakehouses:
        if len(sql_endpoints) >= len(lakehouses):
            print(f"\n✅ SQL Endpoints: {len(sql_endpoints)} (matching {len(lakehouses)} Lakehouses)")
        else:
            print(f"\n⚠️ SQL Endpoints: {len(sql_endpoints)} for {len(lakehouses)} Lakehouses — some may still be provisioning")
    
    # 4. Check for recent job failures (if admin access)
    try:
        # This would use admin APIs — see admin_apis.md
        print(f"\n✅ Health check complete")
    except Exception:
        print(f"\n✅ Basic health check complete (admin check skipped)")
```

---

## Cross-References

| Topic | Agent | File |
|-------|-------|------|
| Capacity scaling/management | workspace-admin-agent | `capacity_management.md` |
| Pipeline execution | orchestrator-agent | `pipelines.md` |
| Notebook execution | orchestrator-agent | `notebooks.md` |
| EventStream health | eventstream-agent | `known_issues.md` |
| KQL query optimization | rti-kusto-agent | `eventhouse_kql.md` |
| Fabric API auth patterns | root | `fabric_api.md` |

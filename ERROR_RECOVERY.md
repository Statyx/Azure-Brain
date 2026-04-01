# Error Recovery Playbook — Cross-Agent Failure Handling

This file provides decision trees and recovery strategies for common failures across all Fabric agents.
When an operation fails, consult this file before retrying blindly.

> For preventive patterns (what works vs what doesn't), see [known_issues.md](known_issues.md).

---

## Master Decision Tree

When ANY Fabric operation fails:

```
1. What HTTP status code?
   ├── 401 / 403 → AUTH FAILURE (Section 1)
   ├── 404       → RESOURCE NOT FOUND (Section 2)
   ├── 409       → CONFLICT / DUPLICATE (Section 3)
   ├── 429       → THROTTLED (Section 4)
   ├── 400       → BAD REQUEST (Section 5)
   ├── 500 / 502 / 503 → SERVICE ERROR (Section 6)
   └── 202 then poll → Failed → ASYNC FAILURE (Section 7)

2. No HTTP error but wrong results?
   ├── Empty/blank visuals → SILENT FAILURE (Section 8)
   ├── Missing items → PROVISIONING DELAY (Section 9)
   └── Data mismatch → DATA INTEGRITY (Section 10)
```

---

## Section 1: Authentication Failures (401, 403)

### Symptoms
- `401 Unauthorized` — Token expired or wrong scope
- `403 Forbidden` — Insufficient permissions

### Decision Tree

```
401 Unauthorized?
├── Check token age (tokens expire after 60–90 minutes)
│   ├── Expired → Refresh: az account get-access-token --resource "..."
│   └── Fresh → Wrong token scope
│       ├── Fabric API → scope: https://api.fabric.microsoft.com
│       ├── OneLake DFS → scope: https://storage.azure.com
│       └── ARM (capacity) → scope: https://management.azure.com
│
403 Forbidden?
├── Check workspace role (need Contributor+ for create/edit)
├── Check capacity assignment (some ops need capacity)
├── Check tenant admin settings (some APIs need admin consent)
└── SPN? → Verify "Service principals can use Fabric APIs" = ON in admin portal
```

### Recovery Pattern

```python
import subprocess, time

def get_fresh_token(resource: str) -> str:
    """Always get a fresh token before critical operations."""
    result = subprocess.run(
        f'az account get-access-token --resource "{resource}" --query accessToken -o tsv',
        capture_output=True, text=True, shell=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Token acquisition failed: {result.stderr}")
    return result.stdout.strip()

# Pattern: refresh token and retry once
def api_call_with_retry(method, url, resource, **kwargs):
    token = get_fresh_token(resource)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = method(url, headers=headers, **kwargs)
    if resp.status_code == 401:
        time.sleep(2)
        token = get_fresh_token(resource)
        headers["Authorization"] = f"Bearer {token}"
        resp = method(url, headers=headers, **kwargs)
    return resp
```

---

## Section 2: Resource Not Found (404)

### Common Causes

| Cause | Symptom | Fix |
|-------|---------|-----|
| Capacity paused | All workspace items return 404 | Resume capacity via ARM API |
| Wrong workspace ID | Items not found | Verify `resource_ids.md` |
| Item not yet provisioned | Just-created item returns 404 | Wait + poll (Section 9) |
| Deleted item | Previously existing item gone | Check audit logs |
| Case sensitivity | KQL table name mismatch | Verify exact names |

### Recovery Pattern

```python
def check_capacity_first(ws_id, headers):
    """Before investigating 404s, verify capacity is running."""
    resp = requests.get(f"{API}/workspaces/{ws_id}", headers=headers)
    if resp.status_code == 404:
        print("⚠️  Workspace not found — capacity may be paused")
        print("   Resume with: workspace-admin-agent capacity resume")
        return False
    return True
```

---

## Section 3: Conflict / Duplicate (409)

### Pattern: Idempotent Create

**ALWAYS** handle 409 as "already exists" — find and reuse:

```python
def create_or_get(ws_id, item_name, item_type, headers, definition=None):
    """Idempotent item creation — handles 409 gracefully."""
    body = {"displayName": item_name, "type": item_type}
    if definition:
        body["definition"] = definition
    
    resp = requests.post(f"{API}/workspaces/{ws_id}/items", headers=headers, json=body)
    
    if resp.status_code == 409:
        # Already exists — find it
        items = requests.get(
            f"{API}/workspaces/{ws_id}/items?type={item_type}", headers=headers
        ).json()["value"]
        match = next((i for i in items if i["displayName"] == item_name), None)
        if match:
            print(f"✅ {item_type} '{item_name}' already exists: {match['id']}")
            return match["id"]
        raise RuntimeError(f"409 but item not found by name: {item_name}")
    
    elif resp.status_code in (200, 201):
        return resp.json()["id"]
    
    elif resp.status_code == 202:
        # Async creation — poll
        return poll_and_get_id(resp, headers)
    
    else:
        resp.raise_for_status()
```

---

## Section 4: Throttling (429)

### Fabric API Rate Limits

| API | Limit | Window |
|-----|-------|--------|
| Fabric REST (most) | 200 req/min | Per workspace |
| OneLake DFS | 2000 req/min | Per account |
| Admin APIs | 30 req/min | Per tenant |
| Kusto REST | 100 req/min | Per cluster |

### Recovery Pattern: Exponential Backoff

```python
import time, random

def call_with_backoff(method, url, headers, max_retries=5, **kwargs):
    """Retry with exponential backoff for 429 and 5xx errors."""
    for attempt in range(max_retries):
        resp = method(url, headers=headers, **kwargs)
        
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
            jitter = random.uniform(0, 1)
            wait = retry_after + jitter
            print(f"  ⏳ Throttled (429). Waiting {wait:.1f}s (attempt {attempt + 1})")
            time.sleep(wait)
            continue
        
        if resp.status_code in (500, 502, 503):
            wait = 2 ** attempt + random.uniform(0, 1)
            print(f"  ⏳ Server error ({resp.status_code}). Retrying in {wait:.1f}s")
            time.sleep(wait)
            continue
        
        return resp
    
    raise RuntimeError(f"Max retries exceeded for {url}")
```

---

## Section 5: Bad Request (400)

### Common 400 Errors by Agent

| Agent | Error Message | Root Cause | Fix |
|-------|--------------|-----------|-----|
| semantic-model | "Property is not defined in the metadata" | `definition.pbism` has extra properties | Use ONLY `{"version": "1.0"}` |
| report-builder | Visuals render blank | Wrong format (PBIR instead of Legacy PBIX) | Use `report.json` with `sections[]` |
| lakehouse | Notebook execution fails | `.ipynb` format used | Use `.py` fabric notebook format |
| ontology | Binding validation error | Source table doesn't exist yet | Deploy data sources first |
| eventstream | Destination error | Used Eventhouse ID instead of KQL DB ID | Use KQL Database ID |
| ai-skills | Agent invisible in portal | Only draft parts deployed | Include published/ parts + publish_info.json |

### Pattern: Validate Payload Before Sending

```python
def validate_item_definition(item_type, definition):
    """Pre-flight checks before API call."""
    parts = definition.get("parts", [])
    part_paths = [p["path"] for p in parts]
    
    if item_type == "SemanticModel":
        assert "definition.pbism" in part_paths, "Missing definition.pbism"
        pbism = next(p for p in parts if p["path"] == "definition.pbism")
        # Decode and check
        import base64, json
        content = json.loads(base64.b64decode(pbism["payload"]))
        assert content == {"version": "1.0"}, f"pbism must be exactly {{'version': '1.0'}}, got {content}"
    
    if item_type == "Report":
        assert "report.json" in part_paths, "Missing report.json — using PBIR format? Switch to Legacy PBIX"
    
    if item_type == "Notebook":
        nb = next((p for p in parts if "content" in p["path"].lower()), None)
        if nb:
            assert "ipynb" not in p["path"].lower(), "Use .py format, not .ipynb"
```

---

## Section 6: Service Errors (500, 502, 503)

### Strategy

1. **Wait and retry** — most 5xx errors are transient (use backoff from Section 4)
2. **Check Fabric service health**: https://admin.fabric.microsoft.com/health
3. **Check capacity state** — overloaded capacity causes 503s
4. If persistent after 3 retries → log full response body and escalate

---

## Section 7: Async Operation Failures

### Polling Pattern with Error Extraction

```python
def poll_operation(op_id, headers, interval=5, timeout=120):
    """Poll async operation with detailed error extraction."""
    elapsed = 0
    while elapsed < timeout:
        resp = requests.get(f"{API}/operations/{op_id}", headers=headers)
        if resp.status_code != 200:
            print(f"⚠️  Poll returned {resp.status_code}")
            time.sleep(interval)
            elapsed += interval
            continue
        
        result = resp.json()
        status = result.get("status", "Unknown")
        
        if status in ("Succeeded", "Completed"):
            return result
        
        if status in ("Failed", "Cancelled", "Deduped"):
            error = result.get("error", {})
            failure = result.get("failureReason", "No details")
            print(f"❌ Operation {status}")
            print(f"   Reason: {failure}")
            print(f"   Error: {json.dumps(error, indent=2)}")
            
            # Classify the failure
            if "capacity" in str(failure).lower():
                print("   → Capacity issue: check if capacity is running and not overloaded")
            elif "permission" in str(failure).lower() or "auth" in str(failure).lower():
                print("   → Auth issue: refresh token and check workspace role")
            elif "not found" in str(failure).lower():
                print("   → Dependency missing: check if referenced items exist")
            
            return result
        
        print(f"  ⏳ {status} ({elapsed}s)")
        time.sleep(interval)
        elapsed += interval
    
    raise TimeoutError(f"Operation {op_id} timed out after {timeout}s")
```

---

## Section 8: Silent Failures (No Error, Wrong Results)

The most dangerous category — no error code, but things don't work.

| Symptom | Root Cause | Detection | Fix |
|---------|-----------|-----------|-----|
| Blank visuals in report | PBIR format used | Check for `sections[]` in report.json | Rebuild in Legacy PBIX format |
| Blank visuals in report | Missing `prototypeQuery` | Check `dataTransforms` in visual config | Add prototypeQuery with correct measure refs |
| Blank visuals in report | Measure name mismatch | Compare visual refs vs model.bim | Fix case/whitespace in measure names |
| Data Agent invisible | Only draft parts deployed | Check for `published/` in definition | Deploy with published/ + publish_info |
| KQL table empty | Streaming ingestion not enabled | `.show table policy streamingingestion` | `.alter table policy streamingingestion enable` |
| Ontology bindings fail | Table doesn't exist yet | Check deployment order | Deploy data sources before ontology |

---

## Section 9: Provisioning Delays

Some Fabric resources take time to provision. **Always poll, never assume.**

| Resource | Delay | Poll Pattern |
|----------|-------|-------------|
| SQL Endpoint (after Lakehouse create) | 30–120s | Poll `GET /items?type=SQLEndpoint` until name match |
| KQL Database (after Eventhouse create) | 10–30s | Poll `GET /items?type=KQLDatabase` until name match |
| Streaming ingestion policy | 15s | Fixed wait after `.alter table policy` |
| EventStream topology | 10–30s | Poll topology status |
| Semantic Model refresh | 5–60s | Poll operation ID |
| Notebook execution | 30–300s | Poll job status |

### Universal Polling Helper

```python
def wait_for_item(ws_id, item_name, item_type, headers, max_attempts=20, interval=10):
    """Wait for an item to appear in workspace listing."""
    for attempt in range(max_attempts):
        resp = requests.get(
            f"{API}/workspaces/{ws_id}/items?type={item_type}", headers=headers
        )
        if resp.status_code == 200:
            items = resp.json().get("value", [])
            match = next((i for i in items if i["displayName"] == item_name), None)
            if match:
                print(f"✅ {item_type} '{item_name}' ready after {attempt * interval}s")
                return match
        time.sleep(interval)
    
    raise TimeoutError(f"{item_type} '{item_name}' not available after {max_attempts * interval}s")
```

---

## Section 10: Data Integrity Issues

### Reconciliation Checklist

When data doesn't match expectations:

1. **Source → Lakehouse**: Compare CSV row count vs Delta table row count
   ```python
   # In Spark notebook
   csv_count = spark.read.csv("Files/raw/data.csv", header=True).count()
   delta_count = spark.read.format("delta").load("Tables/fact_data").count()
   assert csv_count == delta_count, f"Row mismatch: CSV={csv_count}, Delta={delta_count}"
   ```

2. **Lakehouse → Semantic Model**: Compare SQL query vs DAX query
   ```sql
   -- SQL Endpoint
   SELECT COUNT(*) FROM fact_sales
   ```
   ```dax
   -- DAX query (via XMLA or REST)
   EVALUATE ROW("Count", COUNTROWS(fact_sales))
   ```

3. **Semantic Model → Report**: Verify measure formula correctness
   ```dax
   -- Test each measure independently
   EVALUATE ROW("Total Revenue", [Total Revenue])
   EVALUATE ROW("YoY Growth", [YoY Growth %])
   ```

4. **Streaming → KQL**: Compare generator count vs KQL count
   ```kql
   SensorReading | count
   SensorReading | summarize count() by bin(Timestamp, 1m) | order by Timestamp desc | take 5
   ```

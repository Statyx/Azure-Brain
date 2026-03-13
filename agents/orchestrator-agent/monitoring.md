# Monitoring & Error Handling — Complete Reference

## Overview

All Fabric orchestration operations are async. Monitoring means:
1. Polling operation status after creation/execution
2. Tracking pipeline/notebook job runs
3. Handling errors and retries gracefully

---

## 1. Operation Polling (Async Pattern)

Every `POST` that returns **HTTP 202** includes `x-ms-operation-id` in response headers.

### Standard Polling Function

```python
import requests, time

API = "https://api.fabric.microsoft.com/v1"

def poll_operation(op_id: str, headers: dict, timeout_sec: int = 300, interval: int = 5):
    """
    Poll a Fabric async operation until completion.
    
    Returns:
        dict: Operation result on success
    Raises:
        TimeoutError: If operation doesn't complete within timeout
        RuntimeError: If operation fails
    """
    start = time.time()
    
    for i in range(timeout_sec // interval):
        op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
        status = op.get("status", "Unknown")
        
        if status == "Succeeded":
            # Try to get result (not all operations have one)
            result_resp = requests.get(f"{API}/operations/{op_id}/result", headers=headers)
            if result_resp.status_code == 200:
                return result_resp.json()
            return op
        
        if status in ("Failed", "Cancelled"):
            error = op.get("error", {})
            raise RuntimeError(
                f"Operation {op_id} {status}: "
                f"{error.get('errorCode', 'Unknown')} - {error.get('message', 'No details')}"
            )
        
        elapsed = time.time() - start
        print(f"  [{elapsed:.0f}s] Status: {status}")
        time.sleep(interval)
    
    raise TimeoutError(f"Operation {op_id} did not complete within {timeout_sec}s")
```

### Usage
```python
resp = requests.post(f"{API}/workspaces/{WS_ID}/items/{pipeline_id}/jobs/instances?jobType=Pipeline",
                     headers=headers, json={"executionData": {}})

if resp.status_code == 202:
    op_id = resp.headers["x-ms-operation-id"]
    result = poll_operation(op_id, headers, timeout_sec=600)  # 10 min for pipelines
    print("Pipeline completed successfully!")
```

---

## 2. Job Instance Tracking

### Get Job Status
```python
# After triggering a job, track via the item's job instances
resp = requests.get(
    f"{API}/workspaces/{WS_ID}/items/{item_id}/jobs/instances",
    headers=headers
)
jobs = resp.json().get("value", [])
for job in jobs:
    print(f"  Job {job['id']}: {job['status']} ({job.get('startTimeUtc', 'pending')})")
```

### Job Status Flow
```
NotStarted → InProgress → Succeeded
                        → Failed
                        → Cancelled
```

**On F16 capacity**: expect ~2 minutes in `NotStarted` before `InProgress` (Spark cold start).

---

## 3. Error Categories & Recovery

### Category 1: Capacity Issues

| Error | Symptom | Recovery |
|-------|---------|----------|
| Capacity paused | 404 on items, empty workspace | Resume capacity (see below) |
| Capacity throttled | 429 responses | Respect `Retry-After` header |
| Capacity overloaded | Slow jobs, timeouts | Wait or scale up SKU |

**Resume capacity:**
```powershell
$sub = "9b51a6b4-ec1a-4101-a3af-266c89e87a52"
$rg = "rg-fabric-demo"
$cap = "cdrfabricdemo"
az rest --method POST --url "https://management.azure.com/subscriptions/$sub/resourceGroups/$rg/providers/Microsoft.Fabric/capacities/$cap/resume?api-version=2023-11-01"
```

**Check capacity status:**
```powershell
az rest --method GET --url "https://management.azure.com/subscriptions/$sub/resourceGroups/$rg/providers/Microsoft.Fabric/capacities/$cap?api-version=2023-11-01" --query "properties.state" -o tsv
```

### Category 2: API Errors

| Error Code | Meaning | Fix |
|------------|---------|-----|
| `CorruptedPayload` | Invalid base64 or bad JSON | Re-encode, validate JSON structure |
| `ItemDisplayNameAlreadyInUse` | Duplicate name | Delete existing or pick unique name |
| `ItemNotFound` | Wrong ID or capacity paused | Verify ID, check capacity |
| `OperationNotSupportedForItem` | Wrong API for item type | Check endpoint matches item type |
| `InvalidItemType` | Type mismatch | Use correct type string |

### Category 3: Job Failures

| Failure | Likely Cause | Fix |
|---------|-------------|-----|
| Notebook `Failed` | Code error in Spark | Check notebook output / logs |
| Pipeline `Failed` | Activity error | Check specific activity error |
| Copy `Failed` | Source unavailable | Check source connectivity |
| Timeout | Long-running query | Increase timeout, optimize query |

---

## 4. Retry Pattern

```python
import time

def retry_with_backoff(func, max_retries=3, base_delay=5, max_delay=60):
    """
    Retry a function with exponential backoff.
    Handles 429 (rate limit) with Retry-After header.
    """
    for attempt in range(max_retries + 1):
        try:
            result = func()
            
            # Handle HTTP responses with rate limiting
            if hasattr(result, 'status_code'):
                if result.status_code == 429:
                    retry_after = int(result.headers.get("Retry-After", base_delay))
                    print(f"  Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                if result.status_code >= 500:
                    raise RuntimeError(f"Server error: {result.status_code}")
            
            return result
            
        except Exception as e:
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            print(f"  Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
```

---

## 5. End-to-End Monitoring Example

Complete monitoring for a pipeline run:

```python
def run_and_monitor_pipeline(pipeline_id: str, headers: dict, ws_id: str):
    """Run a pipeline and monitor to completion with full logging."""
    
    print(f"Starting pipeline {pipeline_id}...")
    
    # Trigger
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/items/{pipeline_id}/jobs/instances?jobType=Pipeline",
        headers=headers,
        json={"executionData": {}}
    )
    
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Failed to start pipeline: {resp.status_code} {resp.text}")
    
    if resp.status_code == 200:
        print("Pipeline completed synchronously (unusual)")
        return resp.json()
    
    # Async polling
    op_id = resp.headers.get("x-ms-operation-id")
    if not op_id:
        print("Warning: No operation ID returned. Cannot track.")
        return None
    
    print(f"Operation ID: {op_id}")
    
    start = time.time()
    last_status = None
    
    for i in range(120):  # 10 min max (120 * 5s)
        op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
        status = op.get("status", "Unknown")
        elapsed = time.time() - start
        
        if status != last_status:
            print(f"  [{elapsed:.0f}s] {last_status or 'Start'} → {status}")
            last_status = status
        
        if status == "Succeeded":
            print(f"\n✓ Pipeline completed in {elapsed:.0f}s")
            return op
        
        if status in ("Failed", "Cancelled"):
            error = op.get("error", {})
            print(f"\n✗ Pipeline {status} after {elapsed:.0f}s")
            print(f"  Error: {error.get('errorCode', 'Unknown')}")
            print(f"  Message: {error.get('message', 'No details')}")
            raise RuntimeError(f"Pipeline {status}")
        
        time.sleep(5)
    
    raise TimeoutError("Pipeline did not complete within 10 minutes")
```

---

## 6. Health Check Script

Quick diagnostic to run at session start:

```python
def fabric_health_check(headers: dict, ws_id: str):
    """Run a quick health check on the Fabric workspace."""
    
    print("=== Fabric Health Check ===\n")
    
    # 1. Workspace access
    resp = requests.get(f"{API}/workspaces/{ws_id}", headers=headers)
    if resp.status_code == 200:
        ws = resp.json()
        print(f"✓ Workspace: {ws['displayName']} ({ws['id']})")
    else:
        print(f"✗ Workspace access failed: {resp.status_code}")
        return False
    
    # 2. List items
    resp = requests.get(f"{API}/workspaces/{ws_id}/items", headers=headers)
    if resp.status_code == 200:
        items = resp.json()["value"]
        by_type = {}
        for item in items:
            t = item["type"]
            by_type[t] = by_type.get(t, 0) + 1
        for t, count in sorted(by_type.items()):
            print(f"  {t}: {count}")
    else:
        print(f"✗ Item listing failed: {resp.status_code}")
    
    # 3. Capacity check
    print("\n✓ Health check complete")
    return True
```

# Orchestrator Agent — Known Issues

## Issue #1: Async Polling Infinite Loop

**Symptom**: Polling script never terminates; operation stays in "Running" state.

**Root Cause**: The operation actually completed but status endpoint returns stale data, OR the capacity was paused during execution.

**Fix**:
1. Always set a timeout (120s default, 300s for large notebooks)
2. After timeout, check the item directly — it may have been created despite "Running" status
3. Check capacity state if all operations seem stuck

```python
# Pattern: poll with fallback check
def poll_with_fallback(op_id, ws_id, item_name, item_type, headers, timeout=120):
    try:
        return poll_operation(op_id, headers, timeout=timeout)
    except TimeoutError:
        # Fallback: check if item was actually created
        items = requests.get(f"{API}/workspaces/{ws_id}/items?type={item_type}", headers=headers).json()["value"]
        match = next((i for i in items if i["displayName"] == item_name), None)
        if match:
            print(f"⚠️  Polling timed out but item exists: {match['id']}")
            return {"status": "Succeeded", "itemId": match["id"]}
        raise
```

---

## Issue #2: Pipeline Activity Fails with "ItemNotFound"

**Symptom**: Data Pipeline activities fail with `ItemNotFound` even though the item exists.

**Root Cause**: 
- The pipeline was created before the referenced item (wrong deployment order)
- The item ID in the pipeline definition is from a different workspace/environment
- The item was recently re-created and has a new ID

**Fix**:
1. Always deploy in dependency order: Lakehouse → Notebooks → Pipelines
2. Parameterize item IDs in pipeline definitions
3. After re-creating items, update pipeline references
4. See `../../WORKFLOWS.md` for correct deployment sequences

---

## Issue #3: Notebook Execution Returns "Failed" Without Details

**Symptom**: `POST /items/{notebookId}/jobs/instances` returns 202, but poll shows `Failed` with no `failureReason`.

**Root Cause**: Notebook code error (Python exception), but the error message is in the Spark logs, not in the Fabric API response.

**Fix — Step-by-step Spark log retrieval**:

1. **Open Monitoring Hub**  
   Fabric portal → left nav → **Monitor** (or `https://app.fabric.microsoft.com/monitoringhub`)

2. **Find the failed run**  
   Filter by: Activity type = **Notebook** → Status = **Failed** → Time range covers the run.  
   Click the notebook name to open the run details.

3. **Open Spark session logs**  
   In the run detail pane → click **View Logs** (top-right) → opens Apache Spark Session view.  
   Alternatively: click the notebook name → **Recent Runs** tab → click the run ID.

4. **Read stderr / driver logs**  
   - **Diagnostics tab**: shows structured error category + message  
   - **Logs tab → stderr**: the raw Python traceback (most useful)  
   - **Logs tab → stdout**: your `print()` output  
   Look for `Traceback (most recent call last):` — the last exception is the root cause.

5. **Common root causes & fixes**:

   | Error in stderr | Cause | Fix |
   |-----------------|-------|-----|
   | `ModuleNotFoundError: No module named 'xxx'` | Package not in Fabric Spark runtime | Add to Environment or use `%pip install xxx` in cell 1 |
   | `AnalysisException: Path does not exist: /lakehouse/...` | Wrong OneLake path (case-sensitive!) | Verify exact path with `mssparkutils.fs.ls()` |
   | `Py4JJavaError: ... java.lang.OutOfMemoryError` | Data too large for driver | Use `.repartition()`, increase Spark pool, or filter earlier |
   | `PermissionError` or `403 Forbidden` | Missing workspace/lakehouse role | Verify notebook identity has Contributor on lakehouse |
   | `DeltaTable ... already exists` | Re-run without `overwriteSchema` | Add `.option("overwriteSchema", "true")` or `.mode("overwrite")` |
   | `IllegalArgumentException: requirement failed` | Schema mismatch on append | Use `mergeSchema` or fix source data |

6. **Programmatic log retrieval** (for automation):
   ```python
   # List recent job instances for a notebook
   resp = requests.get(
       f"{API}/workspaces/{WS_ID}/items/{NB_ID}/jobs/instances?limit=5",
       headers=headers
   )
   for run in resp.json()["value"]:
       print(f"{run['id']}  {run['status']}  {run.get('failureReason', {}).get('message', 'n/a')}")
   ```
   > Note: `failureReason` is populated only for some error types. For full details, use the portal logs.

7. **Prevention**: Always test notebooks manually in the portal before automating via REST API.

---

## Issue #4: Copy Job Gets "Deduped" Status

**Symptom**: Polling returns `"status": "Deduped"` instead of `Succeeded` or `Failed`.

**Root Cause**: Another instance of the same job was already running. Fabric deduplicates concurrent runs of the same job.

**Fix**:
1. Check for running instances before starting: `GET /items/{itemId}/jobs/instances?status=Running`
2. Wait for existing run to complete before starting a new one
3. Use sequential execution for dependent jobs (don't parallelize same-item jobs)

---

## Issue #5: Pipeline Scheduling Drift

**Symptom**: Scheduled pipelines gradually drift from their intended run time.

**Root Cause**: Schedule is based on Fabric service time, not local time. Daylight saving time changes can cause 1-hour drift.

**Fix**:
1. Use UTC in all scheduling configurations
2. Monitor actual vs expected run times weekly
3. For business-critical pipelines, use Azure Logic Apps or Automation for scheduling (more reliable)

---

## Issue #6: Dataflow Gen2 Refresh Timeout

**Symptom**: Dataflow refresh hangs for 60+ minutes then fails with timeout.

**Root Cause**: 
- Source is slow (large dataset without query folding)
- No staging Lakehouse configured (all processing through Power Query engine)
- Memory pressure on capacity from concurrent workloads

**Fix**:
1. Enable Staging Lakehouse for large datasets (>100K rows)
2. Ensure query folding is happening (check "Applied Steps" indicator in Power Query editor)
3. Reduce concurrent workloads during Dataflow refresh
4. Split large Dataflows into multiple smaller ones

---

## Issue #7: Capacity Paused Causes Silent Failures

**Symptom**: All operations return 404 or fail without clear error messages.

**Root Cause**: Fabric capacity was paused/suspended. Unlike Azure infrastructure errors, Fabric doesn't always say "capacity paused" — it returns 404 for workspace items.

**Fix**: Always check capacity status first when debugging widespread failures.

```python
import requests, subprocess

def check_capacity_status(sub_id, rg, cap_name):
    """Check if Fabric capacity is running."""
    token = subprocess.check_output(
        'az account get-access-token --resource "https://management.azure.com" --query accessToken -o tsv',
        shell=True
    ).decode().strip()
    
    url = f"https://management.azure.com/subscriptions/{sub_id}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{cap_name}?api-version=2023-11-01"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    
    if resp.status_code == 200:
        state = resp.json().get("properties", {}).get("state", "Unknown")
        print(f"Capacity state: {state}")
        if state == "Paused":
            print("⚠️  Capacity is paused! Resume it before running any operations.")
        return state
    else:
        print(f"❌ Failed to check capacity: {resp.status_code}")
        return "Unknown"
```

---

## Issue #8: Notebook Import Fails with "Invalid Format"

**Symptom**: `POST /items` for Notebook returns 400 "Invalid definition format".

**Root Cause**: Using `.ipynb` format instead of Fabric's `.py` notebook format.

**Fix**: Use the proprietary `.py` format:
```
# Fabric notebook source


# CELL ********************
# your code here


# CELL ********************
# next cell
```

See `../lakehouse-agent/instructions.md` Rule 4 for full format specification.

---

## Issue #9: Concurrent Pipeline Runs Cause Data Corruption

**Symptom**: Fact table has duplicate rows or missing data after parallel pipeline runs.

**Root Cause**: Multiple pipelines writing to the same Delta table concurrently without proper merge/dedup logic.

**Fix**:
1. Use Delta MERGE for idempotent writes (upsert pattern)
2. Serialize writes to the same table (don't parallelize)
3. Use write-audit-publish pattern: write to staging table → validate → MERGE into target
4. See `../lakehouse-agent/spark_advanced.md` for merge patterns

---

## Issue #10: `az rest` Hangs in Python subprocess

**Symptom**: `subprocess.run("az rest ...")` never returns. Script appears frozen.

**Root Cause**: `az` on Windows is a `.cmd` wrapper. When invoked via subprocess with certain argument combinations, it hangs waiting for input.

**Fix**: **NEVER** use `az rest` from Python subprocess. Always:
1. Get token separately: `az account get-access-token --resource "..." --query accessToken -o tsv`
2. Use `requests` library for the actual API call

```python
# ✅ CORRECT
token = subprocess.check_output(
    'az account get-access-token --resource "https://api.fabric.microsoft.com" --query accessToken -o tsv',
    shell=True
).decode().strip()
resp = requests.get(f"{API}/workspaces", headers={"Authorization": f"Bearer {token}"})

# ❌ WRONG — will hang
subprocess.run('az rest --method GET --url "https://api.fabric.microsoft.com/v1/workspaces"', shell=True)
```

---

## Issue #11: `%pip install` Crashes Notebooks in Scheduled Mode

**Symptom**: Notebook works perfectly in interactive mode (portal) but fails in ~38 seconds with "Job instance failed without detail error" when run via Jobs API or pipeline.

**Root Cause**: `%pip install` magic is **blocked** in scheduled/Jobs API execution mode. The Spark session terminates immediately when encountering `%pip`.

**Diagnostic pattern**: The job always fails in exactly 30-45 seconds regardless of notebook complexity, and there's no useful error in `failureReason`.

**Fix**: Replace `%pip install` with `subprocess.check_call`:
```python
# ❌ CRASHES in scheduled mode
%pip install azure-eventhub --quiet

# ✅ Works in both interactive AND scheduled mode
import subprocess as _sp
_sp.check_call(["pip", "install", "azure-eventhub", "--quiet"])
```

> **Rule**: NEVER use `%pip` or `%conda` magic in notebooks intended for Jobs API, pipeline, or schedule execution. Use `subprocess.check_call` instead.

---

## Issue #12: Notebook Appears Empty After `.py` Format Push

**Symptom**: Notebook pushed via updateDefinition with `.py` format shows up in the portal with 0 cells visible, even though the definition contains valid content.

**Root Cause**: Missing blank line after section headers. Fabric's `.py` parser requires:
```
# CELL ********************
<blank line here>
code
```

Without the blank line, the parser ignores the cell entirely.

**Fix**: Always include a blank line after `# CELL ********************`, `# MARKDOWN ********************`, and `# METADATA ********************` headers.

```python
# ❌ No blank line — cell won't render
"# CELL ********************\nprint('hello')\n"

# ✅ Blank line after header — works
"# CELL ********************\n\nprint('hello')\n"
```

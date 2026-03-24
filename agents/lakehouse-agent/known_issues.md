# Lakehouse Agent — Known Issues & Workarounds

## Common Issues

### 1. SQL Endpoint Not Available After Lakehouse Creation
**Symptom**: `GET /workspaces/{wsId}/items?type=SQLEndpoint` returns empty list right after creating a Lakehouse.  
**Cause**: SQL Endpoint auto-provisioning takes 30–120 seconds.  
**Fix**: Poll with retries:
```python
import time
for i in range(20):
    items = requests.get(f"{API}/workspaces/{WS_ID}/items?type=SQLEndpoint", headers=headers).json()["value"]
    match = [x for x in items if x["displayName"] == lakehouse_name]
    if match:
        break
    time.sleep(10)
else:
    raise TimeoutError("SQL Endpoint not provisioned after 200 seconds")
```

### 2. Notebook Upload Returns `InvalidNotebookContent`
**Symptom**: `updateDefinition` call returns 400 with "Invalid notebook content".  
**Cause**: Using `"format": "ipynb"` or wrong content format.  
**Fix**: 
- Remove any `"format"` field from the definition JSON
- Use path `notebook-content.py` (not `.ipynb`)
- First line must be `# Fabric notebook source` with 2 blank lines after

### 3. OneLake Upload Returns 404
**Symptom**: PUT to `onelake.dfs.fabric.microsoft.com` returns 404.  
**Cause**: Wrong token type or incorrect URL path.  
**Fix**:
- Token must use scope `https://storage.azure.com` (NOT `https://api.fabric.microsoft.com`)
- URL pattern: `/{workspaceId}/{itemId}/Files/{path}` — all GUIDs, not names
- Verify workspace and lakehouse IDs exist

### 4. Flush Position Mismatch — File Remains Empty
**Symptom**: 3-step upload completes without error, but file is empty (0 bytes).  
**Cause**: `position` parameter in flush step doesn't match actual bytes uploaded.  
**Fix**: Use `len(content)` where `content` is the exact `bytes` object uploaded:
```python
content = file_text.encode("utf-8")  # Get bytes
# In flush: position={len(content)}
```

### 5. CSV Files Have BOM Characters in Column Headers
**Symptom**: First column name starts with `\ufeff` or `ï»¿` when read in Spark.  
**Cause**: CSV saved with UTF-8 BOM (Byte Order Mark).  
**Fix**: Read source files with `encoding="utf-8-sig"` to strip BOM before upload:
```python
with open("data.csv", "r", encoding="utf-8-sig") as f:
    content = f.read()
clean_bytes = content.encode("utf-8")  # Re-encode without BOM
```

### 6. Delta Table Not Visible in SQL Endpoint
**Symptom**: Spark notebook writes table successfully, but SQL Endpoint doesn't show it.  
**Cause**: 
- (a) Table written to wrong path (e.g., `Tables/subfolder/tablename` — SQL only sees top-level)
- (b) SQL Endpoint metadata sync delay (up to 60 seconds)
- (c) Notebook execution failed silently  
**Fix**:
- Write directly to `Tables/{table_name}` — no subdirectories
- Wait 60 seconds and refresh
- Check notebook job status via API

### 7. `RunNotebook` Job Returns "Failed" Without Details
**Symptom**: Notebook job status is "Failed" but no error message.  
**Cause**: The `jobType` parameter must be exactly `RunNotebook` (case-sensitive).  
**Fix**: 
```python
# Correct
requests.post(f"{API}/workspaces/{ws}/items/{nb}/jobs/instances?jobType=RunNotebook", ...)

# Wrong — will fail
requests.post(f"{API}/workspaces/{ws}/items/{nb}/jobs/instances?jobType=runNotebook", ...)
```

### 8. Shortcut Returns "Connection Not Found"
**Symptom**: Creating shortcut via API returns 400 with "connection not found".  
**Cause**: The `connectionId` must reference a connection pre-configured in Fabric portal.  
**Fix**: 
- For OneLake shortcuts: no connectionId needed (just `workspaceId` + `itemId` + `path`)
- For ADLS/S3 shortcuts: create the connection in Fabric Portal → Settings → Connections first

### 9. OPTIMIZE / VACUUM Fails on Streaming Table
**Symptom**: `OPTIMIZE` or `VACUUM` fails or hangs on a table receiving EventStream data.  
**Cause**: Active streaming writes conflict with maintenance operations.  
**Fix**: 
- Schedule OPTIMIZE during low-traffic periods
- Or use `delta.autoOptimize.autoCompact = true` instead of manual OPTIMIZE
- VACUUM is generally safe even during streaming writes

### 10. Delta Merge Fails With "Target Row Matched Multiple Source Rows"
**Symptom**: `merge()` throws error about multiple matches.  
**Cause**: Source data has duplicate keys.  
**Fix**: Deduplicate source before merge:
```python
df_source = df_source.dropDuplicates(["key_column"])
```

---

## What Works and What Doesn't

| Operation | Status | Notes |
|-----------|--------|-------|
| Create Lakehouse via API | ✅ Works | POST `/v1/workspaces/{wsId}/lakehouses` |
| Create Schema-Enabled Lakehouse | ⚠️ Preview | `creationPayload: { enableSchemas: true }` |
| Upload files via OneLake DFS | ✅ Works | 3-step protocol with storage token |
| Create Notebook via API | ✅ Works | `.py` format only, `notebook-content.py` |
| Run Notebook via API | ✅ Works | `jobType=RunNotebook` (exact casing) |
| Create Shortcut (OneLake) | ✅ Works | No connection needed |
| Create Shortcut (ADLS/S3) | ✅ Works | Requires pre-existing connection |
| List Tables via API | ✅ Works | GET `/v1/workspaces/{wsId}/lakehouses/{lhId}/tables` |
| Load Table via API | ✅ Works | POST with CSV/Parquet format, Overwrite/Append modes |
| Table Maintenance via API | ✅ Works | Optimize (Z-Order + V-Order) + Vacuum (retention period) |
| Materialized Lake Views | ✅ Works | On-demand refresh + scheduled (max 20 schedulers) |
| Livy Sessions API | ⚠️ Beta | List/Get sessions with date/state/submitter filters |
| SQL Endpoint auto-creation | ⚠️ Delayed | 30-120s; check `provisioningStatus`: InProgress→Success/Failed |
| SQL Endpoint provisioningStatus | ✅ Works | Available in GET response: `properties.sqlEndpointProperties.provisioningStatus` |
| Writing Delta to Tables/ subdirs | ❌ Not recommended | SQL Endpoint only sees top-level tables |
| Getting table schema via API | ⚠️ Limited | Tables API returns type (Managed/External) but not columns |
| Cross-workspace Shortcuts | ✅ Works | Both workspaces must be Fabric-enabled |
| Notebook with `format: ipynb` | ❌ Fails | Don't include format field |
| Get/Update Definition | ✅ Works | Base64-encoded definition parts |

---

## Capacity Considerations

| Capacity | Max Concurrent Spark Jobs | Spark Cores | Recommended For |
|----------|--------------------------|-------------|-----------------|
| Trial | 1 | Limited | Development only |
| F2 | 1-2 | 8 | Small demos |
| F16 | 4-8 | 64 | Department analytics |
| F64 | 16-32 | 256 | Enterprise workloads |
| F128+ | 32+ | 512+ | Large-scale data engineering |

> **Trial capacity**: Only supports 1 concurrent Spark job. Queue additional notebook runs and wait for each to complete before starting the next.

---

## Tenant Settings

Ensure these settings are enabled in Fabric Admin Portal:

- **OneLake file explorer** — Allows OneLake DFS access
- **Service principals can use Fabric APIs** — Required for automated deployments
- **Users can create Fabric items** — Required for Lakehouse and Notebook creation
- **Allow XMLA endpoints and Analyze in Excel** — For SQL Endpoint access (advanced)

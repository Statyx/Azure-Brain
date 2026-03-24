# Known Issues — Dataflow Gen2

## Issue Catalog

### ISSUE-DF-001: Mashup Document Format Errors
**Symptom**: `400 Bad Request` or `InvalidDefinition` when pushing Dataflow via API  
**Cause**: The mashup document (`document.pq`) must follow exact section syntax — any M parse error rejects the entire definition  
**Fix**:
1. Validate M syntax before Base64-encoding — use Power Query Online editor as a syntax checker
2. Ensure `section Section1;` header is present
3. Ensure each query uses `shared <name> = let ... in ...;` syntax (note the trailing semicolon)
4. Escape special characters in identifiers: `#"Step With Spaces"`

### ISSUE-DF-002: Staging Lakehouse Required — Silent Failure
**Symptom**: Dataflow refresh fails with vague error or hangs indefinitely  
**Cause**: No staging Lakehouse assigned when the Dataflow uses transformations that require Fabric compute (e.g., merging tables from different sources)  
**Fix**:
1. Always assign a staging Lakehouse when creating a Dataflow:
   ```python
   # Set staging Lakehouse in Dataflow configuration
   config = {
       "stagingLakehouse": {
           "workspaceId": workspace_id,
           "lakehouseId": staging_lakehouse_id
       }
   }
   ```
2. The staging Lakehouse can be dedicated or shared with the destination
3. **Rule**: When in doubt, always set a staging Lakehouse

### ISSUE-DF-003: Destination Table Schema Conflict on Append
**Symptom**: `Schema mismatch` or `Column not found` error on Append runs  
**Cause**: The M query output schema changed (added/removed/renamed columns) between runs, but the destination table still has the old schema  
**Fix**:
- For Lakehouse destinations: DROP the table and re-run with Replace mode first, then switch back to Append
- For Warehouse destinations: `ALTER TABLE` to match new schema
- **Prevention**: Lock down column names in the M query using `Table.SelectColumns` as the final step

### ISSUE-DF-004: Incremental Refresh Parameters Not Recognized
**Symptom**: Full refresh runs every time despite configuring `RangeStart` / `RangeEnd`  
**Cause**: Parameters must be named exactly `RangeStart` and `RangeEnd` (case-sensitive) and typed as `datetime`  
**Fix**:
1. Verify parameter names are exactly `RangeStart` and `RangeEnd`
2. Verify they are typed as `type datetime`
3. Verify the source query filters on these parameters: `each [Date] >= RangeStart and [Date] < RangeEnd`
4. Verify the destination is configured for incremental (not available on all destination types)

### ISSUE-DF-005: Timeout on Large Dataset Refresh
**Symptom**: Refresh fails after 2-24 hours with timeout error  
**Cause**: Dataflow Gen2 has a maximum refresh duration. Large datasets without staging or with non-folding queries are slow  
**Fix**:
1. Enable staging Lakehouse (significantly improves performance)
2. Push filters to source (ensure query folding for SQL sources)
3. Remove unnecessary columns early in the query
4. Use incremental refresh for large fact tables
5. Split into multiple Dataflows if needed (e.g., one per table)
6. Consider using a Spark Notebook instead for very large datasets (> 10M rows)

### ISSUE-DF-006: API Definition Push — Mixed Results
**Symptom**: `updateDefinition` returns 200 but the Dataflow shows empty or wrong queries in the portal  
**Cause**: The part structure must match exactly what Fabric expects. Common mismatches:
- Wrong `path` in the definition parts (must be `definition/document.pq`)
- Missing metadata or wrong metadata format
- Content not properly Base64-encoded  
**Fix**:
1. Always use `definition/document.pq` as the path for the mashup document
2. Base64-encode the M content properly (UTF-8, no BOM)
3. Verify by reading the definition back after pushing:
   ```python
   response = requests.post(
       f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/dataflows/{df_id}/getDefinition",
       headers=headers
   )
   ```

### ISSUE-DF-007: Gateway Required for On-Premises Sources
**Symptom**: `DataSource.Error: Could not connect` when source is on-premises or VNet-protected  
**Cause**: Dataflow Gen2 runs in Fabric cloud compute — it needs a gateway to reach non-public data sources  
**Fix**:
1. Install and configure an on-premises data gateway
2. Bind the data source to the gateway in Fabric settings
3. **Alternative for demos**: Copy data to Lakehouse Files first (via Pipeline Copy activity), then use Dataflow to transform from Lakehouse

### ISSUE-DF-008: Concurrent Refresh Conflicts
**Symptom**: `409 Conflict` or second refresh queued indefinitely  
**Cause**: Only one refresh can run at a time per Dataflow  
**Fix**:
1. Check refresh status before triggering a new one
2. Use sequential orchestration in Pipelines
3. Monitor with:
   ```python
   # Check if a refresh is already running
   response = requests.get(
       f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/items/{df_id}/jobs/instances?jobType=Pipeline",
       headers=headers
   )
   running = [j for j in response.json().get("value", []) if j["status"] in ("InProgress", "NotStarted")]
   ```

### ISSUE-DF-009: Gen1 vs Gen2 Confusion
**Symptom**: Code examples or API calls fail because they target Gen1 Dataflows  
**Cause**: Gen1 Dataflows use different APIs (Power BI REST API) and different definition formats  
**Fix**:
- **Fabric Dataflow Gen2**: Item type `Dataflow`, uses Fabric REST API `api.fabric.microsoft.com`
- **Power BI Dataflow Gen1**: Uses `api.powerbi.com/v1.0/myorg/groups/{groupId}/dataflows`
- **Never confuse the two** — Gen2 is the only supported type for new Fabric demos
- Gen1 cannot target Lakehouse/Warehouse/KQL destinations

### ISSUE-DF-010: M Expression Functions Not Available
**Symptom**: `Expression.Error: The name 'X' wasn't recognized` at refresh time  
**Cause**: Some M functions available in Power BI Desktop are not available in Dataflow Gen2 cloud compute  
**Fix**:
- Avoid desktop-only functions: `File.Contents` (local path), `Folder.Contents` (local), `Access.Database`
- Use Fabric-compatible connectors: `Lakehouse.Contents`, `Sql.Database`, `Web.Contents`, `OData.Feed`
- Test in Power Query Online (Fabric portal) to verify function availability before API push

---

## What Works / What Doesn't

| Feature | Status | Notes |
|---|---|---|
| Create Dataflow via API | ✅ Works | POST `/v1/workspaces/{wsId}/dataflows` |
| Push definition via API | ✅ Works | `updateDefinition` with mashup document |
| Lakehouse table destination | ✅ Works | Replace and Append modes |
| Warehouse table destination | ✅ Works | Replace and Append modes |
| KQL Database destination | ✅ Works | Append mode only |
| Trigger refresh via API | ✅ Works | `jobType=Execute` or `jobType=ApplyChanges` |
| Monitor refresh status | ✅ Works | Poll Location header |
| Incremental refresh | ✅ Works | `RangeStart`/`RangeEnd` parameters |
| Discover parameters | ✅ Works | GET `/dataflows/{id}/parameters` — 9 typed values |
| Parameter override at execution | ✅ Works | Pass parameters in `executionData` body |
| Execute Query (Arrow) | ✅ Works | Returns Apache Arrow stream, supports custom mashup |
| Schedule via API | ✅ Works | Create/Update/Delete schedules (max 20 per dataflow) |
| On-premises sources | ⚠️ Requires gateway | Gateway must be pre-configured |
| Custom M functions | ⚠️ Limited | Some desktop-only functions unavailable |
| Read definition via API | ✅ Works | `getDefinition` endpoint |
| Gen1 → Gen2 migration | ⚠️ Manual | Export/import PQT, copy/paste, or Save As |

---

## Capacity Requirements

| Capacity SKU | Max Dataflow Refresh Duration | Concurrent Refreshes | Staging Performance |
|---|---|---|---|
| Trial (F2) | 2 hours | 1 | Basic |
| F4-F8 | 5 hours | 2 | Good |
| F16-F64 | 24 hours | 5-10 | Fast |
| F128+ | 24 hours | 20+ | Fastest |

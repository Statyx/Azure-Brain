# Known Issues & Lessons Learned

Comprehensive list of every issue encountered and resolved during this project.

---

## Quick Reference: What Works vs What Doesn't

| Approach | Result |
|----------|--------|
| PBIR folder format (`visual.json` per visual) | ❌ API accepts, **never renders** |
| Legacy PBIX format (`report.json` + `sections`) | ✅ Renders correctly |
| `definition.pbism` with `datasetReference` | ❌ Rejected by API |
| `definition.pbism` with `{"version": "1.0"}` only | ✅ Works |
| `calloutValue` default font size (cards) | ❌ Clips in cards |
| `calloutValue` with explicit `27D` fontSize | ✅ Readable |
| Multi-measure chart (2-3 measures on Y) | ✅ Works with multiple Projections |
| Cross-table measures in one visual | ✅ Works if all tables in From clause |
| Sidebar nav replicated per page | ✅ Works (no shared visuals across pages) |
| Visual with `projections` but no `prototypeQuery` | ❌ Empty — "drag fields to populate" |
| `prototypeQuery` with From/Select/OrderBy | ✅ Data renders correctly |
| Theme mismatch (CY24SU11 in JSON, CY26SU02 in parts) | ❌ Report fails to load |
| `deploy_report.py --from-file report.json` | ✅ Deploys local multi-page report |
| MCP `upload_file` for OneLake CSVs | ❌ Returns 400 |
| OneLake DFS API (PUT→PATCH→PATCH) | ✅ Works |
| `az rest` in Python subprocess | ❌ Hangs or FileNotFoundError |
| `requests` lib + pre-fetched token | ✅ Works |
| PowerShell `Out-File` for JSON | ❌ Adds UTF-8 BOM |
| `[System.IO.File]::WriteAllText()` | ✅ BOM-free |
| DataAgent creation via REST API (`POST /items` type `DataAgent`) | ✅ Works |
| DataAgent instructions via `updateDefinition` (Python `requests`) | ✅ Works |
| DataAgent instructions via `updateDefinition` (PowerShell) | ❌ JSON encoding fails on markdown w/ special chars |
| DataAgent data source binding via REST API | ❌ No public endpoint — must use portal |
| DataAgent dataSources in `data_agent.json` definition | ❌ Ignored (schema only has `$schema`) |
| Notebook creation with `"format": "ipynb"` in definition | ❌ `InvalidNotebookContent` — Fabric parses .py as JSON |
| Notebook creation WITHOUT `format` field, path `notebook-content.py` | ✅ Works |
| Notebook jobType `SparkJob` | ❌ Fails — wrong job type |
| Notebook jobType `RunNotebook` | ✅ Works |
| EventStream Custom Endpoint connection string via REST API | ❌ No public endpoint — must get from portal UI |
| EventStream topology API (`GET .../eventstreams/{id}/topology`) | ✅ Returns sources, streams, destinations |
| EventStream destination `itemId` = Eventhouse ID | ❌ Must be **KQL Database ID** |
| EventStream destination `itemId` = KQL Database ID | ✅ Works |
| EventStream ingestion via Event Hub SDK (`azure-eventhub`) | ✅ Works |
| ReadOnly lock prevents capacity `/suspend` POST | ❌ ReadOnly only blocks PUT/DELETE/PATCH, not POST |

---

## Environment Issues

### 1. Python PATH Not in Terminal Sessions
- **Symptom**: `python` or `az` not found
- **Cause**: Python 3.12 per-user install; PATH not inherited
- **Fix**: Run at start of every session:
```powershell
$env:PATH = "C:\Users\<USER>\AppData\Local\Programs\Python\Python312;C:\Users\<USER>\AppData\Local\Programs\Python\Python312\Scripts;$env:PATH"
```

### 2. `az rest` Hangs in Python subprocess
- **Symptom**: `subprocess.run("az rest ...")` hangs forever
- **Cause**: `az` is a `.cmd` wrapper; subprocess can't locate it properly
- **Fix**: Use `az account get-access-token` + Python `requests`. NEVER use `az rest` from Python.

### 3. PowerShell Out-File Adds UTF-8 BOM
- **Symptom**: `json.JSONDecodeError: Unexpected UTF-8 BOM`
- **Fix**: Use `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))`

### 4. French Locale Terminal
- **Symptom**: Ctrl+C shows `Terminer le programme de commandes (O/N) ?`
- **Fix**: Type `O` + Enter, or open new terminal

---

## OneLake & Data Issues

### 5. MCP upload_file Returns 400
- **Fix**: Use OneLake DFS API directly (3-step: PUT→PATCH→PATCH). See `onelake.md`.

### 6. Paused Capacity Hides Everything
- **Symptom**: Workspace OK but Lakehouse/files → 404 or empty
- **Fix**: Resume capacity first:
```powershell
az rest --method POST --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{cap}/resume?api-version=2023-11-01"
```

### 7. Pipeline Shows "NotStarted" for Minutes
- **Symptom**: Status stays `NotStarted` 1-2 min before `InProgress`
- **Cause**: Normal Spark cold-start on F16
- **Fix**: Just wait. Total pipeline: ~4 minutes.

---

## Semantic Model Issues

### 8. definition.pbism Only Accepts `{"version": "1.0"}`
- **Symptom**: `POST /items` fails with "Property is not defined in the metadata"
- **Fix**: Only `{"version": "1.0"}` — absolutely nothing else.

### 9. Fabric API Item Creation Is Async
- **Symptom**: `POST /items` returns 202 with no body
- **Fix**: Poll `x-ms-operation-id` from response headers:
```python
op_id = response.headers["x-ms-operation-id"]
while True:
    op = requests.get(f"{api}/operations/{op_id}", headers=h).json()
    if op["status"] in ("Succeeded", "Failed"):
        break
    time.sleep(5)
```

---

## Report Issues (THE BIG ONES)

### 10. ⚠️ PBIR Folder Format Does NOT Render
- **THE single biggest issue in this project**
- **Symptom**: Report created, getDefinition returns all parts, but **BLANK** in portal
- **Cause**: PBIR folder format is accepted by API but not rendered by Fabric viewer
- **Fix**: Use **Legacy PBIX format** EXCLUSIVELY. See `report_format.md` for full specification.

### 11. Visual Type Must Be `cardVisual` (not `card`)
- **Symptom**: Card visuals don't render
- **Fix**: `"visualType": "cardVisual"` with `projections.Data` (not `Values`)

### 12. Missing `prototypeQuery` = Empty Visuals
- **Symptom**: Visuals render as empty boxes with title but no data
- **Fix**: Every data visual MUST have `prototypeQuery` with `Version:2, From:[], Select:[], OrderBy:[]`

### 13. Card Values Clipped (Font Too Large)
- **Symptom**: KPI numbers cut off / overflow container
- **Fix**: Explicit `calloutValue.fontSize: 27D` and card height ≥ 120px

### 14. Measure Name Mismatch = Silent Failure
- **Symptom**: Visuals blank despite correct structure
- **Cause**: Code used `Total_Revenue`, model has `Total Revenue`
- **Fix**: Names are **case-sensitive** and **whitespace-sensitive**. Always verify against model.bim.

### 15. definition.pbir Connection String Format
- **Symptom**: Report doesn't connect to model
- **Fix**: Must be V2 schema with full XMLA connection string:
```
Data Source="powerbi://api.powerbi.com/v1.0/myorg/{workspace_name}";
initial catalog={model_name};
integrated security=ClaimsToken;
semanticmodelid={model_guid}
```

### 16. layoutOptimization Required in report.json
- **Symptom**: Import fails with "Required properties are missing"
- **Fix**: Add `"layoutOptimization": 0` (integer, not string) to report.json

---

## Resolution Priority

When debugging Fabric report issues, check in this order:
1. Is the format Legacy PBIX? (not PBIR folder)
2. Does `definition.pbir` have the correct connection string?
3. Do measure names match the model exactly?
4. Does every visual have a `prototypeQuery`?
5. Is `layoutOptimization: 0` present?
6. Is the base theme included in `StaticResources/`?
7. Are card fonts sized explicitly?

---

## Multi-Page Report Lessons

### 17. Multi-Measure Charts Work With Cross-Table References
- **Pattern**: A chart can show measures from different tables (e.g., `fact_budgets.Budget Amount` + `fact_forecasts.Forecast Amount`)
- **Requirement**: All source tables must be listed in the query's `From` clause, each with a unique alias
- **Binding**: `Values.Projections` must list indices `[1, 2, ...]` for all measures

### 18. Sidebar Navigation Is Per-Page Replication
- **Pattern**: Each page replicates the full sidebar (shapes + textboxes) with the active label changed
- **Reason**: Fabric report pages are independent — no shared visual containers across pages
- **Implication**: Sidebar changes must be applied to ALL pages (use `build_chrome()` helper)

### 19. Page Config `name` Must Match Section `name`
- **Symptom**: Page renders but shows wrong navigation state
- **Fix**: `section.config` JSON must contain the same `name` as `section.name`

### 20. `card` (Old) Works But `cardVisual` (New) Preferred
- **Finding**: The existing report uses `card` with `Values` bucket (not `cardVisual` with `Data`)
- **Both work** for now, but `cardVisual` is the modern recommended approach
- **Key**: `card` uses `Values` projection; `cardVisual` uses `Data` projection

### 21. ⚠️ `prototypeQuery` Is MANDATORY — Even If Projections Are Set
- **THE #2 biggest issue after PBIR format**
- **Symptom**: Visuals render but show "Select or drag fields to populate this visual" — completely empty
- **Cause**: `projections` tells Fabric WHAT the visual should show, but `prototypeQuery` tells it HOW to query the data. Without `prototypeQuery`, Fabric treats the visual as unconfigured.
- **Fix**: Every data visual (card, chart, slicer) MUST have:
```json
"prototypeQuery": {
  "Version": 2,
  "From": [{"Name": "a", "Entity": "table_name", "Type": 0}],
  "Select": [{"Measure": {"Expression": {"SourceRef": {"Source": "a"}}, "Property": "Measure Name"}, "Name": "table.Measure Name"}],
  "OrderBy": [{"Direction": 2, "Expression": {...}}]
}
```
- **Script**: `temp/fix_prototype_queries.py` auto-generates prototypeQuery from projections
- **Rule**: NEVER create a visual with projections but no prototypeQuery

### 22. Theme References Must Be Consistent Across JSON and Parts
- **Symptom**: "Unable to load report" error in Fabric portal
- **Cause**: `report.json` referenced `CY24SU11` theme but deployed parts only included `CY26SU02.json`
- **Fix**: All three must reference the SAME theme version:
  1. `config.themeCollection.baseTheme.name` (inside stringified config)
  2. `resourcePackages[].items[].path` (e.g., `BaseThemes/CY26SU02.json`)
  3. Actual theme file in `StaticResources/SharedResources/BaseThemes/`
- **Current working theme**: `CY26SU02`

### 23. `deploy_report.py --from-file` for Local report.json
- **Pattern**: Use `--from-file report.json` to deploy the local file instead of generating from code
- **Use case**: After `add_pages.py` modifies report.json with new pages, deploy with `--from-file`
- **Default**: Without `--from-file`, the script generates a single-page dashboard from `build_finance_dashboard()`

---

## EventStream Issues

### 24. ⚠️ EventStream Custom Endpoint Connection String NOT Available via API
- **Symptom**: No REST API endpoint returns the EventStream Custom Endpoint connection string
- **Tried and failed**: `GET /eventstreams/{id}`, `getDefinition`, topology, various undocumented paths — all return 404 or omit the connection string
- **Fix**: Get the connection string manually from the **Fabric portal** → EventStream → Custom Endpoint source → connection details
- **Format**: `Endpoint=sb://{host}.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...;EntityPath=...`

### 25. ⚠️ EventStream Destination `itemId` Must Be KQL Database ID
- **Symptom**: EventStream destination fails to connect, data doesn't flow to KQL tables
- **Cause**: Used the Eventhouse ID instead of the KQL Database ID as `itemId` in the destination configuration
- **Fix**: Always use the **KQL Database ID** (found at `GET /workspaces/{wsId}/kqlDatabases`), NOT the Eventhouse ID

### 26. EventStream Uses Event Hub Protocol
- **Pattern**: Send data to EventStream Custom Endpoint using `azure-eventhub` SDK
- **SDK**: `EventHubProducerClient.from_connection_string(conn_str)`
- **Routing**: Add `_table` field to each JSON event for multi-table routing in EventStream topology
- **Batch limits**: Event Hub max batch ~1 MB; send in sub-batches of ~100 events
```python
from azure.eventhub import EventHubProducerClient, EventData
import json

producer = EventHubProducerClient.from_connection_string(CONN_STR)
batch = producer.create_batch()
for record in records:
    record["_table"] = "SensorReading"  # routing field
    batch.add(EventData(json.dumps(record)))
producer.send_batch(batch)
```

---

## Notebook Issues

### 27. ⚠️ Notebook Upload: Do NOT Include `"format": "ipynb"` in Definition
- **THE biggest notebook issue**
- **Symptom**: `InvalidNotebookContent` error: "Failed to cast json string to type: IPythonNotebook"
- **Cause**: Including `"format": "ipynb"` makes Fabric try to parse the `.py` content as JSON
- **Fix**: Omit the `format` field entirely from the definition body:
```python
# WRONG ❌
body = {"definition": {"format": "ipynb", "parts": [{"path": "notebook-content.py", ...}]}}

# CORRECT ✅
body = {"definition": {"parts": [{"path": "notebook-content.py", ...}]}}
```

### 28. Notebook jobType Is `RunNotebook`, NOT `SparkJob`
- **Symptom**: Job fails to start or returns error
- **Fix**: Use `?jobType=RunNotebook` when triggering notebook execution:
```python
POST /workspaces/{wsId}/items/{nbId}/jobs/instances?jobType=RunNotebook
```

### 29. Fabric Notebook Internal Format Is `.py` Not `.ipynb`
- **Symptom**: Trying to upload a standard Jupyter `.ipynb` JSON file fails
- **Fix**: Fabric uses a proprietary `.py` format with special cell markers. See `notebooks.md` for the full format specification.
- **Markers**: `# Fabric notebook source` (header), `# CELL ********************` (code), `# MARKDOWN ********************` (markdown)

---

## Azure Capacity Issues

### 30. ReadOnly Lock Does NOT Prevent Capacity Suspend
- **Symptom**: Capacity gets paused despite having a ReadOnly lock
- **Cause**: ReadOnly locks only block ARM write operations (PUT/DELETE/PATCH). POST actions like `/suspend` are NOT blocked.
- **Fix**: Don't rely on ReadOnly locks to prevent capacity pause. Delete any automation (Azure Automation runbooks) that calls `/suspend`.

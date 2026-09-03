# Known Issues & Lessons Learned

Comprehensive list of every issue encountered and resolved during this project.

> For HTTP error recovery with decision trees and retry code, see [ERROR_RECOVERY.md](ERROR_RECOVERY.md).

---

## Quick Reference: What Works vs What Doesn't

| Approach | Result |
|----------|--------|
| PBIR folder format, v2.0 rules **not** applied | ❌ API accepts, renders blank / freezes on load |
| PBIR folder format, v2.0 rules applied | ✅ Renders — **default for new reports** (see `report-builder-agent/known_issues.md` #19) |
| Legacy PBIX format (`report.json` + `sections`) | ✅ Renders — keep for maintaining reports already shipped in it |
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
| DataAgent without "always query" instruction | ❌ Orchestrator skips the query tool, hallucinated answers |
| DataAgent with "ALWAYS query ... using DAX" (semantic model source) | ✅ Forces DAX tool invocation on every question — the wording must name **the source's own language**; DAX is wrong on a lakehouse |
| DataAgent `aiInstructions` with measures list | ✅ Orchestrator reformulates questions using measure names |
| DataAgent data source binding via REST API | ❌ No public endpoint — must use portal |
| DataAgent dataSources in `data_agent.json` definition | ❌ Ignored (schema only has `$schema`) |
| DataAgent thread reuse (messages accumulate) | ❌ After ~50 msgs: `BadRequest`, agent skips DAX, returns stale data |
| DataAgent thread DELETE with `stage` param | ❌ `400 BAD_REQUEST: 'stage=sandbox' not supported`. Use `api-version` only |
| DataAgent thread DELETE + recreate before each question | ✅ Fresh thread = full DAX pipeline (6 steps) |
| DataAgent thread recycling (reuse N, then DELETE) | ❌ Cascading 404 errors + "queued" hangs after Q2-Q3 (67% error rate) |
| DataAgent thread DELETE + POST immediate GET | ❌ 404 eventual consistency (1-3s propagation delay) |
| DataAgent 404 retry on POST only | ❌ Misses 404 on GET /messages and /steps — causes errors Q4+ |
| DataAgent 404 retry on ALL endpoints (POST + GET) | ✅ Eliminates all 404 errors (0% error rate) |
| DataAgent `requests.Session()` connection pooling | ✅ Reduces per-question overhead by ~2-3s (TCP/TLS reuse) |
| DataAgent adaptive polling (0.5s→3s ramp) | ✅ Saves 2-5s/question vs fixed 2s interval |
| DataAgent parallel GET messages + steps | ✅ Saves 0.5-1s/question via ThreadPoolExecutor(2) |
| DataAgent parallel questions (single identity) | ❌ Same thread returned for all POST /threads — runs corrupt each other |
| DataAgent parallel questions (N service principals) | ✅ Each SP gets own thread — true parallelism |
| DataAgent run_steps returns only 1 step (fewshots.loading) | ❌ Thread pollution — agent didn't run DAX |
| DataAgent run_steps returns 6 steps (fewshots→nl2code→execute) | ✅ Full pipeline, proper DAX generation |
| DAX executeQueries via `/semanticModels/{id}/executeQueries` | ❌ 404 EntityNotFound (Fabric API) |
| DAX executeQueries via Power BI API `/datasets/{id}/executeQueries` | ✅ Works |
| `requests.post()` with `allow_redirects=True` (default) | ❌ Location header redirect hangs on SSL read |
| `requests.post()` with `allow_redirects=False` | ✅ Returns 202 properly, poll via `x-ms-operation-id` |
| `RefreshType=Full` after relationship change on DirectLake | ❌ May fail if source schema changed |
| `RefreshType=Calculate` after relationship change on DirectLake | ✅ Sufficient for relationship metadata hydration |
| Hidden columns in Verified Answers | ❌ Silently ignored — DAX tool can't resolve hidden column references |
| Descriptions via TMDL `///` doc comments | ✅ Extracted by NL2DAX for disambiguation |
| `.create-merge table` (idempotent KQL) | ✅ Creates if new, merges if exists |
| `.create table` (non-idempotent KQL) | ❌ Fails if table already exists |
| Lakehouse with `enableSchemas: true` | ✅ Multi-schema (bronze/silver/gold) |
| Changing `enableSchemas` after creation | ❌ Cannot be changed — must recreate |
| Warehouse `ALTER TABLE DROP COLUMN` | ❌ Not supported — use CTAS + RENAME |
| Warehouse `MERGE` statement | ⚠️ Preview — use DELETE + INSERT pattern |
| Warehouse write-write on same table | ❌ Conflicts at TABLE level (not row) |
| CTAS for large table rebuilds | ✅ Parallel, avoids locks |
| KQL `has` for text search | ✅ Uses term index — fast |
| KQL `contains` for text search | ⚠️ Full scan — slow on large tables |
| `az rest` without `--resource` flag | ❌ Wrong token audience → 401 |
| `az rest` with `--resource` flag | ✅ Correct token for target API |
| KQL pipes in `az rest` inline body | ❌ Shell interprets `\|` — use temp file |
| OneLake shortcuts for cross-workspace | ✅ Requires Workspace Identity |
| Descriptions via TMDL `///` doc comments | ✅ Extracted by NL2DAX for disambiguation |
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

### 10. ⚠️ PBIR Folder Format Renders Blank — **SOLVED 2026-06-13**
- **Symptom**: Report created, `getDefinition` returns all parts, but **BLANK** in portal
  (or freezes forever on *"Loading your report…"* with an HTTP 405 access-request)
- **Cause**: *not* the format. Four specific metadata defects:
  - `version.json` set to `4.0.0` instead of **`2.0.0`**
  - `report.json` missing `reportSource` / `settings` / `objects`
  - `baseTheme` pointing at a custom name instead of a real built-in (e.g. `CY26SU05`) with its theme json
  - `visualContainer` schema `2.5.0` instead of **`2.10.0`**
- **Fix**: apply the four rules above — see `Fabric-Brain/agents/report-builder-agent/known_issues.md`
  **issue 19** for the full diagnosis procedure (`getDefinition` on a working QuickCreate report and diff).
- **Historical note**: this entry used to read *"use Legacy PBIX EXCLUSIVELY"*. That prohibition
  outlived the bug and spread to ~11 files. PBIR is the default for new reports; Legacy PBIX
  remains valid for maintaining reports already shipped in it.

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

---

## Warehouse & SQL Issues

> Source: [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric)

### 31. ⚠️ Write-Write Conflicts at TABLE Level
- **Symptom**: Concurrent UPDATE/INSERT on the same Warehouse table → one transaction fails
- **Cause**: Fabric Warehouse snapshot isolation detects conflicts at the TABLE level (not row/page). Even if two transactions touch different rows, they conflict.
- **Fix**: Serialize writes (pipeline sequencing), use CTAS + RENAME instead of UPDATE, or partition work across different tables.

### 32. ALTER TABLE Cannot DROP or ALTER Columns
- **Symptom**: `ALTER TABLE ... DROP COLUMN` or `ALTER COLUMN` fails
- **Cause**: Fabric Warehouse does not support column drops or type changes via ALTER
- **Fix**: Use CTAS to create a new table without the column, then `RENAME OBJECT`.

### 33. No Cursors in Fabric Warehouse
- **Symptom**: `DECLARE CURSOR` fails
- **Fix**: Replace with set-based operations — CTEs, window functions, or staged temp tables.

### 34. MERGE Statement Is in Preview
- **Symptom**: `MERGE` may not be available or may behave unexpectedly
- **Fix**: Use DELETE + INSERT pattern for upserts until MERGE is GA.

### 35. No Temp Tables (#tables) in Warehouse
- **Symptom**: `CREATE TABLE #temp` fails
- **Fix**: Use CTEs or create permanent staging tables, then drop them after use.

---

## Spark & Lakehouse Issues

### 36. ⚠️ `enableSchemas` Cannot Be Changed After Lakehouse Creation
- **Symptom**: Need multi-schema (bronze/silver/gold) but Lakehouse was created without it
- **Cause**: The `enableSchemas` flag in `lakehouse.metadata.json` is set-once at creation time
- **Fix**: Delete and recreate the Lakehouse with `"enableSchemas": true` in the definition.

### 37. Delta Table Names Are Lowercased
- **Symptom**: `saveAsTable("MyTable")` creates table named `mytable`
- **Fix**: Always use lowercase table names in code. Reference as lowercase in downstream models.

### 38. Starter Pool OOM on Large Datasets
- **Symptom**: Notebook fails with OutOfMemoryError on the Starter Pool
- **Fix**: Configure a Workspace Pool with more memory, or use Custom Pool for specific notebooks.

---

## Eventhouse / KQL Issues

### 39. `.create table` Fails If Table Already Exists
- **Symptom**: Repeated deployment script fails on table creation
- **Fix**: Always use `.create-merge table` (idempotent).

### 40. Inline Ingestion Limit ~64 KB
- **Symptom**: Large `.ingest inline` commands fail or are truncated
- **Fix**: Use batch size of ~50 rows per inline command, or switch to storage ingestion for large datasets.

### 41. `contains` Is Extremely Slow on Large Tables
- **Symptom**: KQL query with `contains` takes minutes
- **Fix**: Use `has` (term index, much faster) instead. Only use `contains` when you need substring matching.

### 42. External Table Queries Are Slower Than Native
- **Symptom**: `external_table('X')` queries lag compared to direct table queries
- **Fix**: Use external tables for cross-engine joins and occasional lookups, not for dashboards or frequent queries.

---

## API / CLI Issues

### 43. `az rest --resource` Required for Fabric
- **Symptom**: `az rest` returns 401 Unauthorized
- **Cause**: Without `--resource`, `az rest` uses wrong token audience
- **Fix**: Always use `--resource "https://api.fabric.microsoft.com"` (or the correct audience for the target API).

### 44. KQL Pipes Break `az rest` Inline Body
- **Symptom**: `az rest --body '{"csl":"T | count"}'` fails or misparses
- **Cause**: Shell interprets `|` as pipe operator
- **Fix**: Write the JSON body to a temp file and use `--body @/tmp/q.json`.

---

## Public Safety / Publication

### 45. A Scanner That CI Never Runs Protects Nothing
- **Symptom**: An external audit found a customer name, a real SQL analytics
  endpoint, a personal name and nine personal-prefix workspace names in the
  tracked tree — after 73 commits — even though this repo already shipped
  `PUBLIC_SAFETY.md`, `Meta-Brain/tools/scan_public_safety.py` and
  `Meta-Brain/tests/test_public_safety.py`.
- **Cause**: Two independent failures, and both were needed.
  1. **No `.github/workflows/`** — the scanner and the test suite were never
     executed by anything except a human remembering to type the command.
  2. **The rules did not cover these classes** — the scanner looked for keys,
     tokens, tenant domains, home paths and GUIDs. A customer name, an owner's
     initials and a Fabric SQL endpoint hostname were simply not patterns it
     knew, so it reported `clean` on a leaking tree. That "clean" is worse than
     no scanner: it is a false assurance.
- **Fix**: `.github/workflows/no-client-leak.yml` (same shape as the sibling
  demo repos) runs the scanner **and** pytest on every push and PR, plus a guard
  that fails if any `.pptx` is tracked. Rules added: `client-name`,
  `client-acronym`, `personal-workspace-prefix`, `fabric-sql-endpoint`, and an
  optional repo-level `.publicsafety-deny`.
- **Lesson**: When a leak survives, ask two questions — *would the tool have
  caught it?* and *would anything have run the tool?* Fixing only one of them
  leaves the same hole.

### 46. A Committed `.pptx` Leaks Tenant GUIDs Even When Encrypted
- **Symptom**: `Fabric-Brain/agents/migration-bo-agent/BO_to_Fabric_Migration.pptx`
  started with `D0 CF 11 E0` (OLE compound file) instead of `50 4B` (OOXML zip):
  the deck had been opened in a rights-protected tenant and saved back as a
  MIP/IRM container.
- **Cause**: The *content* is encrypted and unreadable outside the tenant, but
  the rights-management **envelope is not** — it carries the licensing GUIDs,
  including the corporate tenant.
- **Fix**: `git rm --cached` the deck (`.gitignore` already had `*.pptx`),
  regenerate it locally with `python generate_pptx.py`, and let CI fail if a
  deck is ever tracked again. Ship the generator, never the binary.

### 47. A Scanner That Hardcodes the Names It Forbids Is the Leak

- **Symptom**: the public-safety tool and its tests are clean-looking Python,
  the working tree scans green — and the repo still publishes the customer
  list, because it sits in `CLIENT_NAMES` and in the detection fixtures.
- **Cause**: the obvious way to test "this name must not appear" is to write
  the name down. A sibling repo shipped its whole client portfolio that way,
  inside the very tool meant to catch it.
- **Fix**: the tool holds generic phrases only. Real terms arrive at run time
  via the `CLIENT_DENYLIST` env var (a repository secret in CI) or the
  gitignored `.publicsafety-deny`. Detection tests use **fabricated** values
  of the right shape and exercise the *mechanism* (see
  `test_denylist_adds_repo_specific_terms`); `test_tool_hardcodes_no_customer_name`
  keeps the tool honest.
- **Corollary**: judge the branch, not the working tree. A committed value is
  permanent on a public repo — `git push --force` does not remove it, the old
  SHA still resolves. Before handing work over:
  `git grep -niE "<terms>" \02e4baf2aa206b6f43f0c394a98fb43b0077b1f3 4812d4c0636c233b89f85e09f0879eb25c13281e e392bc680c45cebb624a6da823e6f4b52e1fd8f7 ea81c73925b128ddddd3fc6aec7591817746d285 12d711166ca874a204d8f780ebd0d028d48b445f 775247163369a09f028c8a0a02a64bfa25b1b6e0` must be empty.

### 48. A Diagram Export Is Source Code, and It Names the Workspace Twice

- **Symptom**: a leak guard failed a commit on `docs/architecture.excalidraw`,
  lines 198 and 204 — a Fabric workspace labelled with the author's initials
  (`XX - <Project>`), drawn weeks earlier and never re-read since.
- **Cause**: an `.excalidraw` — like most design-tool saves — is **JSON, not an
  image**. It is perfectly scannable, but it *reads* as an asset, so it drops out
  of human review by habit while preserving every display name ever typed onto
  the canvas.
- **Fix**: rename inside the file, not around it. Excalidraw stores each label
  **twice**, as `"text"` and as `"originalText"`, so a single-occurrence replace
  leaves the name in the second field and the guard fails again on the next line.
  Replace all occurrences, then re-parse the JSON to prove the file still loads.
- **Corollary**: the `personal-workspace-prefix` shape rule worked exactly as
  designed and caught this at commit time — the lesson is not about the rule but
  about **which file classes get read by a human**. Treat every text-serialised
  design artifact as source: `.excalidraw`, `.drawio`, `.puml`, and any exported
  `.svg` carrying `<text>` elements.

---

## Brain Workflow Issues

### 49. An IDE Auto-Commit Published Brain Edits Before the Test Gate Ran

- **Symptom**: mid-write into the brain, `git status --short` returned nothing and
  `git diff --stat` was empty, while the edited content was demonstrably present in
  the working file. `git log` showed a commit that no one in the session had made:
  `Save uncommitted changes`. `git rev-list --left-right --count origin/main...main`
  returned `0 0` — it had also already been **pushed**.
- **Cause**: an editor/agent-host background task periodically commits and pushes the
  whole working tree. It is not aware of the `brain-learn` contract, so it stages
  everything (not named files), and it fires **before** the mandatory test gate rather
  than after it. Evidence that it is recurrent, not a one-off: two commits with the
  identical generated message in the same history.
- **Fix**: after editing and **before** narrating what you did, re-read the actual git
  state instead of assuming your edits are still local — an empty `git diff` means
  *already committed*, not *edit failed*. Then run the gate anyway: the suite and the
  publication scanner still tell you whether what shipped is sound, and a green result
  on an already-pushed tree is exactly as informative. If it is red, the fix is a new
  commit forward, never a rewrite.
- **Corollary**: do **not** `--amend` or force-push to repair the message once the
  commit is on `origin` — a shared brain is not private history. Recover the lost *why*
  in content instead: record the finding, and name the commit hash that carries it, so
  the meaningless message stops mattering. Here `10cf2de` is the commit that introduced
  Pattern F in `Foundry-Brain/orchestration_patterns.md`.
- **Corollary**: an auto-committer silently voids two of `brain-learn`'s three
  guarantees — named-file staging and no-push-on-red. Only append-only survives it,
  because that is a property of the edit rather than of the commit. Design brain writes
  so the *edit itself* is always safe to publish unreviewed.

### 50. The Publication Scanner Reported a Repo's Own Leak Guard as 19 of 20 Leaks

- **Symptom**: `python Meta-Brain/tools/scan_public_safety.py <sibling-repo>` returned
  `20 BLOCK, 27 WARN` on a public demo repo. Nineteen of the twenty BLOCKs pointed at
  that repo's **own** detection fixtures — `tests/test_leak_guard.py`,
  `tests/test_supervisor.py`, `.github/scripts/check_client_leak.py` — matching on
  deliberately fabricated values of the blocked shapes
  (`<stub>.datawarehouse.fabric.microsoft.com`, `<x>.services.ai.azure.com`).
  The **one real finding** was the twentieth line.
- **Cause**: the tool has a `SELF` set that skips its own definitions, "because they
  contain every pattern by construction". But its docstring promises it is
  "deliberately usable **outside** Azure-Brain", and `SELF` is hardcoded to
  *Azure-Brain's* filenames. Any consuming repo responsible enough to own a leak guard
  therefore gets that guard's corpus reported as leaks. The per-repo escape hatch that
  did exist, `.publicsafety-allow`, allowlists **values** — useless here, because a
  fixture value is unique and random, and allowlisting it by value would also silence a
  genuine hit of the same value in shipped code.
- **Fix**: `.publicsafety-allow` now also accepts `path:` entries, matched as globs
  against the repo-relative path, e.g. `path:tests/test_leak_guard.py`. Deliberately
  **not** a blanket `test_*.py` skip — a real GUID in a test file is still published —
  so the repo must name the files, each still carrying a reason.
- **Evidence**: same repo, same commit. Before: `20 BLOCK, 27 WARN`. After adding five
  `path:` lines: `1 BLOCK, 22 WARN`, the survivor being a genuine `client-acronym` hit
  in a shipped `theme/*.json` that had been invisible underneath the noise.
  `Meta-Brain/tests/test_public_safety.py` gained
  `test_path_exclusion_is_scoped_to_the_file`, which asserts both halves: the fixture is
  exempt **and** the identical value in shipped code is still reported.
- **Lesson**: `PUBLIC_SAFETY.md` already stated the principle — *"false positives are
  bugs in the scanner, not facts of life... a scanner that is always red is one nobody
  reads"*. The brain held the rule and the tool still violated it, because the rule was
  only ever tested against **this** repo, where `SELF` happens to be sufficient. A guard
  verified solely on its home repo is unverified for its documented use.
- **Corollary**: this is the same defect class as `agent_principles.md` §3b, seen from
  the other side. There, a correction was *present but read too late* to change
  behaviour; here, a finding is *present but buried* at 95 % noise. In both cases the
  information exists and still fails to act. Signal that arrives late and signal that
  arrives drowned are the same bug.
- **Corollary**: writing this very entry tripped the scanner — quoting the two fixture
  hostnames verbatim produced `2 BLOCK` on `known_issues.md` and failed the gate, which
  is the tool behaving correctly. It is also the clearest argument for path-scoping: the
  *values* must stay redacted even inside a war story, while the *file* that legitimately
  contains them is exempted by name. Redact by value, exempt by path.

### 51. A Second, Stale Clone of the Brain Served a Rule That Had Been Superseded Five Weeks Earlier

- **Symptom**: asked to check a Fabric demo repo against the brain's repository-layout rule,
  the agent read `Meta-Brain/agents/project-presentation-agent/repo_structure.md`, found the
  flat `src/deploy_*.py` Fabric layout, and reported the repo **already compliant** —
  recommending only cosmetic additions (per-folder READMEs). The by-workload layout
  (`fabric/lakehouse/`, `fabric/ontology/`, `fabric/powerbi/`, `design/`) that had replaced it
  as the default was never seen, so the actual restructuring gap was reported as a non-issue.
- **Cause**: two clones of `Statyx/Azure-Brain` exist on the machine. A filesystem search for
  the brain resolved to the non-canonical one. Nothing about it looked wrong — it had the right
  remote, was on `main`, and had a clean working tree — but its HEAD was five weeks old. Its
  `repo_structure.md` was 5,882 bytes and contained only the flat layout; the canonical clone's
  was 15,475 bytes and leads with *"Microsoft Fabric Project Layout — deployment code grouped
  by workload"*, demoting the flat variant to a *"single workload only"* fallback.
- **Fix**: `git pull --ff-only` in the stale clone; both files then hash identically. The
  durable rule: **fast-forward a brain clone before reading a rule out of it.** A clean tree on
  `main` says nothing about freshness — only the commit date does. When two paths can both
  answer "where is the brain", verify which one, do not let a search decide.
- **Evidence**: stale clone HEAD `74f518b` (2026-07-30), `repo_structure.md` 5,882 bytes, last
  written 2026-04-01; canonical clone 15,475 bytes, last written 2026-08-27, whose header
  records *"adopted 2026-08-27 from the public repo `EtienneSIG/Fabric_Fraud_analysis`"*. After
  `git pull --ff-only`, stale clone HEAD `73d8459` (2026-09-03) and SHA-256 of both copies of
  `repo_structure.md` agree (`77F7CCF076E07DD1…`).
- **Lesson**: a rule in this brain is a *versioned* artifact, so reading it from an arbitrary
  path is reading an unknown version of it. `skills/brain-learn` already ranks the canonical
  path first and pulls before writing — but that discipline exists only on the **write** side.
  Every agent that *reads* the brain inherits the same hazard with none of the guard.
- **Corollary**: same defect class as #50, third variant. There a correction arrived too late
  (`agent_principles.md` §3b), or arrived drowned at 95 % noise. Here it was correct, committed
  and pushed on time — and still invisible, because the reader was looking at a different copy
  of the file. Superseding a rule in git does not supersede it on disk.



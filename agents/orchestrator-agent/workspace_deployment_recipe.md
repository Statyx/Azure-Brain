# Workspace Deployment Recipe — Proven Pattern

## Overview

Battle-tested pattern for deploying a complete Fabric workspace from scratch via Python + REST API.
Used successfully on:
- **CDR - Fabric RTI Demo** (IoT sensor monitoring, Eventhouse + Lakehouse)
- **CDR - Financial Platform** (CCE validation, Lakehouse-only)

## Deployment Order

Each step is a separate `deploy_*.py` script. All idempotent via `state.json`.

```
1. generate_data.py          → Create synthetic CSV data locally
2. deploy_workspace.py       → Create workspace on Fabric capacity
3. deploy_lakehouse.py       → Create Lakehouse + upload CSVs via OneLake DFS API
4. deploy_setup_notebook.py  → Deploy notebook (CSV→Delta) + RUN it via Jobs API
5. deploy_semantic_model.py  → Deploy Direct Lake model (AFTER Delta tables exist)
6. deploy_report.py          → Deploy Power BI report (legacy PBIX format)
7. deploy_data_agent.py      → Deploy Data Agent with instructions + fewshots
8. (optional) deploy_eventhouse.py     → For RTI/streaming scenarios
9. (optional) deploy_kql_dashboard.py  → KQL Dashboard for real-time data
```

**CRITICAL ORDER**: Step 4 (notebook → Delta tables) MUST complete before step 5 (semantic model).
Direct Lake mode requires Delta tables to exist. Deploying the model before the notebook runs
causes: `"Direct Lake mode requires a Direct Lake data source"`. The notebook converts CSVs to
Delta tables and must fully execute (Spark cold start ~60-90s) before the model can bind.

## Shared Infrastructure

### helpers.py (copy from RTI Demo)
```python
load_config()           # config.yaml → dict
load_state() / save_state()  # state.json persistence
get_fabric_token()      # az account get-access-token
fabric_headers(token)   # Authorization + Content-Type
create_fabric_item()    # POST /items + async polling
find_item()             # Search by name+type
poll_operation()        # LRO polling loop
b64encode_json()        # Base64 for definition parts
```

### notebook_utils.py (copy from RTI Demo)
```python
ipynb_to_fabric_py()    # Convert .ipynb → Fabric .py format
create_notebook()       # POST /items with notebook-content.py
push_notebook()         # updateDefinition
run_notebook()          # POST /items/{id}/jobs/instances?jobType=RunNotebook
```

### config.yaml
All configuration in one file: workspace name, capacity ID, item names, data schemas, parameters.

### state.json
Auto-populated with IDs as items are created. Enables idempotency — re-run any step safely.

## Critical Patterns

### 1. OneLake File Upload (DFS API)
```python
# Path uses GUID IDs, NOT display names
path = f"{workspace_id}/{lakehouse_id}/Files/{filename}"
# 3-step: PUT create → PATCH append → PATCH flush
requests.put(f"{base}/{path}?resource=file")
requests.patch(f"{base}/{path}?action=append&position=0", data=content)
requests.patch(f"{base}/{path}?action=flush&position={len(content)}")
```

### 2. Direct Lake Semantic Model
```python
# MUST have DatabaseQuery expression pointing to Lakehouse SQL endpoint
# Get SQL endpoint: GET /lakehouses/{id} → .properties.sqlEndpointProperties.connectionString
expressions = [{
    "name": "DatabaseQuery", "kind": "m",
    "expression": [
        "let",
        f'    database = Sql.Database("{sql_endpoint}", "{lakehouse_name}")',
        "in", "    database"
    ]
}]
# Partitions reference the expression
partition = {
    "name": table_name, "mode": "directLake",
    "source": {"type": "entity", "entityName": table_name,
               "expressionSource": "DatabaseQuery"}
}
```
**CRITICAL**: Direct Lake REQUIRES Delta tables. CSVs alone fail with "Direct Lake mode requires a Direct Lake data source". Must run a Spark notebook to convert CSVs → Delta BEFORE deploying the model.

### 3. Notebook Deployment + Execution
```python
# Format: always .py (never ipynb)
# Binding: embed lakehouse_id in METADATA section
# Run: POST /items/{id}/jobs/instances?jobType=RunNotebook
# Cold start: ~60-90s before Spark starts executing
```

### 4. Power BI Report (Legacy PBIX Only)
```python
# Three parts: report.json + definition.pbir + BaseTheme
# definition.pbir uses V2 schema with connectionString
# NEVER use PBIR folder format (renders blank)
# Every data visual MUST have prototypeQuery (no error, just blank)
```

### 5. Data Agent
```python
# 8 definition parts: data_agent.json + stage_config (draft+published)
#   + datasource (draft+published) + fewshots (draft+published) + publish_info
# MUST publish (draft-only agents invisible in portal)
# MUST include "ALWAYS query the semantic model" in instructions
# Thread management: DELETE thread before each question (prevents context overflow)
```

## File Structure Template
```
project/
├── data/raw/              ← Generated CSV files
├── notebooks/             ← .ipynb source files
└── src/
    ├── config.yaml        ← All configuration
    ├── state.json         ← Auto-populated deployment state
    ├── helpers.py         ← Shared utilities (copy from RTI Demo)
    ├── notebook_utils.py  ← Notebook deploy/run (copy from RTI Demo)
    ├── generate_data.py   ← Synthetic data generator
    ├── deploy_all.py      ← Master orchestrator
    ├── deploy_workspace.py
    ├── deploy_lakehouse.py
    ├── deploy_setup_notebook.py
    ├── deploy_semantic_model.py
    ├── deploy_report.py
    └── deploy_data_agent.py
```

## Known Issues & Workarounds

| Issue | Fix |
|-------|-----|
| `Sql.Database(null, null)` → Direct Lake error | Use actual SQL endpoint from Lakehouse properties |
| OneLake path with display name → 400 | Use GUID IDs for both workspace and lakehouse |
| Partition `"type": "none"` → no data | Use `"type": "entity"` with `expressionSource` for Direct Lake |
| Notebook `format: ipynb` → silent job failure | Always use .py format via `notebook_utils` |
| Report PBIR format → renders blank | Always use legacy PBIX (report.json + sections) |
| Data Agent draft-only → invisible | Include `published/` parts + `publish_info.json` |
| Spark notebook cold start → 60-90s | Normal — poll until Completed |

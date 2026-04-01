# orchestrator-agent / templates

Ready-to-use code templates for Fabric orchestration. Copy, customize the `CONFIG` / `parameters` section, and deploy.

---

## Template Index

| File | Type | Purpose | Complexity |
|------|------|---------|------------|
| `pipeline_ingest_transform.json` | Pipeline JSON | Minimal 2-activity pipeline (Wait → Notebook) | ⭐ Starter |
| `pipeline_bronze_silver_gold.json` | Pipeline JSON | Production 6-activity pipeline (ForEach Bronze → Silver → Gold → Refresh + failure notification) | ⭐⭐⭐ Production |
| `notebook_csv_to_delta.py` | Spark Notebook | Auto-discover CSV subfolders → write Delta tables | ⭐⭐ Standard |
| `orchestrate_ingestion.py` | Python Script | End-to-end: auth → OneLake upload → pipeline run → poll | ⭐⭐ Standard |

---

## How to Use

### Pipeline JSON templates

**Option A — REST API** (see `../pipelines.md`):
```python
import json, base64, requests

with open("templates/pipeline_bronze_silver_gold.json") as f:
    definition = json.load(f)

# Customize parameters
definition["properties"]["parameters"]["workspace_id"]["defaultValue"] = "your-ws-id"
definition["properties"]["parameters"]["nb_bronze_id"]["defaultValue"] = "your-nb-id"
# ... set other defaults

payload = {
    "definition": {
        "parts": [{
            "path": "pipeline-content.json",
            "payload": base64.b64encode(json.dumps(definition).encode()).decode(),
            "payloadType": "InlineBase64"
        }]
    }
}

resp = requests.post(
    f"{API}/workspaces/{WS_ID}/dataPipelines",
    headers=headers,
    json={"displayName": "PL_MyProject_Orchestration", **payload}
)
```

**Option B — fabric-cli** (see `../fabric-cli-agent/`):
```bash
fab import ws.Workspace/PL_MyOrch.DataPipeline -i templates/pipeline_bronze_silver_gold.json
```

### Notebook template

1. Read the `.py` file
2. Base64-encode the content
3. Upload via Notebook REST API with path `notebook-content.py` (never `.ipynb`)
4. See `../notebooks.md` for the full protocol

### Python script

```bash
# Prerequisites
pip install requests

# Configure
# Edit the CONFIG section at the top of orchestrate_ingestion.py
# Set WS_ID, LH_ID, NB_ID, PL_ID, LOCAL_DATA

# Run
python orchestrate_ingestion.py
```

---

## Customization Checklist

### `pipeline_bronze_silver_gold.json`

| Parameter | What to set | Where to find it |
|-----------|------------|-----------------|
| `workspace_id` | Your workspace GUID | `../../resource_ids.md` or Fabric portal URL |
| `lakehouse_id` | Target Lakehouse GUID | `fab ls ws.Workspace` → find `.Lakehouse` |
| `nb_bronze_id` | Bronze notebook GUID | Create from `notebook_csv_to_delta.py` template |
| `nb_silver_id` | Silver notebook GUID | Your Silver transform notebook |
| `nb_gold_id` | Gold notebook GUID | Your Gold aggregation notebook |
| `model_id` | Semantic model GUID (optional) | Leave empty to skip refresh |
| `mode` | `"full"` or `"incremental"` | Controls overwrite vs append |
| `tables` | Array of `{name, source}` objects | One entry per table to load |
| `On_Failure_Notify.url` | Your webhook URL | Teams / Slack incoming webhook |

### `pipeline_ingest_transform.json`

| Parameter | What to set |
|-----------|------------|
| `source_folder` | Subfolder in `Files/` containing CSVs |
| `notebook_id` | GUID of notebook to run after wait |

### `orchestrate_ingestion.py`

| Variable | What to set |
|----------|------------|
| `WS_ID` | Workspace GUID |
| `LH_ID` | Lakehouse GUID |
| `NB_ID` | Notebook GUID (for CSV→Delta) |
| `PL_ID` | Pipeline GUID (or `None` to create one) |
| `LOCAL_DATA` | Local folder path with CSV files |

---

## Pipeline Architecture

```
pipeline_bronze_silver_gold.json

  Set_Start_Time
       │
       ▼
  Load_Bronze_Tables (ForEach, parallel)
  ┌────┬────┬────┐
  │ T1 │ T2 │ T3 │  ← one SparkNotebook per table
  └────┴────┴────┘
       │ all succeed              │ any fail
       ▼                          ▼
  Transform_Silver           On_Failure_Notify
       │                     (webhook → Teams/Slack)
       ▼
  Build_Gold
       │
       ▼
  Check_Gold_Success (IfCondition)
       │
       ├─ model_id provided → Refresh_Semantic_Model
       └─ no model_id → skip
```

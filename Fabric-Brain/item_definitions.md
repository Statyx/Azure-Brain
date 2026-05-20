# Item Definitions — Definition Envelope Reference

> Source: [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) — ITEM-DEFINITIONS-CORE.md

## Definition Envelope Structure

Every Fabric item definition follows this envelope:

```json
{
  "definition": {
    "format": "<optional format hint>",
    "parts": [
      {
        "path": "<file path within definition>",
        "payload": "<base64-encoded content>",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

- **`format`**: Optional. Only needed for some item types (e.g., `"TMDL"` for SemanticModel)
- **`parts`**: Array of files that make up the item definition
- **`payload`**: Always base64-encoded
- **`payloadType`**: Always `"InlineBase64"`

### Encode / Decode Helpers

```python
import base64, json

def encode_part(path: str, content: str) -> dict:
    return {
        "path": path,
        "payload": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "payloadType": "InlineBase64"
    }

def decode_part(part: dict) -> str:
    return base64.b64decode(part["payload"]).decode("utf-8")
```

---

## Per-Item-Type Definition Parts

### Notebook

| Part Path | Description |
|-----------|-------------|
| `notebook-content.py` | Fabric's proprietary `.py` format with cell markers |
| `.platform` | Platform metadata (optional on create) |

**Format**: Do NOT set `"format": "ipynb"` — causes `InvalidNotebookContent` error.

Cell markers in `.py` format:
```python
# Fabric notebook source

# METADATA ********************
# META { "kernel_info": {"name": "synapse_pyspark"} }

# CELL ********************
# Code cell content here

# MARKDOWN ********************
# # Markdown title
```

### Data Pipeline

| Part Path | Description |
|-----------|-------------|
| `pipeline-content.json` | Pipeline definition with activities |

Activity types include: `Copy`, `ForEach`, `IfCondition`, `SetVariable`, `Wait`, `WebActivity`, `SparkNotebook`, `SparkJob`, `DataflowGen2`, `Script`, `Lookup`, `GetMetadata`, `Filter`, `AppendVariable`, `Switch`, `Until`, `ExecutePipeline`, `TridentNotebook`, `FailActivity`, `StoredProcedure`.

### Semantic Model

**TMSL format (default):**

| Part Path | Description |
|-----------|-------------|
| `definition.pbism` | Connection metadata — ONLY `{"version": "1.0"}` |
| `model.bim` | TMSL model (tables, columns, measures, relationships) |

**TMDL format** (request with `?format=TMDL`):

| Part Path | Description |
|-----------|-------------|
| `definition.pbism` | Same as above |
| `definition/model.tmdl` | Model-level properties |
| `definition/tables/{table}.tmdl` | One file per table (columns, measures, partitions) |
| `definition/relationships.tmdl` | All relationships |
| `definition/expressions.tmdl` | M expressions (data source connections) |
| `definition/roles/{role}.tmdl` | RLS roles |
| `definition/cultures/{culture}.tmdl` | Translations |

### Report

**PBIR-Legacy format** (the only format that renders — see `report_format.md`):

| Part Path | Description |
|-----------|-------------|
| `definition.pbir` | Connection to semantic model (V2 XMLA connection string) |
| `report.json` | Full report definition (pages, visuals, config) |
| `StaticResources/SharedResources/BaseThemes/{theme}.json` | Theme file |

**PBIR format** (accepted by API but does NOT render):

| Part Path | Description |
|-----------|-------------|
| `definition.pbir` | Connection metadata |
| `report.json` | Report-level config |
| `pages/{pageId}/page.json` | Per-page definition |
| `pages/{pageId}/visuals/{visualId}/visual.json` | Per-visual definition |

> ⚠️ **Always use PBIR-Legacy**. PBIR folder format is accepted by the API but renders blank.

### Lakehouse

| Part Path | Description |
|-----------|-------------|
| `lakehouse.metadata.json` | `{"enableSchemas": true/false}` |
| `shortcuts.metadata.json` | Shortcut definitions (optional) |

### Eventhouse

| Part Path | Description |
|-----------|-------------|
| `EventhouseProperties.json` | Eventhouse properties |

### KQL Database

| Part Path | Description |
|-----------|-------------|
| `DatabaseProperties.json` | Database properties (`parentEventhouseItemId`) |
| `DatabaseSchema.kql` | Schema script (`.create-merge table` statements) |

### Spark Job Definition

| Part Path | Description |
|-----------|-------------|
| `SparkJobDefinitionV1.json` | Job definition (main file, args, Lakehouse ref) |

### Environment

| Part Path | Description |
|-----------|-------------|
| `environment.yml` | Conda-style dependency file |
| `Setting/Sparkcompute.yml` | Spark compute configuration |

### Variable Library

| Part Path | Description |
|-----------|-------------|
| `variables.json` | Variable definitions with types and values |

Variable types: `String`, `Integer`, `Boolean`, `Array`, `Float`, `Pipeline`, `Spark`, `Double`.

> ⚠️ **Gotcha**: Pipeline activity parameter types differ from Variable Library types. `Float` in variables maps to `Float` in pipelines, but other mappings require care.

### KQL Dashboard

| Part Path | Description |
|-----------|-------------|
| `RealTimeDashboard.json` | Dashboard definition with tiles, data sources, parameters |

### KQL Queryset

| Part Path | Description |
|-----------|-------------|
| `RealTimeQueryset.json` | Saved KQL queries |

### Warehouse

| Part Path | Description |
|-----------|-------------|
| `warehouse.metadata.json` | Warehouse config |

---

## Common API Patterns

### Create Item with Definition
```python
body = {
    "displayName": "MyItem",
    "type": "Notebook",  # or SemanticModel, DataPipeline, etc.
    "definition": {
        "parts": [
            encode_part("notebook-content.py", notebook_content)
        ]
    }
}
resp = requests.post(f"{API}/workspaces/{ws_id}/items", headers=h, json=body, allow_redirects=False)
```

### Get Item Definition (Always Async)
```python
resp = requests.post(
    f"{API}/workspaces/{ws_id}/items/{item_id}/getDefinition",
    headers=h, allow_redirects=False
)
# Always returns 202 — poll operation, then GET /operations/{opId}/result
```

### Update Item Definition (Replace All Parts)
```python
resp = requests.post(
    f"{API}/workspaces/{ws_id}/items/{item_id}/updateDefinition",
    headers=h, json={"definition": {"parts": [...]}}, allow_redirects=False
)
# updateDefinition replaces the entire definition — you cannot patch individual parts
```

> **Rule**: `getDefinition` is **always** async (202). `updateDefinition` replaces ALL parts — always include every part file.

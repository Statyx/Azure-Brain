# Report Structure — Legacy PBIX Format

> **THE critical knowledge**: This file defines the only report format that works in Fabric.

---

## Format Choice: Legacy PBIX Only

| Format | Structure | API Accepts? | Renders? |
|--------|-----------|:---:|:---:|
| **PBIR Folder** | `definition/pages/{page}/visuals/{vis}/visual.json` | YES | **NO** (BLANK) |
| **Legacy PBIX** | `report.json` at root with `sections[].visualContainers[]` | YES | **YES** |

The API silently accepts PBIR with no error. The report item appears in the workspace.
But visuals are **completely blank** when opened. This was discovered after hours of debugging.

---

## Required Definition Parts

A working report needs these parts in the API payload:

| Part | Path | Required? | Notes |
|------|------|:---------:|-------|
| Report definition | `report.json` | **Yes** | The entire report in one file |
| Connection info | `definition.pbir` | **Yes** | Links report to semantic model |
| Base theme | `StaticResources/SharedResources/BaseThemes/CY26SU02.json` | Recommended | Without it, default theme is ugly |
| Custom resources | `StaticResources/RegisteredResources/{file}` | Optional | Logos, custom themes |
| Platform metadata | `.platform` | Auto-generated | Don't include manually |

### API Payload Structure
```json
{
  "definition": {
    "parts": [
      {"path": "report.json", "payload": "<base64>", "payloadType": "InlineBase64"},
      {"path": "definition.pbir", "payload": "<base64>", "payloadType": "InlineBase64"},
      {"path": "StaticResources/SharedResources/BaseThemes/CY26SU02.json", "payload": "<base64>", "payloadType": "InlineBase64"}
    ]
  }
}
```

---

## definition.pbir

### V2 Schema (ALWAYS USE THIS)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {
    "byConnection": {
      "connectionString": "Data Source=\"powerbi://api.powerbi.com/v1.0/myorg/CDR - Demo Finance Fabric\";initial catalog=SM_Finance;integrated security=ClaimsToken;semanticmodelid=236080b8-3bea-4c14-86df-d1f9a14ac7a8"
    }
  }
}
```

### Connection String Template
```
Data Source="powerbi://api.powerbi.com/v1.0/myorg/{WORKSPACE_NAME}";initial catalog={MODEL_NAME};integrated security=ClaimsToken;semanticmodelid={MODEL_GUID}
```

### Shorthand Alternative
```json
"connectionString": "semanticmodelid=236080b8-3bea-4c14-86df-d1f9a14ac7a8"
```
Works but the full XMLA string is preferred (matches Fabric Copilot's own output).

### V1 Schema (NEVER USE)
The `1.0.0` schema requires `pbiServiceModelId`, `pbiModelVirtualServerName`, etc. — nearly impossible to get right. Always use V2.

---

## report.json — Top-Level Structure

```json
{
  "config": "<STRINGIFIED JSON>",
  "layoutOptimization": 0,
  "resourcePackages": [
    {
      "resourcePackage": {
        "name": "SharedResources",
        "type": 2,
        "items": [
          {
            "type": 202,
            "path": "BaseThemes/CY26SU02.json",
            "name": "CY26SU02"
          }
        ],
        "disabled": false
      }
    }
  ],
  "sections": [],
  "theme": "CY26SU02"
}
```

### Critical Fields

| Field | Type | Value | Notes |
|-------|------|-------|-------|
| `config` | string | Stringified JSON | Report-level config (see below) |
| `layoutOptimization` | integer | `0` | **REQUIRED** — without it, import fails |
| `sections` | array | Page objects | Each page is a section |
| `theme` | string | `"CY26SU02"` | Must match resourcePackages theme name |
| `resourcePackages` | array | Theme refs | Links to base theme file |

### Report Config (stringified into `config` field)

```json
{
  "version": "5.70",
  "themeCollection": {
    "baseTheme": {
      "name": "CY26SU02",
      "version": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
      "type": 2
    }
  },
  "activeSectionIndex": 0,
  "defaultDrillFilterOtherVisuals": true,
  "settings": {
    "useNewFilterPaneExperience": true,
    "allowChangeFilterTypes": true,
    "useStylableVisualContainerHeader": true,
    "exportDataMode": 1
  }
}
```

---

## Section (Page) Structure

```json
{
  "name": "PageInternalName",
  "displayName": "Page Display Name",
  "displayOption": 1,
  "width": 1280,
  "height": 720,
  "config": "{\"name\":\"PageInternalName\"}",
  "filters": "[]",
  "visualContainers": []
}
```

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Internal ID (no spaces, no special chars) |
| `displayName` | string | User-visible tab title |
| `displayOption` | integer | `1` = fit to page |
| `width` / `height` | integer | Standard: 1280 × 720 (16:9) |
| `config` | string | **Stringified** `{"name": "<name>"}` |
| `filters` | string | **Stringified** `[]` |
| `visualContainers` | array | Array of visual objects |

---

## Visual Container Structure

Each visual in `visualContainers[]`:

```json
{
  "x": 30.0,
  "y": 60.0,
  "z": 1,
  "width": 390.0,
  "height": 120.0,
  "config": "<STRINGIFIED JSON>",
  "filters": "[]"
}
```

**`config` is STRINGIFIED** — `json.dumps(config_dict)`, not an embedded object.

The config object inside follows this pattern:
```json
{
  "name": "unique_hex_id",
  "layouts": [{"id": 0, "position": {"x": 30, "y": 60, "z": 1, "width": 390, "height": 120}}],
  "singleVisual": {
    "visualType": "cardVisual",
    "projections": {},
    "prototypeQuery": {},
    "drillFilterOtherVisuals": true,
    "objects": {},
    "vcObjects": {}
  },
  "howCreated": "Copilot"
}
```

### Position Rules
- `x`, `y`, `z`, `width`, `height` must appear **both** at visual container level AND inside `layouts[0].position`
- `z` determines stacking order (higher = on top)
- Coordinates are in pixels relative to the 1280×720 canvas

---

## Python: Base64 Encoding

```python
import base64, json

def encode_part(obj) -> str:
    """Encode a Python dict/string to base64 for API payload."""
    if isinstance(obj, dict):
        content = json.dumps(obj, ensure_ascii=False)
    else:
        content = str(obj)
    return base64.b64encode(content.encode("utf-8")).decode("ascii")

# Example usage
report_b64 = encode_part(report_json_dict)
pbir_b64 = encode_part(definition_pbir_dict)
```

---

## Python: Stringifying Configs

```python
import json

def make_visual_container(x, y, z, w, h, config_dict):
    """Build a visual container with properly stringified config."""
    return {
        "x": float(x),
        "y": float(y),
        "z": z,
        "width": float(w),
        "height": float(h),
        "config": json.dumps(config_dict),
        "filters": "[]"
    }

def make_section(name, display_name, visual_containers):
    """Build a page section."""
    return {
        "name": name,
        "displayName": display_name,
        "displayOption": 1,
        "width": 1280,
        "height": 720,
        "config": json.dumps({"name": name}),
        "filters": "[]",
        "visualContainers": visual_containers
    }
```

---

## REST API: Create Report

```python
import requests, base64, json

API = "https://api.fabric.microsoft.com/v1"
WS_ID = "133c6c70-2e26-4d97-aac1-8ed423dbbf34"

body = {
    "displayName": "RPT_Finance_Dashboard",
    "definition": {
        "parts": [
            {"path": "report.json", "payload": report_b64, "payloadType": "InlineBase64"},
            {"path": "definition.pbir", "payload": pbir_b64, "payloadType": "InlineBase64"},
            {"path": "StaticResources/SharedResources/BaseThemes/CY26SU02.json",
             "payload": theme_b64, "payloadType": "InlineBase64"},
        ]
    }
}

resp = requests.post(f"{API}/workspaces/{WS_ID}/reports", headers=headers, json=body)

if resp.status_code == 202:
    op_id = resp.headers["x-ms-operation-id"]
    # Poll until Succeeded...
```

## REST API: Get Definition (for editing)

```python
# Step 1: Start async getDefinition
resp = requests.post(f"{API}/workspaces/{WS_ID}/reports/{REPORT_ID}/getDefinition", headers=headers)
op_id = resp.headers["x-ms-operation-id"]

# Step 2: Poll until done
# ... (see fabric_api.md for polling pattern)

# Step 3: Get result
result = requests.get(f"{API}/operations/{op_id}/result", headers=headers).json()

# Step 4: Decode report.json
for part in result["definition"]["parts"]:
    if part["path"] == "report.json":
        report_json = json.loads(base64.b64decode(part["payload"]).decode("utf-8"))
        break
```

## REST API: Update Definition

```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/reports/{REPORT_ID}/updateDefinition",
    headers=headers,
    json={"definition": {"parts": updated_parts}}
)
# updateDefinition replaces the ENTIRE definition — no partial patches
```

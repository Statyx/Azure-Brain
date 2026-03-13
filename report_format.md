# Report Format — Legacy PBIX (THE Critical Knowledge)

> **This is the single most important file in this brain.**
> Getting the report format wrong means visuals will never render,
> and the API will happily accept the broken definition without any error.

## The Two Formats

| Format | Structure | API Accepts? | Renders in Portal? |
|--------|-----------|:---:|:---:|
| **PBIR Folder** | `definition/pages/{page}/visuals/{vis}/visual.json` | YES | **NO** |
| **Legacy PBIX** | `report.json` at root with `sections[].visualContainers[]` | YES | **YES** |

**Always use the Legacy PBIX format.**

The PBIR folder format is a trap — the API accepts it, `getDefinition` returns all the parts,
the report item appears in the workspace, but the visuals are **blank** when you open it.
There is no error message. Hours of debugging led to this discovery.

## Required Parts

A working report definition needs 3-4 parts:

| Part | Path | Required? |
|------|------|:---------:|
| Report definition | `report.json` | **Yes** |
| Connection info | `definition.pbir` | **Yes** |
| Base theme | `StaticResources/SharedResources/BaseThemes/CY26SU02.json` | Recommended |
| Platform metadata | `.platform` | Auto-generated |

## definition.pbir

Uses V2 schema with a full XMLA connection string:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {
    "byConnection": {
      "connectionString": "Data Source=\"powerbi://api.powerbi.com/v1.0/myorg/{WORKSPACE_NAME}\";initial catalog={MODEL_NAME};integrated security=ClaimsToken;semanticmodelid={MODEL_GUID}"
    }
  }
}
```

**V1 format pitfall**: The 1.0.0 schema requires `pbiServiceModelId`, `pbiModelVirtualServerName`,
etc. — these are nearly impossible to get right. Always use V2.

The shorthand `"connectionString": "semanticmodelid={guid}"` also works for V2 but the full
XMLA string is what Fabric's own Copilot-created reports use, so prefer the full form.

## report.json Structure

```json
{
  "config": "<STRINGIFIED JSON — report-level config>",
  "layoutOptimization": 0,
  "resourcePackages": [{ "resourcePackage": { "name": "SharedResources", "type": 2, "items": [{ "type": 202, "path": "BaseThemes/CY26SU02.json", "name": "CY26SU02" }], "disabled": false } }],
  "sections": [ /* pages */ ],
  "theme": "CY26SU02"
}
```

### Report Config (stringified)
```json
{
  "version": "5.70",
  "themeCollection": {
    "baseTheme": {
      "name": "CY26SU02",
      "version": { "visual": "2.6.0", "report": "3.1.0", "page": "2.3.0" },
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

### `layoutOptimization`

**REQUIRED**. Without it, report import fails.
- Legacy format: integer `0`
- PBIR format: string `"None"` (if you ever need it)

### Section (Page)
```json
{
  "name": "PageInternalName",
  "displayName": "Page Display Name",
  "displayOption": 1,
  "width": 1280,
  "height": 720,
  "config": "{\"name\":\"PageInternalName\"}",
  "filters": "[]",
  "visualContainers": [ /* visuals */ ]
}
```

Standard canvas: 1280 × 720 (16:9).

### Visual Container

Each visual is a `visualContainer` object in the `visualContainers` array:

```json
{
  "x": 30.0,
  "y": 60.0,
  "z": 1,
  "width": 390.0,
  "height": 120.0,
  "config": "<STRINGIFIED JSON — visual config>",
  "filters": "[]"
}
```

**config is STRINGIFIED** — this is critical. It's `json.dumps(config_dict)`, not an embedded object.

## Visual Config Structure

Every visual config follows this pattern:

```json
{
  "name": "unique_id_20hex",
  "layouts": [{ "id": 0, "position": { "x": 30, "y": 60, "z": 1, "width": 390, "height": 120 } }],
  "singleVisual": {
    "visualType": "cardVisual",
    "projections": { /* data bindings */ },
    "prototypeQuery": { /* required for data visuals */ },
    "drillFilterOtherVisuals": true,
    "objects": { /* visual-specific formatting */ },
    "vcObjects": { /* container-level styling */ }
  },
  "howCreated": "Copilot"
}
```

### Visual Types

| Visual | `visualType` value | Projection Buckets | Notes |
|--------|-------------------|-------------------|-------|
| KPI Card | `cardVisual` | `Data` | NOT `card` (deprecated) |
| Bar Chart | `clusteredBarChart` | `Category` + `Y` | Horizontal bars |
| Column Chart | `clusteredColumnChart` | `Category` + `Y` | Vertical bars |
| Line Chart | `lineChart` | `Category` + `Y` | |
| Donut | `donutChart` | `Category` + `Y` | |
| Text Label | `textbox` | none | No prototypeQuery needed |

**PITFALL**: Using `card` (old visual) instead of `cardVisual` (new visual) will cause rendering issues.

### Projections

Cards:
```json
"projections": {
  "Data": [{ "queryRef": "fact_general_ledger.Total Revenue" }]
}
```

Charts:
```json
"projections": {
  "Category": [{ "queryRef": "dim_cost_centers.region" }],
  "Y": [{ "queryRef": "fact_general_ledger.Total Revenue" }]
}
```

**PITFALL**: Cards use `Data` bucket (not `Values`).

## prototypeQuery — Required for All Data Visuals

Without `prototypeQuery`, visuals render as empty containers. No error, just blank.

```json
{
  "prototypeQuery": {
    "Version": 2,
    "From": [
      { "Name": "f", "Entity": "fact_general_ledger", "Type": 0 }
    ],
    "Select": [
      {
        "Measure": {
          "Expression": { "SourceRef": { "Source": "f" } },
          "Property": "Total Revenue"
        },
        "Name": "fact_general_ledger.Total Revenue",
        "NativeReferenceName": "Total Revenue"
      }
    ],
    "OrderBy": [
      {
        "Direction": 2,
        "Expression": {
          "Measure": {
            "Expression": { "SourceRef": { "Source": "f" } },
            "Property": "Total Revenue"
          }
        }
      }
    ]
  }
}
```

### From Clause
```json
{ "Name": "<alias>", "Entity": "<table_name>", "Type": 0 }
```
Alias is typically a single letter. `Type: 0` means table.

### Select — Measure
```json
{
  "Measure": {
    "Expression": { "SourceRef": { "Source": "<alias>" } },
    "Property": "<measure_name>"
  },
  "Name": "<table>.<measure>"
}
```

### Select — Column
```json
{
  "Column": {
    "Expression": { "SourceRef": { "Source": "<alias>" } },
    "Property": "<column_name>"
  },
  "Name": "<table>.<column>"
}
```

### OrderBy
```json
{
  "Direction": 2,
  "Expression": { "Measure": { "Expression": { "SourceRef": { "Source": "<alias>" } }, "Property": "<name>" } }
}
```
Direction 2 = Descending.

## Measure Names — Must Match Exactly

Measure names in `prototypeQuery`, `projections`, and `Select` must match the semantic model
**exactly** — including spaces, capitalization, and special characters.

| Model Definition | Visual Reference | Works? |
|:---:|:---:|:---:|
| `Total Revenue` | `Total Revenue` | YES |
| `Total Revenue` | `Total_Revenue` | **NO** |
| `Total Revenue` | `total revenue` | **NO** |
| `Gross Margin %` | `Gross Margin %` | YES |

Always verify measure names against `model.bim` or via DAX `EVALUATE` queries.

---

## Multi-Page Reports

### Adding Pages

Each page is a `section` in `sections[]`. Pages display as tabs.

```json
{
  "name": "PnLSection",
  "displayName": "P&L Analysis",
  "filters": "[]",
  "ordinal": 1,
  "visualContainers": [],
  "config": "{\"name\":\"PnLSection\",\"layouts\":[{\"id\":0,\"position\":{\"x\":0,\"y\":0,\"width\":1280,\"height\":720}}],\"singleVisualGroup\":null}",
  "displayOption": 1,
  "width": 1280,
  "height": 720
}
```

**Rules:**
- `name` must be unique, no spaces — matches `config.name` 
- `ordinal` controls page order (0-based)
- `activeSectionIndex` in report config determines default page

### Multi-Measure Charts

To show multiple measures on one chart (e.g., Budget vs Actual):

```json
"projections": {
  "Category": [{"queryRef": "fact_budgets.period_month"}],
  "Y": [
    {"queryRef": "fact_budgets.Budget Amount"},
    {"queryRef": "fact_budgets.Actual Amount"}
  ]
}
```

Binding must list all measure indices:
```json
"Binding": {
  "Primary": {"Groupings": [{"Projections": [0]}]},
  "Values": [{"Projections": [1, 2]}],
  ...
}
```

For cross-table measures, include all tables in `From`:
```json
"From": [
  {"Name": "c", "Entity": "dim_cost_centers", "Type": 0},
  {"Name": "b", "Entity": "fact_budgets", "Type": 0},
  {"Name": "f", "Entity": "fact_forecasts", "Type": 0}
]
```

### Sidebar Navigation Pattern

Simulates tab navigation within each page using shapes + textboxes:
- Dark sidebar shape (140×720) at x=0
- Blue rounded rectangle behind active label
- Textbox labels: active = white bold, inactive = grey (#8899BB) normal
- Each page replicates the sidebar with different active state

### Generation Script

`temp/add_pages.py` — Python script that programmatically generates report pages.
Idempotent (safe to run multiple times). Matches the existing dark blue theme.

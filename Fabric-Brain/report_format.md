# Report Format — Legacy PBIX (maintenance reference)

> **Scope — read this first.**
> This file documents the **Legacy PBIX** format (`report.json` + `sections[].visualContainers[]`).
> It is **not** the default for new work.
>
> | Situation | Format | Source of truth |
> |---|---|---|
> | **New report** | **PBIR folder** | [`agents/report-builder-agent/instructions.md`](agents/report-builder-agent/instructions.md) — authoritative |
> | Maintaining a pre-v2.0 report already shipped in Legacy | Legacy PBIX | this file + [`agents/report-builder-agent/known_issues.legacy.md`](agents/report-builder-agent/known_issues.legacy.md) |
>
> Do not start a new report from this file.

## The Two Formats

| Format | Structure | API Accepts? | Renders in Portal? |
|--------|-----------|:---:|:---:|
| **PBIR Folder** | `definition/pages/{page}/visuals/{vis}/visual.json` | YES | **YES — once the v2.0 rules are followed** |
| **Legacy PBIX** | `report.json` at root with `sections[].visualContainers[]` | YES | **YES** |

### Historical note — why this file used to say "never PBIR"

PBIR reports really did render blank, and this file carried an absolute prohibition for it.
**That failure was diagnosed and fixed on 2026-06-13.** The cause was never the format itself:

- `version.json` must be `"2.0.0"` (**not** `4.0.0`)
- `report.json` must carry `reportSource` + `settings` + `objects`
- `baseTheme` must be a real built-in (e.g. `CY26SU05`) with its theme json — no custom-name
  `baseTheme`, no `customTheme` + `RegisteredResources`
- `visualContainer` schema must be `2.10.0` (not `2.5.0`)

Full detail: `agents/report-builder-agent/known_issues.md` **issue 19**.

The prohibition outlived the bug it protected against and was propagated to a dozen files.
If you find a document still asserting *"PBIR renders blank"* or *"never PBIR"*, it is stale —
fix it, and keep `Meta-Brain/tests/test_consistency.py` green.

Both formats render. Legacy remains valid and is still maintained (see the persona / Template 8
notes of 2026-07-28) — it is simply no longer the default.

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

> **EXCEPTION — hiding the category label**: `cardVisual` **ignores** `categoryLabel show=false`, so the measure's (often English) label stays and gets **truncated** in short cards. When you want value-only cards with a custom title (e.g. a French label via `vcObjects.title`), use the CLASSIC `visualType: "card"` with `categoryLabels` (plural) `show=false`, value styled via `labels`, and projection bucket **`Values`**. cardVisual = modern look; classic `card` = reliable label control.

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

**PITFALL**: Cards use `Data` bucket (not `Values`). *(Classic `card` uses `Values` — see the label-hiding exception above.)*

### Visual gotchas (learned from deploys)

- **Textbox over a colored band (persona banner)**: a legacy `textbox` has an OPAQUE white background by default → white/light title becomes invisible **and** shows a vertical scrollbar. Fix: `vcObjects.background show=false` (transparent) + `border show=false` + textbox `z` ABOVE the band shape.
- **Textbox scrollbar**: appears when text height ≈ container. Fix: put title+subtitle in **ONE** textbox as 2 paragraphs with GENEROUS height (~58px), not two tight stacked textboxes (each adds its own scrollbar).
- **Table `CouldNotResolveSemanticQueryDefinition`** — *"two expressions in its select clause with identical native reference name"*: two columns share a property name (e.g. two `name` columns). Fix: make **`NativeReferenceName` UNIQUE** per column (pass a caption e.g. `Sponsor` / `Zone`); the `Name` (`{table}.{prop}`) is already unique.
- **Deploy LRO looks hung but isn't**: `poll_operation` sleeps silently up to 120s → a sync terminal backgrounds before the `✅`. Redirect deploy output to a file (`python -u deploy_report.py *> _out.txt`) and read it; `state.json` `report_id` is written only on success. After a redeploy, **fully reopen** the report (or a private window) to bust the Fabric render cache.

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

## Design Quality Checklist (pre-deploy)

Before deploying any report, verify:

1. **Chart labels**: Every axis/category uses a **human-readable** column (e.g., `description`, `name`),
   NEVER raw ID/code columns (e.g., `level1`, `id`, `code`). Codes render as meaningless numbers.
2. **Scatter plots**: Check for outliers that compress the rest of the data into a narrow band.
   Use description labels so outliers are identifiable.
3. **Slicers**: Each slicer has a visible title (e.g., "Pays", "Discipline") set in `vcObjects`.
4. **Card values**: `calloutValue` font not too large (max 27D to avoid clipping).
5. **prototypeQuery**: Every data visual has one (no error, just blank without it).
6. **Overlap check**: No visuals overlap each other (compare x/y/w/h coordinates).

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

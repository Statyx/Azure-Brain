# Report Structure — PBIR Folder Format

> Authoritative anatomy of a `<Report>.Report/` PBIR folder, the schema URLs each file references, and the exact payload shape for Fabric REST.

---

## Folder Layout

```
<Report>.Report/
├─ definition/
│  ├─ version.json                # PBIR format version (REQUIRED)
│  ├─ report.json                 # top-level report metadata + theme reference
│  ├─ pages/
│  │  ├─ pages.json               # ordered list of page folders + active page
│  │  └─ <pageId>/
│  │     ├─ page.json             # page-level config (size, filters, display name)
│  │     ├─ filters.json          # optional, page-scoped filters
│  │     └─ visuals/
│  │        └─ <visualId>/
│  │           ├─ visual.json     # the visual definition
│  │           ├─ filters.json    # optional, visual-scoped filters
│  │           └─ mobile.json     # optional, mobile layout overrides
│  ├─ filters.json                # optional, report-scoped filters
│  ├─ bookmarks/                  # optional
│  │  ├─ bookmarks.json
│  │  └─ <bookmark>.bookmark.json
│  └─ reportExtensions.json       # optional, report-level measures
├─ StaticResources/
│  ├─ SharedResources/
│  │  └─ BaseThemes/
│  │     └─ <theme>.json
│  └─ RegisteredResources/        # optional logos, custom theme files, images
│     └─ <file>
└─ definition.pbir                # connection binding — at ROOT, not under definition/
```

The `definition.pbir` file is **at the root** of `<Report>.Report/`, not inside `definition/`. The `definition/` subfolder holds everything that describes pages, visuals, filters, and the top-level `report.json`. The `version.json` file is **required** — without it `validate` fails with `PBIR_VERSION_MISSING`.

---

## Schema URLs

Every JSON file in `definition/` declares a `$schema`. The schemas live under `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/`. The directory name on disk and the schema name **do not always match** — use this table as the canonical reference. Versions shown are current as of the migration; check [CHANGELOGs](https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definition) for newer revisions.

| File | `$schema` |
|---|---|
| `definition/version.json` | `.../versionMetadata/1.0.0/schema.json` |
| `definition/report.json` | `.../report/3.3.0/schema.json` |
| `definition/pages/pages.json` | `.../pagesMetadata/1.1.0/schema.json` |
| `definition/pages/<id>/page.json` | `.../page/2.1.0/schema.json` |
| `definition/pages/<id>/visuals/<vid>/visual.json` | `.../visualContainer/2.5.0/schema.json` |
| `definition/**/filters.json` *(any filters.json)* | `.../filterConfiguration/1.2.0/schema.json` |
| `definition.pbir` | `.../definitionProperties/2.0.0/schema.json` |
| `StaticResources/SharedResources/BaseThemes/<t>.json` | `.../theme/2.140.0/schema.json` |

> **Schema names vs file names** — note that `pages.json` uses the **`pagesMetadata`** schema, `page.json` uses **`page`**, and `visual.json` uses **`visualContainer`** (not `visual`). The CLI will surface mismatches as `PBIR_FORMATTING_*` or `PBIR_VCO_*` errors. If `validate --format text` reports a missing-property error, do not silence it — re-check property names in `cli_knowledge/`.

---

## `definition.pbir` — Connection Binding

**V2 schema, byConnection, full XMLA — always.**

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {
    "byConnection": {
      "connectionString": "Data Source=\"powerbi://api.powerbi.com/v1.0/myorg/<WORKSPACE_NAME>\";initial catalog=<MODEL_NAME>;integrated security=ClaimsToken;semanticmodelid=<MODEL_GUID>",
      "pbiServiceModelId": null,
      "pbiModelVirtualServerName": null,
      "pbiModelDatabaseName": null
    }
  }
}
```

| Field | Value |
|---|---|
| `version` | `"4.0"` |
| `byConnection.connectionString` | full XMLA string with `Data Source`, `initial catalog`, `semanticmodelid` |
| Other `pbi*` fields | leave `null` |

Shorthand `"semanticmodelid=<GUID>"` works but the full XMLA is preferred — it round-trips through `getDefinition` cleanly and matches Fabric's own output.

---

## `report.json` — Top-Level Report

Minimal viable shape:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
  "themeCollection": {
    "baseTheme": { "name": "AzureBrainLight" }
  },
  "publicCustomVisuals": []
}
```

`report.json` carries:

- `themeCollection.baseTheme.name` — must match a `BaseThemes/<name>.json` file
- optional `themeCollection.customTheme` for user-provided palettes
- `publicCustomVisuals[]` — IDs of marketplace visuals (usually empty)
- `objects` / `pods` / etc. — rarely needed; let Fabric apply defaults

## `version.json` — Format Version

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
  "version": "4.0.0"
}
```

Version pattern: `major.minor.0`, major ≥ 1, patch is always `0`. Required.

---

## `pages/pages.json` — Page Index

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
  "activePageName": "overview",
  "pageOrder": ["overview", "trends", "details"]
}
```

| Field | Value |
|---|---|
| `pageOrder` | array of page folder names — order = tab order |
| `activePageName` | folder name shown on open |

Every entry must correspond to an existing `pages/<name>/page.json`.

---

## `pages/<pageId>/page.json` — Page Metadata

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
  "name": "overview",
  "displayName": "Overview",
  "displayOption": "FitToPage",
  "height": 720,
  "width": 1280,
  "visualInteractions": [],
  "objects": {}
}
```

| Field | Notes |
|---|---|
| `name` | must match folder name |
| `displayName` | user-visible page title in the tab |
| `displayOption` | `"FitToPage"` (default) / `"ActualSize"` / `"FitToWidth"` |
| `height` / `width` | 720×1280 standard 16:9; 1080×1920 for big screens |
| `objects` | page-level VCOs (background, displayArea, outspace, …) — values must be PBIR expressions |

---

## `visuals/<visualId>/visual.json` — Visual Definition

Skeleton (cardVisual example):

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "<uuid>",
  "position": { "x": 20, "y": 80, "z": 0, "width": 200, "height": 120, "tabOrder": 0 },
  "visual": {
    "visualType": "cardVisual",
    "query": {
      "queryState": {
        "Data": {
          "projections": [
            { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "fact_general_ledger" }}, "Property": "Total Revenue" }}, "queryRef": "fact_general_ledger.Total Revenue", "nativeQueryRef": "Total Revenue" }
          ]
        }
      },
      "sortDefinition": { "sort": [], "isDefaultSort": true }
    },
    "objects": {
      "value": [{ "properties": { "fontSize": { "expr": { "Literal": { "Value": "27D" }}}, "fontColor": { "solid": { "color": { "expr": { "ThemeDataColor": { "ColorId": 1, "Percent": 0 }}}}} }}]
    },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" }}}, "text": { "expr": { "Literal": { "Value": "'Total Revenue'" }}} }}]
    },
    "drillFilterOtherVisuals": true
  }
}
```

| Section | Source of truth |
|---|---|
| `visualType` | [`cli_knowledge/visual_types.json`](cli_knowledge/visual_types.json) |
| `query.queryState.<Role>` | [`cli_knowledge/visuals/<type>/catalog.json`](cli_knowledge/visuals/) — see `roles` map |
| `objects.<obj>` | [`cli_knowledge/visuals/<type>/formatting.json`](cli_knowledge/visuals/) — `objects[]` / `objectsBase[]` |
| `objects.<obj>[].properties.<prop>` | [`cli_knowledge/visuals/<type>/objects/<obj>.json`](cli_knowledge/visuals/) |
| `visualContainerObjects.<vco>` | [`cli_knowledge/vcos/<vco>.json`](cli_knowledge/vcos/) |

> Property values are **always** PBIR literal expressions. Use `powerbi-report-author expr encode --kind <kind> <value>` whenever in doubt. See [`themes_styling.md`](themes_styling.md) for the full cheatsheet.

---

## Required Parts for `updateDefinition`

When sending the report to Fabric REST, **every file under `<Report>.Report/`** becomes a `part`:

```json
{
  "definition": {
    "parts": [
      { "path": "definition.pbir", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": "definition/version.json", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": "definition/report.json", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": "definition/pages/pages.json", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": "definition/pages/overview/page.json", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": "definition/pages/overview/visuals/abc/visual.json", "payload": "<base64>", "payloadType": "InlineBase64" },
      { "path": "StaticResources/SharedResources/BaseThemes/AzureBrainLight.json", "payload": "<base64>", "payloadType": "InlineBase64" }
    ]
  }
}
```

Rules:
- `path` is **relative to the `<Report>.Report/` root**, with forward slashes.
- `payload` is **base64 of the file's UTF-8 bytes** (no BOM).
- `updateDefinition` is a **full replace** — omit a file and it disappears from the report.
- Do not send `.platform` — Fabric generates it.

The reference uploader is [`templates/deploy_report.py`](templates/deploy_report.py); the walker is `walk(<Report>.Report)` → exclude `.platform`.

---

## Validation Before Deployment

```powershell
powerbi-report-author validate "<Report>.Report" --format text
```

`validate` performs:
- schema check against `developer.microsoft.com` URLs (use `--no-schema` to go offline)
- cross-reference check (every page in `pages.json` exists, every visualType is in the catalog, every formatting object is valid for its visualType, every VCO is a known VCO, every measure/column is `entity.field`-shaped)
- `$schema` URL freshness check

Fix every `error` and ideally every `warning` before calling REST.

---

## Cross-References

- Property lookups → [`cli_knowledge/`](cli_knowledge/)
- Expression encoding → [`themes_styling.md`](themes_styling.md)
- Visual selection by archetype → [`visual_catalog.md`](visual_catalog.md)
- Page grid system → [`pages_layout.md`](pages_layout.md)
- Deployment script reference → [`templates/deploy_report.py`](templates/deploy_report.py)
- Known issues → [`known_issues.md`](known_issues.md)

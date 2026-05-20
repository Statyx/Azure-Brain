# Known Issues — Report-Specific

All report-related gotchas discovered during this project, with fixes.

---

## Issue Table

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| 1 | PBIR folder format renders blank | **CRITICAL** | Use Legacy PBIX format exclusively |
| 2 | Missing prototypeQuery = empty visuals | **HIGH** | Add prototypeQuery with Version 2, From, Select |
| 3 | `card` vs `cardVisual` confusion | HIGH | Always use `cardVisual` with `Data` bucket |
| 4 | Card values clipped/overflow | MEDIUM | Set `calloutValue.fontSize: 14D` or `27D`, height ≥ **120px** |
| 5 | Measure name mismatch = silent blank | **HIGH** | Exact match: case + whitespace sensitive |
| 6 | Missing `layoutOptimization` | HIGH | Add `"layoutOptimization": 0` (integer) to report.json |
| 7 | V1 definition.pbir schema fails | HIGH | Use V2 schema (2.0.0) with full XMLA connectionString |
| 8 | Config not stringified | HIGH | `json.dumps(config_dict)`, not embedded object |
| 9 | Filters not stringified | MEDIUM | `"[]"` string, not `[]` array |
| 10 | Base theme missing = ugly default | LOW | Include CY26SU02.json in StaticResources part |
| 11 | `updateDefinition` is full replace | MEDIUM | Re-send ALL parts, not just changed ones |
| 12 | `getDefinition` is always async | MEDIUM | Even for small reports, returns 202 → poll |
| 13 | `colorByCategory` not working via API | **HIGH** | Use Series projection instead (see below) |
| 14 | All bars same color (Fluent blue) | **HIGH** | Add category to both `Category` AND `Series` projections |
| 15 | Slicer height too small with title | **HIGH** | Height must be ≥75px with vcObjects.title enabled |
| 16 | Card height inconsistent across pages | **HIGH** | ALL cards must be 120px — even on slicer pages |
| 17 | Separator overlaps card bottom | MEDIUM | Gap formula: `separator_y = card_y + card_h + 8` |
| 18 | Slicer missing styling (no shadow) | MEDIUM | Add vcObjects: background, dropShadow, border=false |

---

## Detailed Fixes

### 1. PBIR Folder Format Renders Blank

**THE single biggest issue in this project.**

- **Symptom**: Report created, `getDefinition` returns all parts, but visuals are **completely blank** in portal
- **Cause**: PBIR folder format (`definition/pages/{page}/visuals/{vis}/visual.json`) is accepted by the API but not rendered by the Fabric viewer
- **Fix**: Use **Legacy PBIX format** (`report.json` at root with `sections[].visualContainers[]`)
- **Detection**: If your definition has paths like `definition/pages/*/visuals/*/visual.json`, you're using the wrong format

### 2. Missing prototypeQuery

- **Symptom**: Visual renders as empty box with title but no data
- **Cause**: No `prototypeQuery` in the visual config
- **Fix**: Every data visual MUST have:
  ```json
  "prototypeQuery": {
    "Version": 2,
    "From": [{"Name": "f", "Entity": "table_name", "Type": 0}],
    "Select": [/* measure/column references */]
  }
  ```
- **Exception**: `textbox`, `shape`, `image` don't need prototypeQuery

### 3. `card` vs `cardVisual`

- **Symptom**: Card visual doesn't render or looks broken
- **Fix**: Use `"visualType": "cardVisual"` (new card)
- **Bucket**: `Data` (not `Values`)
- The old `card` visual uses `Values` bucket and is deprecated

### 4. Card Values Clipped

- **Symptom**: KPI numbers cut off or overflow container
- **Fix**: 
  - Set `calloutValue.fontSize` to `27D` (27pt) in objects
  - Ensure card height ≥ 120px
  - Default font size is enormous and always clips

### 5. Measure Name Mismatch

- **Symptom**: Visual blank despite correct structure
- **Cause**: `Total_Revenue` in code, `Total Revenue` in model (underscore vs space)
- **Fix**: Names are **case-sensitive** and **whitespace-sensitive**
- **Verification**: Query model.bim or run `EVALUATE` DAX query to list exact measure names

### 6. Missing layoutOptimization

- **Symptom**: `CorruptedPayload` or "Required properties are missing" error
- **Fix**: Add `"layoutOptimization": 0` to report.json (integer, not string)
- Legacy format uses integer `0`; PBIR uses string `"None"`

### 7. V1 definition.pbir

- **Symptom**: Report doesn't connect to semantic model
- **Fix**: Always use V2 schema (`2.0.0`) with `byConnection` and full XMLA connection string
- V1 requires `pbiServiceModelId`, `pbiModelVirtualServerName` — nearly impossible to get right

### 8. Config Not Stringified

- **Symptom**: API rejects definition or visuals render incorrectly
- **Fix**: Both `visualContainer.config` and `section.config` must be `json.dumps(dict)`, not embedded objects
- **Common mistake**: Writing `"config": {...}` instead of `"config": "{\"name\":\"...\"}"` 

### 9. Filters Not Stringified

- **Symptom**: Subtle rendering issues
- **Fix**: `"filters": "[]"` (stringified empty array), not `"filters": []`

### 10. Base Theme Missing

- **Symptom**: Report works but uses ugly default theme
- **Fix**: Include base theme in API parts:
  ```json
  {"path": "StaticResources/SharedResources/BaseThemes/CY26SU02.json", "payload": "<base64>", "payloadType": "InlineBase64"}
  ```
- Extract from existing report via `getDefinition` if you don't have the theme file

### 11. updateDefinition Is Full Replace

- **Symptom**: After update, some parts disappear (e.g., theme gone)
- **Fix**: Always send ALL parts (report.json, definition.pbir, theme) in `updateDefinition`
- There is no partial patch — the entire definition is replaced

### 12. getDefinition Is Always Async

- **Symptom**: Expecting 200 with body, getting 202 with no body
- **Fix**: Always poll `x-ms-operation-id` from 202 response headers, then `GET /operations/{id}/result`

### 13. colorByCategory Does NOT Work via API

- **Symptom**: Setting `"dataPoint": [{"properties": {"colorByCategory": _lit("true")}}]` in `objects` has no effect — all bars/dots stay the same first-theme color
- **Cause**: `dataPoint.colorByCategory` is ignored when deploying report definitions via API (Fabric REST). It only works when set interactively in the portal
- **Fix**: Add the **same category column** to the `Series` projection bucket:
  ```json
  "projections": {
    "Category": [{"queryRef": "dim_disciplines.discipline_name"}],
    "Y": [{"queryRef": "fact_benchmarks.Total Benchmark Lines"}],
    "Series": [{"queryRef": "dim_disciplines.discipline_name"}]
  }
  ```
  This forces PBI to assign a different Fluent 2 theme color per category value.
- **Side effect**: A redundant legend appears (duplicates axis labels). Hide it:
  ```json
  "legend": [{"properties": {"show": _lit("false")}}]
  ```
- **Applies to**: `clusteredBarChart`, `clusteredColumnChart`, `scatterChart`, `donutChart`, and other chart types with a single data series

### 14. All Bars Same Color (Single-Series Problem)

- **Symptom**: Every bar in a bar chart is the same blue (#118DFF), no matter how many categories
- **Cause**: When a bar chart has only one measure in `Y` and no `Series`, PBI treats it as a single data series — all bars get the first theme color
- **Fix**: Same as Issue #13 — add category column to `Series` projection

### 15. Slicer Height Too Small With Title

- **Symptom**: Slicer dropdown appears crushed, barely clickable, or title overlaps the dropdown control
- **Cause**: When `vcObjects.title.show: true`, the title renders INSIDE the visual height. At 55px, the title takes ~22px, leaving only ~33px for the dropdown — unusable.
- **Fix**: Set slicer height to **75px** minimum when using `vcObjects.title`. Without title, 50px is OK.
- **Height budget**:
  ```
  title zone     = 22px (font 10D + padding)
  dropdown zone  = 40px (control + internal padding)  
  container pad  = 8px
  total          = 70px minimum, 75px recommended
  ```
- **Detection**: Any `_slicer()` call with `h < 70` and `vcObjects.title.show: true`

### 16. Card Height Inconsistent Across Pages

- **Symptom**: Category label text (e.g., "Anomaly Count", "Composite Score") is cut off at the bottom on some pages but not others
- **Cause**: Pages with slicers were given 100px card heights to save space, while non-slicer pages used 120px. The 100px is technically enough (formula = 99px), but with ZERO margin the categoryLabel clips.
- **Fix**: **ALL cards MUST be 120px** regardless of page type. If vertical space is tight on slicer pages, shrink the charts below instead.
- **Rule**: When adding slicers to a page, cascade +20px to cards/charts below but KEEP card height at 120px.
- **Vertical chain for slicer pages**:
  ```
  slicers:    y=8,   h=75  → bottom=83
  cards:      y=93,  h=120 → bottom=213
  separator:  y=221
  charts:     y=229
  ```

### 17. Separator Overlaps Card Bottom

- **Symptom**: A thin line appears to cut through the bottom of card visuals
- **Cause**: Separator `y` value is less than `card_y + card_h`. Common when cascading layout changes (e.g., increasing card height without adjusting separator).
- **Fix**: Formula: `separator_y = max(card_y + card_h for all cards in row) + 8`
- **Self-test**: Run `_audit_layout.py` which checks `gap >= 4px` between card bottoms and next separator

### 18. Slicer Missing Container Styling

- **Symptom**: Slicers look like plain floating dropdowns, disconnected from the card/chart grid. No background, no shadow.
- **Cause**: The `_slicer()` function had no `vcObjects` for background, border, or dropShadow — only a bare title.
- **Fix**: Add full vcObjects to `_slicer()` matching card/chart styling:
  ```json
  "vcObjects": {
    "title": [{...fontSize: "10D", fontColor: "#616161"...}],
    "visualHeader": [{"show": false}],
    "background": [{"show": true}],
    "border": [{"show": false}],
    "dropShadow": [{...same as cards...}]
  }
  ```
- **Visual impact**: Dramatic — slicers now look like integrated dashboard elements instead of floating orphans

---

## Debugging Checklist

When a report isn't rendering correctly:

```
□ 1. Is format Legacy PBIX? (report.json at root, not definition/pages/...)
□ 2. Is layoutOptimization: 0 present in report.json?
□ 3. Is definition.pbir using V2 schema with connectionString?
□ 4. Does connectionString contain correct workspace name + model GUID?
□ 5. Is config stringified in every visualContainer?
□ 6. Is config stringified in every section?
□ 7. Are filters stringified ("[]" not [])?
□ 8. Does every data visual have prototypeQuery?
□ 9. Do prototypeQuery measure/column names exactly match model?
□ 10. Is visualType correct? (cardVisual not card)
□ 11. Is calloutValue.fontSize set for cards?
□ 12. Is card height ≥ 120px?
□ 13. Is base theme included in definition parts?
□ 14. Do position values match between container level and layouts[0].position?
□ 15. Are bar/scatter charts multi-colored? (Category col in Series projection)
□ 16. Are Fluent 2 structural colors applied? (#252423 text, #c7c8ce border, #cccccc shadow)
□ 17. Does each page have an accent bar at y=0?
□ 18. Are card heights CONSISTENT (120px) across ALL pages? (slicer pages too)
□ 19. Are slicer heights ≥75px when using vcObjects.title?
□ 20. Do slicers have background + dropShadow vcObjects? (matching cards)
□ 21. Is separator_y > max(card_bottom) with ≥4px gap?
□ 22. Run _audit_layout.py — 0 errors, 0 warnings?
```

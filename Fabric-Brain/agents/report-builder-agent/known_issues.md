# Known Issues — PBIR Reports

PBIR-specific gotchas, with detection and fix. For Legacy PBIX issues, see [`known_issues.legacy.md`](known_issues.legacy.md) — kept only for migration reference.

---

## Issue Table

| # | Issue | Severity | Fix |
|---|---|---|---|
| 1 | Property values not wrapped as PBIR expressions | **CRITICAL** | Use `expr encode --kind ...` — every value goes inside `{"expr":{"Literal":{"Value":...}}}` or `{"solid":{"color":...}}` |
| 2 | Hex color without single-quote padding | **HIGH** | `"'#118DFF'"` not `"#118DFF"` |
| 3 | Number missing `D` suffix, integer missing `L` suffix | **HIGH** | `100D` for doubles, `12L` for integers |
| 4 | Page folder missing from `pages.json.pageOrder` | **HIGH** | Page becomes invisible in tabs |
| 5 | Visual references non-existent measure/column | **HIGH** | Visual renders blank silently — check `nativeQueryRef` against semantic model |
| 6 | Formatting object name with `(selector: ...)` suffix | MEDIUM | Strip suffix when calling `describe-object`; use `objectsBase[]` in `formatting.json` |
| 7 | `updateDefinition` missing a file | MEDIUM | Full-replace: omit a file and it's deleted from the report |
| 8 | Property put under `objects` instead of `visualContainerObjects` (or vice versa) | MEDIUM | Container styling (title, background, …) goes under `visualContainerObjects`; visual-specific properties (labels, axis, …) go under `objects` |
| 9 | Slicer/textbox visual carries a non-empty query | LOW | Strip `query` for non-data visuals (`textbox`, `shape`, `image`, `basicShape`, `actionButton`, `bookmarkNavigator`, `pageNavigator`) |
| 10 | `$schema` URL points to an outdated version | LOW | Schemas use semver; latest minor is forward-compatible. Re-pin from a known-valid report periodically. |
| 11 | Visual position off-canvas | MEDIUM | `validate` flags this; ensure `x + width ≤ canvasWidth` and `y + height ≤ canvasHeight` |
| 12 | UUID for `visualId` collides across pages | LOW | Use full UUIDs; the CLI tolerates collisions but `getDefinition` can return weird ordering |
| 13 | `actionButton` without action target | MEDIUM | Bind `action` to `PageNavigation`, `Bookmark`, `Drill`, or `Url` — otherwise click does nothing |
| 14 | Theme file references colors not in `dataColors[]` | LOW | `ThemeDataColor.ColorId` is 1-based and clamps to `dataColors.length` — extras are ignored |
| 15 | Async `updateDefinition` 202 with no `Location` header | MEDIUM | Use the `x-ms-operation-id` response header instead; poll `/v1/operations/{id}` |
| 16 | Card callout height < 120 px clips numbers | MEDIUM | Always height ≥ 120 px AND set `value.fontSize` explicitly on cardVisual (NOT `cardCalloutArea.fontSize` — that property does not exist; `cardCalloutArea` only owns padding/background/cornerRadius) |
| 17 | `displayName` differs from `name` in `page.json` | LOW | OK — `name` is the folder ID, `displayName` is the tab label |
| 18 | Filter file (`filters.json`) at wrong scope | LOW | Report-scoped: `definition/filters.json`. Page-scoped: `pages/<id>/filters.json`. Visual-scoped: `pages/<id>/visuals/<vid>/filters.json` |
| 19 | **Report freezes on "Loading your report..." forever (HTTP 405 access-request)** | **CRITICAL** | CLI validates 0/0 but the LIVE renderer hangs. Required: `version.json` = `"2.0.0"` (NOT `4.0.0`); `report.json` MUST have `reportSource` + `settings` + `objects`; `baseTheme` MUST be a real built-in (e.g. `CY26SU05`) with its theme json — no custom-name baseTheme, no `customTheme`+`RegisteredResources`; `visualContainer` schema `2.10.0` (not 2.5.0). Diagnose by `getDefinition` on a working QuickCreate report and diffing. |
| 20 | "Cannot load model — CapacityNotActive" (report renders, model won't load) | HIGH | The Fabric capacity is **Paused**. Resume: `az fabric capacity resume --capacity-name <n> --resource-group <rg>`. Not a report bug. |

---

## Detailed Fixes

### 1. Property values must be PBIR expressions

**Symptom**: Visual renders but the property has no effect (color stays default, title stays empty, etc.).

**Cause**: Raw JSON value placed where the schema expects an expression envelope.

**Wrong**:
```json
"title": [{ "properties": { "text": "Total Revenue" }}]
```

**Right**:
```json
"title": [{ "properties": { "text": { "expr": { "Literal": { "Value": "'Total Revenue'" }}}}}]
```

When in doubt, round-trip through the CLI:
```powershell
powerbi-report-author expr encode --kind string "Total Revenue"
```

### 2. Hex colors need single-quote padding

**Symptom**: Color reverts to default theme color.

**Wrong**: `"Value": "#118DFF"` — interpreted as something other than a string literal.

**Right**: `"Value": "'#118DFF'"` — note the single quotes inside the JSON string.

### 3. Number/integer suffixes

| Want | Wrong | Right |
|---|---|---|
| Double `100.5` | `"100.5"` | `"100.5D"` |
| Integer `12` | `"12"` | `"12L"` |
| Percentage `25%` | `"25"` | `"25L"` (it's an int in PBIR) |

### 4. Page invisible despite `page.json` existing

**Cause**: `pages.json.pageOrder` doesn't include the folder name.

**Fix**:
```json
{
  "pageOrder": ["overview", "pnl", "<missing_page_here>"]
}
```

### 5. Visual blank — measure name mismatch

**Symptom**: Visual container renders, query runs, but data area is empty.

**Cause**: `nativeQueryRef` doesn't match the measure name in the semantic model. **Case + whitespace sensitive.**

**Fix**:
```powershell
# Verify exact name
az rest --method POST --url "https://api.fabric.microsoft.com/v1/workspaces/<ws>/semanticModels/<sm>/queries" --body '{ "queries": [{ "query": "EVALUATE DISTINCT(VALUES(''SELECTEDMEASURE''))" }]}'
```

Or load the model with `dax_queries.md` patterns from `agents/semantic-model-agent/`.

### 6. `FORMATTING_OBJECT_UNKNOWN` with decorated names

**Cause**: `formatting.json.objects[]` sometimes contains names like `"fill (selector: default|hover|selected|disabled)"`. The CLI `describe-object` rejects the decorated form.

**Fix**: Use the **base name** only (just `fill`). Each `cli_knowledge/visuals/<type>/formatting.json` has an `objectsBase[]` array with deduped, stripped names — use that for code generation.

### 7. `updateDefinition` is a full replace

**Symptom**: A file you didn't touch is missing from the report after redeployment.

**Cause**: `updateDefinition` replaces the entire `parts[]` set. Any file not in the new `parts[]` is deleted.

**Fix**: Always walk the entire `<Report>.Report/` directory and include every file in the parts array. See [`templates/deploy_report.py`](templates/deploy_report.py).

### 8. `objects` vs `visualContainerObjects`

Decision rule:

| Property type | Where it goes |
|---|---|
| Title, background, border, dropShadow, padding, spacing, header, tooltip, link, lockAspect, stylePreset, divider, subTitle | `visualContainerObjects` |
| Anything visual-specific: labels, axis, legend, dataPoint, cardCalloutArea, plotArea, valueAxis, categoryAxis, smallMultiplesLayout, etc. | `objects` |

The exhaustive lists are in [`cli_knowledge/visuals/<type>/formatting.json`](cli_knowledge/visuals/) — fields `objects[]` and `visualContainerObjects[]`.

### 11. Off-canvas visuals

**Detection**: `powerbi-report-author validate` reports `POSITION_OUT_OF_BOUNDS`.

**Fix**: ensure `x + width ≤ width` and `y + height ≤ height` from `page.json`. For 1280×720: max visual right edge is 1280, max bottom is 720.

### 13. `actionButton` without a target

**Symptom**: Button renders but clicking does nothing.

**Fix**: Set the `action` property:
```json
"action": [{ "properties": {
  "type": { "expr": { "Literal": { "Value": "'PageNavigation'" }}},
  "navigateTo": { "expr": { "Literal": { "Value": "'overview'" }}}
}}]
```

Action types: `PageNavigation`, `Bookmark`, `Drill`, `Url`, `Q&A`, `WebUrl`.

### 15. Async `updateDefinition` polling

```powershell
$resp = Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/workspaces/$wsId/reports/$id/updateDefinition" `
                          -Method POST -Headers @{ Authorization = "Bearer $token" } `
                          -Body $payload -ContentType "application/json"
# Look for x-ms-operation-id header in the 202 response
$opId = $resp.Headers["x-ms-operation-id"]
do {
    Start-Sleep -Seconds 3
    $status = Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/operations/$opId" -Headers @{ Authorization = "Bearer $token" }
} while ($status.status -in @("NotStarted", "Running"))
if ($status.status -ne "Succeeded") { throw $status.error }
```

---

## Debugging Checklist

When a report misbehaves, walk this list in order:

1. **`powerbi-report-author validate <Report>.Report`** — fix every `error`, review every `warning`
2. Compare your visual's JSON against [`cli_knowledge/visuals/<type>/effective.json`](cli_knowledge/visuals/) — does the property exist? at the right path?
3. Round-trip each suspicious value through `expr encode --kind ...`
4. Inspect a known-good report with `preview-visuals` — compare structure
5. Use `getDefinition` after deployment — does the round-tripped definition still contain your changes? If Fabric stripped them, they were invalid.

---

## Cross-References

- Mandatory rules → [`instructions.md`](instructions.md)
- PBIR folder + payload → [`report_structure.md`](report_structure.md)
- Expression encoding → [`themes_styling.md`](themes_styling.md)
- Property catalog → [`cli_knowledge/`](cli_knowledge/)
- Legacy issues (kept for migration only) → [`known_issues.legacy.md`](known_issues.legacy.md)
- Global brain known issues → [`../../known_issues.md`](../../known_issues.md)

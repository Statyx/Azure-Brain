# Semantic Model — Known Issues & Gotchas

Issues specific to semantic model creation, deployment, and maintenance.
For general Fabric issues, see `../../known_issues.md`.

---

## Quick Reference

| Approach | Result |
|----------|--------|
| `definition.pbism` with `{"version": "1.0"}` | ✅ Works |
| `definition.pbism` with `datasetReference` | ❌ "Property not defined in metadata" |
| `definition.pbism` with `connectionString` | ❌ Rejected |
| `"mode"` on Direct Lake partitions | ❌ Not needed, can cause issues |
| `defaultMode: "directLake"` at model level | ✅ Correct |
| Measure name `Total_Revenue` (underscores) | ❌ Silent mismatch |
| Measure name `Total Revenue` (spaces) | ✅ Matches model |
| `entityName` matching Delta table name | ✅ Required |
| `entityName` with wrong casing | ❌ Table shows 0 rows |

---

## Issue 1: definition.pbism Strict Format

**Symptom**: `POST /items` fails with "Property is not defined in the metadata"  
**Root cause**: Any property beyond `{"version": "1.0"}` is rejected  
**Fix**: Use ONLY `{"version": "1.0"}` — nothing else, ever

## Issue 2: Measure Name Sensitivity

**Symptom**: Report visuals are blank despite correct structure  
**Root cause**: Measure names in report don't match model exactly  
**Fix**: Names are **case-sensitive** AND **whitespace-sensitive**
- `Total Revenue` ✅
- `Total_Revenue` ❌
- `total revenue` ❌
- `TotalRevenue` ❌

**Prevention**: Copy exact measure names from model.bim when building reports.

## Issue 3: Direct Lake Partition Mode

**Symptom**: Unexpected behavior or errors when specifying partition mode  
**Root cause**: Direct Lake partitions should NOT have a `"mode"` property  
**Fix**: Only set `"defaultMode": "directLake"` at the model level. Partitions use `"type": "entity"` with no mode.

## Issue 4: Entity Name Must Match Delta Table

**Symptom**: Table appears in model but shows 0 rows  
**Root cause**: `entityName` in the partition source doesn't match the Delta table name in the Lakehouse  
**Fix**: `entityName` must exactly match the table name as shown in the Lakehouse Tables section

## Issue 5: Schema Name Always "dbo"

**Symptom**: Table not found or 0 rows  
**Root cause**: Using wrong schema name  
**Fix**: For Lakehouse Delta tables, `schemaName` is always `"dbo"`

## Issue 6: Expression Source Must Match

**Symptom**: Partition can't connect to data  
**Root cause**: `expression` and `expressionSource` in partition don't reference a valid M expression  
**Fix**: Both must reference an expression name that exists in the model's `expressions` array (typically `"DatabaseQuery"`)

## Issue 7: Ambiguous Relationship Paths

**Symptom**: DAX query returns "A relationship between tables has an ambiguous path"  
**Root cause**: Multiple active paths between two tables  
**Fix**: Make one relationship `isActive: false`, use `USERELATIONSHIP()` in DAX

## Issue 8: Format String Missing

**Symptom**: Measures display raw numbers without formatting (e.g., 0.4532 instead of 45.3%)  
**Root cause**: No `formatString` on the measure  
**Fix**: Always add `formatString`:
- Currency: `"#,0.00"`
- Percentage: `"0.0%;-0.0%;0.0%"`
- Integer: `"#,0"`

## Issue 9: Model Deploy Returns 202 Then Fails Silently

**Symptom**: Operation poll shows `Failed` with vague error  
**Root cause**: Invalid TMSL in model.bim (wrong data type, missing required field, etc.)  
**Fix**: Validate model.bim JSON structure before encoding:
1. Valid JSON syntax
2. All columns have `name`, `dataType`, `sourceColumn`
3. All relationships reference existing tables/columns
4. All partitions reference a valid expression

## Issue 10: Compatibility Level Mismatch

**Symptom**: Model deploys but features like Direct Lake don't work  
**Root cause**: Using old compatibility level  
**Fix**: Use `1604` for Fabric Direct Lake models

## Issue 11: Relationship Direction Causes Duplicate Key Errors or Blank RELATED()

**Symptom**: DAX query fails with "duplicate value found on the one-side" or `RELATED()` returns blanks  
**Root cause**: The relationship direction is reversed — the fact table (with duplicate keys) is on the One side instead of the Many side  
**Example**: `marketing_sends[send_id] → marketing_events[send_id]` had events on the One side, but events has multiple rows per send_id (open, click, bounce). Correct: `marketing_events[send_id] → marketing_sends[send_id]` (events=Many, sends=One)  
**Fix**:
1. Delete the incorrect relationship
2. Recreate with fact table on Many side, dimension/lookup on One side
3. Run `RefreshType=Calculate` to hydrate (see Issue 12)

**Detection**: Check all relationships — the table on the One side must have unique values in the key column. Use `EVALUATE DISTINCT(table[column])` to verify cardinality.

## Issue 12: New/Modified Relationships Not Active Until Calculate Refresh

**Symptom**: After creating or modifying a relationship, queries return errors or the change has no effect  
**Root cause**: DirectLake models cache relationship metadata. Changes require a metadata refresh.  
**Fix**: Run `RefreshType=Calculate`:
- MCP: `model_operations Refresh RefreshType=Calculate`
- REST: `POST /v1/workspaces/{wsId}/semanticModels/{modelId}/refresh` with `{"type": "Calculate"}`

**Important**: `Full` refresh may fail if source Delta table schemas have changed (missing columns like `attribution_source` or `Classification`). `Calculate` is sufficient for relationship hydration.

## Issue 13: Time Intelligence Annotation Overrides Measure Definitions

**Symptom**: A measure designed to return all-time results (e.g., `[Active Customers]`) gets auto-filtered by current year  
**Root cause**: `__PBI_TimeIntelligenceEnabled=1` model annotation causes the Data Agent orchestrator to inject year filters into ALL questions  
**Impact**: Affects Data Agent/Copilot DAX generation — not the measure itself. Verified Answers, measure descriptions, and CopilotInstructions do NOT override this behavior.  
**Fix options**:
1. Set `__PBI_TimeIntelligenceEnabled` to `0` (affects all questions)
2. Accept all answers are year-scoped by default
3. Train users to say "across all years" explicitly

---

## Debugging Checklist

When a semantic model deployment fails or behaves unexpectedly:

1. [ ] Is `definition.pbism` exactly `{"version": "1.0"}`?
2. [ ] Is `compatibilityLevel` set to `1604`?
3. [ ] Is `defaultMode` set to `"directLake"`?
4. [ ] Does every partition `entityName` match a Delta table?
5. [ ] Is `schemaName` set to `"dbo"`?
6. [ ] Does the M expression reference the correct SQL endpoint?
7. [ ] Do all relationships reference existing tables and columns?
8. [ ] Are there no ambiguous relationship paths?
9. [ ] Do all measure expressions reference correct table/column names?
10. [ ] Are format strings included on all measures?

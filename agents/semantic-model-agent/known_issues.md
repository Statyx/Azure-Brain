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

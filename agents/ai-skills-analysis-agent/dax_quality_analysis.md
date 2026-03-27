# DAX Quality Analysis — Best Practice Analyzer & Scoring

## Overview

The DAX Quality Analysis framework evaluates generated DAX queries against 24 rules across 6 categories, producing a 0-3 star quality score. This framework is used to assess Data Agent DAX generation quality during automated evaluation runs.

---

## Quality Stars (0–3)

| Stars | Criteria | Meaning |
|-------|----------|---------|
| ⭐⭐⭐ (3) | Clean query, uses proper measures, no BPA violations, < 15 lines | Production-ready DAX |
| ⭐⭐ (2) | Works but has warnings: > 15 lines, auto-filters detected, minor BPA issues | Acceptable but could improve |
| ⭐ (1) | Query error, empty result, or > 1 BPA error-level violation | Needs attention |
| ☆ (0) | No DAX query generated, or critical errors | Broken — fix immediately |

### Star Assignment Logic

```
IF no DAX query generated → 0 stars
IF query execution error → 1 star
IF empty result set → 1 star
IF BPA error count > 1 → 1 star
IF BPA error count == 1 OR query > 15 lines OR auto-filters detected → 2 stars
ELSE → 3 stars
```

---

## DAX Extraction

DAX queries are extracted from Data Agent tool call outputs (`analyze.database.nl2code`):

- Wrapped in markdown fences: `` ```dax ... ``` ``
- Max capture: 3,000 characters
- If no DAX fence found → 0 stars (no query generated)

---

## Best Practice Analyzer (BPA) — 24 Rules

### Category 1: Performance (5 rules)

| ID | Rule | Severity | Pattern |
|----|------|----------|---------|
| PERF-001 | Avoid `FILTER(ALL(...))` | Error | Use `CALCULATE` + `REMOVEFILTERS` instead |
| PERF-002 | Avoid nested `CALCULATE` ≥ 3 levels | Warning | Refactor into intermediate `VAR` steps |
| PERF-003 | Avoid `IFERROR` wrapping entire expressions | Warning | Use `DIVIDE` for division; handle specific errors |
| PERF-004 | Avoid division without zero-check | Error | Use `DIVIDE(numerator, denominator, 0)` |
| PERF-005 | Avoid `SUMX` / `AVERAGEX` over large tables without filters | Warning | Pre-filter with `CALCULATETABLE` or use measures |

### Category 2: Correctness (5 rules)

| ID | Rule | Severity | Pattern |
|----|------|----------|---------|
| CORR-001 | Never use `==` operator | Error | Use `=` for comparison (DAX has no `==`) |
| CORR-002 | Avoid comparing to `BLANK()` with `=` | Warning | Use `ISBLANK()` function instead |
| CORR-003 | Avoid `VALUES()` in scalar context | Error | Use `SELECTEDVALUE()` or wrap with `CALCULATE` |
| CORR-004 | Avoid `IF(HASONEVALUE(...), ...)` pattern | Warning | Use `SELECTEDVALUE()` with alternate value |
| CORR-005 | Avoid `FIRSTNONBLANK` / `LASTNONBLANK` misuse | Warning | Ensure iterator column is correct |

### Category 3: Time Intelligence (4 rules)

| ID | Rule | Severity | Pattern |
|----|------|----------|---------|
| TIME-001 | Detect `__PBI_TimeIntelligenceEnabled` auto-filter | Info | Injected date filters not in measure definition |
| TIME-002 | Avoid manual date filtering when TI measures exist | Warning | Use `DATEADD`, `SAMEPERIODLASTYEAR` instead |
| TIME-003 | Detect `TREATAS` used for date binding | Info | May indicate relationship issue or role-playing dim |
| TIME-004 | Avoid hardcoded year values in filters | Error | Use `TODAY()`, `YEAR(NOW())`, or relative references |

### Category 4: Readability (4 rules)

| ID | Rule | Severity | Pattern |
|----|------|----------|---------|
| READ-001 | Query > 8 lines without `VAR` declarations | Warning | Break into named `VAR` steps |
| READ-002 | Cryptic aliases (single letters, abbreviations) | Info | Use descriptive names |
| READ-003 | Hardcoded numeric values without explanation | Warning | Use `VAR` with descriptive name |
| READ-004 | Deeply nested expressions (> 4 levels) | Warning | Flatten with `VAR` |

### Category 5: Measure Usage (3 rules)

| ID | Rule | Severity | Pattern |
|----|------|----------|---------|
| MEAS-001 | Raw `SUM(column)` instead of existing measure | Warning | Reference the model's pre-defined measure |
| MEAS-002 | Raw `AVERAGE(column)` instead of existing measure | Warning | Reference the model's pre-defined measure |
| MEAS-003 | Inline calculation duplicating an existing measure | Error | Use the measure directly |

### Category 6: Data Agent Specific (3 rules)

| ID | Rule | Severity | Pattern |
|----|------|----------|---------|
| AGENT-001 | Query returns > 100 rows without `TOPN` | Warning | Add `TOPN` or summary aggregation |
| AGENT-002 | Query references hidden columns | Error | Hidden columns may not resolve correctly |
| AGENT-003 | Query uses `EVALUATE` without `ORDER BY` | Info | Results may be non-deterministic |

---

## Severity Levels

| Level | BPA Impact | Description |
|-------|-----------|-------------|
| **Error** | Counts toward star reduction | Likely produces wrong results or fails |
| **Warning** | Flagged in report | Works but suboptimal or risky |
| **Info** | Noted only | Observation, no correction needed |

---

## Auto-Filter Detection

The `__PBI_TimeIntelligenceEnabled=1` model annotation causes the Data Agent orchestrator to inject date filters. Detection:

1. Parse the generated DAX query for `TREATAS` or explicit date filter expressions
2. Check if those filters appear in the measure definition
3. If filters are injected but NOT in the measure → flag as auto-filter (TIME-001)

**Impact**: All measures return current-year-only results unless the user explicitly asks "across all years".

---

## Integration with Evaluation Pipeline

```
For each question in evaluation run:
  1. Extract DAX from nl2code tool output
  2. Run 24 BPA rules against extracted DAX
  3. Calculate star rating (0-3)
  4. Include in batch_summary.json per-question results
  5. Aggregate: avg stars, BPA violation distribution, top violations
```

### Batch Summary DAX Quality Section

```json
{
  "dax_quality": {
    "avg_stars": 2.4,
    "star_distribution": { "0": 1, "1": 2, "2": 5, "3": 7 },
    "total_violations": 12,
    "by_category": {
      "performance": 3,
      "correctness": 2,
      "time_intelligence": 4,
      "readability": 2,
      "measure_usage": 1,
      "agent_specific": 0
    },
    "top_violations": ["PERF-004", "TIME-001", "CORR-001"]
  }
}
```

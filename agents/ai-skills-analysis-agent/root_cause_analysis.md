# Root Cause Analysis & Action Framework

## Overview

When a Data Agent produces a wrong answer, the failure maps to one of 8 root cause categories. Each category has specific diagnostic signals and recommended remedial actions. This framework is used during automated evaluation runs and manual diagnostic analysis.

---

## Root Cause Categories

### RCA-1: AGENT_ERROR

**Signal**: Agent run status ≠ `completed`, or `error` field present in run metadata.

**Typical causes**:
- Capacity throttling (429)
- Agent timeout
- Internal service error (500)
- Data source disconnected

**Fix**: Retry the question. If persistent, check capacity health and data source connectivity.

---

### RCA-2: QUERY_ERROR

**Signal**: DAX query generated but execution failed — syntax error, missing column, invalid reference.

**Typical causes**:
- Column or table name changed in model
- Measure reference typo (case-sensitive)
- Invalid DAX function usage
- Schema drift after model refresh

**Fix**: Check Prep for AI descriptions match current model schema. Update Verified Answers with correct query patterns.

---

### RCA-3: EMPTY_RESULT

**Signal**: DAX query executed successfully but returned 0 rows.

**Typical causes**:
- Filter values don't exist in data (e.g., "Q5 2025" when data only has Q1-Q4)
- Date range outside data coverage
- Misspelled filter values in WHERE/FILTER clause
- `__PBI_TimeIntelligenceEnabled` auto-filtering to current year

**Fix**: Add few-shot examples showing correct filter values. Add data range descriptions to Prep for AI instructions.

---

### RCA-4: FILTER_CONTEXT

**Signal**: Query returns data but with unexpected scope — too narrow or too broad.

**Typical causes**:
- Time intelligence auto-filter injecting current year
- `TREATAS` imposing unintended filter
- Missing `ALL()` / `REMOVEFILTERS()` when aggregating across dimensions
- Slicer context leaking into the query

**Fix**: For time intelligence: either disable `__PBI_TimeIntelligenceEnabled` or document scope in instructions. For context issues: add Verified Answers with explicit `CALCULATETABLE` + `REMOVEFILTERS`.

---

### RCA-5: MEASURE_SELECTION

**Signal**: Query runs and returns data, but uses the wrong measure for the question.

**Typical causes**:
- Similar measure names (e.g., "Revenue" vs "Net Revenue" vs "Gross Revenue")
- Missing or ambiguous measure descriptions in Prep for AI
- Agent instructions don't link business terms to specific measures
- No Verified Answer for this question pattern

**Fix**: Add explicit measure descriptions. Add Verified Answer mapping the question to the correct measure. List key measures in Data Agent instructions.

---

### RCA-6: RELATIONSHIP

**Signal**: Query joins tables incorrectly — wrong cardinality, missing join, inactive relationship.

**Typical causes**:
- Multiple paths between tables (ambiguous relationship)
- Inactive relationship not activated with `USERELATIONSHIP()`
- Relationship direction reversed (fact on One side)
- Missing relationship between involved tables

**Fix**: Audit model relationships. Add `USERELATIONSHIP()` in Verified Answers for inactive relationships. Fix directionality if reversed.

---

### RCA-7: REFORMULATION

**Signal**: Agent understood the question differently than intended — the DAX query answers a different question.

**Typical causes**:
- Ambiguous business terminology
- Question phrasing doesn't match model vocabulary
- Agent instructions lack domain glossary
- No few-shot example for this question type

**Fix**: Add few-shot examples matching the question pattern. Add business glossary to Data Agent instructions. Clarify terminology in Prep for AI descriptions.

---

### RCA-8: SYNTHESIS

**Signal**: DAX query is correct, data is correct, but the agent's natural language answer misrepresents the results.

**Typical causes**:
- Agent misreads table (wrong row, wrong column)
- Formatting confusion (percentages vs decimals)
- Agent adds incorrect commentary or trends
- Rounding/truncation in response

**Fix**: Add response formatting rules to Data Agent instructions. Add specific examples of how to present results for common patterns.

---

### RCA-9: UNKNOWN

**Signal**: Cannot determine root cause from available pipeline data.

**Typical causes**:
- Incomplete diagnostic data
- New failure mode not yet categorized
- Agent returned no answer and no error

**Fix**: Start by adding Prep for AI descriptions to tables and columns involved. Add a Verified Answer for the question. If persistent, collect full diagnostic JSON for manual review.

---

## Schema Cross-Referencing (NEW)

When a schema snapshot is available, RCA automatically cross-references generated DAX queries against the model's known measures, columns, and hidden columns:

| Signal | Detection | RCA Category |
|--------|-----------|-------------|
| **Measure case mismatch** | Query uses `[total revenue]` but model defines `Total Revenue` | MEASURE_SELECTION |
| **Unknown identifier** | Query references `[NonExistent]` — not in measures or columns | MEASURE_SELECTION |
| **Hidden column reference** | Query uses `[Account_ID]` which is `is_hidden: true` | MEASURE_SELECTION |
| **USERELATIONSHIP** | Explicit inactive relationship traversal | RELATIONSHIP |
| **CROSSFILTER** | Cross-filter direction override | RELATIONSHIP |

The schema is loaded from `snapshots/{profile}/schema.json` and passed to `grade_result(result, test_case, schema=schema)`.

---

## Decision Tree: RCA Assignment

```
Was agent status "completed"?
  NO → RCA-1: AGENT_ERROR

Was a DAX query generated?
  NO → RCA-7: REFORMULATION (agent didn't understand → no tool call)

Did the DAX query execute successfully?
  NO → RCA-2: QUERY_ERROR

Did the query return results (> 0 rows)?
  NO → RCA-3: EMPTY_RESULT

Were unexpected auto-filters detected?
  YES → RCA-4: FILTER_CONTEXT

Was the correct measure used?
  NO → RCA-5: MEASURE_SELECTION

Were the correct tables/joins used?
  NO → RCA-6: RELATIONSHIP

Does the data match expected values?
  YES → RCA-8: SYNTHESIS (data correct, answer wrong)
  NO → Re-check RCA-2 through RCA-6

Nothing above matches?
  → RCA-9: UNKNOWN
```

**Priority ordering** (when multiple signals present): QUERY_ERROR > EMPTY_RESULT > FILTER_CONTEXT > MEASURE_SELECTION > RELATIONSHIP > REFORMULATION > SYNTHESIS > UNKNOWN

---

## Answer Grading System

### Match Types

| Type | Logic | Example |
|------|-------|---------|
| `exact` | Normalized string equality (case-insensitive, whitespace-trimmed) | Expected: "42.5%" — Agent: "42.5%" |
| `contains` | Expected value appears as substring in agent answer | Expected: "Paris" — Agent: "The top city is Paris" |
| `numeric` | Numeric comparison with tolerance; magnitude-aware (K/M/B/T) | Expected: "1695514236" — Agent: "1,695.5M" (within tolerance) |
| `numeric_pct` | Like numeric but treats 0.57 and 57% as equivalent | Expected: 57 — Agent: "0.57" → pass |
| `regex` | Regex pattern match against agent answer | Expected: `r"\d+\.\d+%"` — Agent: "12.3%" |
| `any_of` | Any value from a list matches | Expected: ["Q1", "Q2"] — Agent: "Q1" |
| `list_contains` | ALL items from expected list found in answer (order-irrelevant) | Expected: ["Alpha", "Beta"] — Agent: "Beta, Alpha" → pass |
| `ordered_list` | Like list_contains but validates rank order in answer | Expected: ["Alpha", "Beta"] — Agent: "1. Beta 2. Alpha" → fail |

**Magnitude-aware number extraction**: Handles `$1,234.56`, `23.5M`, `1.7B`, `500K`, `2.3BN`, `57%`, negative numbers.

### Verdicts

| Verdict | Meaning | Action |
|---------|---------|--------|
| `pass` | Agent answer matches expected within match criteria | None |
| `fail` | Agent answer does not match expected | Investigate with RCA |
| `no_expected` | No expected answer defined — requires manual review | Add expected answer to test suite |

### Comparison Report

For each question, the grading produces:
```
Question: "What is Q1 revenue?"
Expected: "$1.2M" (match_type: contains)
Actual: "Q1 2025 revenue was $1,234,567"
Verdict: PASS (contains "$1.2M" → found "$1,234,567" within tolerance)
```

---

## Action Suggestions — 3-Layer Instruction Model

Every suggestion labels which layer to fix, matching the Analyzer's 3-layer model:

| Layer | System | What it Controls | Where to Fix |
|-------|--------|-----------------|---------------|
| **Layer 1** | Agent Instructions | WHETHER to call DAX tool | Data Agent `aiInstructions` |
| **Layer 2** | Prep for AI | WHAT DAX to generate | Power BI → Prep for AI (AI Data Schema, AI Instructions, Verified Answers) |
| **Layer 3** | Agent Instructions | HOW to present results | Data Agent `aiInstructions` (formatting section) |

When failures are detected, the framework suggests one of 7 action types:

| Action Type | Layer | When Suggested | What To Do |
|-------------|-------|----------------|------------|
| `PREP_FOR_AI` | 2 | DAX query wrong, missing filters, wrong measure | Open Prep for AI: fix AI Data Schema visibility, add AI Instructions, add Verified Answers |
| `INSTRUCTION` | 1 or 3 | Agent skips DAX, misroutes, or formats badly | Add/modify Data Agent `aiInstructions` |
| `FEWSHOT` | 2 | Agent doesn't understand question pattern | Add Verified Answer in Prep for AI |
| `DESCRIPTION` | 2 | Missing or ambiguous column/table descriptions | Add descriptions in Prep for AI → AI Data Schema |
| `EXPECTED` | — | Expected answer may be wrong or outdated | Review and update expected value in test suite |
| `MEASURE` | — | Agent writes inline calc for a common metric | Create a dedicated DAX measure in the semantic model |
| `DATA` | — | Query correct but data doesn't match expectations | Verify source data, refresh schedules, permissions |

### Context-Specific Suggestions per RCA

Each RCA category now generates artifact-aware suggestions. For example:
- **QUERY_ERROR** + filter values in query → "[Layer 2 — Prep for AI] Query filtered on ['Active', 'Q1'] — add column descriptions with valid enum values"
- **EMPTY_RESULT** + time filter → "[Layer 2 — Prep for AI → AI Instructions] Add: 'Default time period is FY2025'"
- **MEASURE_SELECTION** + hidden column → "[Layer 2 — Prep for AI] Unhide column or create a visible measure wrapper"
- **REFORMULATION** + no DAX → "[Layer 1 — Agent Instructions] Add: 'ALWAYS query the semantic model using DAX'"
- **SYNTHESIS** + numeric mismatch → "[Expected] Agent returned ~1,695,514. Update expected if correct"

### Action-to-RCA Mapping

| RCA Category | Primary Actions | Secondary Actions |
|-------------|-----------------|-------------------|
| AGENT_ERROR | `DATA` (retry/infra) | `INSTRUCTION` |
| QUERY_ERROR | `PREP_FOR_AI`, `FEWSHOT` | `INSTRUCTION` |
| EMPTY_RESULT | `PREP_FOR_AI`, `FEWSHOT` | `DATA` |
| FILTER_CONTEXT | `PREP_FOR_AI`, `FEWSHOT` | — |
| MEASURE_SELECTION | `PREP_FOR_AI`, `INSTRUCTION` | `MEASURE` |
| RELATIONSHIP | `PREP_FOR_AI`, `FEWSHOT` | — |
| REFORMULATION | `INSTRUCTION`, `FEWSHOT` | — |
| SYNTHESIS | `EXPECTED`, `INSTRUCTION` | `FEWSHOT` |
| UNKNOWN | `PREP_FOR_AI`, `FEWSHOT` | `INSTRUCTION` |

---

## Run Output Format

### Per-Run Directory

```
runs/{profile}/{timestamp}/
├── batch_summary.json        # Aggregated scores, RCA distribution
├── test_cases.yaml           # Frozen copy of questions for reproducibility
└── diagnostics/
    └── Q{i}_full_diag_{slug}.json    # One JSON per question
```

### Batch Summary Structure

```json
{
  "metadata": {
    "timestamp": "20260327_143000",
    "profile": "marketing360",
    "agent_id": "...",
    "semantic_model_id": "..."
  },
  "schema_stats": {
    "tables": 12,
    "columns": 87,
    "measures": 24,
    "relationships": 11,
    "description_coverage": {
      "columns": 92.0,
      "measures": 100.0
    }
  },
  "grading": {
    "total": 15,
    "pass": 12,
    "fail": 2,
    "no_expected": 1,
    "score_pct": 85.7,
    "rca_distribution": {
      "QUERY_ERROR": 1,
      "MEASURE_SELECTION": 1
    }
  },
  "dax_quality": { "..." },
  "comparison": {
    "vs_previous": "20260326_091500",
    "fixed": ["Q3", "Q7"],
    "regressed": [],
    "unchanged_fail": ["Q11"]
  }
}
```

### Post-Run Report Sections

1. **Summary** — pass/fail/error counts with score percentage
2. **Comparison** — vs previous run: fixed, regressed, unchanged
3. **Root Cause Distribution** — bar chart of RCA categories
4. **DAX Quality** — average stars, BPA violation breakdown
5. **Action Suggestions** — grouped by type with specific recommendations

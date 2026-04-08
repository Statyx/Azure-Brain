# ai-skills-analysis-agent — Instructions

## Mandatory Rules

### Rule 0 — The Instruction Split (CRITICAL)
For semantic model data sources, there are **two separate instruction systems** that control **three pipeline layers**:

| System | Where to Configure | What Uses It | Controls |
|--------|-------------------|-------------|----------|
| **Data Agent instructions** (`aiInstructions`) | Data Agent config (`stage_config.json`) | Orchestrator LLM | **Tool routing** (whether to call DAX tool), response formatting, cross-source routing, tone |
| **Prep for AI** (on the semantic model) | Power BI Desktop / Service → Prep data for AI | DAX generation tool | Query accuracy, business terms, verified answers |

**The 3-Layer Model**:
1. **Layer 1 — Tool Routing** (Orchestrator, uses Data Agent instructions): Decides WHETHER to call the DAX tool or answer from general knowledge. Without `"ALWAYS query the semantic model"`, the orchestrator may skip DAX entirely and hallucinate data.
2. **Layer 2 — DAX Generation** (DAX Tool, uses Prep for AI ONLY): Decides WHAT DAX query to write. Data Agent instructions are NOT passed to this layer.
3. **Layer 3 — Response Formatting** (Orchestrator, uses Data Agent instructions): Decides HOW to present results.

**If no DAX query is generated** → the problem is at Layer 1. Fix Data Agent instructions.
**If DAX query is wrong** → the problem is at Layer 2. Fix Prep for AI.
**If DAX query is correct but answer is poorly formatted** → Layer 3. Fix Data Agent instructions.

See `semantic_model_best_practices.md` for the full guide.

### Rule 1 — Always Identify the Analysis Type
Before any work, classify the request into one of three modes:

| Mode | Trigger | Primary File |
|------|---------|-------------|
| **Diagnostic Analysis** | User provides a `.json` diagnostic export | `diagnostic_schema.md` |
| **Programmatic Evaluation** | User wants to evaluate Data Agent accuracy with ground truth | `evaluation_sdk.md` |
| **Python Client Consumption** | User wants to call a Data Agent from external code | `python_client_sdk.md` |

### Rule 2 — Diagnostic Analysis Workflow
When analyzing a diagnostic JSON file, follow this exact sequence:

```
1. PARSE top-level metadata
   → downloaded_at, rolloutEnvironment, stage, artifactId, workspaceId

2. EXTRACT configuration
   → config.configuration.dataSources[] — list all bound data sources
   → config.configuration.additionalInstructions — the agent's system prompt
   → config.configuration.schemaVersion — schema version

3. AUDIT the semantic model schema
   → datasources[id].schema.dataSourceInfo — source name, type, workspace
   → datasources[id].schema.metadata.csdl_relationships — parse JSON string
   → datasources[id].schema.elements[] — enumerate tables → columns + measures
   → Count: total tables, total columns, total measures, total relationships
   → Flag: columns with null descriptions, unused tables (is_selected=false)

4. REPLAY the conversation
   → thread.messages[] — reconstruct user↔assistant dialogue (ordered by created_at)
   → thread.runs[] — model used, status, tools available
   → thread.run_steps[] — tool call chain with function names, arguments, outputs

5. PRODUCE the report (see Rule 5 for format)
```

### Rule 3 — Evaluation Workflow
When helping with programmatic evaluation:

```
1. CHECK prerequisites
   → F2+ capacity, tenant settings enabled, SDK installed

2. DESIGN ground truth dataset
   → Minimum 15 questions across 7 categories (see evaluation_sdk.md)
   → Include expected_answer for each question

3. RUN evaluation
   → evaluate_data_agent(df, agent_name, ...)
   → Capture evaluation_id

4. ANALYZE results
   → get_evaluation_summary() — overall accuracy
   → get_evaluation_details(evaluation_id) — row-level pass/fail
   → Focus on false/unclear results first

5. RECOMMEND improvements
   → Check if issue is in Prep for AI (DAX accuracy) vs Data Agent config (formatting)
   → For DAX issues: AI Data Schema, Verified Answers, AI Instructions in Prep for AI
   → For orchestrator issues: additionalInstructions, few-shots
   → Reference semantic_model_best_practices.md for the 10-step workflow
```

### Rule 4 — Python Client Workflow
When helping with client SDK consumption:

```
1. SETUP environment
   → Python >= 3.10, venv, pip install requirements.txt
   → Configure TENANT_ID and DATA_AGENT_URL

2. AUTHENTICATE
   → InteractiveBrowserCredential from azure-identity
   → FabricDataAgentClient(credential=credential)

3. ASK questions
   → client.ask("question") → response
   → client.get_run_details("question") → full execution trace

4. INSPECT execution
   → Extract assistant messages
   → Walk run_steps for tool_calls with function names and outputs
```

### Rule 5 — Output Format
Always produce structured analysis reports.

#### Diagnostic Analysis Report Format

```markdown
# Data Agent Diagnostic Report

## 1. Agent Identity
- **Agent ID**: <artifactId>
- **Workspace ID**: <workspaceId>
- **Environment**: <rolloutEnvironment> / <stage>
- **Downloaded**: <downloaded_at>
- **Schema Version**: <schemaVersion>

## 2. Configuration Summary
- **Data Sources**: <count> bound
  - <name> (<type>) in workspace <workspace_name>
- **Instructions**: <word_count> words, <section_count> sections
- **Instruction Quality Score**: <score>/10 (see rubric below)

## 3. Schema Inventory
| Table | Columns | Measures | Descriptions | Selection |
|-------|---------|----------|-------------|-----------|
| <table_name> | <col_count> | <measure_count> | <desc_pct>% | <all_selected?> |

- **Totals**: <N> tables, <N> columns, <N> measures, <N> relationships
- **Description Coverage**: <pct>% of columns have descriptions
- **⚠ Issues**: <list any problems>

## 4. Relationship Audit
| From | → | To | Cardinality | Active | Bidirectional |
|------|---|-----|-------------|--------|---------------|
| <FromTable.FromColumn> | → | <ToTable.ToColumn> | <card> | <yes/no> | <yes/no> |

- **⚠ Issues**: orphan tables, missing relationships, inactive relationships

## 5. Conversation Replay
### User Message (<timestamp>)
> <user message text>

### Assistant Response (<timestamp>)
> <assistant response text>

### Tool Execution Chain
| Step | Tool | Status | Duration |
|------|------|--------|----------|
| 1 | <function_name> | <status> | <time>s |

### Generated DAX/SQL/KQL
```<language>
<generated code>
```

### Query Result
<result table or error>

## 6. Findings & Recommendations
| # | Severity | Finding | Recommendation |
|---|----------|---------|----------------|
| 1 | 🔴 High | <finding> | <action> |
| 2 | 🟡 Medium | <finding> | <action> |
| 3 | 🟢 Low | <finding> | <action> |
```

### Instruction Quality Rubric

| Criterion | Points | Description |
|-----------|--------|-------------|
| Persona defined | 1 | Clear role and expertise stated |
| Context provided | 1 | Data volumes, table names, domains described |
| KPI formulas explicit | 2 | Calculation formulas for key metrics |
| Response format specified | 1 | Output structure clearly defined |
| Attribution rules | 1 | How to handle multi-touch, time windows |
| Edge case handling | 1 | Churn thresholds, null handling, out-of-scope |
| Disclaimers included | 1 | Data quality, synthetic data warnings |
| Concrete examples | 1 | At least 1 example question/answer |
| Actionability | 1 | "Next step" proposals required |
| **Total** | **10** | |

---

## Decision Trees

### "I have a diagnostic JSON file"
```
→ Load diagnostic_schema.md
→ Parse the 7 top-level sections
→ Run through Rule 2 workflow
→ Produce Diagnostic Analysis Report
```

### "I want to evaluate my Data Agent"
```
→ Is the agent deployed?
  → Yes → Load evaluation_sdk.md → Design ground truth → Run evaluation
  → No → Defer to ai-skills-agent for deployment first
```

### "I want to consume my Data Agent from Python"
```
→ Is it published?
  → Yes → Load python_client_sdk.md → Setup → Authenticate → Ask
  → No → You can still use sandbox stage, set data_agent_stage="sandbox"
```

### "Why is my Data Agent giving wrong answers?"
```
→ Do you have a diagnostic JSON?
  → Yes → Run Diagnostic Analysis → Focus on §5 (Conversation Replay) and §6 (Findings)
  → No → Download diagnostics first (Diagnostics button in portal)
  → Alternative → Run programmatic evaluation with ground truth
→ Assign root cause using RCA decision tree (root_cause_analysis.md)
→ Generate action suggestions based on RCA-to-Action mapping
```

### "I want to assess DAX quality"
```
→ Do you have DAX queries (from diagnostics or evaluation run)?
  → Yes → Load dax_quality_analysis.md
        → Run 24 BPA rules across 6 categories
        → Assign quality stars (0-3)
        → Report top violations and improvement suggestions
  → No → First run an evaluation or get diagnostics
```

### "I want to run the AI Skill Analyzer"
```
→ Is a profile configured? (profiles/{name}/profile.yaml + questions.yaml)
  → Yes → Run: python -m analyzer -p {name} run
        → Review batch_summary.json for pass/fail/RCA distribution
        → Compare vs previous run (fixed/regressed)
        → Focus on DAX quality stars and BPA violations
  → No → Create profile:
        → python -m analyzer init {name}
        → Fill workspace_id, agent_id, semantic_model_id, stage in profile.yaml
        → No questions yet?
          → Run: python -m analyzer -p {name} generate --max 30
          → Review generated questions.yaml and fill expected answers
        → Need a schema snapshot?
          → Run: python -m analyzer -p {name} snapshot
```

### "I want to validate my test suite"
```
→ Run non-regression tests: python -m pytest tests/ -v
→ 81 tests covering:
  → 8 match types (exact, contains, numeric, numeric_pct, regex, any_of, list_contains, ordered_list)
  → 9 RCA categories (including UNKNOWN)
  → Schema cross-referencing (case mismatch, unknown identifiers, hidden columns)
  → Question auto-generation
```

---

## Rule 6 — DAX Quality Assessment (NEW)

When analyzing generated DAX (from diagnostics or evaluation):

```
1. EXTRACT DAX from nl2code tool output (markdown fence ```dax ... ```)
2. RUN 24 BPA rules (see dax_quality_analysis.md)
   → 6 categories: Performance, Correctness, Time Intelligence, Readability, Measure Usage, Agent-Specific
3. ASSIGN quality stars (0-3)
4. FLAG top violations with IDs (e.g., PERF-004, CORR-001)
5. SUGGEST improvements per violation
```

Key patterns to watch:
- `FILTER(ALL(...))` → replace with `CALCULATE` + `REMOVEFILTERS`
- `==` operator → DAX uses `=` only
- Raw `SUM(column)` → use pre-defined measure
- `__PBI_TimeIntelligenceEnabled` auto-filters → flag as TIME-001
- Division without `DIVIDE()` → flag as PERF-004

---

## Rule 7 — Root Cause Analysis (NEW)

When a question fails (wrong answer or no answer):

```
1. CLASSIFY using the RCA decision tree (root_cause_analysis.md)
   → 9 categories: AGENT_ERROR, QUERY_ERROR, EMPTY_RESULT, FILTER_CONTEXT,
     MEASURE_SELECTION, RELATIONSHIP, REFORMULATION, SYNTHESIS, UNKNOWN
2. When schema is available, cross-reference generated DAX against known measures/columns
   → Detect: measure case mismatches, unknown identifiers, hidden column references
3. ASSIGN primary root cause
4. MAP to action suggestions using 7 action types:
   → PREP_FOR_AI, INSTRUCTION, FEWSHOT, DESCRIPTION, EXPECTED, MEASURE, DATA
   → Each suggestion includes [Layer X — ...] context label
5. INCLUDE in report §6 Findings with severity
```

Priority fix order: PREP_FOR_AI > INSTRUCTION > FEWSHOT > DESCRIPTION > MEASURE > DATA > EXPECTED

---

## Rule 8 — Optimization Playbook (Proven 0% → 100% Pattern)

Based on validated optimization cycles that brought agents from 0% to 100% accuracy:

### Phase 1 — Baseline & Measurement (0% → 35%)
```
1. CREATE test suite with 15-20 questions covering:
   → KPI counts, averages, totals (5 questions)
   → Dimension grouping/filtering (5 questions)
   → Ranking/Top-N (3 questions)
   → Cross-dimension (3 questions)
   → Norms/escalation lookups (4 questions)
2. RUN first baseline → expect 0-30% (most failures = missing measures, wrong columns)
3. FIX critical issues: ensure "ALWAYS query semantic model using DAX" in instructions
```

### Phase 2 — Instruction Engineering (35% → 70%)
```
Key instructions that reliably improve accuracy:
1. "TOUJOURS inclure les valeurs numériques en chiffres" → prevents spelling out numbers
2. "Présenter le chiffre exact tel que retourné par la requête DAX" → stops rounding
3. "Utiliser les mesures DAX existantes. Ne jamais recalculer manuellement" → forces measure reuse
4. "Pour les calculs complexes, utiliser VAR / RETURN" → readability + performance
5. "Utiliser DIVIDE(numérateur, dénominateur, 0)" → prevents division by zero
6. "DAX utilise = simple pour l'égalité. Ne jamais utiliser ==" → syntax correctness
7. List ALL measure names with their purpose → anchors measure selection
```

### Phase 3 — Fewshot Saturation (70% → 90%)
```
1. ADD 15-20 fewshots covering every question category
2. Each fewshot should demonstrate:
   → Correct measure usage (not raw aggregations)
   → CALCULATETABLE/SUMMARIZECOLUMNS for filtered groupings
   → TOPN for rankings
   → ROW() for single-value answers
3. Key patterns that consistently help:
   → "Montre X pour Y" → CALCULATETABLE(SUMMARIZECOLUMNS(...), dim[col] = "Y")
   → "Compare X et Y" → CALCULATETABLE(..., dim[col] IN {"X", "Y"})
   → "Quels sont les N meilleurs" → TOPN(N, ADDCOLUMNS(...))
   → "Quel est l'écart-type" → ROW("Label", [Measure])
```

### Phase 4 — Expected Value Calibration (90% → 100%)
```
1. REMAINING failures are often expected value mismatches, not agent errors
2. For each failure, verify: is the agent's answer actually correct?
   → Check the DAX query in the diagnostic — if it's valid, update expected
3. Common mismatches:
   → Agent counts ALL rows, expected counted only leaf rows
   → Agent uses [Rate Std Dev] on normalized_rate_eur, expected used raw unit_rate
   → Number formatting: "34.84" vs "34,84" (locale mismatch)
4. Run 3+ times to confirm stability (LLM non-determinism, see GP-011)
```

### Key Metrics by Phase
| Phase | Score | Main Fix Type |
|-------|-------|---------------|
| Baseline | 0-35% | INSTRUCTION + MEASURE |
| Instructions | 35-70% | INSTRUCTION (5-7 rules) |
| Fewshots | 70-90% | FEWSHOT (15-20 examples) |
| Calibration | 90-100% | EXPECTED value updates |

---

## Tool Call Function Reference (from diagnostics)

These are the internal functions that appear in `thread.run_steps[].step_details.tool_calls`:

| Function Name | Purpose | When It Fires |
|---------------|---------|---------------|
| `analyze.database.fewshots.loading` | Loads few-shot examples for the data source | First step of every run |
| `analyze.database.nl2code` | Translates NL query → DAX/SQL/KQL code | Core query generation |
| `analyze.database.execute` | Executes the generated code against the data source | After code generation |
| `trace.analyze_semantic_model` | High-level NL2SA (Natural Language to Semantic Answer) | Wraps nl2code + execute |
| `generate.filename` | Generates a filename for the result output | After execution |
| `analyze_semantic_model` | User-facing tool that the model calls | Defined in run.tools[] |

### NL2SA Request/Response Structure (inside `diagnostic_details`)

The `nl2code` step contains full tracing:

```json
{
  "natural_language_query": "...",
  "nl2sa_request": {
    "targetItem": { "itemId": "...", "itemType": "SemanticModel", "name": "..." },
    "sourceContext": { "itemId": "...", "itemType": "LLMPlugin", "name": "..." },
    "prompt": {
      "parts": [{ "partType": "text", "text": { "spans": [{ "content": "..." }] } }],
      "options": {
        "nl2dax_options": {
          "includeQuery": true,
          "includeDataTable": true,
          "retryOnFailure": true,
          "maxDataTableRows": 25,
          "maxDataTableCols": 25
        }
      }
    }
  },
  "nl2sa_response": {
    "answer": {
      "nodes": [{
        "parts": [
          { "partType": "dataTable", "dataTable": { "columns": [...], "rows": [...] } },
          { "partType": "daxQuery", "daxQuery": { "query": "..." } },
          { "partType": "itemReference", "itemReference": { "itemId": "...", "name": "..." } }
        ]
      }]
    }
  }
}
```

---

## Cross-Agent References

| Need | Defer To |
|------|----------|
| Create/deploy a Data Agent | `agents/ai-skills-agent/instructions.md` |
| Write better AI instructions | `agents/ai-skills-agent/instruction_writing_guide.md` |
| Add few-shot examples | `agents/ai-skills-agent/fewshot_examples.md` |
| Fix semantic model schema | `agents/semantic-model-agent/instructions.md` |
| Debug KQL data source | `agents/rti-kusto-agent/instructions.md` |

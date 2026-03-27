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
```

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

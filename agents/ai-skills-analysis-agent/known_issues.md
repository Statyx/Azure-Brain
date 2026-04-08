# Known Issues & Troubleshooting

---

## Diagnostic JSON Issues

### DI-001: `csdl_relationships` is a JSON string inside JSON

**Symptom**: Trying to access relationships directly returns a raw string, not an array.

**Cause**: The `metadata.csdl_relationships` field is a **stringified JSON** embedded inside the diagnostic JSON.

**Fix**: Parse it twice:
```python
import json
relationships = json.loads(datasource["schema"]["metadata"]["csdl_relationships"])
```

---

### DI-002: Messages are ordered newest-first

**Symptom**: Reading `thread.messages[]` in order shows the assistant response before the user question.

**Cause**: The diagnostic export orders messages by `created_at` **descending** (newest first).

**Fix**: Sort by `created_at` ascending before replaying:
```python
messages = sorted(thread["messages"], key=lambda m: m["created_at"])
```

---

### DI-003: `run_steps` may not appear in older exports

**Symptom**: `thread.run_steps` key is missing or empty.

**Cause**: Older diagnostic schema versions (pre-2.1.0) may not include step-level tracing.

**Fix**: Check for existence before accessing:
```python
run_steps = thread.get("run_steps", [])
```

---

### DI-004: `diagnostic_details` only present on `nl2code` steps

**Symptom**: Trying to access `diagnostic_details` on every step returns `null`.

**Cause**: Only `analyze.database.nl2code` steps contain the deep NL2SA trace. Other steps
(fewshots.loading, generate.filename, execute) have `diagnostic_details: null`.

**Fix**: Filter for nl2code steps:
```python
nl2code_steps = [
    s for s in run_steps
    if any(
        tc["function"]["name"] == "analyze.database.nl2code"
        for tc in s.get("step_details", {}).get("tool_calls", [])
    )
]
```

---

### DI-005: `description: null` on most schema elements

**Symptom**: Virtually all columns and measures have `description: null` in the diagnostic.

**Cause**: Descriptions must be added explicitly in the semantic model (via Tabular Editor, TMDL, or REST API).
Most models don't have them.

**Impact**: NL2DAX accuracy suffers when column descriptions are missing — the model relies on
display_name alone for disambiguation.

**Fix**: Add descriptions to critical columns in the semantic model, then re-export diagnostics.

---

### DI-006: Large diagnostic files (>100KB)

**Symptom**: Diagnostic files with many tables or long conversations can exceed 100KB.

**Cause**: The schema section includes every table/column/measure with full GUIDs. Long threads
with multiple messages and runs compound the size.

**Fix**: When analyzing programmatically, stream-parse with `ijson` or extract specific sections
rather than loading the entire file into memory.

---

## Evaluation SDK Issues

### EV-001: SDK only works in Fabric notebooks

**Symptom**: `ModuleNotFoundError: No module named 'fabric.dataagent'` when running locally.

**Cause**: `fabric-data-agent-sdk` is designed exclusively for Fabric notebook environments.

**Fix**: Use Fabric notebooks for evaluation. For local testing, use the Python client SDK
(`fabric-data-agent-client`) instead.

---

### EV-002: `evaluate_data_agent` creates TWO tables

**Symptom**: After evaluation, you see two tables in the lakehouse instead of one.

**Cause**: By design, the SDK creates:
- `<table_name>` — summary results (accuracy metrics)
- `<table_name>_steps` — detailed reasoning and step-by-step execution

**Fix**: This is expected behavior. Use `get_evaluation_summary()` for the summary table
and `get_evaluation_details()` for the steps table.

---

### EV-003: Evaluation results show `unclear` status

**Symptom**: Some evaluation results are marked `unclear` instead of `true` or `false`.

**Cause**: The critic model (used to compare expected vs actual answers) couldn't determine
equivalence — usually because the formats differ significantly (e.g., "9.92%" vs "$9.92 percent").

**Fix**: 
1. Use a custom `critic_prompt` with lenient matching criteria
2. Standardize expected_answer format to match the agent's typical output style
3. Include format hints in the critic prompt

---

### EV-004: `thread_url` only visible to the evaluation runner

**Symptom**: Thread URLs in evaluation details return 403 for other users.

**Cause**: By design, evaluation threads are scoped to the user who ran the evaluation.

**Fix**: Share the DataFrame output instead of the thread URLs. For shared debugging,
export the diagnostic JSON from the portal.

---

### EV-005: Timeout on large evaluation sets

**Symptom**: Evaluation hangs or times out with >50 questions.

**Cause**: Each question requires a full agent invocation (model call + tool execution +
result formatting). 50 questions can take 10+ minutes.

**Fix**: Break large datasets into batches of 15-25 questions. Run sequentially and
merge results.

---

## Python Client SDK Issues

### PC-001: Browser popup blocked in headless environments

**Symptom**: `InteractiveBrowserCredential` fails with "unable to open browser" in Docker/CI.

**Cause**: `InteractiveBrowserCredential` requires a browser for interactive sign-in.

**Fix**: Use alternative credentials for headless environments:
```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id="<tenant-id>",
    client_id="<client-id>",
    client_secret="<client-secret>"
)
```

---

### PC-002: `DATA_AGENT_URL` not found

**Symptom**: Client fails to connect — URL is empty or invalid.

**Cause**: The published URL is only available after the agent is published to production.

**Fix**: 
1. Publish the agent in the Fabric portal
2. Copy the URL from the publish confirmation
3. Set it as `DATA_AGENT_URL` in your environment

---

### PC-003: `get_run_details` structure differs from diagnostics

**Symptom**: The structure returned by `client.get_run_details()` doesn't match the diagnostic JSON.

**Cause**: The client SDK returns a simplified structure while the diagnostic export includes
additional internal fields (`diagnostic_details`, `mcp_details`).

**Fix**: Use the client SDK structure:
```python
# Client SDK
run_details['messages']['data']       # messages array
run_details['run_steps']['data']      # steps array

# Diagnostic JSON
thread['messages']                    # messages array
thread['run_steps']                   # steps array
```

---

### PC-004: Agent only accessible with user's own permissions

**Symptom**: Agent returns "no data found" for queries that work in the portal.

**Cause**: The client SDK inherits the authenticated user's data permissions. If the user
doesn't have access to the underlying data source, the agent can't query it.

**Fix**: Ensure the user has at least Read permissions on:
- The Data Agent item
- The bound data sources (semantic models, lakehouses, etc.)
- The workspace(s) containing those items

---

## General Patterns

### GP-001: Model version changes over time

**Symptom**: Diagnostic shows `gpt-4.1-PowerBICopilot` but behavior changes.

**Cause**: Microsoft may update the underlying model version without changing the label.

**Fix**: Track evaluation accuracy over time to detect regressions from model updates. Use
the evaluation SDK for automated regression testing.

---

### GP-002: "0 fewshots loaded" in diagnostics

**Symptom**: `analyze.database.fewshots.loading` step shows "Loaded 0 fewshots".

**Cause**: No example queries (few-shots) were configured for the data source.

**Impact**: The model has less context for generating accurate queries, especially for
domain-specific terminology or complex joins.

**Fix**: Add few-shot examples via the Data Agent configuration. See
`agents/ai-skills-agent/fewshot_examples.md` for guidance.

---

### GP-003: `nl2sa_request` contains the enriched prompt

**Symptom**: The natural language query in `nl2code` arguments differs from the user's original question.

**Cause**: The orchestrator model reformulates the user's question into a more precise
natural language query before sending it to the NL2SA/NL2DAX engine.

**Example**:
- User asked: "give me the churn rate please"
- NL2SA received: "Calculate the churn rate for customers for the full year 2025. Indicate the number of churned customers and the percentage. Use CRM tables."

**Impact**: This reformulation is usually beneficial — it adds specificity. But if the
reformulation introduces assumptions (like specific time periods), it may cause unexpected results.

---

### GP-004: Data Agent instructions control tool routing, NOT DAX generation

**Symptom**: You add detailed DAX-specific instructions (e.g., "use TREATAS for campaign joins")
to `aiInstructions` in the Data Agent config, but the generated DAX doesn't change.

**Cause**: The DAX generation tool does **not read** Data Agent instructions. It ONLY reads
**Prep for AI** configurations set on the semantic model itself:
- **AI Data Schema** — descriptions on tables, columns, measures
- **Verified Answers** — pre-built DAX queries triggered by keywords
- **AI Instructions** — unstructured guidance for the DAX engine

**However**, Data Agent instructions DO control the **orchestrator**, which decides:
1. **Whether to call the DAX tool at all** (tool routing)
2. **How to reformulate the question** before sending to DAX
3. **How to format the response** after DAX returns results

**Real-world impact**: Without `"ALWAYS query the semantic model using DAX"` in `aiInstructions`,
the orchestrator may skip the DAX tool entirely and answer from general knowledge, producing
hallucinated data that looks plausible but is completely fabricated.

**Fix**:
- For DAX **accuracy** issues (wrong query, wrong measures): Fix Prep for AI on the semantic model
- For **missing DAX queries** (no DAX at all, hallucinated answers): Add `"ALWAYS query the semantic model using DAX. NEVER answer from general knowledge."` to Data Agent aiInstructions
- For **measure selection**: List available measures in Data Agent instructions so the orchestrator mentions them in the reformulated question
- See `semantic_model_best_practices.md` for the 3-Layer Model and 10-step workflow

---

### GP-005: Prep for AI configs are NOT visible in diagnostic exports

**Symptom**: You configured AI Data Schema, Verified Answers, or AI Instructions on the
semantic model, but none of them appear in the diagnostic JSON.

**Cause**: The diagnostic export captures only the Data Agent configuration and the NL2SA
request/response — it does **not** include the Prep for AI settings stored on the semantic model.

**Fix**: To verify Prep for AI is configured:
1. Open Power BI Desktop → Model view → check column/table descriptions
2. Open Power BI Service → Settings → Prep data for AI → check each component
3. In the diagnostic, check `nl2sa_request` → if `verified_answers` or `ai_instructions` appear
   in the NL2SA payload, they are being sent (but this is an internal field, not always visible)

---

### GP-006: Hidden columns break Verified Answers silently

**Symptom**: A Verified Answer with correct DAX returns wrong or empty results.

**Cause**: If the DAX in a Verified Answer references columns that are **hidden** in the model
and the AI Data Schema doesn't describe them, the DAX tool may fail to resolve them.

**Fix**: Ensure all columns referenced in Verified Answers are either:
1. Visible in the model, OR
2. Explicitly described in the AI Data Schema with their hidden status noted

---

### GP-007: Time Intelligence auto-filtering overrides Verified Answers and Measure Descriptions

**Symptom**: A measure like `[Active Customers]` (defined as `COUNTROWS(FILTER(crm_customers, crm_customers[is_active] = TRUE()))`) returns 49 instead of 18,016. The generated DAX adds an unwanted `YEAR(crm_customers[first_seen_at]) == 2025` filter.

**Cause**: The model annotation `__PBI_TimeIntelligenceEnabled` is set to `1`. This causes the orchestrator to **auto-scope ALL questions to the current year**, even when:
- The measure description explicitly says "Do NOT filter by date"
- A Verified Answer exists with the exact question and correct DAX (no date filter)
- CopilotInstructions contain explicit disambiguation rules

The time intelligence annotation takes priority over all Prep for AI configurations in the NL2SA reformulation step.

**Impact**: Any question about cumulative/all-time metrics is silently scoped to the current year. The diagnostic shows the reformulated prompt in `nl2sa_request` with added time constraints.

**Fix options**:
1. **Disable time intelligence**: Set `__PBI_TimeIntelligenceEnabled` to `0` (but this affects ALL questions)
2. **Accept the behavior**: Acknowledge all answers are year-scoped by default
3. **Explicit time ranges in questions**: Users must say "across all years" or "regardless of date" to override

**Detection**: Compare DAX in diagnostic `nl2code.arguments` against the measure definition. Look for injected date filters on columns the measure doesn't reference.

---

### GP-008: Relationship direction matters — duplicate key errors

**Symptom**: DAX query fails with "duplicate value found on the one-side of a relationship" or RELATED() functions return blanks.

**Cause**: The relationship direction is reversed. In a Many-to-One relationship, the table on the **One side must have unique values** in the key column. If you accidentally set the fact table (with duplicates) on the One side, every lookup fails.

**Example**: `marketing_sends[send_id] → marketing_events[send_id]` was configured with `marketing_events` as the One side. But `marketing_events` has multiple rows per `send_id` (open, click, bounce). The correct direction is `marketing_events[send_id] → marketing_sends[send_id]` (events=Many, sends=One).

**Fix**:
1. Delete the incorrect relationship
2. Recreate with the correct direction: fact table = Many side, dimension/lookup = One side
3. Run `RefreshType=Calculate` to hydrate the new relationship (see GP-009)

**Detection**: In diagnostics, look for NL2SA errors mentioning "relationship" or "duplicate key". Also check `RELATED()` calls that return blank where values are expected.

---

### GP-009: Calculate refresh required after relationship changes on DirectLake models

**Symptom**: After creating or modifying a relationship, queries return "relationship needs to be recalculated" or the new relationship has no effect.

**Cause**: DirectLake models cache relationship metadata. New or modified relationships are not active until the metadata is refreshed.

**Fix**: Run a `Calculate` refresh:
- Via MCP: `model_operations Refresh RefreshType=Calculate`
- Via REST API: `POST /v1/workspaces/{wsId}/semanticModels/{modelId}/refresh` with `{"type": "Calculate"}`

**Important**: A `Full` refresh may fail if the source lakehouse Delta tables have schema changes (missing columns). `Calculate` is sufficient for relationship metadata hydration.

---

### GP-010: NL2SA reformulation adds unintended assumptions

**Symptom**: The agent's answer includes data filtered by time period, category, or other dimension that the user didn't ask for.

**Cause**: The orchestrator model reformulates the user's question before sending to NL2SA. It may add:
- Time period scoping (especially with `__PBI_TimeIntelligenceEnabled=1`)
- Table routing hints ("Use CRM tables")
- Metric assumptions ("Indicate the number and percentage")

**Example**:
- User asked: "how many active customers do we have"
- NL2SA received: "Calculate the number of active customers for the year 2025. Use the crm_customers table."

**Detection**: In the diagnostic JSON, compare `user_question` (original) vs the `query` field in `nl2code.arguments` (reformulated). Any added constraints came from the orchestrator.

**Mitigation**:
- Add explicit Verified Answers for questions where reformulation is harmful
- Use CopilotInstructions to anchor metric definitions
- Note that neither fully overrides the reformulation when time intelligence is enabled

---

### GP-011: LLM non-determinism causes score variance between runs

**Symptom**: Same test suite, same agent config — score fluctuates between runs (e.g., 90% → 100% → 95%).

**Cause**: The underlying LLM is non-deterministic. Identical questions may generate different DAX queries, use different measures, or interpret ambiguous column names differently between invocations.

**Examples observed**:
- Q8 "distinct WBS codes": Agent counts only leaf-level WBS (55) in one run but all WBS (96) in the next
- Q17 "standard deviation": Agent uses raw `unit_rate` column (15239) in one run but `[Rate Std Dev]` measure on `normalized_rate_eur` (3785) in another

**Fix**:
1. **Increase fewshot coverage**: Add explicit few-shots for ambiguous questions. The more specific the demonstrated DAX, the more consistent the output
2. **Use existing measures**: Instruct the agent to always use pre-defined measures rather than computing raw aggregations. Measures have fixed semantics
3. **Run multiple times**: When evaluating, run 3+ times and take the modal score to smooth variance
4. **Anchor with `INSTRUCTIONS`**: Include explicit measure names and column semantics in instructions (e.g., "For standard deviation, always use `[Rate Std Dev]`")

---

### GP-012: `==` operator in generated DAX causes silent correctness issues

**Symptom**: DAX query uses `==` but returns correct results in some contexts. BPA flags it.

**Cause**: DAX supports `==` as strict equality (exact match, case-sensitive, no BLANK coercion). Most users expect `=` (standard equality with BLANK handling). The model (GPT-4.1) trained on Python/JS tends to generate `==` by default.

**Impact**: `==` may fail on BLANK comparisons or produce unexpected results with text columns. BPA rule `CORR-004` flags it.

**Fix**: Add to Data Agent instructions: `"DAX uses single = for equality. Never use ==."` This consistently eliminates the issue.

---

### GP-013: Agent uses raw aggregations instead of pre-defined measures

**Symptom**: Generated DAX computes `AVERAGE(fact_table[column])` instead of using `[Avg Measure]`. Works correctly but is verbose, harder to maintain, and inconsistent with model semantics.

**Cause**: The DAX generation layer doesn't always detect pre-defined measures, especially when:
- The measure name doesn't closely match the question
- The question is phrased differently from fewshot examples
- Multiple measures could apply

**Fix**:
1. List key measures explicitly in Data Agent instructions with their purpose
2. Add instruction: `"Always reference existing measures inside CALCULATE instead of wrapping raw SUM/AVERAGE/COUNT"`
3. Add fewshots demonstrating measure usage for each key metric
4. In the semantic model, add descriptions to measures that match natural language patterns

---

### GP-014: Fabric API intermittent failures (404, 400, DNS resolution)

**Symptom**: Data Agent API calls fail with 404 on threads/messages, 400 Bad Request, or DNS resolution failures (`Failed to resolve 'api.fabric.microsoft.com'`).

**Cause**: Fabric API has intermittent server-side issues. These are transient and not related to agent configuration.

**Impact**: Automated test suites may score lower due to skipped/errored questions.

**Fix**:
1. Implement retry logic with exponential backoff (3 retries, 2s/4s/8s delays)
2. Add `process_timeout=30` to `AzureCliCredential` to avoid token acquisition hangs
3. Use `timeout=120` on `requests.post` calls to the Fabric API
4. When evaluating, discard runs with >10% error rate and re-run

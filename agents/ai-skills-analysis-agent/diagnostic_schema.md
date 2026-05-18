# Diagnostic JSON Schema Reference (v2.1.0)

The Fabric Data Agent Diagnostics button exports a single JSON file containing a full snapshot
of the agent's configuration, schema, conversation thread, and execution trace.

**Schema**: `https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataAgent/2.1.0/schema.json`

---

## Top-Level Structure

```json
{
  "downloaded_at": "2026-03-24T15:38:55.767Z",
  "rolloutEnvironment": "PROD",
  "stage": "sandbox | production",
  "artifactId": "<guid>",
  "workspaceId": "<guid>",
  "config": { ... },
  "datasources": { ... },
  "files": { ... },
  "latency": { ... },
  "thread": { ... }
}
```

| Key | Type | Description |
|-----|------|-------------|
| `downloaded_at` | string (ISO 8601) | Timestamp when the diagnostic was exported |
| `rolloutEnvironment` | string | Fabric ring: `PROD`, `PREPROD`, `CANARY` |
| `stage` | string | Agent stage: `sandbox` (draft) or `production` (published) |
| `artifactId` | GUID | The Data Agent item ID |
| `workspaceId` | GUID | The workspace containing the Data Agent |
| `config` | object | Agent configuration (instructions, data sources, schema version) |
| `datasources` | object | Full schema of all bound data sources |
| `files` | object | Attached files (usually empty for Data Agents) |
| `latency` | object | True per-tool-call durations (see Latency section below). **Always prefer this over wall-clock** from `run_steps`. |
| `thread` | object | OpenAI-compatible conversation thread with messages, runs, and run_steps |

---

## Section: `config`

```json
{
  "config": {
    "configuration": {
      "dataSources": [ ... ],
      "additionalInstructions": "<system prompt text>",
      "schemaVersion": "https://developer.microsoft.com/json-schemas/.../2.1.0/schema.json"
    }
  }
}
```

### `config.configuration.dataSources[]`

Array of bound data source references.

```json
{
  "type": "semantic_model",
  "workspaceId": "<guid>",
  "artifactId": "<guid>"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Data source type: `semantic_model`, `lakehouse`, `warehouse`, `kql_database`, `ontology` |
| `workspaceId` | GUID | Workspace containing the data source |
| `artifactId` | GUID | The data source item ID |

### `config.configuration.additionalInstructions`

The agent's **system prompt** — free-text string written by the agent creator. This is the most
important field for quality analysis. Contains:
- Persona/role definition
- Data context (table names, volumes, domains)
- KPI formulas and calculation rules
- Response format requirements
- Attribution rules (e.g., last-touch, time windows)
- Edge case handling (churn thresholds, null behavior)
- Disclaimers

**Audit tip**: Count words, sections, and check for the 10-point instruction quality rubric
(see `instructions.md`).

---

## Section: `datasources`

Keyed by the data source artifact ID. Each entry contains:

```json
{
  "datasources": {
    "<artifactId>": {
      "schema": {
        "dataSourceInfo": { ... },
        "metadata": { ... },
        "elements": [ ... ]
      },
      "etag": "\"0x...\""
    }
  }
}
```

### `datasources[id].schema.dataSourceInfo`

```json
{
  "type": "semantic_model",
  "semantic_model_id": "<guid>",
  "semantic_model_name": "Marketing360_Model",
  "workspace_id": "<guid>",
  "workspace_name": "CDR - Demo CRM Fabric",
  "display_name": "Marketing360_Model",
  "user_description": null,
  "additional_instructions": null
}
```

| Field | Description |
|-------|-------------|
| `type` | Same as in config: `semantic_model`, `lakehouse`, etc. |
| `semantic_model_id` / `semantic_model_name` | ID and name of the semantic model |
| `workspace_id` / `workspace_name` | Workspace location |
| `display_name` | User-facing name |
| `user_description` | Optional data source description (often null) |
| `additional_instructions` | Optional per-data-source instructions (often null) |

### `datasources[id].schema.metadata.csdl_relationships`

**IMPORTANT**: This is a **JSON string inside JSON** — must be parsed twice.

```json
{
  "csdl_relationships": "[{\"FromTable\":\"orders\",\"FromColumn\":\"customer_id\",\"ToTable\":\"crm_customers\",\"ToColumn\":\"customer_id\",\"IsActive\":true,\"IsBidirectional\":false,\"Cardinality\":\"ManyToOne\"}, ...]"
}
```

Each relationship object:

| Field | Type | Description |
|-------|------|-------------|
| `FromTable` | string | Source table (many-side) |
| `FromColumn` | string | Source column |
| `ToTable` | string | Target table (one-side) |
| `ToColumn` | string | Target column |
| `IsActive` | bool | Whether the relationship is active |
| `IsBidirectional` | bool | Whether cross-filter direction is both ways |
| `Cardinality` | string | `ManyToOne`, `OneToOne`, `ManyToMany` |

**Audit tips**:
- Check for orphan tables (tables with no relationships)
- Check for inactive relationships (may cause unexpected filter behavior)
- Check for bidirectional relationships (can cause ambiguity)
- Verify cardinality matches the data model design

### `datasources[id].schema.elements[]`

Array of table definitions. Each table contains child columns and measures.

```json
{
  "id": "<guid>",
  "is_selected": true,
  "display_name": "crm_customers",
  "type": "semantic_model.table",
  "description": null,
  "children": [
    {
      "id": "<guid>",
      "is_selected": true,
      "display_name": "customer_id",
      "type": "semantic_model.column",
      "data_type": "String",
      "description": null,
      "children": []
    },
    {
      "id": "<guid>",
      "is_selected": true,
      "display_name": "Total Customers",
      "type": "semantic_model.measure",
      "data_type": "Int64",
      "description": null,
      "children": []
    }
  ]
}
```

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `id` | GUID | — | Unique element ID |
| `is_selected` | bool | `true`/`false` | Whether included in agent's scope |
| `display_name` | string | — | Table/column/measure name |
| `type` | string | `semantic_model.table`, `semantic_model.column`, `semantic_model.measure` | Element type |
| `data_type` | string | `String`, `Int64`, `Double`, `DateTime`, `Boolean` | Data type (columns/measures only) |
| `description` | string\|null | — | User-provided description |
| `children` | array | — | Nested columns and measures (for tables) |

**Audit tips**:
- Count columns with `description: null` → low description coverage hurts NL2DAX accuracy
- Check `is_selected: false` → excluded elements won't be available to the agent
- Verify measure data types match expected KPIs (e.g., percentages should be `Double`)

---

## Section: `files`

```json
{
  "files": {}
}
```

Usually empty for Data Agents. May contain attached reference documents in future versions.

---

## Section: `thread`

OpenAI Assistants API-compatible conversation thread.

### `thread.messages[]`

Array of messages ordered by `created_at` (newest first in the export).

```json
{
  "id": "msg_...",
  "object": "thread.message",
  "created_at": 1774366674,
  "assistant_id": null,
  "thread_id": "thread_...",
  "run_id": null,
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": {
        "value": "give me the churn rate please",
        "annotations": []
      }
    }
  ],
  "attachments": [],
  "metadata": {}
}
```

| Field | Description |
|-------|-------------|
| `role` | `user` or `assistant` |
| `content[].text.value` | The message text |
| `run_id` | Links assistant messages to their run (null for user messages) |
| `created_at` | Unix timestamp |

### `thread.runs[]`

Array of run executions. Each run represents one agent invocation.

```json
{
  "id": "run_fab...",
  "object": "thread.run",
  "status": "completed",
  "model": "gpt-4.1-PowerBICopilot",
  "instructions": "<full system prompt including safety measures>",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "analyze_semantic_model",
        "description": "Returns data from a semantic model using natural language...",
        "parameters": { ... }
      }
    }
  ],
  "started_at": 1774366705,
  "completed_at": 1774366708
}
```

| Field | Description |
|-------|-------------|
| `status` | `completed`, `failed`, `cancelled`, `expired`, `requires_action` |
| `model` | LLM model used (e.g., `gpt-4.1-PowerBICopilot`) |
| `instructions` | Full system prompt sent to the model (includes safety measures + additionalInstructions) |
| `tools[]` | Available tools the model can call |
| `started_at` / `completed_at` | Unix timestamps for latency calculation |

### `thread.run_steps[]`

Detailed execution trace for each run. This is the most valuable section for debugging.

```json
{
  "id": "step_fab...",
  "object": "thread.run.step",
  "type": "tool_calls",
  "status": "completed",
  "step_details": {
    "type": "tool_calls",
    "tool_calls": [
      {
        "type": "function",
        "function": {
          "name": "analyze.database.nl2code",
          "arguments": "{...}",
          "output": "...",
          "diagnostic_details": {
            "natural_language_query": "...",
            "nl2sa_request": "{...}",
            "nl2sa_response": "{...}"
          }
        },
        "id": "call_..."
      }
    ]
  },
  "created_at": 1774366679,
  "completed_at": 1774366703
}
```

| Field | Description |
|-------|-------------|
| `type` | Always `tool_calls` for Data Agent steps |
| `step_details.tool_calls[]` | Array of function calls in this step |
| `function.name` | Internal tool name (see Tool Call Reference in instructions.md) |
| `function.arguments` | JSON string with call arguments |
| `function.output` | Tool result (markdown table, JSON, or error) |
| `function.diagnostic_details` | Deep trace with NL2SA request/response (only on `nl2code` steps) |

**Execution flow** (typical):
1. `analyze.database.fewshots.loading` → loads few-shot examples
2. `analyze.database.nl2code` → generates DAX/SQL/KQL code
3. `generate.filename` → names the result file
4. `analyze.database.execute` → runs the generated code
5. Model produces assistant message using the results

---

## Quick Parsing Checklist

```
□ Top-level: artifactId, workspaceId, stage, rolloutEnvironment
□ Config: count dataSources, extract additionalInstructions
□ Schema: for each datasource, count tables/columns/measures
□ Relationships: JSON.parse(csdl_relationships), count and validate
□ Thread: count messages, identify user vs assistant
□ Runs: check status, model, latency (completed_at - started_at)
□ Steps: walk tool_calls, extract generated code and results
□ Diagnostic details: parse nl2sa_request/response for deep trace
□ Latency: join latency.tool_calls[].step_id → true per-tool execution time
□ Orchestrator overhead: run_total_s - sum(latency.tool_calls.duration_seconds)
```

---

## Section: `latency` (top-level)

True, runtime-measured durations for each tool call. **More accurate than wall-clock** because
it excludes scheduling/queue time. Some exports nest this section under `thread.latency`.

```json
{
  "latency": {
    "tool_calls": [
      { "step_id": "step_fab_abc...", "duration_seconds": 12.47 },
      { "step_id": "step_fab_def...", "duration_seconds": 0.32 }
    ]
  }
}
```

| Field | Description |
|-------|-------------|
| `tool_calls[].step_id` | Foreign key to `thread.run_steps[].id` |
| `tool_calls[].duration_seconds` | True execution time of that tool call (float, seconds) |

**Usage pattern**: build `{step_id: duration_seconds}` map, attach to parsed steps. Use this
for any latency analysis; fall back to `completed_at - created_at` only when missing.
Derive **orchestrator overhead** as `run_total_s - sum(tool_call_durations)` — this is time
spent in queue / LLM planning / serialization, not in actual data tools.

Full treatment in [`latency_analysis.md`](./latency_analysis.md).

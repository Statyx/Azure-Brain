# Definition Structure — Fabric Data Agent API Format

This file documents the complete structure of a Fabric Data Agent definition, including all JSON schemas, file paths, and encoding rules.

---

## Overview

A Data Agent definition is a set of **parts** (files), each base64-encoded, that together define:
1. The agent's schema version
2. AI instructions (system prompt)
3. Data source bindings
4. Few-shot examples
5. Publishing state

---

## Part Layout

```
Files/Config/
├── data_agent.json                          # Agent schema (required)
├── publish_info.json                        # Publishing metadata (after publish)
├── draft/
│   ├── stage_config.json                    # AI instructions (draft)
│   ├── semantic_model-SM_Finance/
│   │   ├── datasource.json                  # Data source config
│   │   └── fewshots.json                    # Few-shot examples
│   └── lakehouse-MyLakehouse/               # (if using lakehouse)
│       ├── datasource.json
│       └── fewshots.json
└── published/                               # (after publishing)
    ├── stage_config.json                    # AI instructions (published)
    └── semantic_model-SM_Finance/
        ├── datasource.json
        └── fewshots.json
```

### Folder Naming Convention
Data source folders follow the pattern: `{dataSourceType}-{dataSourceName}`

| Data Source Type | Folder Prefix | Example |
|-----------------|---------------|---------|
| Semantic Model | `semantic_model-` | `semantic_model-SM_Finance` |
| Lakehouse | `lakehouse-` | `lakehouse-MyLakehouse` |
| Data Warehouse | `data_warehouse-` | `data_warehouse-SalesWarehouse` |
| KQL Database | `kusto-` | `kusto-LogsDB` |

---

## Part 1: data_agent.json (Required)

The top-level schema declaration.

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataAgent/2.1.0/schema.json"
}
```

**Current schema version**: `2.1.0`

Python:
```python
data_agent_json = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataAgent/2.1.0/schema.json"
}
```

---

## Part 2: stage_config.json (Required)

Contains the AI instructions for the agent. Exists in both `draft/` and `published/` (identical or different content).

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/stageConfiguration/1.0.0/schema.json",
  "aiInstructions": "You are a Finance Controller expert. You help analyze P&L, budget vs actual..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$schema` | string | Yes | Schema version: `1.0.0` |
| `aiInstructions` | string | Yes | The full system prompt text |
| `experimental` | object | No | Experimental properties (property bag) |

**Critical**: The `aiInstructions` value is a single string. For multi-line instructions, use `\n` or read from a markdown file and pass as-is.

Python:
```python
stage_config = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/stageConfiguration/1.0.0/schema.json",
    "aiInstructions": instructions_text,  # string from .md file
}
```

---

## Part 3: datasource.json (Per Data Source)

Binds a Fabric item (semantic model, lakehouse, warehouse, etc.) to the agent.

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
  "artifactId": "236080b8-3bea-4c14-86df-d1f9a14ac7a8",
  "workspaceId": "133c6c70-2e26-4d97-aac1-8ed423dbbf34",
  "displayName": "SM_Finance",
  "type": "semantic_model",
  "userDescription": "Finance semantic model with 11 tables covering GL, budgets, invoices, products, customers",
  "dataSourceInstructions": "Use this source for all financial analysis queries",
  "elements": [...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$schema` | string | Yes | `1.0.0` |
| `artifactId` | string (uuid) | Yes | The Fabric item ID of the data source |
| `workspaceId` | string (uuid) | Yes | The workspace containing the data source |
| `displayName` | string | Yes | Human-readable name |
| `type` | enum | Yes | See data source types below |
| `userDescription` | string | No | Description of what this data source contains |
| `dataSourceInstructions` | string | No | Extra instructions specific to this data source |
| `metadata` | object | No | Property bag for extra parameters |
| `elements` | array | No | Table/column selection and descriptions |

### Data Source Types

| Type Value | Fabric Item |
|-----------|-------------|
| `semantic_model` | Power BI Semantic Model |
| `lakehouse` | Lakehouse (tables + files) |
| `lakehouse-tables` | Lakehouse (tables only) |
| `data_warehouse` | Synapse Data Warehouse |
| `kusto` | KQL Database (Eventhouse) |
| `graph` | GraphQL API |
| `mirrored_database` | Mirrored Database |

### Elements Array

The `elements` array lets you control which tables/columns are visible to the agent and provide descriptions.

For a **semantic model**:
```json
"elements": [
  {
    "display_name": "fact_general_ledger",
    "type": "semantic_model.table",
    "is_selected": true,
    "description": "General ledger entries with amounts, accounts, periods",
    "children": [
      {
        "display_name": "Total Revenue",
        "type": "semantic_model.measure",
        "is_selected": true,
        "description": "SUM of revenue from invoice lines"
      },
      {
        "display_name": "amount_eur",
        "type": "semantic_model.column",
        "data_type": "double",
        "is_selected": true,
        "description": "Transaction amount in EUR"
      }
    ]
  }
]
```

Element types by data source:

| Data Source | Table Type | Column Type | Extra Types |
|------------|-----------|-------------|-------------|
| Semantic Model | `semantic_model.table` | `semantic_model.column` | `semantic_model.measure` |
| Lakehouse | `lakehouse_tables.table` | `lakehouse_tables.column` | `lakehouse_tables.schema` |
| Warehouse | `warehouse_tables.table` | `warehouse_tables.column` | `warehouse_tables.schema` |
| KQL | `kusto.table` | `kusto.column` | `kusto.functions` |

---

## Part 4: fewshots.json (Per Data Source)

Provides example question-query pairs to improve agent accuracy.

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/fewShots/1.0.0/schema.json",
  "fewShots": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "question": "What is the total revenue?",
      "query": "EVALUATE ROW(\"Total Revenue\", [Total Revenue])"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "question": "Show top 5 customers by revenue",
      "query": "EVALUATE TOPN(5, SUMMARIZE(fact_general_ledger, dim_customers[customer_name], \"Revenue\", [Total Revenue]), [Revenue], DESC)"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$schema` | string | Yes | `1.0.0` |
| `fewShots` | array | No | List of example Q&A pairs |
| `fewShots[].id` | string (uuid) | Yes | Unique ID for each example |
| `fewShots[].question` | string | Yes | Natural language question |
| `fewShots[].query` | string | Yes | DAX, SQL, or KQL query |

---

## Part 5: publish_info.json (After Publishing)

Created when the agent is published.

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/publishInfo/1.0.0/schema.json",
  "description": "Finance Controller v1.0 — Published on 2026-03-14"
}
```

---

## Encoding Rules

Every part `payload` must be **base64-encoded UTF-8 JSON**.

```python
import base64, json

def b64(obj):
    """Base64-encode a Python dict/list as JSON."""
    return base64.b64encode(
        json.dumps(obj, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")

# Example
payload = b64({"$schema": "2.1.0"})
# → "eyIkc2NoZW1hIjogIjIuMS4wIn0="
```

The full definition body:
```python
body = {
    "displayName": "Finance_Controller",
    "description": "Finance Controller for P&L, Budget, Cash Flow analysis",
    "type": "DataAgent",
    "definition": {
        "parts": [
            {"path": "Files/Config/data_agent.json", "payload": b64(data_agent_json), "payloadType": "InlineBase64"},
            {"path": "Files/Config/draft/stage_config.json", "payload": b64(stage_config), "payloadType": "InlineBase64"},
            {"path": "Files/Config/draft/semantic_model-SM_Finance/datasource.json", "payload": b64(datasource), "payloadType": "InlineBase64"},
            {"path": "Files/Config/draft/semantic_model-SM_Finance/fewshots.json", "payload": b64(fewshots), "payloadType": "InlineBase64"},
        ]
    }
}
```

---

## Schema URLs Reference

| Part | Schema URL |
|------|-----------|
| data_agent.json | `https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataAgent/2.1.0/schema.json` |
| stage_config.json | `https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/stageConfiguration/1.0.0/schema.json` |
| datasource.json | `https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json` |
| fewshots.json | `https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/fewShots/1.0.0/schema.json` |
| publish_info.json | `https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/publishInfo/1.0.0/schema.json` |

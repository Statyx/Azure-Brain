# Data Source Configuration — Binding Fabric Items to Data Agents

---

## Supported Data Source Types

| Type | Value in JSON | Query Language | Best For |
|------|--------------|----------------|----------|
| Semantic Model | `semantic_model` | DAX | Pre-built measures, star schema, business logic |
| Lakehouse (tables) | `lakehouse-tables` | SQL (Spark) | Raw/curated Delta tables |
| Lakehouse (full) | `lakehouse` | SQL + file access | Tables + unstructured files |
| Data Warehouse | `data_warehouse` | T-SQL | Enterprise DW, complex joins |
| KQL Database | `kusto` | KQL | Log analytics, time series |
| GraphQL | `graph` | GraphQL | Graph relationships |
| **Ontology** | `ontology` | **GQL** | **Knowledge graph: entities + relationships, multi-hop RCA / impact** |
| Mirrored Database | `mirrored_database` | SQL | External DB mirrors |

> **Ontology source** (`type: "ontology"`, folder prefix `ontology-{name}`, `artifactId` = ontology item id): accepted by `updateDefinition` (202 Succeeded, no 400) as of 2026-06 — see `../ontology-agent/`. fewshots `query` = GQL strings. Owned by `ontology-agent`.

---

## Choosing the Right Data Source

```
Do you have a semantic model with DAX measures?
  │
  ├─ YES → Use `semantic_model`
  │         ✅ Best option: pre-computed measures, business logic baked in
  │         ✅ Agent generates DAX (simpler, more accurate)
  │         ✅ Leverages star schema relationships
  │
  └─ NO → Is data in a Lakehouse or Warehouse?
       │
       ├─ Lakehouse → Use `lakehouse-tables`
       │               ⚠️ Agent generates SQL
       │               ⚠️ No pre-built measures — calculations in SQL
       │
       └─ Warehouse → Use `data_warehouse`
                       ⚠️ Agent generates T-SQL
                       ⚠️ Need schema descriptions for accuracy
```

**Recommendation**: When possible, always use a **semantic model** as the data source. The DAX measures encapsulate business logic, making the agent dramatically more accurate.

---

## Folder Naming Convention

Data source files live inside folders named `{type}-{displayName}` under `draft/` and `published/`:

```
Files/Config/draft/semantic-model-SM_Finance/datasource.json
Files/Config/draft/semantic-model-SM_Finance/fewshots.json
```

**Critical**: The folder prefix uses a **hyphen** (`semantic-model-`), not an underscore. The `displayName` part matches the item's display name exactly (case-sensitive).

| Data Source Type | Folder Prefix | Example |
|-----------------|---------------|---------|
| Semantic Model | `semantic-model-` | `semantic-model-SM_Finance` |
| Lakehouse | `lakehouse-` | `lakehouse-MyLakehouse` |
| Data Warehouse | `data_warehouse-` | `data_warehouse-SalesWarehouse` |
| KQL Database | `kusto-` | `kusto-LogsDB` |

---

## Configuring a Semantic Model Data Source

### datasource.json
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
  "artifactId": "<YOUR_MODEL_ID>",
  "workspaceId": "<YOUR_WORKSPACE_ID>",
  "displayName": "SM_Finance",
  "type": "semantic_model",
  "userDescription": "Finance semantic model — 11 tables, 26 DAX measures covering P&L, budgets, cash flow",
  "dataSourceInstructions": "Primary data source for all financial queries. Use DAX measures whenever possible instead of raw column calculations."
}
```

### With Element Selection (Optional but Recommended)
Use `elements` to control which tables/measures are visible and add descriptions:

```json
"elements": [
  {
    "display_name": "fact_general_ledger",
    "type": "semantic_model.table",
    "is_selected": true,
    "description": "Core financial transactions — amounts, accounts, periods, cost centers",
    "children": [
      {"display_name": "Total Revenue", "type": "semantic_model.measure", "is_selected": true, "description": "Sum of all revenue entries"},
      {"display_name": "COGS", "type": "semantic_model.measure", "is_selected": true, "description": "Cost of Goods Sold"},
      {"display_name": "Gross Margin %", "type": "semantic_model.measure", "is_selected": true, "description": "(Revenue - COGS) / Revenue"},
      {"display_name": "EBITDA", "type": "semantic_model.measure", "is_selected": true, "description": "Earnings before interest, taxes, depreciation, amortization"},
      {"display_name": "amount_eur", "type": "semantic_model.column", "data_type": "double", "is_selected": true}
    ]
  },
  {
    "display_name": "dim_calendar",
    "type": "semantic_model.table",
    "is_selected": true,
    "description": "Date dimension — fiscal year, quarter, month, period",
    "children": [
      {"display_name": "fiscal_year", "type": "semantic_model.column", "data_type": "string", "is_selected": true},
      {"display_name": "quarter", "type": "semantic_model.column", "data_type": "string", "is_selected": true},
      {"display_name": "period_month", "type": "semantic_model.column", "data_type": "string", "is_selected": true}
    ]
  }
]
```

### Element Best Practices for Semantic Models
- **Select measures over columns** — Measures encapsulate business logic
- **Add descriptions to measures** — "Gross Margin %" alone is ambiguous; describe the formula
- **Deselect internal/technical columns** — Hide surrogate keys, ETL flags
- **Describe dimension tables** — "dim_calendar: fiscal year, quarter, month" helps the agent pick the right filter
- **Use `dataSourceInstructions`** — Tell the agent to prefer measures: "Always use DAX measures when available rather than raw column calculations"

### Auto-Generating Elements from model.bim

Instead of manually listing every table/column, read `model.bim` and generate the full elements array:

```python
DTYPE_MAP = {
    "string": "string", "int64": "int64", "double": "double",
    "boolean": "boolean", "dateTime": "dateTime", "decimal": "decimal",
}

def build_elements():
    """Read model.bim and generate elements with all tables selected."""
    with open("model.bim", "r", encoding="utf-8") as f:
        model = json.load(f)
    elements = []
    for table in model["model"]["tables"]:
        children = []
        for col in table.get("columns", []):
            children.append({
                "id": None, "display_name": col["name"],
                "type": "semantic_model.column",
                "data_type": DTYPE_MAP.get(col.get("dataType", "string"), "string"),
                "is_selected": True, "description": None, "children": [],
            })
        for measure in table.get("measures", []):
            children.append({
                "id": None, "display_name": measure["name"],
                "type": "semantic_model.measure",
                "is_selected": True, "description": None, "children": [],
            })
        elements.append({
            "id": None, "display_name": table["name"],
            "type": "semantic_model.table", "is_selected": True,
            "description": None, "children": children,
        })
    return elements
```

This ensures the agent sees ALL tables and measures. Without elements, the agent may show "no tables selected" in the portal.

---

## Configuring a Lakehouse Data Source

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
  "artifactId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "workspaceId": "<YOUR_WORKSPACE_ID>",
  "displayName": "LH_Finance",
  "type": "lakehouse-tables",
  "userDescription": "Finance lakehouse with Delta tables for GL, invoices, budgets",
  "dataSourceInstructions": "Tables use Delta format. Join fact tables to dimensions via _id columns. Dates are in ISO format (YYYY-MM-DD).",
  "elements": [
    {
      "display_name": "dbo",
      "type": "lakehouse_tables.schema",
      "is_selected": true,
      "children": [
        {
          "display_name": "fact_general_ledger",
          "type": "lakehouse_tables.table",
          "is_selected": true,
          "description": "General ledger entries with amount_eur, account_id, cost_center_id, period_date"
        }
      ]
    }
  ]
}
```

### Lakehouse-Specific Tips
- Always use `lakehouse-tables` (not `lakehouse`) unless you need file access
- Describe join keys: "Join on `account_id` to `dim_accounts.account_id`"
- Describe data types: "amount_eur is DOUBLE, dates are DATE type"
- Note any partitioning: "Partitioned by fiscal_year"

---

## Configuring a Warehouse Data Source

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
  "artifactId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "workspaceId": "<YOUR_WORKSPACE_ID>",
  "displayName": "WH_Finance",
  "type": "data_warehouse",
  "userDescription": "Finance data warehouse — star schema with fact and dimension tables",
  "dataSourceInstructions": "Use T-SQL. All monetary amounts are in EUR. Join facts to dims using surrogate keys (*_id columns).",
  "elements": [
    {
      "display_name": "dbo",
      "type": "warehouse_tables.schema",
      "is_selected": true,
      "children": [
        {
          "display_name": "fact_general_ledger",
          "type": "warehouse_tables.table",
          "is_selected": true,
          "description": "GL entries"
        }
      ]
    }
  ]
}
```

---

## Multiple Data Sources

A Data Agent can have **multiple data sources**. Each gets its own folder:

```
Files/Config/draft/
├── semantic-model-SM_Finance/
│   ├── datasource.json
│   └── fewshots.json
├── lakehouse-LH_RawData/
│   ├── datasource.json
│   └── fewshots.json
```

**When to use multiple sources:**
- Semantic model for curated metrics + lakehouse for raw data exploration
- Different domains (finance model + HR model)

**Caution**: The agent may struggle to pick the right source for cross-domain questions. Use `dataSourceInstructions` to guide routing.

---

## Pattern — Dual-source: Ontology (GQL) + Semantic Model (DAX)

This is the reusable **RTI Operations / Digital Twin** Data Agent: one agent answers both
*"how do things connect / who is impacted"* (topology, root-cause, impact) **and**
*"what is the number"* (live telemetry metrics), by combining **two** sources with an explicit
routing rule. Proven on the Live Event Operations and Network Operations demos — see the
`digital-twin` preset in `../../../Meta-Brain/SCENARIOS.md` (this pattern is module `M-AGENT`).

**Why two sources?** The ontology is unbeatable for multi-hop RCA/impact via GQL, but the Fabric
IQ TimeSeries selector may return empty telemetry *values* in a Data Agent (see
`../rti-kusto-agent/ontology.md`). So topology → ontology (GQL), numbers → semantic model (DAX)
over the telemetry (mirrored to Direct Lake via `../rti-kusto-agent/kql_onelake_directlake.md`).

| Source | `type` | Query lang | Answers |
|--------|--------|-----------|---------|
| Ontology (knowledge graph) | `ontology` | GQL | topology, relationships, root-cause, **impact** (who/what is affected) |
| Semantic model (Direct Lake) | `semantic_model` | DAX | **live telemetry numbers**: occupancy, wait, density, counts, rankings |

### Folder layout (each source = its own folder, in both draft + published)

```
Files/Config/{draft,published}/
├── ontology-<OntologyName>/
│   ├── datasource.json      (type "ontology", artifactId = ontology id, fewshots = GQL)
│   └── fewshots.json
└── semantic-model-<ModelName>/
    ├── datasource.json      (type "semantic_model", artifactId = model id, elements = table/column/measure tree)
    └── fewshots.json        (fewshots = EVALUATE DAX)
```

### The routing rule (put it in BOTH `aiInstructions` and each `dataSourceInstructions`)

Top-level `aiInstructions` must state the split plainly, e.g.:

> *"Answer by querying a source, never from general knowledge. If the question asks for a
> **number / metric / ranking** (occupancy, wait, density, comfort, counts, capacities) →
> use the **Semantic Model (DAX)** and reuse the existing measures. If it asks **how things
> connect or who is impacted** → use the **Ontology (GQL)**. For 'detect then impact'
> questions: get the number from the Semantic Model, then traverse impact in the Ontology."*

Then reinforce per source with `dataSourceInstructions`:

- **Ontology source**: *"Use for TOPOLOGY, RELATIONSHIPS, ROOT-CAUSE and IMPACT (GQL). Node
  label = entity name, edge label = relationship name. Do NOT use for telemetry numbers — use
  the semantic model."*
- **Semantic model source**: *"Use for ALL live telemetry numbers and aggregates. ALWAYS reuse
  the existing DAX measures; NEVER recompute from raw columns or filter the KPI column (the
  measures already filter it). Group with `dim_*[name]`."*

### Reusable rules

1. **List the key DAX measures by name** in `aiInstructions` — the orchestrator uses them when
   reformulating the question. Without the list it may recompute from raw columns.
2. **Remove telemetry few-shots from the ontology source** — keep the ontology few-shots pure
   topology GQL; put all number few-shots on the semantic model as `EVALUATE` DAX.
3. **Both sources must be emitted in draft AND published** — draft-only agents are invisible in
   the portal.
4. **`elements` tree** on the semantic model source = `semantic_model.table` →
   `semantic_model.column` / `semantic_model.measure` (see the multi-source folder layout below).
5. Validate the routing end-to-end: one number question (must trace `analyze_semantic_model`,
   DAX) and one impact question (must trace `analyze_ontology`, GQL).

---

## Getting the artifactId


To find a data source's ID:

```python
# List semantic models
resp = requests.get(
    f"{API}/workspaces/{WORKSPACE_ID}/items?type=SemanticModel",
    headers=headers
)
for item in resp.json()["value"]:
    print(f"  {item['displayName']}: {item['id']}")

# List lakehouses
resp = requests.get(
    f"{API}/workspaces/{WORKSPACE_ID}/items?type=Lakehouse",
    headers=headers
)
```

Or from `resource_ids.md`:
```
SM_Finance: <YOUR_MODEL_ID>
```

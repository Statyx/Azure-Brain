# MCP Power BI Model — Tool Reference

> **Source**: [powerbi-modeling-mcp](https://github.com/microsoft/powerbi-modeling-mcp)  
> **MCP Tools prefix**: `mcp_powerbi-model_*`  
> **Connects to**: Power BI Desktop, Fabric Service (XML/A), Analysis Services

---

## Why This Matters

The MCP Power BI Model server provides **direct programmatic access** to semantic models without REST API calls or Python scripts. It's the fastest way to:

- **Prep for AI**: Add descriptions, synonyms, set summarizeBy, hide columns — all the metadata that controls DAX generation quality
- **Create/modify measures**: Add new DAX measures directly to a Fabric semantic model
- **Execute DAX**: Validate queries against the live model
- **Deploy models**: Export/import TMDL, deploy to Fabric workspaces
- **Profile performance**: Trace query execution

---

## Connection — Always Start Here

### Connect to Fabric Semantic Model

```
mcp_powerbi-model_connection_operations
  operation: "ConnectFabric"
  workspaceName: "CDR - Demo Marketing"        # exact match
  semanticModelName: "Marketing360_Model"       # exact match
```

### Connect to Power BI Desktop (Local)

```
mcp_powerbi-model_connection_operations
  operation: "Connect"
  connectionString: "Data Source=localhost:<port>"
  # Find port with: operation: "ListLocalInstances"
```

### Other Connection Operations

| Operation | Purpose |
|-----------|---------|
| `ListConnections` | Show all active connections |
| `GetConnection` | Details of a specific connection |
| `Disconnect` | Close a connection |
| `ListLocalInstances` | Find running PBI Desktop instances |
| `ConnectFolder` | Connect to local TMDL folder |

---

## Tool Catalog (21 Tools)

### Core Modeling

| Tool | Key Operations | Use For |
|------|---------------|---------|
| `table_operations` | List, Create, Update, Delete, Refresh, Rename, GetSchema, ExportTMDL | Table CRUD, descriptions, hidden flag |
| `column_operations` | List, Create, Update, Delete, Rename, ExportTMDL | Descriptions, summarizeBy, dataCategory, isHidden, sortByColumn |
| `measure_operations` | List, Create, Update, Delete, Rename, Move, ExportTMDL | DAX measures, descriptions, displayFolder, formatString |
| `relationship_operations` | List, Create, Update, Delete, Find, Activate/Deactivate, ExportTMDL | Star schema, cardinality, cross-filtering |
| `model_operations` | Get, Update, Refresh, Rename, ExportTMDL | Model-level settings (discourageImplicitMeasures, annotations, culture) |

### Advanced Modeling

| Tool | Key Operations | Use For |
|------|---------------|---------|
| `calculation_group_operations` | CreateGroup, ListGroups, CreateItems, ExportTMDL | Time intelligence, currency conversion |
| `calendar_operations` | Create, List, CreateColumnGroups, ExportTMDL | DAX time intelligence calendars (compat >= 1701) |
| `partition_operations` | List, Create, Update, Refresh, ExportTMDL | DirectLake entity partitions, M expressions |
| `perspective_operations` | Create, AddTables, AddMeasures, AddColumns | Model perspectives |
| `user_hierarchy_operations` | Create, AddLevels, ReorderLevels, ExportTMDL | Drill-through hierarchies |

### Queries & Execution

| Tool | Key Operations | Use For |
|------|---------------|---------|
| `dax_query_operations` | Execute, Validate | Run DAX queries, validate syntax |
| `trace_operations` | Start, Stop, Fetch, ExportJSON | Profile queries, capture VertiPaq events |
| `transaction_operations` | Begin, Commit, Rollback | Atomic multi-step changes |

### Metadata & Deployment

| Tool | Key Operations | Use For |
|------|---------------|---------|
| `database_operations` | ExportTMDL, ExportTMSL, ImportFromTmdlFolder, DeployToFabric | Model import/export/deploy |
| `culture_operations` | Create, List, GetValidNames | Localization (en-US, fr-FR) |
| `object_translation_operations` | Create, Update, List | Translated names/descriptions per culture |
| `named_expression_operations` | Create, Update, CreateParameter | Power Query M expressions, parameters |
| `function_operations` | Create, Update, List | DAX functions |
| `query_group_operations` | Create, List | Organize queries in groups |
| `security_role_operations` | Create, CreatePermissions, ExportTMDL | Row-level security (RLS) |
| `connection_operations` | Connect, ConnectFabric, Disconnect | Session management |

---

## Prep for AI Workflows

### 1. Add Descriptions to Tables

```
mcp_powerbi-model_table_operations
  operation: "Update"
  definitions:
    - name: "crm_customers"
      description: "Customer master data. One row per customer. Contains demographics, segment, lifecycle stage."
    - name: "orders"
      description: "E-commerce orders. One row per order. Links to customers via customer_id."
```

### 2. Add Descriptions to Columns

```
mcp_powerbi-model_column_operations
  operation: "Update"
  definitions:
    - tableName: "crm_customers"
      name: "churn_risk_score"
      description: "Churn risk score from 0-100. Higher = more likely to churn. Updated monthly."
      summarizeBy: "none"
    - tableName: "crm_customers"
      name: "customer_id"
      description: "Unique customer identifier (PK)."
      isHidden: true
      summarizeBy: "none"
    - tableName: "crm_customers"
      name: "country"
      description: "Customer country."
      dataCategory: "Country"
```

### 3. Add Descriptions to Measures

```
mcp_powerbi-model_measure_operations
  operation: "Update"
  definitions:
    - name: "Total Revenue"
      description: "Sum of all order line amounts in EUR. Responds to date, customer, product filters."
      displayFolder: "Revenue"
    - name: "Churn Rate %"
      description: "Percentage of churned customers. COUNTROWS(churned) / COUNTROWS(all). Do NOT filter by date."
      displayFolder: "Customer KPIs"
```

### 4. Create New Measures

```
mcp_powerbi-model_measure_operations
  operation: "Create"
  definitions:
    - name: "Revenue YTD"
      tableName: "order_lines"
      expression: "TOTALYTD([Total Revenue], 'orders'[order_at])"
      description: "Year-to-date revenue based on order date."
      formatString: "#,##0.00"
      displayFolder: "Revenue"
```

### 5. Set Model AI Annotations (CopilotInstructions)

```
mcp_powerbi-model_model_operations
  operation: "Update"
  definition:
    discourageImplicitMeasures: true
    annotations:
      - key: "__PBI_CopilotInstructions"
        value: "When users ask about revenue, use [Total Revenue]. Default period is full year 2025."
      - key: "__PBI_TimeIntelligenceEnabled"
        value: "0"
```

### 6. Add Synonyms via Column Annotations

```
mcp_powerbi-model_column_operations
  operation: "Update"
  definitions:
    - tableName: "crm_customers"
      name: "company_name"
      annotations:
        - key: "synonyms"
          value: "[\"customer name\",\"client name\",\"account name\"]"
```

### 7. Set Verified Answers

```
mcp_powerbi-model_model_operations
  operation: "Update"
  definition:
    annotations:
      - key: "__PBI_VerifiedAnswers"
        value: "[{\"Question\":\"what is the email open rate\",\"Answer\":\"The Email Open Rate is...\",\"Query\":\"EVALUATE ROW(\\\"Open Rate\\\", [Open Rate %])\",\"Description\":\"Returns open rate percentage\"}]"
```

### 8. Hide Technical Columns (Batch)

```
mcp_powerbi-model_column_operations
  operation: "Update"
  definitions:
    - tableName: "crm_customers"
      name: "customer_id"
      isHidden: true
      summarizeBy: "none"
    - tableName: "orders"
      name: "customer_id"
      isHidden: true
      summarizeBy: "none"
    - tableName: "orders"
      name: "attributed_campaign_id"
      isHidden: true
      summarizeBy: "none"
```

---

## DAX Query Execution

### Execute a DAX Query

```
mcp_powerbi-model_dax_query_operations
  operation: "Execute"
  query: |
    EVALUATE
      SUMMARIZECOLUMNS(
        'marketing_campaigns'[campaign_name],
        "Revenue", [Total Revenue]
      )
    ORDER BY [Revenue] DESC
  maxRows: 10
```

### Validate DAX Syntax Only

```
mcp_powerbi-model_dax_query_operations
  operation: "Validate"
  query: "EVALUATE ROW(\"Test\", [Total Revenue])"
```

---

## Model Export & Deploy

### Export Full Model as TMDL

```
mcp_powerbi-model_database_operations
  operation: "ExportTMDL"
  tmdlExportOptions:
    maxReturnCharacters: -1
    serializationOptions:
      includeChildren: true
```

### Export to TMDL Folder (Local)

```
mcp_powerbi-model_database_operations
  operation: "ExportToTmdlFolder"
  tmdlFolderPath: "C:\\path\\to\\tmdl_output"
```

### Deploy Model to Fabric

```
mcp_powerbi-model_database_operations
  operation: "DeployToFabric"
  deployToFabricRequest:
    targetWorkspaceName: "CDR - Demo Marketing"
    newDatabaseName: "Marketing360_Model_v2"
```

---

## Query Profiling

### Start a Trace

```
mcp_powerbi-model_trace_operations
  operation: "Start"
  events:
    - "QueryBegin"
    - "QueryEnd"
    - "VertiPaqSEQueryBegin"
    - "VertiPaqSEQueryEnd"
    - "ExecutionMetrics"
```

### Fetch Trace Results

```
mcp_powerbi-model_trace_operations
  operation: "Fetch"
  columns: ["EventClassName", "TextData", "Duration", "CpuTime"]
  clearAfterFetch: true
```

---

## Key Patterns

### Pattern: Full Prep for AI Pipeline

```
1. ConnectFabric → workspace + model name
2. table_operations List → get all tables
3. column_operations List → get all columns
4. measure_operations List → get all measures
5. For each table:  Update description
6. For each column: Update description, summarizeBy, isHidden, dataCategory
7. For each measure: Update description, displayFolder
8. model_operations Update → set discourageImplicitMeasures, CopilotInstructions
9. dax_query_operations Validate → test key measures
10. Disconnect
```

### Pattern: Create Measure + Validate

```
1. measure_operations Create → new measure with expression
2. dax_query_operations Execute → test the measure returns expected value
3. If error → measure_operations Update → fix expression
```

### Pattern: Batch Description Push

```
1. column_operations Update with definitions[] array
   → All columns in one call (supports batch)
   → Each definition: {tableName, name, description, summarizeBy, ...}
2. Same for measures and tables
```

---

## Gotchas & Tips

| Issue | Fix |
|-------|-----|
| Connection not found | Use `ListConnections` to verify, then `ConnectFabric` if needed |
| "Uses last connection if omitted" | Most tools auto-use the last connected model — no need to pass connectionName |
| Annotation values are strings | Synonyms and VerifiedAnswers must be double-encoded JSON strings |
| Measure names are case-sensitive | `[Total Revenue]` ≠ `[total revenue]` |
| Update vs Create | Update modifies existing objects. Create fails if object exists. |
| Move measures between tables | Use `Move` operation, not `Update` (Update can't change tableName) |
| `ExportTMDL` maxReturnCharacters | Set to `-1` for full export, `0` for file-only, `>0` for truncated |
| Batch operations | All CRUD tools support arrays — send multiple definitions in one call |
| Transactions | Use `transaction_operations` Begin/Commit for atomic multi-step changes |
| Refresh after relationship changes | Use `model_operations Refresh` with `refreshType: "Calculate"` |

---

## Integration with Data Agent Workflow

The MCP Power BI tools replace the need for custom Python scripts when doing Prep for AI:

| Task | Before (Python + REST API) | Now (MCP) |
|------|---------------------------|-----------|
| Add descriptions | `getDefinition` → decode b64 → modify model.bim → `updateDefinition` | `column_operations Update` with `description` field |
| Add measures | Build TMDL → push via REST | `measure_operations Create` |
| Set CopilotInstructions | Modify model annotations in model.bim | `model_operations Update` with annotations array |
| Validate DAX | `executeQueries` on api.powerbi.com | `dax_query_operations Execute` |
| Deploy model | Custom script with async LRO | `database_operations DeployToFabric` |

**MCP is faster, safer, and gives immediate feedback** — no base64 encoding, no LRO polling, no manual JSON manipulation.

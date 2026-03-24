# Data Destinations — Output Configuration for Dataflow Gen2

> **Source**: [MS Learn — Dataflow Gen2 Overview](https://learn.microsoft.com/en-us/fabric/data-factory/dataflows-gen2-overview)

## Supported Destinations (from MS Learn)

| Destination | Load Modes | Use Case |
|---|---|---|
| **Fabric Lakehouse Tables** | Replace, Append | Standard analytics — Delta tables via SQL EP |
| **Fabric Lakehouse Files** | N/A | Raw file output |
| **Fabric Warehouse** | Replace, Append | Enterprise warehousing — T-SQL access |
| **Fabric KQL Database** | Append | Real-time / time-series data |
| **Fabric SQL Database** | Replace, Append | Fabric-native SQL |
| **Azure SQL Database** | Replace, Append | Azure PaaS SQL |
| **Azure Data Explorer (Kusto)** | Append | External ADX clusters |
| **Azure Data Lake Gen2** | N/A | File output to ADLS |
| **Snowflake Database** | Replace, Append | Cross-platform data sharing |
| **SharePoint Files** | N/A | File output to SharePoint |

> **Rule**: The destination item (Lakehouse/Warehouse/KQL DB) **must exist** before the Dataflow runs. Dataflow Gen2 can create the table on first run, but cannot create the item itself.

---

## Lakehouse Table Destination

### Configuration via API
When pushing a Dataflow definition via the API, the destination is configured in the mashup document's metadata annotation.

```json
{
  "destinationSettings": {
    "type": "LakehouseTable",
    "lakehouseId": "<lakehouse-guid>",
    "workspaceId": "<workspace-guid>",
    "tableName": "dim_customers",
    "loadMode": "Replace"
  }
}
```

### Load Modes

| Mode | Behavior | When to Use |
|---|---|---|
| `Replace` | Drops and recreates the table on each run | Dimension tables, full snapshots, small datasets |
| `Append` | Adds new rows to existing table | Incremental loads, fact tables, daily batches |

### Column Mapping
The Dataflow maps columns from the Power Query output to the destination table:
- On **first run** with Replace mode: table schema is created from query output
- On **subsequent runs** with Append mode: columns must match by name
- **Type mapping**: M types are mapped to Delta types:

| M Type | Delta Type |
|---|---|
| `type text` | `string` |
| `type number` | `double` |
| `Int64.Type` | `long` |
| `type date` | `date` |
| `type datetime` | `timestamp` |
| `type logical` | `boolean` |
| `type binary` | `binary` |
| `Currency.Type` | `decimal(19,4)` |
| `Percentage.Type` | `double` |

### Staging Lakehouse
A **staging lakehouse** is required when using Fabric compute for transformations. Without it, the Dataflow will fail for large datasets.

```
Staging flow:
  Source → [Staging Lakehouse (temp parquet)] → Transform → Destination Lakehouse Table
```

- **Set at the Dataflow level** — one staging Lakehouse per Dataflow
- The staging Lakehouse can be the same as or different from the destination Lakehouse
- Temporary files in staging are auto-cleaned

---

## Warehouse Table Destination

### Configuration
```json
{
  "destinationSettings": {
    "type": "WarehouseTable",
    "warehouseId": "<warehouse-guid>",
    "workspaceId": "<workspace-guid>",
    "schemaName": "dbo",
    "tableName": "dim_customers",
    "loadMode": "Replace"
  }
}
```

### Type Mapping (M → Warehouse SQL)

| M Type | Warehouse SQL Type |
|---|---|
| `type text` | `varchar(8000)` |
| `Int64.Type` | `bigint` |
| `type number` | `float` |
| `type date` | `date` |
| `type datetime` | `datetime2(6)` |
| `type logical` | `bit` |
| `Currency.Type` | `decimal(19,4)` |

### Notes
- Warehouse destination uses the T-SQL endpoint
- Schema creation is automatic on first Replace
- For Append mode, table must exist with compatible schema

---

## KQL Database Destination

### Configuration
```json
{
  "destinationSettings": {
    "type": "KQLDatabaseTable",
    "kqlDatabaseId": "<database-guid>",
    "workspaceId": "<workspace-guid>",
    "tableName": "SensorReadings",
    "loadMode": "Append"
  }
}
```

### Notes
- KQL destinations typically use **Append** mode (time-series data is additive)
- KQL ingestion mapping is auto-generated from column names
- Ensure column names in the query output match KQL table columns exactly
- Use `type datetime` for KQL `datetime` columns — this is mandatory for time-based queries

---

## Incremental Refresh Configuration

Incremental refresh lets Dataflow only process new/changed data on each run.

### Setup Steps
1. Create two **date/datetime parameters** in the Dataflow:
   - `RangeStart` (type `datetime`)
   - `RangeEnd` (type `datetime`)
2. Filter the source query using these parameters:
   ```m
   Table.SelectRows(Source, each [ModifiedDate] >= RangeStart and [ModifiedDate] < RangeEnd)
   ```
3. Configure incremental refresh on the destination:
   - **Refresh period**: e.g., last 30 days
   - **Archive period**: e.g., 3 years
   - The engine manages partition boundaries automatically

### When to Use
- Fact tables with > 100K rows
- Sources with a reliable datetime column for changes
- Daily batch processing patterns

### When NOT to Use
- Dimension tables (usually small enough for full Replace)
- Data without a reliable change-tracking column
- Near-real-time scenarios (use EventStream instead)

---

## Multi-Destination Pattern

A single Dataflow can have multiple queries, each going to a different destination.

```
Dataflow Gen2: "Customer ETL"
  ├── Query: "dim_customers"  → Lakehouse Table (Replace)
  ├── Query: "dim_addresses"  → Lakehouse Table (Replace)  
  └── Query: "fact_orders"    → Lakehouse Table (Append)
```

### Implementation
Each query in the mashup document can have its own destination annotation:
```m
// Query 1 — goes to dim_customers table
section Section1;

shared dim_customers = let
    Source = ...,
    Result = ...
in
    Result;

shared dim_addresses = let
    Source = ...,
    Result = ...
in
    Result;
```

Each `shared` query maps to one destination table.

---

## Scheduling Refresh

### Via API
```python
def schedule_dataflow_refresh(workspace_id, dataflow_id, token):
    """Trigger an on-demand refresh of a Dataflow Gen2."""
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{dataflow_id}/jobs/instances?jobType=Pipeline"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    
    if response.status_code == 202:
        location = response.headers.get("Location")
        print(f"Refresh started. Monitor at: {location}")
        return location
    else:
        raise Exception(f"Failed to start refresh: {response.status_code} — {response.text}")
```

### Via Pipeline
Dataflows Gen2 can be triggered as activities within a Fabric Data Pipeline:
```
Pipeline: "Daily ETL"
  ├── Activity 1: Dataflow "Staging Load"   (wait for completion)
  ├── Activity 2: Dataflow "Transform"      (wait for completion)
  └── Activity 3: Notebook "Post-Process"   (wait for completion)
```

### Via Schedule
- Set in the Fabric portal under the Dataflow settings
- Supports: daily, hourly, or custom cron-like schedules
- Max 48 refreshes per day

---

## Common Destination Errors

| Error | Cause | Fix |
|---|---|---|
| "Destination not found" | Lakehouse/Warehouse was deleted or renamed | Recreate the destination item and reconfigure |
| "Schema mismatch" | Column names or types changed between runs | Use Replace mode or ALTER the destination table |
| "Staging lakehouse required" | Transformation requires compute but no staging set | Assign a staging Lakehouse in Dataflow settings |
| "Table locked" | Another process is writing to the same table | Avoid concurrent writes; schedule Dataflows sequentially |
| "Timeout during load" | Large dataset with complex transforms | Enable staging; simplify query; filter rows earlier |
| "Column not found" | M query output column name doesn't match destination | Rename columns in M to match destination schema |

---

## Decision Guide: Which Destination?

```
Is the data for...
├── Analytics / Reporting?
│   ├── Do you need T-SQL queries?
│   │   ├── Yes → Warehouse Table
│   │   └── No → Lakehouse Table (recommended default)
│   └── Time-series / Real-time queries?
│       └── Yes → KQL Database Table
└── Staging / Intermediate?
    └── Use staging Lakehouse (auto-managed)
```

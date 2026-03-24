# Lakehouse Agent — Instructions

## System Prompt

You are an expert at creating and managing Microsoft Fabric Lakehouses — the unified storage layer combining raw files and Delta tables. You understand OneLake DFS API, Spark notebooks (PySpark), Delta Lake management, SQL Endpoint, Shortcuts, and medallion architecture patterns.

**Before any Lakehouse work**, load this file plus `onelake_operations.md` and `spark_notebooks.md`.

---

## Mandatory Rules

### Rule 1: Files/ Is for Raw Data, Tables/ Is for Delta Only
- `Files/` — raw files (CSV, Parquet, JSON, images, anything). Accessible via OneLake DFS API.
- `Tables/` — **Delta Lake tables only**. Created by Spark notebooks, `COPY INTO`, or EventStream destinations.

> Uploading a CSV to `Tables/` does NOT create a Delta table. Always use `Files/` for uploads, then Spark notebook to create Delta tables.

### Rule 2: Use the 3-Step DFS Protocol for OneLake Uploads
OneLake implements ADLS Gen2 protocol. Every file upload requires 3 sequential HTTP calls:
1. `PUT ?resource=file` — Create empty file
2. `PATCH ?action=append&position=0` — Upload content
3. `PATCH ?action=flush&position={byte_count}` — Commit

The `position` in flush **MUST** equal the exact byte count uploaded.

**Token**: `https://storage.azure.com` (NOT `https://api.fabric.microsoft.com`)

### Rule 3: Wait for SQL Endpoint After Lakehouse Creation
The SQL Endpoint is auto-provisioned after Lakehouse creation but takes 30–120 seconds. Always poll until available:
```python
for _ in range(20):
    items = requests.get(f"{API}/workspaces/{WS_ID}/items?type=SQLEndpoint", headers=headers).json()["value"]
    sql_ep = [i for i in items if i["displayName"] == lakehouse_name]
    if sql_ep:
        break
    time.sleep(10)
```

### Rule 4: Notebooks Use `.py` Format, NOT `.ipynb`
Fabric notebooks use a proprietary `.py` format:
- Header: `# Fabric notebook source` + 2 blank lines
- Cell separators: `# CELL ********************` or `# MARKDOWN ********************`
- Upload path: `notebook-content.py`
- **Never** include `"format": "ipynb"` in the definition JSON

### Rule 5: Delta Table Names Follow Convention
- Dimension tables: `dim_` prefix (e.g., `dim_customers`, `dim_products`)
- Fact tables: `fact_` prefix (e.g., `fact_sales`, `fact_general_ledger`)
- Streaming tables: descriptive name (e.g., `SensorReading`, `EquipmentAlert`)
- All lowercase, underscores for spaces

---

## Decision Trees

### "I need to load data into a Lakehouse"
```
├── Where is the data?
│   ├── Local files (CSV/Parquet/JSON)
│   │   ├── Upload to Files/ → OneLake DFS API (3-step protocol)
│   │   └── Transform to Delta → Spark notebook (CSV → Delta pattern)
│   ├── Azure Blob / ADLS Gen2
│   │   ├── One-time load → Copy Job or Pipeline Copy Activity
│   │   ├── Ongoing real-time → EventStream → Lakehouse destination
│   │   └── Virtual access → Shortcut (no data movement)
│   ├── Azure SQL / On-premises DB
│   │   └── Pipeline Copy Activity (via gateway if on-prem)
│   ├── S3 / GCS
│   │   └── Shortcut (preferred) or Copy Job
│   └── Streaming source
│       └── EventStream → Lakehouse destination (append-only Delta)
├── Is it a one-time or ongoing load?
│   ├── One-time → Upload + Notebook (overwrite mode)
│   └── Ongoing → Incremental load (merge/upsert) or append
└── Post-load: verify with SQL Endpoint query or Spark read
```

### "I need to transform data"
```
├── Simple rename/cast/filter → Spark notebook (PySpark)
├── Complex joins / aggregation → Spark notebook (Spark SQL)
├── Medallion layering → Bronze→Silver→Gold notebooks
├── Incremental update → Delta merge/upsert pattern
└── Deduplication → dropDuplicates() or Delta merge
```

### "I need to optimize table performance"
```
├── Large table with slow queries
│   ├── Run OPTIMIZE → compacts small files into larger ones
│   ├── Add Z-ORDER → co-locates data by frequently filtered columns
│   ├── Add V-ORDER → Fabric-specific Parquet optimization
│   └── Use Table Maintenance API → POST /lakehouses/{id}/tables/{name}/maintenance
│       ├── optimizeSettings: { zOrderBy: [...], vOrder: true }
│       └── vacuumSettings: { retentionPeriod: "7:00:00:00" }
├── Old data accumulated
│   └── Run VACUUM → removes old Delta log files (retention format: "d:hh:mm:ss")
├── Schema changed
│   └── Use mergeSchema option or ALTER TABLE
├── Too many small files
│   └── OPTIMIZE + VACUUM
└── Need materialized views
    └── Use MaterializedLakeViews API (schedule refresh, max 20 schedulers)
```

---

## Lakehouse Architecture

```
Lakehouse
├── Files/                          ← Raw file storage (OneLake DFS)
│   ├── raw/                        ← Landing zone (CSVs, JSON, Parquet)
│   │   ├── customers/
│   │   ├── products/
│   │   └── sales/
│   └── processed/                  ← Intermediate files (optional)
├── Tables/                         ← Delta Lake tables
│   ├── dim_customers               ← Dimension table
│   ├── dim_products                ← Dimension table
│   ├── fact_sales                  ← Fact table
│   └── staging_raw_events          ← Streaming append table
└── SQL Endpoint                    ← Auto-provisioned T-SQL access
```

---

## API Quick Reference

> **Scopes**: `Item.Read.All`, `Item.ReadWrite.All`, `Lakehouse.Read.All`, `Lakehouse.ReadWrite.All`  
> Service principals and managed identities are supported.

### Core CRUD

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create Lakehouse | POST | `/v1/workspaces/{wsId}/lakehouses` |
| Get Lakehouse | GET | `/v1/workspaces/{wsId}/lakehouses/{lhId}` |
| List Lakehouses | GET | `/v1/workspaces/{wsId}/lakehouses` |
| Update Lakehouse | PATCH | `/v1/workspaces/{wsId}/lakehouses/{lhId}` |
| Delete Lakehouse | DELETE | `/v1/workspaces/{wsId}/lakehouses/{lhId}` |
| Get Definition | POST | `/v1/workspaces/{wsId}/lakehouses/{lhId}/getDefinition` |
| Update Definition | POST | `/v1/workspaces/{wsId}/lakehouses/{lhId}/updateDefinition` |

### Tables API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List Tables | GET | `/v1/workspaces/{wsId}/lakehouses/{lhId}/tables` |
| Load Table | POST | `/v1/workspaces/{wsId}/lakehouses/{lhId}/tables/{tableName}/load` |

### Table Maintenance API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Run Table Maintenance | POST | `/v1/workspaces/{wsId}/lakehouses/{lhId}/tables/{tableName}/maintenance` |

### Livy Sessions API (Beta)

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List Livy Sessions | GET | `/v1/workspaces/{wsId}/lakehouses/{lhId}/livySessions` |
| Get Livy Session | GET | `/v1/workspaces/{wsId}/lakehouses/{lhId}/livySessions/{sessionId}` |

### Materialized Lake Views API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Refresh MLV (on-demand) | POST | `/v1/workspaces/{wsId}/lakehouses/{lhId}/materializedLakeViews/refresh` |
| Create MLV Schedule | POST | `/v1/workspaces/{wsId}/lakehouses/{lhId}/materializedLakeViews/schedule` |
| Update MLV Schedule | PATCH | `/v1/workspaces/{wsId}/lakehouses/{lhId}/materializedLakeViews/schedule/{scheduleId}` |
| Delete MLV Schedule | DELETE | `/v1/workspaces/{wsId}/lakehouses/{lhId}/materializedLakeViews/schedule/{scheduleId}` |

### Shortcut Operations

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create Shortcut | POST | `/v1/workspaces/{wsId}/items/{lhId}/shortcuts` |
| Get Shortcut | GET | `/v1/workspaces/{wsId}/items/{lhId}/shortcuts/{name}` |
| Delete Shortcut | DELETE | `/v1/workspaces/{wsId}/items/{lhId}/shortcuts/{name}` |

### OneLake DFS (File Upload)

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Upload File (3-step) | PUT+PATCH+PATCH | `https://onelake.dfs.fabric.microsoft.com/{wsId}/{lhId}/Files/...` |

### Create Lakehouse
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/lakehouses",
    headers=headers,
    json={
        "displayName": "SalesLakehouse",
        "description": "Central data store for sales analytics"
    }
)
lakehouse_id = resp.json()["id"]
```

### Create Schema-Enabled Lakehouse (Preview)
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/lakehouses",
    headers=headers,
    json={
        "displayName": "EnterpriseLakehouse",
        "description": "Schema-enabled lakehouse with multiple schemas",
        "creationPayload": {
            "enableSchemas": True
        }
    }
)
# Response includes defaultSchema in properties
```

### Load Table via API
```python
# Load a CSV/Parquet file from OneLake Files/ into a Delta table
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/lakehouses/{LH_ID}/tables/dim_customers/load",
    headers=headers,
    json={
        "relativePath": "Files/raw/customers.csv",
        "pathType": "File",          # "File" or "Folder"
        "mode": "Overwrite",         # "Overwrite" or "Append"
        "formatOptions": {
            "format": "Csv",         # "Csv" or "Parquet"
            "header": True,
            "delimiter": ","
        }
    }
)
# Returns 202 with Location header for LRO polling
```

### Table Maintenance (Optimize + Vacuum)
```python
# Optimize with Z-Order and V-Order
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/lakehouses/{LH_ID}/tables/fact_sales/maintenance",
    headers=headers,
    json={
        "executionData": {
            "optimizeSettings": {
                "zOrderBy": ["customer_id", "sale_date"],
                "vOrder": True
            }
        }
    }
)

# Vacuum with retention period (format: "d:hh:mm:ss")
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/lakehouses/{LH_ID}/tables/fact_sales/maintenance",
    headers=headers,
    json={
        "executionData": {
            "vacuumSettings": {
                "retentionPeriod": "7:00:00:00"  # 7 days
            }
        }
    }
)
```

### Lakehouse Properties (from GET response)
```json
{
    "id": "lakehouse-guid",
    "displayName": "SalesLakehouse",
    "properties": {
        "oneLakeTablesPath": "https://onelake.dfs.fabric.microsoft.com/{wsId}/{lhId}/Tables",
        "oneLakeFilesPath": "https://onelake.dfs.fabric.microsoft.com/{wsId}/{lhId}/Files",
        "sqlEndpointProperties": {
            "id": "sql-ep-guid",
            "connectionString": "...",
            "provisioningStatus": "Success"
        },
        "defaultSchema": "dbo"
    }
}
```
> **sqlEndpointProperties.provisioningStatus**: `InProgress` → `Success` or `Failed`. Poll until `Success`.

---

## Medallion Architecture

| Layer | Purpose | Table Prefix | Data Quality |
|-------|---------|-------------|-------------|
| **Bronze** | Raw ingestion, minimal transformation | `bronze_` or `raw_` | As-is from source |
| **Silver** | Cleansed, deduplicated, typed | `dim_`, `fact_` | Validated, typed |
| **Gold** | Aggregated, business-ready | `agg_`, `summary_` | Business rules applied |

### Implementation Pattern

```python
# Bronze: Read raw CSV
df_bronze = spark.read.format("csv").option("header", True).option("inferSchema", True).load("Files/raw/sales/")

# Silver: Cleanse and type
from pyspark.sql.functions import col, to_date, trim, upper
df_silver = df_bronze \
    .withColumn("customer_name", trim(upper(col("customer_name")))) \
    .withColumn("sale_date", to_date(col("sale_date"), "yyyy-MM-dd")) \
    .dropDuplicates(["transaction_id"])

# Gold: Aggregate
df_gold = df_silver.groupBy("product_id", "sale_date").agg(
    {"amount": "sum", "quantity": "sum"}
)

# Write each layer
df_bronze.write.format("delta").mode("overwrite").save("Tables/bronze_sales")
df_silver.write.format("delta").mode("overwrite").save("Tables/fact_sales")
df_gold.write.format("delta").mode("overwrite").save("Tables/agg_daily_sales")
```

---

## Shortcut Configuration

### OneLake Shortcut (Cross-Workspace)
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/items/{LH_ID}/shortcuts",
    headers=headers,
    json={
        "name": "shared_dimensions",
        "path": "Tables",
        "target": {
            "type": "OneLake",
            "oneLake": {
                "workspaceId": "{sourceWorkspaceId}",
                "itemId": "{sourceLakehouseId}",
                "path": "Tables/dim_customers"
            }
        }
    }
)
```

### ADLS Gen2 Shortcut
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/items/{LH_ID}/shortcuts",
    headers=headers,
    json={
        "name": "external_data",
        "path": "Files",
        "target": {
            "type": "AdlsGen2",
            "adlsGen2": {
                "connectionId": "<fabric-connection-guid>",
                "location": "https://storageaccount.dfs.core.windows.net",
                "subpath": "/container/folder"
            }
        }
    }
)
```

### S3 Shortcut
```python
{
    "name": "s3_data",
    "path": "Files",
    "target": {
        "type": "AmazonS3",
        "amazonS3": {
            "connectionId": "<fabric-connection-guid>",
            "location": "https://bucket.s3.amazonaws.com",
            "subpath": "/prefix/"
        }
    }
}
```

---

## Error Recovery

| Error | Cause | Fix |
|-------|-------|-----|
| 404 on file upload | Wrong base URL or token | Use `storage.azure.com` token, verify workspace/item IDs |
| Flush position mismatch | byte count ≠ actual bytes uploaded | Count bytes precisely (file size, not string length) |
| SQL Endpoint not found | Just created Lakehouse | Poll with retries (30–120s provisioning delay) |
| `InvalidNotebookContent` | Used `"format": "ipynb"` | Remove `format` field; use `notebook-content.py` path |
| Delta table not visible | Notebook write not committed | Check Spark job completed; verify path starts with `Tables/` |
| Shortcut "connection not found" | Invalid connectionId | Create the connection in Fabric portal first |

---

## Cross-References

| Topic | Agent | File |
|-------|-------|------|
| Pipeline orchestration for Lakehouse loads | orchestrator-agent | `pipelines.md` |
| EventStream → Lakehouse destination | eventstream-agent | `sources_destinations.md` |
| Semantic Model over Lakehouse (Direct Lake) | semantic-model-agent | `model_deployment.md` |
| Ontology NonTimeSeries bindings | ontology-agent | `entity_types_bindings.md` |
| Fabric CLI file operations | fabric-cli-agent | `commands_reference.md` |

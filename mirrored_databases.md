# Mirrored Databases — Patterns & API

> Replicate external databases into Fabric OneLake as read-only Delta tables with near real-time sync.

---

## Concept

Fabric Mirroring creates a continuously-synchronized **read-only copy** of an external database inside a Fabric workspace. Data lands as Delta/Parquet in OneLake and is queryable via a SQL Analytics Endpoint (same as Lakehouse).

```
┌─────────────────┐    CDC / Change Feed     ┌──────────────────┐
│  External DB    │  ─────────────────────►   │  Mirrored DB     │
│  (Azure SQL,    │     Near real-time        │  (OneLake Delta)  │
│   Cosmos, etc.) │                           │  + SQL Endpoint   │
└─────────────────┘                           └──────────────────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │ Semantic Model │
                                              │ / Reports      │
                                              └───────────────┘
```

## Supported Sources

| Source | Sync Method | Notes |
|--------|-----------|-------|
| Azure SQL Database | CDC (Change Data Capture) | CDC must be enabled on source tables |
| Azure SQL Managed Instance | CDC | Same as Azure SQL DB |
| Azure Cosmos DB | Change Feed | NoSQL API only; analytical store recommended |
| Snowflake | Change tracking | Read from Snowflake → Delta in OneLake |
| Azure Databricks | Unity Catalog | Delta Sharing protocol |
| Azure Database for PostgreSQL | Logical replication | Flexible Server only |
| Azure Database for MySQL | Binlog replication | Flexible Server only |

## API Reference

Base URL: `https://api.fabric.microsoft.com/v1`

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create mirrored database | `POST` | `/workspaces/{wsId}/mirroredDatabases` |
| List mirrored databases | `GET` | `/workspaces/{wsId}/mirroredDatabases` |
| Get mirrored database | `GET` | `/workspaces/{wsId}/mirroredDatabases/{id}` |
| Get definition | `POST` | `/workspaces/{wsId}/mirroredDatabases/{id}/getDefinition` |
| Update definition | `POST` | `/workspaces/{wsId}/mirroredDatabases/{id}/updateDefinition` |
| Delete | `DELETE` | `/workspaces/{wsId}/mirroredDatabases/{id}` |
| Start mirroring | `POST` | `/workspaces/{wsId}/mirroredDatabases/{id}/startMirroring` |
| Stop mirroring | `POST` | `/workspaces/{wsId}/mirroredDatabases/{id}/stopMirroring` |
| Get mirroring status | `GET` | `/workspaces/{wsId}/mirroredDatabases/{id}/getMirroringStatus` |

---

## Creation Pattern (Azure SQL DB)

### Prerequisites
1. **CDC enabled** on the source Azure SQL DB tables:
```sql
-- On the Azure SQL DB source
EXEC sys.sp_cdc_enable_db;

EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'fact_sales',
    @role_name     = NULL;
```

2. **Connection** stored as Fabric connection or connection string

### Create via API
```python
import requests

token = get_fabric_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

body = {
    "displayName": "Mirror_SalesDB",
    "description": "Mirror of Azure SQL production sales database",
    "definition": {
        "parts": [
            {
                "path": "mirroring.json",
                "payload": encode_base64({
                    "properties": {
                        "source": {
                            "type": "AzureSqlDatabase",
                            "typeProperties": {
                                "connectionId": "<fabric-connection-id>"
                            }
                        },
                        "target": {
                            "type": "MountedRelationalDatabase"
                        }
                    }
                })
            }
        ]
    }
}

resp = requests.post(
    f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/mirroredDatabases",
    headers=headers,
    json=body
)
mirror_id = resp.json()["id"]
```

### Start Mirroring
```python
requests.post(
    f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/mirroredDatabases/{mirror_id}/startMirroring",
    headers=headers
)
```

### Monitor Status
```python
status = requests.get(
    f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/mirroredDatabases/{mirror_id}/getMirroringStatus",
    headers=headers
).json()
# status["status"] → "Running", "Stopped", "Initializing", etc.
```

---

## Decision Tree: Lakehouse vs. Mirror vs. Shortcut

```
Where does the source data live?
  │
  ├─ External relational DB (SQL, Cosmos, Snowflake, PostgreSQL)
  │     │
  │     ├─ Do you need near real-time sync?
  │     │     ├─ YES → Mirrored Database
  │     │     └─ NO  → Pipeline Copy Activity → Lakehouse
  │     │
  │     └─ Is it one-time / batch?
  │           └─ YES → Pipeline Copy Activity → Lakehouse
  │
  ├─ Azure Storage (ADLS Gen2 / Blob)
  │     │
  │     ├─ Do you own the storage?
  │     │     ├─ YES → OneLake Shortcut (zero-copy)
  │     │     └─ NO  → Shortcut if read-only OK, else Copy
  │     │
  │     └─ Is it Delta format?
  │           ├─ YES → Shortcut (best)
  │           └─ NO  → Shortcut for Parquet/CSV; Copy for others
  │
  └─ Streaming (IoT, events)
        └─ EventStream → Lakehouse or Eventhouse
```

---

## Table Selection

By default, Mirroring replicates **all tables** with CDC enabled. To select specific tables:

```python
# Update definition to select specific tables
update_body = {
    "definition": {
        "parts": [
            {
                "path": "mirroring.json",
                "payload": encode_base64({
                    "properties": {
                        "source": {
                            "type": "AzureSqlDatabase",
                            "typeProperties": {
                                "connectionId": "<fabric-connection-id>",
                                "tableSelection": {
                                    "includedTables": [
                                        {"schemaName": "dbo", "tableName": "fact_sales"},
                                        {"schemaName": "dbo", "tableName": "dim_customers"},
                                        {"schemaName": "dbo", "tableName": "dim_products"}
                                    ]
                                }
                            }
                        }
                    }
                })
            }
        ]
    }
}

requests.post(
    f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/mirroredDatabases/{mirror_id}/updateDefinition",
    headers=headers,
    json=update_body
)
```

---

## Gotchas

1. **Read-only** — Mirrored tables cannot be written to. They are Delta read-only. Any writes must go to the source database.
2. **CDC required** — For Azure SQL DB, CDC must be enabled on each table you want to mirror. Tables without CDC are skipped.
3. **Initial sync can be slow** — The first sync copies all data. For large tables (100M+ rows), this can take hours.
4. **Schema changes** — Adding columns to the source is auto-detected. Dropping columns may require stopping and restarting mirroring.
5. **SQL Endpoint only** — No Spark/notebook write access. Use the SQL Analytics Endpoint for queries, same as Lakehouse.
6. **One source per mirror** — Each Mirrored Database connects to one external database. Multiple sources = multiple mirrors.
7. **Capacity required** — Mirroring consumes CU. Monitor via capacity metrics.
8. **Cosmos DB** — Only NoSQL API is supported. Enable analytical store for best performance.
9. **Latency** — Near real-time means seconds-to-minutes, not milliseconds. Typical latency: 5-30 seconds for Azure SQL, 1-5 minutes for Cosmos DB.
10. **Not a Lakehouse** — A Mirrored DB has a SQL Endpoint but is NOT a Lakehouse. You cannot attach notebooks to it or run Spark jobs on it directly. Cross-query from a Lakehouse/Warehouse instead.

# MCP Kusto — Tool Reference

## Overview

The MCP Kusto tools provide **read-only** access to Kusto (Azure Data Explorer / Fabric Eventhouse) clusters. These are available as MCP tools in Copilot and can be used to explore schemas, sample data, and run KQL queries.

All tools are prefixed with `mcp_azure_mcp_kusto`.

## Tools

### 1. kusto_query
Run a KQL query against a database.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `database` | ✅ | Database name |
| `query` | ✅ | KQL query string |
| `cluster-uri` | ✅* | Cluster URI (e.g., `https://xyz.z0.kusto.fabric.microsoft.com`) |
| `cluster` | ✅* | Cluster name (alternative to cluster-uri) |
| `subscription` | - | Azure subscription ID (needed with `cluster` param) |

*Provide either `cluster-uri` or `cluster` + `subscription`.

**Usage**: Execute any KQL query — aggregations, time-series analysis, joins, etc.

```
kusto_query(
    database="RefineryKQL",
    query="SensorReading | where IsAnomaly == true | take 10",
    cluster-uri="https://trd-abc123.z0.kusto.fabric.microsoft.com"
)
```

### 2. kusto_sample
Get sample rows from a table.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `database` | ✅ | Database name |
| `table` | ✅ | Table name |
| `cluster-uri` | ✅* | Cluster URI |
| `limit` | - | Number of rows (default: 5) |

**Usage**: Quick preview of table contents.

```
kusto_sample(
    database="RefineryKQL",
    table="SensorReading",
    cluster-uri="https://trd-abc123.z0.kusto.fabric.microsoft.com",
    limit=10
)
```

### 3. kusto_cluster_list
List Kusto clusters in a subscription.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `subscription` | ✅ | Azure subscription ID |

**Usage**: Discover available clusters/Eventhouses.

### 4. kusto_cluster_get
Get details about a specific cluster.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cluster` | ✅ | Cluster name or URI |
| `subscription` | - | Azure subscription ID |

**Usage**: Get cluster URI, state, SKU, and other metadata.

### 5. kusto_database_list
List databases in a cluster.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cluster-uri` | ✅ | Cluster URI |

**Usage**: Discover available KQL databases in an Eventhouse.

### 6. kusto_table_list
List tables in a database.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `database` | ✅ | Database name |
| `cluster-uri` | ✅* | Cluster URI |
| `cluster` | ✅* | Cluster name (alternative) |
| `subscription` | - | Azure subscription ID |

**Usage**: See all tables in a KQL database.

### 7. kusto_table_schema
Get schema (columns + types) for a table.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `database` | ✅ | Database name |
| `table` | ✅ | Table name |
| `cluster-uri` | ✅* | Cluster URI |
| `cluster` | ✅* | Cluster name (alternative) |
| `subscription` | - | Azure subscription ID |

**Usage**: Get column names and data types.

---

## Finding the Cluster URI

For Fabric Eventhouses, the cluster URI follows this pattern:
```
https://{eventhouse-guid}.{region}.kusto.fabric.microsoft.com
```

You can find it by:
1. **MCP**: `kusto_cluster_list(subscription="...")` then look for the Eventhouse
2. **Fabric API**: `GET /workspaces/{id}/items?type=Eventhouse` → find `queryServiceUri` in properties
3. **Portal**: Open Eventhouse → Properties → Query URI

## Common Patterns

### Explore a new Eventhouse
```
1. kusto_database_list(cluster-uri="https://...")
2. kusto_table_list(database="MyDB", cluster-uri="https://...")
3. kusto_table_schema(database="MyDB", table="SensorReading", cluster-uri="https://...")
4. kusto_sample(database="MyDB", table="SensorReading", cluster-uri="https://...", limit=5)
```

### Diagnose anomalies
```
kusto_query(
    database="MyDB",
    query="""
        SensorReading
        | where Timestamp > ago(1h) and IsAnomaly == true
        | summarize Count=count() by SensorId
        | top 10 by Count desc
    """,
    cluster-uri="https://..."
)
```

### Check table sizes
```
kusto_query(
    database="MyDB",
    query=".show tables details | project TableName, TotalRowCount, TotalExtentSize",
    cluster-uri="https://..."
)
```

## Limitations

- **Read-only**: Cannot create tables, ingest data, or modify schema
- **No management commands**: `.create table`, `.ingest`, `.drop` are not available through MCP
- **For write operations**: Use the Kusto REST Management API directly (`{clusterUri}/v1/rest/mgmt`)
- **Auth**: MCP handles authentication automatically via Azure login context

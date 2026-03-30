# Eventhouse Authoring — Table Management, Ingestion & Policies

> Source: [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) — EVENTHOUSE-AUTHORING-CORE.md

## Table Management

### Idempotent Table Creation
Always use `.create-merge table` (NOT `.create table`) — it creates if new, merges schema if exists:

```kql
.create-merge table SensorReading
    (SensorId:string, Timestamp:datetime, ReadingValue:real, Unit:string, IsAnomaly:bool)
```

### Alter Table (Add Columns)
```kql
.alter-merge table SensorReading (NewColumn:string)
```

### Drop Column
```kql
.alter table SensorReading drop column NewColumn
```

### Rename Column
```kql
.rename column SensorReading.OldName to NewName
```

### Drop Table
```kql
.drop table SensorReading ifexists
```

---

## Data Ingestion Patterns

### 1. Inline Ingestion (< 64 KB per batch)
Best for small datasets, testing, and seed data:
```kql
.ingest inline into table SensorReading with (format='csv') <|
SN001,2025-12-01T01:00:00,450.2,DegF,false
SN002,2025-12-01T01:00:00,510.0,PSI,false
```

### 2. Set-or-Append (Idempotent bulk load)
Uses a tag to prevent duplicate ingestion:
```kql
.set-or-append SensorReading with (ingestIfNotExists='["tag_2025_12_01"]') <|
    externaldata(SensorId:string, Timestamp:datetime, ReadingValue:real)
    [@"https://storage.blob.core.windows.net/container/data.csv"]
    with (format='csv', ignoreFirstRecord=true)
```

> **`set-or-append`** checks the `ingestIfNotExists` tag — if already ingested with that tag, skips. Perfect for idempotent batch loads.

### 3. Storage Ingestion (Azure Blob, ADLS, OneLake)
```kql
.ingest into table SensorReading
    (h@'https://account.blob.core.windows.net/container/file.csv;secretkey')
    with (format='csv', ignoreFirstRecord=true)
```

### 4. Streaming Ingestion (via EventStream)
Streaming must be enabled on the table:
```kql
.alter table SensorReading policy streamingingestion enable
```

Then data flows from EventStream → KQL Database automatically.

### 5. OneLake Shortcut Ingestion
Create a shortcut from Eventhouse to OneLake data, then query directly:
```kql
.create external table ExternalSensors (SensorId:string, Timestamp:datetime, ReadingValue:real)
kind=delta
(
    @"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/sensor_readings"
)
```

---

## Data Mappings

### CSV Mapping
```kql
.create table SensorReading ingestion csv mapping 'SensorCsvMapping'
    '[{"Column":"SensorId","DataType":"string","Ordinal":0},'
    '{"Column":"Timestamp","DataType":"datetime","Ordinal":1},'
    '{"Column":"ReadingValue","DataType":"real","Ordinal":2}]'
```

### JSON Mapping
```kql
.create table SensorReading ingestion json mapping 'SensorJsonMapping'
    '[{"Column":"SensorId","Properties":{"Path":"$.sensorId"}},'
    '{"Column":"Timestamp","Properties":{"Path":"$.timestamp"}},'
    '{"Column":"ReadingValue","Properties":{"Path":"$.reading.value"}}]'
```

---

## Policies

### Retention Policy
Controls how long data is kept. Default: unlimited.
```kql
-- Set 90-day retention
.alter table SensorReading policy retention
    '{"SoftDeletePeriod": "90.00:00:00", "Recoverability": "Enabled"}'

-- Database-level default
.alter database MyDB policy retention
    '{"SoftDeletePeriod": "365.00:00:00", "Recoverability": "Enabled"}'
```

### Caching Policy
Controls hot (SSD/RAM) vs cold (blob) storage. Default: unlimited hot cache.
```kql
-- Keep 30 days in hot cache
.alter table SensorReading policy caching hot = 30d

-- Database-level default
.alter database MyDB policy caching hot = 7d
```

> **Rule of thumb**: Set hot cache to cover your most common query range. Historical queries still work on cold data, just slower.

### Partitioning Policy
Optimizes query performance for large tables:
```kql
.alter table SensorReading policy partitioning '{'
    '"PartitionKeys": [{'
        '"ColumnName": "Timestamp",'
        '"Kind": "UniformRange",'
        '"Properties": {"Reference": "2024-01-01T00:00:00", "RangeSize": "1.00:00:00", "OverrideCreationTime": false}'
    '}]'
'}'
```

### Merge Policy
Controls how extents (data shards) are merged:
```kql
.alter table SensorReading policy merge
    '{"MaxRangeInHours": 24, "RowCountUpperBoundForMerge": 1000000}'
```

### Batching Policy (Ingestion)
Controls how ingestion batches are formed:
```kql
.alter table SensorReading policy ingestionbatching
    '{"MaximumBatchingTimeSpan": "00:00:30", "MaximumNumberOfItems": 500, "MaximumRawDataSizeMB": 1024}'
```

---

## Materialized Views

Pre-computed aggregations kept up-to-date automatically:

```kql
-- Create materialized view for hourly averages
.create materialized-view HourlySensorAvg on table SensorReading
{
    SensorReading
    | summarize AvgReading=avg(ReadingValue), MaxReading=max(ReadingValue), Count=count()
        by SensorId, bin(Timestamp, 1h)
}
```

### Supported Aggregations in Materialized Views
`count()`, `sum()`, `avg()`, `min()`, `max()`, `dcount()`, `countif()`, `sumif()`, `any()`, `arg_min()`, `arg_max()`, `percentile()`, `take_any()`, `hll()`, `make_set()`, `make_list()`, `make_bag()`

### Backfill Existing Data
```kql
.create materialized-view with (backfill=true) HourlySensorAvg on table SensorReading
{
    SensorReading
    | summarize AvgReading=avg(ReadingValue) by SensorId, bin(Timestamp, 1h)
}
```

### Monitor View Health
```kql
.show materialized-view HourlySensorAvg
| project MaterializedTo, IsHealthy, IsEnabled
```

---

## Stored Functions

Reusable KQL functions:

```kql
.create-or-alter function with (docstring='Get anomalies for a sensor in last N hours')
GetAnomalies(sensorId:string, hours:int) {
    SensorReading
    | where SensorId == sensorId and Timestamp > ago(hours * 1h) and IsAnomaly == true
    | order by Timestamp desc
}
```

Call: `GetAnomalies("SN001", 24)`

---

## Update Policies

Automatically transform data as it's ingested into a source table:

```kql
-- 1. Create target table
.create-merge table EnrichedReadings (SensorId:string, Timestamp:datetime, ReadingValue:real, Status:string)

-- 2. Create transform function
.create-or-alter function EnrichReadings() {
    SensorReading
    | extend Status = iff(IsAnomaly, "ALERT", "Normal")
    | project SensorId, Timestamp, ReadingValue, Status
}

-- 3. Set update policy (runs on every ingestion into SensorReading)
.alter table EnrichedReadings policy update
    '[{"IsEnabled": true, "Source": "SensorReading", "Query": "EnrichReadings()", "IsTransactional": true}]'
```

> **Transactional**: If `IsTransactional=true`, ingestion fails if the update policy function fails. Set to `false` for best-effort.

---

## External Tables

### OneLake External Table (Delta)
```kql
.create external table ExternalSales (ProductId:string, Amount:real, SaleDate:datetime)
kind=delta
(
    @"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/fact_sales"
)
```

### ADLS Gen2 External Table
```kql
.create external table ExternalLogs (Timestamp:datetime, Level:string, Message:string)
kind=storage
(
    h@'https://account.dfs.core.windows.net/container/logs/;impersonate'
)
with (format='parquet')
```

### Query External Table
```kql
external_table('ExternalSales')
| summarize TotalSales=sum(Amount) by ProductId
| top 10 by TotalSales desc
```

---

## Permission Model

| Role | Scope | Permissions |
|------|-------|-------------|
| `viewer` | Query data (read-only) | `SELECT` on tables |
| `user` | Query + limited management | `SELECT` + function creation |
| `ingestor` | Ingest data only | `.ingest` commands |
| `admin` | Full control | All operations |

```kql
-- Grant viewer role
.add database MyDB viewers ('aaduser=user@domain.com')

-- Grant ingestor role
.add database MyDB ingestors ('aadapp={client_id};{tenant_id}')
```

---

## Gotchas

1. **`.create table` fails if table exists** — Always use `.create-merge table`
2. **Inline ingestion limit ~64 KB** — Use storage ingestion or streaming for larger data
3. **Materialized view backfill can be slow** — On large tables, may take hours
4. **Update policies run synchronously** — Complex transforms slow ingestion
5. **Streaming ingestion must be explicitly enabled** per table
6. **external_table() queries are slower** than native tables — use for cross-engine joins, not primary queries
7. **CSV inline ingestion**: Datetime values must be ISO 8601 format
8. **JSON mapping paths are case-sensitive** — `$.sensorId` ≠ `$.SensorId`
9. **Retention policy SoftDeletePeriod includes hot + cold** — not just hot cache
10. **Partitioning policy changes don't retroactively repartition** — only new extents

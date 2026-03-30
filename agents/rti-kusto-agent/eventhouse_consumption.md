# Eventhouse Consumption — Querying, Performance & Monitoring

> Source: [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) — EVENTHOUSE-CONSUMPTION-CORE.md

## Connection Fundamentals

### Discover Cluster URI
The query service URI is on the Eventhouse item properties:
```python
eh = requests.get(f"{API}/workspaces/{ws_id}/eventhouses/{eh_id}", headers=h).json()
cluster_uri = eh["properties"]["queryServiceUri"]
# e.g., https://trd-abc123.z0.kusto.fabric.microsoft.com
```

### Query via REST API
```python
kusto_token = credential.get_token("https://kusto.kusto.windows.net/.default").token
resp = requests.post(
    f"{cluster_uri}/v1/rest/query",
    headers={"Authorization": f"Bearer {kusto_token}", "Content-Type": "application/json"},
    json={"db": "MyDatabase", "csl": "SensorReading | take 10"}
)
```

### Query via `az rest` (CLI)
KQL with pipe `|` characters requires a temp file:
```bash
# Write query to temp file (pipes in KQL conflict with shell)
echo '{"db": "MyDB", "csl": "SensorReading | where Timestamp > ago(1h) | count"}' > /tmp/q.json

az rest --method POST \
  --url "{clusterUri}/v1/rest/query" \
  --resource "https://kusto.kusto.windows.net" \
  --body @/tmp/q.json
```

---

## Schema Discovery

```kql
-- List all tables
.show tables

-- Table schema (columns + types)
.show table SensorReading schema as json

-- Table details (row count, extent count, size)
.show tables details | project TableName, TotalRowCount, TotalExtentSize

-- Database schema (all tables, columns, types)
.show database schema as json
```

---

## Performance Best Practices

### The Golden Rules
1. **Time filter FIRST** — Always filter by time range before other predicates
2. **`has` over `contains`** — `has` uses term index (fast), `contains` scans full text (slow)
3. **`project` early** — Select only needed columns as early as possible in the pipeline
4. **Avoid `*`** — `T | take 10` is fine, but `T | project *` prevents optimization
5. **`in` over multiple `or`** — `where Status in ("Active", "Pending")` is faster than `or`
6. **`let` for reuse** — Use `let` statements for values used multiple times

### String Matching Performance Matrix

| Operator | Index? | Case Sensitive? | Performance | Use When |
|----------|--------|-----------------|-------------|----------|
| `==` | Yes | Yes | ★★★★★ | Exact match |
| `has` | Yes (term) | No | ★★★★☆ | Word/token search |
| `has_cs` | Yes (term) | Yes | ★★★★☆ | Case-sensitive word search |
| `startswith` | Yes (prefix) | No | ★★★☆☆ | Prefix match |
| `contains` | No (scan) | No | ★★☆☆☆ | Substring (avoid on large tables) |
| `matches regex` | No (scan) | Depends | ★☆☆☆☆ | Complex patterns (expensive) |

> **Rule**: Use `has` by default for text search. Only use `contains` or `matches regex` when `has` doesn't work for your use case.

### Anti-Patterns
```kql
-- ❌ BAD: No time filter, full table scan
SensorReading | where SensorType == "Temperature"

-- ✅ GOOD: Time filter first
SensorReading | where Timestamp > ago(24h) | where SensorType == "Temperature"

-- ❌ BAD: contains on large table
SensorReading | where Message contains "error"

-- ✅ GOOD: has uses term index
SensorReading | where Message has "error"

-- ❌ BAD: project * with complex pipeline
SensorReading | extend x = ReadingValue * 2 | project *

-- ✅ GOOD: project only what you need
SensorReading | project SensorId, Timestamp, ReadingValue | extend x = ReadingValue * 2
```

---

## Monitoring & Diagnostics

### Active Queries
```kql
.show queries
| where State == "InProgress"
| project User, Text, StartedOn, Duration
```

### Ingestion Failures
```kql
.show ingestion failures
| where FailedOn > ago(24h)
| summarize count() by FailureKind, Details
```

### Database Statistics
```kql
.show database MyDB extents
| summarize TotalSize=sum(OriginalSize), ExtentCount=count() by TableName
| order by TotalSize desc
```

### Materialized View Health
```kql
.show materialized-views
| project Name, IsHealthy, IsEnabled, MaterializedTo, LastRun
```

---

## Common Consumption Patterns

### Time-Series Analysis
```kql
SensorReading
| where Timestamp between (ago(7d) .. now())
| summarize AvgReading=avg(ReadingValue), MaxReading=max(ReadingValue)
    by SensorId, bin(Timestamp, 1h)
| render timechart
```

### Top-N Analysis
```kql
SensorReading
| where Timestamp > ago(24h) and IsAnomaly == true
| summarize AnomalyCount=count() by SensorId
| top 10 by AnomalyCount desc
```

### Percentile Analysis
```kql
SensorReading
| where Timestamp > ago(7d)
| summarize P50=percentile(ReadingValue, 50),
            P95=percentile(ReadingValue, 95),
            P99=percentile(ReadingValue, 99)
    by SensorId
```

### Dynamic Field Exploration
```kql
-- Parse and explore JSON in dynamic columns
SensorReading
| where Timestamp > ago(1h)
| extend Details = parse_json(RawPayload)
| project SensorId, Timestamp, Status=tostring(Details.status), Value=todouble(Details.value)
```

### Cross-Database Join (Eventhouse + OneLake)
```kql
SensorReading
| where Timestamp > ago(1h) and IsAnomaly == true
| join kind=inner (external_table('DimSensors') | project SensorId, Location, Equipment)
    on SensorId
| summarize Alerts=count() by Location, Equipment
```

---

## Gotchas

1. **KQL pipes in `az rest` body** — Use temp file for `--body @/tmp/q.json`, not inline
2. **Query timeout default is 4 minutes** — Set `servertimeout` for longer queries: `set notruncation; set servertimeout=10m;`
3. **`take` without `where`** = random rows — Not a reliable sample for analysis
4. **External table queries are slower** — Don't use as primary data source for dashboards
5. **Cluster URI token scope** — Try cluster URI first, then fallback to `https://kusto.kusto.windows.net`
6. **`contains` on high-cardinality columns** — Extremely slow, prefer `has` or `startswith`
7. **Timestamp comparison** — Use `between` for ranges, `ago()` for relative, avoid string comparison
8. **Results truncated at 500K rows** — Use `set notruncation` to override (careful with memory)
9. **`mv-expand` on large arrays** — Can explode row count; filter before expanding
10. **Query results are not cached by default** — Same query re-runs full computation
11. **`render` only works in dashboards/UI** — Ignored in REST API responses
12. **`evaluate` plugins (autocluster, basket, etc.)** — May not be available in Fabric Eventhouse

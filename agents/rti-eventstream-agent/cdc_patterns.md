# CDC & Schema Evolution Patterns for EventStream

## Purpose

Patterns for Change Data Capture (CDC), schema evolution handling, and data quality validation in EventStream pipelines.

---

## CDC Source Connectors

EventStream supports CDC from these databases via DeltaFlow:

| Source | Connector | CDC Method | Supported Operations |
|--------|-----------|-----------|---------------------|
| Azure SQL | SQL CDC Connector | SQL Server CDC | Insert, Update, Delete |
| PostgreSQL | PostgreSQL CDC | Logical replication (WAL) | Insert, Update, Delete |
| MySQL | MySQL CDC | Binlog | Insert, Update, Delete |
| Cosmos DB | Cosmos DB CDC | Change feed | Insert, Update (no delete) |
| MongoDB | MongoDB CDC | Change streams | Insert, Update, Replace, Delete |

### CDC Event Format

CDC events include an operation type field:

```json
{
    "_op": "u",           // c=create, u=update, d=delete, r=read (snapshot)
    "_ts_ms": 1704067200000,
    "before": {           // Previous state (for updates/deletes)
        "customer_id": 1001,
        "customer_name": "Old Name",
        "region": "Europe"
    },
    "after": {            // New state (for creates/updates)
        "customer_id": 1001,
        "customer_name": "New Name",
        "region": "Europe"
    },
    "source": {
        "connector": "sqlserver",
        "db": "SalesDB",
        "table": "customers"
    }
}
```

---

## DeltaFlow CDC Transform Patterns

### Pattern 1: Apply CDC to Lakehouse (Auto-Merge)

DeltaFlow in EventStream can automatically apply CDC operations to a Delta table in Lakehouse.

**EventStream topology**:
```
SQL CDC Source → DeltaFlow Transform → Lakehouse Destination
```

**Configuration**:
- DeltaFlow mode: `CDC`
- Key columns: `customer_id` (used for MERGE matching)
- Operation column: `_op`
- DeltaFlow handles INSERT/UPDATE/DELETE mapping automatically

### Pattern 2: Route CDC to KQL for Real-Time + Lakehouse for History

```
SQL CDC Source
├── Filter (op != 'r') → KQL Database (real-time changes)
└── DeltaFlow CDC → Lakehouse (accumulated state)
```

This gives you:
- **KQL**: Real-time change stream for monitoring/alerting
- **Lakehouse**: Current state of source data for BI reports

---

## Schema Evolution Handling

### Problem

Source schema changes (new columns, type changes, column renames) can break EventStream pipelines.

### Strategy 1: Permissive Schema (KQL)

KQL tables can handle schema evolution natively with dynamic columns:

```kql
// Create table with explicit columns + dynamic bag for new fields
.create table SensorReading (
    SensorId: string,
    Timestamp: datetime,
    ReadingValue: real,
    Properties: dynamic    // Catches any new fields
)

// Ingestion mapping that puts unknown fields into Properties
.create table SensorReading ingestion json mapping 'SensorMapping' '[
    {"column": "SensorId", "path": "$.SensorId"},
    {"column": "Timestamp", "path": "$.Timestamp"},
    {"column": "ReadingValue", "path": "$.ReadingValue"},
    {"column": "Properties", "path": "$"}
]'
```

> New fields automatically appear in the `Properties` dynamic column, no pipeline change needed.

### Strategy 2: Schema Registry (Event Hub)

Use Azure Schema Registry for strict schema governance:

```python
from azure.schemaregistry import SchemaRegistryClient
from azure.schemaregistry.serializer.avroserializer import AvroSerializer
from azure.identity import DefaultAzureCredential

# Register schema
client = SchemaRegistryClient(
    fully_qualified_namespace="<namespace>.servicebus.windows.net",
    credential=DefaultAzureCredential()
)

# Schema evolution rules:
# - Adding optional fields: COMPATIBLE (no break)
# - Removing fields: BREAKING (requires pipeline update)
# - Changing field types: BREAKING (requires pipeline update)
```

### Strategy 3: Graceful Column Addition (Lakehouse)

When a new column appears in the source:

```python
# In EventStream processing node or downstream Spark notebook
from pyspark.sql import functions as F

def handle_schema_evolution(new_df, table_path):
    """Handle new columns by merging schemas."""
    existing = spark.read.format("delta").load(table_path)
    
    new_columns = set(new_df.columns) - set(existing.columns)
    
    if new_columns:
        # Add new columns to existing schema
        for col in new_columns:
            col_type = new_df.schema[col].dataType.simpleString()
            spark.sql(f"ALTER TABLE delta.`{table_path}` ADD COLUMNS ({col} {col_type})")
            print(f"  ➕ Added column: {col} ({col_type})")
    
    # Now merge normally
    delta_table = DeltaTable.forPath(spark, table_path)
    # ... merge logic ...
```

### Schema Evolution Decision Tree

```
New event has unknown field?
├── KQL destination → Dynamic column absorbs it automatically
├── Lakehouse destination (DeltaFlow) → DeltaFlow handles schema merge
├── Lakehouse destination (manual) → ALTER TABLE ADD COLUMNS
└── Semantic Model → Manual update needed (add column + relationship)

Source removed a field?
├── KQL → Column becomes null for new events (no break)
├── Lakehouse → Column becomes null for new rows (no break)
└── Semantic Model → May break DAX measures referencing that column ⚠️

Source changed field type?
├── KQL → May cause ingestion errors → Update mapping
├── Lakehouse → Delta schema enforcement rejects → Update schema
└── Action: Pause pipeline → Update schema → Resume
```

---

## Data Quality Validation in Stream

### Pattern 1: Filter Invalid Events (Processing Node)

```
EventStream topology:
Source → Filter Node → Destination (clean data)
                    └→ Dead Letter Destination (invalid events)
```

**Filter expression examples**:
```sql
-- Keep only events with valid sensor ID
WHERE SensorId IS NOT NULL AND LEN(SensorId) > 0

-- Keep only events within reasonable value range
WHERE ReadingValue BETWEEN -1000 AND 10000

-- Keep only events with valid timestamp (not future, not too old)
WHERE Timestamp > DATEADD(day, -7, GETUTCDATE()) AND Timestamp <= GETUTCDATE()
```

### Pattern 2: Validate in Python Generator (Before Send)

```python
def validate_event(event: dict) -> tuple:
    """Validate event before sending to EventStream.
    Returns (is_valid, issues).
    """
    issues = []
    
    # Required fields
    required = ["SensorId", "Timestamp", "ReadingValue"]
    for field in required:
        if field not in event or event[field] is None:
            issues.append(f"Missing required field: {field}")
    
    # Type checks
    if "ReadingValue" in event:
        try:
            float(event["ReadingValue"])
        except (TypeError, ValueError):
            issues.append(f"ReadingValue not numeric: {event['ReadingValue']}")
    
    # Range checks
    if "ReadingValue" in event:
        val = float(event.get("ReadingValue", 0))
        if val < -1000 or val > 10000:
            issues.append(f"ReadingValue out of range: {val}")
    
    # Timestamp checks
    if "Timestamp" in event:
        from datetime import datetime, timedelta
        try:
            ts = datetime.fromisoformat(event["Timestamp"].replace("Z", "+00:00"))
            if ts > datetime.utcnow().replace(tzinfo=ts.tzinfo) + timedelta(minutes=5):
                issues.append(f"Timestamp is in the future: {event['Timestamp']}")
        except ValueError:
            issues.append(f"Invalid timestamp format: {event['Timestamp']}")
    
    return (len(issues) == 0, issues)
```

### Pattern 3: Aggregate Quality Metrics in KQL

```kql
// Track data quality metrics over time
SensorReading
| where ingestion_time() > ago(1h)
| summarize
    TotalEvents = count(),
    NullSensorId = countif(isnull(SensorId) or isempty(SensorId)),
    NullReadingValue = countif(isnull(ReadingValue)),
    OutOfRange = countif(ReadingValue < -1000 or ReadingValue > 10000),
    FutureTimestamp = countif(Timestamp > now()),
    StaleTimestamp = countif(Timestamp < ago(1d))
| extend
    QualityScore = round(100.0 * (TotalEvents - NullSensorId - NullReadingValue - OutOfRange) / TotalEvents, 2)
```

---

## EventStream Pause/Resume for Maintenance

### When Schema Changes Require Pipeline Update

```python
import requests

def pause_eventstream_node(ws_id: str, es_id: str, node_id: str, headers: dict):
    """Pause a specific node in EventStream topology for maintenance."""
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/eventstreams/{es_id}/nodes/{node_id}/pause",
        headers=headers
    )
    print(f"Pause: {resp.status_code}")

def resume_eventstream_node(ws_id: str, es_id: str, node_id: str, headers: dict):
    """Resume a paused node after maintenance."""
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/eventstreams/{es_id}/nodes/{node_id}/resume",
        headers=headers
    )
    print(f"Resume: {resp.status_code}")
```

### Maintenance Workflow

```
1. Pause EventStream source node
2. Apply schema changes to destination (KQL ALTER TABLE, Delta ALTER TABLE)
3. Update EventStream processing nodes if needed
4. Resume EventStream source node
5. Verify events flow with new schema
6. Monitor data quality for 15 minutes
```

> **Warning**: Events sent during pause are buffered (Event Hub retention). They will be delivered on resume. Ensure your destination can handle the burst.

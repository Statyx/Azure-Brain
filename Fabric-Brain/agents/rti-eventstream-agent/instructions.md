# EventStream Agent — Instructions

## System Prompt

You are an expert at creating and managing Microsoft Fabric EventStreams — the real-time data ingestion and routing engine built on Azure Event Hubs. You understand 30+ source connectors (Custom Endpoint, Azure Event Hub, IoT Hub, Kafka, CDC connectors for SQL/PostgreSQL/MySQL/Cosmos DB/MongoDB, Google Pub/Sub, Amazon Kinesis, Confluent Kafka, MQTT, HTTP, and more), processing nodes (Filter, Aggregate, Manage Fields, Group By, Union, Expand, Join, SQL operator), destinations (Eventhouse/KQL Database, Lakehouse, Custom Endpoint, Spark Notebook, Derived Stream, Fabric Activator), DeltaFlow CDC transforms, Schema Registry, and data injection via the Event Hub SDK or Kafka protocol.

**Before any EventStream work**, load this file plus `sources_destinations.md` and `data_injection.md`.

---

## Mandatory Rules

### Rule 1: EventStream Destination itemId Must Be KQL Database ID, NOT Eventhouse ID
When routing to a KQL Database, the `itemId` in the destination configuration must be the **KQL Database** ID. Using the Eventhouse ID will fail silently or error.

```
✅ destination.itemId = KQL Database ID
❌ destination.itemId = Eventhouse ID
```

### Rule 2: Custom Endpoint Connection String — API Available for Custom Endpoints Only
The connection string for a Custom Endpoint source **can be retrieved via API** using the Topology Source Connection endpoint — but ONLY for Custom Endpoint sources:

```python
# Works ONLY for Custom Endpoint sources (not Event Hub, IoT Hub, etc.)
resp = requests.get(
    f"{API}/workspaces/{WS_ID}/eventstreams/{es_id}/sources/{source_id}/connection",
    headers=headers
)
connection_info = resp.json()
```

**Alternative**: Open the EventStream in Fabric portal UI → click Custom Endpoint node → Keys tab → copy connection string.

**Format**: `Endpoint=sb://{host}.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...;EntityPath=...`

**For automation**: Store the connection string in a config file or Key Vault after retrieval.

### Rule 3: Use the `_table` Field for Multi-Table Routing
When sending events to one EventStream that feeds multiple KQL tables, include a `_table` field in each JSON event. Configure the EventStream topology to route events based on this field.

```json
{"_table": "SensorReading", "SensorId": "SN001", "ReadingValue": 42.5, "Timestamp": "2025-12-01T00:00:00Z"}
{"_table": "EquipmentAlert", "AlertId": "AL001", "Severity": "High", "Timestamp": "2025-12-01T00:01:00Z"}
```

### Rule 4: Deploy EventStream AFTER Its Destinations Exist
EventStream destinations reference existing items. The KQL Database and Lakehouse must already exist before configuring EventStream destinations pointing to them.

**Deployment order**: Lakehouse → Eventhouse (auto-creates KQL DB) → KQL tables → EventStream

### Rule 5: EventStream Uses Event Hub Protocol
The Custom Endpoint is **Event Hub compatible**. Use the `azure-eventhub` Python package or `Azure.Messaging.EventHubs` .NET package. Do NOT use raw HTTP POST to the endpoint — it requires AMQP protocol.

---

## Decision Trees

### "I need to ingest real-time data"
```
├── Where is the data coming from?
│   ├── Custom application / script → Custom Endpoint source (Event Hub SDK or Kafka protocol)
│   ├── Azure Event Hub → Azure Event Hub source (direct connection)
│   ├── Azure IoT Hub → IoT Hub source
│   ├── Apache Kafka / Confluent / Amazon MSK → Kafka source (multiple connectors)
│   ├── Azure SQL Database (change tracking) → Azure SQL DB CDC source (+ DeltaFlow preview)
│   ├── PostgreSQL → PostgreSQL CDC source (+ DeltaFlow preview)
│   ├── MySQL → MySQL Database CDC source
│   ├── Azure Cosmos DB → Cosmos DB CDC source
│   ├── MongoDB → MongoDB CDC source (preview)
│   ├── Azure SQL Managed Instance → SQL MI CDC source (+ DeltaFlow preview)
│   ├── SQL Server on VM → SQL Server VM CDC source (+ DeltaFlow preview)
│   ├── Google Cloud Pub/Sub → Google Pub/Sub source
│   ├── Amazon Kinesis → Amazon Kinesis Data Streams source
│   ├── MQTT broker → MQTT source (preview)
│   ├── HTTP endpoints → HTTP source (preview, includes public data feeds)
│   ├── Azure Blob events → Blob Storage Events source
│   ├── Azure Event Grid → Event Grid source (MQTT or non-MQTT, preview)
│   ├── Azure Service Bus → Service Bus source (queue or topic, preview)
│   ├── Azure Data Explorer → ADX source (preview)
│   ├── Fabric events → Workspace item / OneLake / Job / Capacity events
│   └── Testing → Sample Data (Bicycles, Yellow Taxi, Stock Market, Buses, S&P 500, Semantic Model Logs)
├── Where should the data go?
│   ├── Real-time analytics → Eventhouse (KQL Database) destination
│   ├── Archival / batch processing → Lakehouse destination (Delta Lake)
│   ├── External consumers → Custom Endpoint destination
│   ├── Spark processing → Spark Notebook destination (preview)
│   ├── Processed sub-stream → Derived Stream
│   ├── Alerting / actions → Fabric Activator destination (preview)
│   └── Multiple targets → Add multiple destinations from same stream
├── Do you need processing in-flight?
│   ├── No-code → Filter, Aggregate, Manage Fields, Group By, Union, Expand, Join
│   ├── Code-first → SQL operator (preview) for custom SQL expressions
│   └── NO processing → Direct source → destination routing
└── Create EventStream → configure sources → add processing → add destinations
```

### "I need to route events to multiple KQL tables"
```
├── Option A: Single EventStream, multiple destinations
│   ├── Add a `_table` field to each event
│   ├── Create one destination per KQL table
│   ├── Add a Filter node before each destination
│   └── Filter by `_table == "TableName"` for each
├── Option B: Multiple EventStreams
│   └── One EventStream per table (simpler but more items)
└── Option A is preferred for most demos
```

### "Data isn't arriving in my KQL table"
```
├── Is the EventStream running?
│   ├── Check topology status: GET /eventstreams/{id}/topology
│   └── Look for "Running" vs "Error" indicators
├── Check the Custom Endpoint connection string
│   ├── Is it the correct EventStream? (verify EntityPath)
│   └── Is the key still valid? (keys don't expire by default)
├── Check the destination configuration
│   ├── Is the itemId the KQL Database ID (not Eventhouse ID)?
│   ├── Does the KQL table exist?
│   └── Do the column names in the event match the table schema?
├── Check the data being sent
│   ├── Is it valid JSON?
│   ├── Are field names matching the KQL table columns?
│   └── Is the `_table` routing field correct?
└── Check Fabric capacity
    └── Is the capacity paused or throttled?
```

---

## EventStream Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │                   EventStream                    │
                    │                                                  │
  [Source]          │   [Stream]    [Processing]    [Destination]      │
  Custom Endpoint ──┤──► Raw ───► Filter/Agg ──► KQL Database         │
  Azure Event Hub ──┤                           ──► Lakehouse          │
  IoT Hub ──────────┤                           ──► Custom App         │
  Kafka ────────────┤                           ──► Derived Stream     │
                    └─────────────────────────────────────────────────┘
```

---

## API Quick Reference

> **Scopes**: `Eventstream.Read.All`, `Eventstream.ReadWrite.All`  
> Service principals and managed identities are supported.

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create EventStream | POST | `/v1/workspaces/{wsId}/eventstreams` |
| Get EventStream | GET | `/v1/workspaces/{wsId}/eventstreams/{esId}` |
| List EventStreams | GET | `/v1/workspaces/{wsId}/eventstreams` |
| Update EventStream | PATCH | `/v1/workspaces/{wsId}/eventstreams/{esId}` |
| Delete EventStream | DELETE | `/v1/workspaces/{wsId}/eventstreams/{esId}` |
| Get Definition | POST | `/v1/workspaces/{wsId}/eventstreams/{esId}/getDefinition` |
| Update Definition | POST | `/v1/workspaces/{wsId}/eventstreams/{esId}/updateDefinition` |
| **Get Topology** | GET | `/v1/workspaces/{wsId}/eventstreams/{esId}/topology` |
| **Pause EventStream** | POST | `/v1/workspaces/{wsId}/eventstreams/{esId}/pause` |
| **Resume EventStream** | POST | `/v1/workspaces/{wsId}/eventstreams/{esId}/resume` |
| **Pause Source** | POST | `/v1/workspaces/{wsId}/eventstreams/{esId}/sources/{srcId}/pause` |
| **Resume Source** | POST | `/v1/workspaces/{wsId}/eventstreams/{esId}/sources/{srcId}/resume` |
| **Pause Destination** | POST | `/v1/workspaces/{wsId}/eventstreams/{esId}/destinations/{dstId}/pause` |
| **Resume Destination** | POST | `/v1/workspaces/{wsId}/eventstreams/{esId}/destinations/{dstId}/resume` |
| **Get Source Connection** | GET | `/v1/workspaces/{wsId}/eventstreams/{esId}/sources/{srcId}/connection` |
| **Get Destination Connection** | GET | `/v1/workspaces/{wsId}/eventstreams/{esId}/destinations/{dstId}/connection` |

### Create EventStream
```python
# Use the dedicated /eventstreams endpoint (NOT /items)
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/eventstreams",
    headers=headers,
    json={
        "displayName": "ES_SensorTelemetry",
        "description": "Ingests sensor telemetry into KQL Database"
    }
)
eventstream_id = resp.json()["id"]
```

### Get Topology (with pause/resume status)
```python
resp = requests.get(
    f"{API}/workspaces/{WS_ID}/eventstreams/{eventstream_id}/topology",
    headers=headers
)
topology = resp.json()
# Returns: sources[], streams[], destinations[] with status per node
```

### Pause/Resume Individual Sources or Destinations
```python
# Pause a specific source
requests.post(
    f"{API}/workspaces/{WS_ID}/eventstreams/{es_id}/sources/{source_id}/pause",
    headers=headers
)

# Resume a specific destination
requests.post(
    f"{API}/workspaces/{WS_ID}/eventstreams/{es_id}/destinations/{dest_id}/resume",
    headers=headers
)
```

---

## EventStream Definition Structure

The definition is a set of Base64-encoded JSON parts pushed via `updateDefinition`:

```json
{
    "definition": {
        "parts": [
            {
                "path": ".platform",
                "payload": "<base64>",
                "payloadType": "InlineBase64"
            },
            {
                "path": "eventstream.json",
                "payload": "<base64>",
                "payloadType": "InlineBase64"
            }
        ]
    }
}
```

The `eventstream.json` contains the full topology definition including sources, processing nodes, and destinations.

---

## Processing Node Types

| Node Type | Purpose | Example |
|-----------|---------|---------|
| **Filter** | Keep/discard events by condition | `_table == "SensorReading"` |
| **Manage Fields** | Add, remove, rename columns | Add `ProcessedTime = NOW()` |
| **Aggregate** | Windowed aggregation (Tumbling, Hopping, Sliding, Session) | `AVG(Temperature) per 5m` |
| **Group By** | Group events by key with complex time windows | Group by `SensorId` per 1m window |
| **Union** | Merge multiple streams into one | Combine 2 sources into 1 stream |
| **Expand** | Flatten nested JSON arrays | Expand `readings[]` array |
| **Join** | Combine data from two streams on matching condition | Join stream A with stream B on key |
| **SQL operator** (preview) | Code-first stream processing with SQL expressions | Custom windowing, joins, aggregations |

> **Enhanced vs Standard capabilities**: Transformation operations are supported for ALL destinations when Enhanced capabilities are enabled. Without Enhanced capabilities, transformations work only for Lakehouse and Eventhouse (event processing before ingestion) destinations.

---

## Limitations (from MS Learn)

| Limit | Value |
|-------|-------|
| Maximum message size | **1 MB** per event |
| Maximum retention period | **90 days** |
| Event delivery guarantee | **At least once** |
| Minimum recommended capacity | **F4** (4 capacity units) |

---

## DeltaFlow — Analytics-Ready CDC Streams (Preview)

DeltaFlow transforms raw CDC events from operational databases into analytics-ready streams:
- **Analytics-ready event shape**: CDC events → tabular format matching source table structure (no Debezium JSON parsing)
- **Automatic Schema Registry**: Auto-discovers source schemas and registers them
- **Auto destination table management**: KQL/Eventhouse tables created and managed automatically
- **Schema evolution**: Detects column additions/table creation, updates schemas and destination tables

**Supported CDC sources with DeltaFlow**:
- Azure SQL Database CDC
- Azure SQL Managed Instance CDC
- SQL Server on VM CDC
- PostgreSQL Database CDC

**Activation**: Choose "Analytics-ready events & auto-updated schema" during schema handling step.

---

## Schema Management

- **Schema Registry (preview)**: Register and version schemas centrally using the Fabric Schema Registry
- **Multiple schema inferencing (preview)**: Infer and work with multiple schemas in a single eventstream, design diverse transformation paths
- **Confluent Schema Registry deserialization (preview)**: When ingesting from Confluent Cloud Kafka, use Confluent Schema Registry to deserialize schema-encoded messages

---

## Apache Kafka on Fabric EventStreams

EventStreams provide native Apache Kafka endpoints (built on Azure Event Hubs):
- Send or consume events using the Kafka protocol
- Update application connection settings to use the Kafka endpoint
- No separate provisioning — an event hub namespace is auto-provisioned
- Kafka endpoint available from Custom Endpoint source details

---

## Operational Capabilities

- **Pause/Resume controls**: Derived eventstreams support pause and resume per-source and per-destination without affecting other nodes
- **Workspace Private Link (preview)**: Select sources and destinations support private network access for secure inbound connections

---

## Error Recovery

| Error | Cause | Fix |
|-------|-------|-----|
| Destination errors "item not found" | Wrong `itemId` (used Eventhouse ID) | Use KQL Database ID instead |
| No events arriving | Wrong connection string | Re-copy from Fabric portal UI |
| Events arriving but no data in table | Column name mismatch | Match JSON field names to KQL table schema |
| Too many events dropped | Payload size > 1MB per event | Split large events, compress, or batch smaller |
| Topology shows "Error" state | Destination item deleted or inaccessible | Recreate destination item, update EventStream |
| Connection refused (AMQP) | SDK using wrong protocol | Must use Event Hub SDK (AMQP), not raw HTTP |

---

## Cross-References

| Topic | Agent | File |
|-------|-------|------|
| KQL Database creation | rti-kusto-agent | `eventhouse_kql.md` |
| KQL table schemas | rti-kusto-agent | `eventhouse_kql.md` |
| Lakehouse as destination | lakehouse-agent | `instructions.md` |
| Ontology TimeSeries bindings to KQL | ontology-agent | `entity_types_bindings.md` |
| Pipeline scheduling to trigger ingestion | orchestrator-agent | `pipelines.md` |

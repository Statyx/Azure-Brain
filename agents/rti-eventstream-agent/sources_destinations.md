# Sources & Destinations — EventStream Configuration

> **Source**: [MS Learn — EventStream Overview](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview)  
> **API Reference**: Fabric REST API — EventStream Topology endpoints

---

## Source Types (Enhanced Capabilities)

> Enable **Enhanced capabilities** when creating an eventstream to access all sources below.

### Streaming & Messaging Sources

| # | Source | Protocol | DeltaFlow Support | Notes |
|---|--------|----------|-------------------|-------|
| 1 | **Custom Endpoint** | Event Hub SDK (AMQP) or Kafka | No | Most common for demos. Connection string via portal or API (`GET /sources/{id}/connection`) |
| 2 | **Azure Event Hubs** | AMQP | No | Direct connection to existing Event Hub |
| 3 | **Azure IoT Hub** | AMQP | No | Device telemetry ingestion |
| 4 | **Apache Kafka** (preview) | Kafka | No | Open-source Kafka brokers |
| 5 | **Confluent Cloud for Apache Kafka** | Kafka | No | Managed Confluent Cloud |
| 6 | **Amazon MSK** | Kafka | No | Amazon Managed Streaming for Kafka |
| 7 | **Google Cloud Pub/Sub** | gRPC/HTTP | No | Google Cloud messaging |
| 8 | **Amazon Kinesis Data Streams** | HTTP | No | AWS streaming |
| 9 | **MQTT** (preview) | MQTT | No | IoT/edge messaging protocol |
| 10 | **HTTP** (preview) | HTTP | No | Standard HTTP requests + predefined public data feeds |
| 11 | **Azure Event Grid** (preview) | MQTT/HTTP | No | Event Grid namespace (MQTT or non-MQTT) |
| 12 | **Azure Service Bus** (preview) | AMQP | No | Queue or topic subscription |
| 13 | **Azure Data Explorer** (preview) | Kusto | No | Ingest from ADX table |
| 14 | **Azure IoT Operations** | AMQP/SASL | No | Entra ID or SASL auth |
| 15 | **Cribl** (preview) | HTTP | No | Observability pipeline |
| 16 | **Solace PubSub+** (preview) | AMQP | No | Enterprise messaging |

### CDC (Change Data Capture) Sources

| # | Source | DeltaFlow Support | Notes |
|---|--------|-------------------|-------|
| 17 | **Azure SQL Database CDC** | ✅ Yes | Snapshot + row-level changes |
| 18 | **Azure SQL Managed Instance CDC** | ✅ Yes | Snapshot + row-level changes |
| 19 | **SQL Server on VM CDC** | ✅ Yes | Snapshot + row-level changes |
| 20 | **PostgreSQL Database CDC** | ✅ Yes | Snapshot + row-level changes |
| 21 | **MySQL Database CDC** | No | Snapshot + row-level changes |
| 22 | **Azure Cosmos DB CDC** | No | Snapshot + row-level changes |
| 23 | **MongoDB CDC** (preview) | No | Collections monitoring |

### Event-Driven Sources

| # | Source | Notes |
|---|--------|-------|
| 24 | **Azure Blob Storage Events** | Triggered on blob create/replace/delete |
| 25 | **Fabric Workspace Item Events** | Item create/update/delete in workspace |
| 26 | **Fabric OneLake Events** | File/folder changes in OneLake |
| 27 | **Fabric Job Events** | Semantic model refresh, pipeline runs, notebook runs |
| 28 | **Fabric Capacity Overview Events** (preview) | Capacity health summary for alerts |

### Testing / Sample Sources

| # | Source | Notes |
|---|--------|-------|
| 29 | **Sample Data** | Bicycles, Yellow Taxi, Stock Market, Buses, S&P 500, Semantic Model Logs |
| 30 | **Real-time Weather** (preview) | Weather data from various locations |
| 31 | **Anomaly Detection Events** (preview) | Anomaly detector integration |

---

### Custom Endpoint Details (Most Common in Demos)

The Custom Endpoint exposes an **Event Hub compatible** AMQP endpoint that any Event Hub SDK can write to. Also supports **Kafka protocol** natively.

**Create**: Automatically created when you add a "Custom Endpoint" source in the EventStream topology (via UI or definition).

**Connection string format**:
```
Endpoint=sb://{host}.servicebus.windows.net/;SharedAccessKeyName={keyName};SharedAccessKey={key};EntityPath={entityPath}
```

**Retrieval**: 
- **API**: `GET /v1/workspaces/{wsId}/eventstreams/{esId}/sources/{srcId}/connection` (Custom Endpoints only)
- **Portal**: EventStream → Custom Endpoint node → Keys tab

**Key facts**:
- Uses Event Hub SDK (`azure-eventhub`) or Kafka protocol for data injection
- Supports JSON, Avro, CSV formats
- Max event size: 1MB per event
- Throughput: depends on Fabric capacity SKU
- No authentication token rotation needed (SAS key)

### CDC Source Configuration Pattern (Example: Azure SQL CDC)
```json
{
    "sourceType": "AzureSqlCDC",
    "connectionId": "<fabric-connection-guid>",
    "database": "SalesDB",
    "tables": ["dbo.Orders", "dbo.Customers"],
    "schemaHandling": "deltaFlow"
}
```
> Enable **DeltaFlow** for Azure SQL, SQL MI, SQL on VM, and PostgreSQL CDC sources to get analytics-ready streams with automatic schema registration.

### Kafka Source Configuration Pattern
```json
{
    "sourceType": "Kafka",
    "bootstrapServers": "broker1:9092,broker2:9092",
    "topic": "sensor-data",
    "consumerGroup": "fabric-consumer",
    "authentication": {
        "type": "SASL_SSL",
        "username": "...",
        "password": "..."
    }
}
```

---

## Destination Types

### 1. Eventhouse / KQL Database (Most Common for RTI)

Routes events to a KQL table in an Eventhouse. Supports two ingestion modes:
- **Direct ingestion**: Events flow directly to KQL table
- **Event processing before ingestion**: Apply transformations before KQL table

**Configuration**:
```json
{
    "destinationType": "KqlDatabase",
    "workspaceId": "{workspaceId}",
    "itemId": "{kqlDatabaseId}",
    "databaseName": "MyEventhouse",
    "tableName": "SensorReading",
    "dataFormat": "Json",
    "mappingRuleName": null
}
```

**Critical rules**:
- `itemId` = **KQL Database ID** (NOT Eventhouse ID)
- Table must already exist in the KQL Database
- Column names in the JSON event must match the KQL table schema
- If `mappingRuleName` is null, uses default column mapping (by name)

### Ingestion Mapping

For custom column mapping, create a mapping in KQL first:
```kql
.create table SensorReading ingestion json mapping 'SensorMapping' 
    '[{"column":"SensorId","path":"$.sensor_id"},{"column":"ReadingValue","path":"$.value"}]'
```

Then reference it: `"mappingRuleName": "SensorMapping"`

### 2. Lakehouse

Routes events to a Delta table in a Lakehouse.

**Configuration**:
```json
{
    "destinationType": "Lakehouse",
    "workspaceId": "{workspaceId}",
    "itemId": "{lakehouseId}",
    "tableName": "raw_sensor_events",
    "dataFormat": "Json"
}
```

**When to use**: Archival of streaming events for batch analytics, or when you need both real-time (KQL) and batch (Lakehouse) copies of the same data.

### 3. Custom Endpoint

Exposes an Event Hub compatible endpoint for downstream consumers.

**When to use**: 
- Sending processed events to external applications
- Fan-out patterns (one source, multiple external consumers)

### 4. Spark Notebook (Preview)

Loads events into a pre-existing Spark Notebook using Spark Structured Streaming.

**When to use**: Complex event processing with Python/Scala logic, ML model inference on streaming data.

### 5. Derived Stream

A specialized destination created after adding stream operations (Filter, Manage Fields, etc.). Represents the transformed stream after processing.

**When to use**:
- Chaining EventStreams together
- Making processed data available in the Real-Time Hub
- Creating multiple transformation branches from one source

### 6. Fabric Activator (Preview)

Triggers automated actions based on event conditions.

**When to use**: Alerting scenarios (e.g., "if temperature > 500°F, send notification"), starting Power Automate workflows.

---

## Multi-Destination Pattern

A single EventStream can route to multiple destinations simultaneously:

```
Custom Endpoint
    │
    ├──[Filter: _table="SensorReading"]──► KQL Database (SensorReading table)
    ├──[Filter: _table="EquipmentAlert"]──► KQL Database (EquipmentAlert table)
    ├──[No filter]──► Lakehouse (raw_events table — all events)
    └──[Filter: severity="Critical"]──► Reflex (alert trigger)
```

### Implementation

1. Create EventStream with Custom Endpoint source
2. Add Filter nodes for each routing condition
3. Add a KQL Database destination per table
4. Optionally add a Lakehouse destination for archival (no filter = all events)

---

## EventStream Topology Model

The topology is a directed acyclic graph (DAG) of nodes:

```json
{
    "sources": [
        {
            "id": "source-node-id",
            "name": "CustomEndpoint",
            "type": "CustomApp",
            "status": "Running"
        }
    ],
    "streams": [
        {
            "id": "stream-node-id",
            "name": "RawStream",
            "status": "Active"
        }
    ],
    "destinations": [
        {
            "id": "dest-node-id",
            "name": "SensorReadingDest",
            "type": "KqlDatabase",
            "itemId": "{kqlDatabaseId}",
            "status": "Running"
        }
    ]
}
```

Retrieve with:
```python
resp = requests.get(
    f"{API}/workspaces/{WS_ID}/eventstreams/{es_id}/topology",
    headers=headers
)
```

---

## Data Format Considerations

| Format | EventStream Support | Notes |
|--------|-------------------|-------|
| JSON | ✅ (default) | Recommended for most scenarios |
| Avro | ✅ | Better for schema evolution |
| CSV | ✅ | Simple but no nested structures |
| Parquet | ❌ (not for streaming) | Use for batch Lakehouse loads |

**JSON best practices**:
- Flat structure (avoid deep nesting when possible)
- Include a timestamp field in every event
- Include a routing field (`_table`) for multi-table scenarios
- Keep events under 1MB each

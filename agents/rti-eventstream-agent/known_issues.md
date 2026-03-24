# Known Issues & Gotchas — EventStream Agent

---

## Common Issues

### 1. Custom Endpoint Connection String — API Works for Custom Endpoints Only

**Symptom**: Created EventStream via API, need connection string for data injection.

**Reality**: The Fabric REST API **does** provide an endpoint to retrieve the connection — but ONLY for Custom Endpoint sources:
```python
# Works for Custom Endpoint sources
resp = requests.get(
    f"{API}/workspaces/{WS_ID}/eventstreams/{es_id}/sources/{source_id}/connection",
    headers=headers
)
connection_info = resp.json()
```

**Limitation**: This endpoint does NOT work for Event Hub, IoT Hub, or other source types. For non-custom sources, connection details are managed through the source's own service.

**Alternative**: Open EventStream in Fabric portal → click Custom Endpoint node → Keys tab → copy connection string.

**For automation**: Store the connection string in a config file or Key Vault after retrieval.

---

### 2. Destination itemId Confusion (Eventhouse vs KQL Database)

**Symptom**: EventStream destination shows error or data never arrives in KQL table.

**Cause**: Used Eventhouse ID as `itemId` instead of KQL Database ID.

**Fix**: Always use the **KQL Database ID**:
```python
# Get KQL Database ID
resp = requests.get(f"{API}/workspaces/{WS_ID}/items?type=KQLDatabase", headers=headers)
kql_db = [i for i in resp.json()["value"] if i["displayName"] == "MyEventhouse"][0]
kql_db_id = kql_db["id"]  # ← Use THIS as destination itemId
```

---

### 3. Events Arriving but Not in KQL Table

**Symptom**: EventStream topology shows "Running", events are being sent, but KQL table is empty.

**Causes**:
- JSON field names don't match KQL table column names (case-sensitive)
- KQL table doesn't exist yet
- Data format mismatch (sending CSV but destination expects JSON)

**Fix checklist**:
1. Verify KQL table exists: `.show table SensorReading`
2. Verify column names match exactly: `.show table SensorReading | project ColumnName`
3. Verify data format in destination config matches what you're sending
4. Check `_table` routing field if using multi-table pattern

---

### 4. AMQP Connection Refused

**Symptom**: `azure-eventhub` client throws connection error.

**Causes**:
- Network firewall blocking AMQP port 5671
- Invalid connection string
- EventStream capacity paused

**Fix**: 
- Verify connection string format: must start with `Endpoint=sb://`
- Check if Fabric capacity is running
- If behind corporate firewall, try AMQP over WebSockets:
```python
from azure.eventhub import EventHubProducerClient, TransportType

producer = EventHubProducerClient.from_connection_string(
    CONNECTION_STRING,
    transport_type=TransportType.AmqpOverWebsocket  # Uses port 443
)
```

---

### 5. Batch Size Exceeded

**Symptom**: `ValueError: The size of EventData has exceeded the max allowed size` when adding to batch.

**Cause**: Individual event exceeds 1MB or batch total exceeds limit.

**Fix**: Handle the `ValueError` to send the current batch and start a new one:
```python
try:
    batch.add(EventData(json.dumps(event)))
except ValueError:
    producer.send_batch(batch)
    batch = producer.create_batch()
    batch.add(EventData(json.dumps(event)))
```

---

### 6. EventStream Definition Push Complexity

**Symptom**: Trying to configure EventStream topology entirely via API is complex and poorly documented.

**Reality**: While `updateDefinition` exists for EventStreams, the internal JSON schema for topology (source → processing → destination) is complex and not publicly documented in detail.

**Recommendation**: 
- Create EventStream via API (simple `POST /items`)
- Configure topology (sources, processing, destinations) in the Fabric portal UI
- Export definition for reference: `POST /eventstreams/{id}/getDefinition`

---

### 7. EventStream Takes Time to Start

**Symptom**: After creating/modifying an EventStream, data doesn't flow immediately.

**Cause**: EventStream needs 30–60 seconds to initialize sources and destinations.

**Fix**: Wait 1–2 minutes after creation/configuration before sending test events. Check topology status:
```python
# Poll until all nodes show "Running"
topology = requests.get(f"{API}/workspaces/{WS_ID}/eventstreams/{es_id}/topology", headers=headers).json()
for node in topology.get("destinations", []):
    print(f"{node['name']}: {node.get('status', 'Unknown')}")
```

---

### 8. Duplicate Events in KQL Table

**Symptom**: Same event appears multiple times in the KQL table.

**Causes**:
- Client retries after timeout (but first send actually succeeded)
- Multiple EventStream destinations pointing to same table

**Fix**:
- Use `EventData.message_id` for idempotent sends
- Add deduplication in KQL: `.set-or-replace table SensorReading_deduped <| SensorReading | distinct *`
- Use `| summarize arg_max(Timestamp, *) by SensorId` in queries

---

## Capacity & Throughput

| Capacity SKU | Approximate Throughput | Notes |
|-------------|----------------------|-------|
| Trial | ~100 events/sec | Sufficient for demos |
| F2 | ~500 events/sec | Basic workloads |
| F4 (minimum recommended) | ~1,000 events/sec | **MS Learn recommends F4 minimum** |
| F16 | ~5,000 events/sec | Production scenarios |
| F64+ | ~50,000+ events/sec | High-throughput streaming |

---

## Verified Limits (from MS Learn)

| Limit | Value | Source |
|-------|-------|--------|
| Maximum message size | 1 MB | MS Learn EventStream overview |
| Maximum retention period | 90 days | MS Learn EventStream overview |
| Event delivery guarantee | At least once | MS Learn EventStream overview |
| Minimum recommended capacity | F4 | MS Learn EventStream overview |

---

## Tenant Settings

| Setting | Required For |
|---------|-------------|
| Real-Time Intelligence | EventStream |
| Real-Time Intelligence Data Hub | Data Hub integration |

> After enabling, wait 5–10 minutes for propagation.

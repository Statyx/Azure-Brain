# Data Injection Patterns — Event Hub SDK & Direct Kusto Streaming

---

## Overview

Two primary injection patterns exist:
1. **EventStream Custom Endpoint** — Uses Azure Event Hub protocol (AMQP) or Kafka protocol. Data flows through EventStream topology to destinations.
2. **Direct Kusto Streaming Ingestion** — Bypasses EventStream entirely. Uses `.ingest inline` KQL command to push data directly into KQL tables. Simpler for demos, no EventStream required.

---

## Pattern 1: EventStream — `azure-eventhub` SDK

### Installation
```bash
pip install azure-eventhub
```

### Basic Injection

```python
from azure.eventhub import EventHubProducerClient, EventData
import json

CONNECTION_STRING = "Endpoint=sb://...;SharedAccessKeyName=...;SharedAccessKey=...;EntityPath=..."

producer = EventHubProducerClient.from_connection_string(CONNECTION_STRING)

with producer:
    batch = producer.create_batch()
    
    event = {
        "SensorId": "SN001",
        "Timestamp": "2025-12-01T01:00:00Z",
        "ReadingValue": 450.2,
        "SensorType": "Temperature",
        "IsAnomaly": False
    }
    
    batch.add(EventData(json.dumps(event)))
    producer.send_batch(batch)

print("Event sent successfully")
```

### Batch Injection (Multiple Events)

```python
from azure.eventhub import EventHubProducerClient, EventData
import json

CONNECTION_STRING = "Endpoint=sb://...;..."

def send_events(events: list[dict]):
    """Send a list of events in batches."""
    producer = EventHubProducerClient.from_connection_string(CONNECTION_STRING)
    
    with producer:
        batch = producer.create_batch()
        sent = 0
        
        for event in events:
            try:
                batch.add(EventData(json.dumps(event)))
            except ValueError:
                # Batch is full — send it and start a new one
                producer.send_batch(batch)
                sent += len(batch)
                batch = producer.create_batch()
                batch.add(EventData(json.dumps(event)))
        
        # Send remaining events
        if len(batch) > 0:
            producer.send_batch(batch)
            sent += len(batch)
    
    print(f"Sent {sent} events")
    return sent
```

### Multi-Table Routing

Include a `_table` field in each event to route to different KQL tables:

```python
import json, random, datetime
from azure.eventhub import EventHubProducerClient, EventData

CONNECTION_STRING = "Endpoint=sb://...;..."

def generate_sensor_reading():
    return {
        "_table": "SensorReading",
        "SensorId": f"SN{random.randint(1, 100):03d}",
        "Timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "ReadingValue": round(random.uniform(100, 600), 2),
        "SensorType": random.choice(["Temperature", "Pressure", "Flow"]),
        "QualityFlag": "Good",
        "IsAnomaly": random.random() < 0.05
    }

def generate_equipment_alert():
    return {
        "_table": "EquipmentAlert",
        "AlertId": f"AL{random.randint(1, 10000):05d}",
        "SensorId": f"SN{random.randint(1, 100):03d}",
        "Timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "AlertType": random.choice(["HighTemp", "LowPressure", "Vibration"]),
        "Severity": random.choice(["Low", "Medium", "High", "Critical"]),
        "Message": "Threshold exceeded"
    }

producer = EventHubProducerClient.from_connection_string(CONNECTION_STRING)
with producer:
    batch = producer.create_batch()
    
    for _ in range(100):
        event = generate_sensor_reading() if random.random() > 0.1 else generate_equipment_alert()
        try:
            batch.add(EventData(json.dumps(event)))
        except ValueError:
            producer.send_batch(batch)
            batch = producer.create_batch()
            batch.add(EventData(json.dumps(event)))
    
    producer.send_batch(batch)
```

### Continuous Streaming (Simulated Real-Time)

```python
import time, json, random, datetime
from azure.eventhub import EventHubProducerClient, EventData

CONNECTION_STRING = "Endpoint=sb://...;..."
EVENTS_PER_SECOND = 10
DURATION_SECONDS = 60

producer = EventHubProducerClient.from_connection_string(CONNECTION_STRING)

with producer:
    total = 0
    start = time.time()
    
    while time.time() - start < DURATION_SECONDS:
        batch = producer.create_batch()
        
        for _ in range(EVENTS_PER_SECOND):
            event = {
                "_table": "SensorReading",
                "SensorId": f"SN{random.randint(1, 50):03d}",
                "Timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "ReadingValue": round(random.uniform(100, 600), 2),
                "SensorType": random.choice(["Temperature", "Pressure", "Flow"]),
                "IsAnomaly": random.random() < 0.05
            }
            batch.add(EventData(json.dumps(event)))
        
        producer.send_batch(batch)
        total += EVENTS_PER_SECOND
        print(f"Sent {total} events ({EVENTS_PER_SECOND}/sec)")
        time.sleep(1.0)

print(f"Done. Total events: {total}")
```

---

## PowerShell — Event Hub SDK

For PowerShell-based demos, use .NET SDK interop:

```powershell
# Option 1: Use Python from PowerShell
python -c "
from azure.eventhub import EventHubProducerClient, EventData
import json

conn = '$ConnectionString'
producer = EventHubProducerClient.from_connection_string(conn)
with producer:
    batch = producer.create_batch()
    batch.add(EventData(json.dumps({'SensorId': 'SN001', 'Value': 42.5})))
    producer.send_batch(batch)
print('OK')
"

# Option 2: Use Azure CLI Event Hub extension (limited)
az eventhubs eventhub send --connection-string $ConnectionString --event-hub $EntityPath --body '{"SensorId":"SN001"}'
```

> **Recommendation**: Use Python for EventStream injection. The `azure-eventhub` SDK is the most reliable and well-documented approach.

---

## Event Schema Design

### Recommended Event Structure

```json
{
    "_table": "SensorReading",
    "SensorId": "SN001",
    "EquipmentId": "EQ001",
    "RefineryId": "REF001",
    "Timestamp": "2025-12-01T01:00:00Z",
    "ReadingValue": 450.2,
    "MeasurementUnit": "DegF",
    "SensorType": "Temperature",
    "QualityFlag": "Good",
    "IsAnomaly": false
}
```

### Schema Rules

| Rule | Why |
|------|-----|
| Flat JSON (no deep nesting) | KQL mapping works column-by-column |
| Include `_table` for routing | Multi-table destination pattern |
| Include ISO 8601 timestamps | KQL `datetime` auto-parsing |
| Use consistent field names | Must match KQL table column names |
| Keep events under 1MB | Event Hub hard limit per event |
| Include all FK columns | Enables joins with dimension tables |

### Type Mapping (JSON → KQL)

| JSON Type | KQL Type | Example |
|-----------|----------|---------|
| `string` | `string` | `"SN001"` |
| `number` (integer) | `long` | `42` |
| `number` (decimal) | `real` | `42.5` |
| `boolean` | `bool` | `true` / `false` |
| `string` (ISO 8601) | `datetime` | `"2025-12-01T01:00:00Z"` |
| `null` | (column default) | `null` |

---

## Batching Best Practices

| Parameter | Recommendation | Notes |
|-----------|---------------|-------|
| Batch size | 100–500 events | Balance throughput vs latency |
| Event size | < 256KB each | Optimal for AMQP; max 1MB |
| Send interval | 1–5 seconds | For simulated streaming demos |
| Total batch size | < 1MB | Event Hub batch limit |
| Compression | Not needed for < 1MB | SDK handles internally |

### Error Handling

```python
from azure.eventhub import EventHubProducerClient, EventData
from azure.eventhub.exceptions import EventHubError
import json, time

def send_with_retry(events: list[dict], connection_string: str, max_retries: int = 3):
    """Send events with retry logic."""
    producer = EventHubProducerClient.from_connection_string(connection_string)
    
    for attempt in range(max_retries):
        try:
            with producer:
                batch = producer.create_batch()
                for event in events:
                    try:
                        batch.add(EventData(json.dumps(event)))
                    except ValueError:
                        producer.send_batch(batch)
                        batch = producer.create_batch()
                        batch.add(EventData(json.dumps(event)))
                producer.send_batch(batch)
            return True
        except EventHubError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff
    
    return False
```

---

## Pattern 2: Direct Kusto Streaming Ingestion (No EventStream)

> **Proven pattern** from `Fabric RTI Demo/src/inject_data.py` — bypasses EventStream entirely by pushing data directly into KQL tables via the Kusto management endpoint.

### When to Use Direct Kusto Streaming
- **Demo simplicity**: No EventStream setup required, no connection string to copy from portal
- **Single destination**: Data goes to one KQL Database only
- **Full control**: Python generates + sends data in one script
- **Limitation**: No processing nodes, no multi-destination fan-out, no Lakehouse archival (use EventStream for those)

### Prerequisites
1. KQL table exists with streaming ingestion enabled:
   ```kql
   .alter table SensorReading policy streamingingestion enable
   ```
2. Kusto token with scope `{queryServiceUri}/.default`

### Implementation (Battle-Tested)
```python
import requests, time, math, random
from datetime import datetime, timezone

def get_kusto_token(query_service_uri: str) -> str:
    """Get Kusto token with multi-scope fallback."""
    import subprocess, json
    scopes = [
        f"{query_service_uri}/.default",
        "https://kusto.kusto.windows.net/.default",
        "https://api.fabric.microsoft.com/.default"
    ]
    for scope in scopes:
        try:
            result = subprocess.run(
                ["az", "account", "get-access-token", "--scope", scope],
                capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)["accessToken"]
        except subprocess.CalledProcessError:
            continue
    raise RuntimeError("Failed to get Kusto token with any scope")

def kusto_mgmt(query_service_uri: str, db_name: str, csl: str, token: str):
    """Execute a KQL management command."""
    resp = requests.post(
        f"{query_service_uri}/v1/rest/mgmt",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"db": db_name, "csl": csl}
    )
    resp.raise_for_status()
    return resp.json()

def ingest_batch(query_service_uri: str, db_name: str, table_name: str, 
                 rows: list[str], token: str):
    """Ingest a batch of CSV rows directly into a KQL table.
    
    Uses `.ingest inline` — each row is a CSV line matching table columns.
    Batch size of ~200 rows works well for streaming ingestion (tested with 100K+ rows).
    Larger batches (500+) may hit request size limits.
    """
    csv_block = "\n".join(rows)
    csl = f".ingest inline into table {table_name} with (format='csv') <|\n{csv_block}"
    kusto_mgmt(query_service_uri, db_name, csl, token)

# Example: Continuous sensor data injection
BATCH_SIZE = 200
INTERVAL_SECONDS = 2

token = get_kusto_token(QUERY_SERVICE_URI)
batch = []

while True:
    # Generate a sensor reading (sinusoidal + noise + anomaly)
    t = time.time()
    base_value = 300 + 100 * math.sin(t / 60)
    noise = random.gauss(0, 5)
    is_anomaly = random.random() < 0.03
    value = base_value + noise + (random.uniform(100, 200) if is_anomaly else 0)
    
    row = f"SN001,SITE01,ZONE_A,{datetime.now(timezone.utc).isoformat()},{value:.2f},Temperature,DegF,{'true' if is_anomaly else 'false'}"
    batch.append(row)
    
    if len(batch) >= BATCH_SIZE:
        ingest_batch(QUERY_SERVICE_URI, DB_NAME, "SensorReading", batch, token)
        print(f"Ingested {len(batch)} rows")
        batch = []
    
    time.sleep(INTERVAL_SECONDS)
```

### Comparison: EventStream vs Direct Kusto Streaming

| Feature | EventStream + Event Hub SDK | Direct Kusto `.ingest inline` |
|---------|---------------------------|-------------------------------|
| Setup complexity | Higher (create ES, copy conn string) | Lower (just KQL table + token) |
| Multi-destination | ✅ KQL + Lakehouse + Custom App | ❌ Single KQL table |
| Processing nodes | ✅ Filter, Aggregate, Join, etc. | ❌ None |
| Protocol | AMQP / Kafka | HTTPS (REST) |
| Throughput | Higher (Event Hub optimized) | Lower (REST overhead) |
| For demos | Good for production-like demos | Best for simple data generation demos |
| Dependencies | `azure-eventhub` package | `requests` only |

---

## Demo Data Generation Patterns

### Pattern 1: Realistic Sensor Telemetry

Generate readings that follow realistic patterns (sine wave + noise):

```python
import math, random, datetime

def generate_realistic_readings(sensor_id: str, base_value: float, 
                                 amplitude: float, noise: float,
                                 count: int, interval_sec: int = 60):
    """Generate realistic sensor readings with periodic pattern + noise."""
    events = []
    start = datetime.datetime.utcnow()
    
    for i in range(count):
        ts = start + datetime.timedelta(seconds=i * interval_sec)
        # Sine wave pattern (24h period) + random noise
        phase = (i * interval_sec / 86400) * 2 * math.pi
        value = base_value + amplitude * math.sin(phase) + random.gauss(0, noise)
        is_anomaly = abs(value - base_value) > 2 * amplitude
        
        events.append({
            "_table": "SensorReading",
            "SensorId": sensor_id,
            "Timestamp": ts.isoformat() + "Z",
            "ReadingValue": round(value, 2),
            "QualityFlag": "Suspect" if is_anomaly else "Good",
            "IsAnomaly": is_anomaly
        })
    
    return events
```

### Pattern 2: Burst + Anomaly Injection

```python
def inject_anomaly_burst(sensor_id: str, base_events: list, burst_start: int, burst_count: int = 5):
    """Insert a burst of anomalous readings at a specific position."""
    for i in range(burst_count):
        idx = burst_start + i
        if idx < len(base_events):
            base_events[idx]["ReadingValue"] *= 2.5  # spike
            base_events[idx]["IsAnomaly"] = True
            base_events[idx]["QualityFlag"] = "Bad"
    return base_events
```

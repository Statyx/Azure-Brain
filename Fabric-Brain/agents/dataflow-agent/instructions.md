# Dataflow Agent — Instructions

## System Prompt

You are an expert at Dataflow Gen2 in Microsoft Fabric. You create ETL pipelines using Power Query M language, configure data destinations, set up staging for performance, and manage incremental refresh patterns. You bridge business-user-friendly visual ETL with the Fabric data platform.

**Before Dataflow work**, load `power_query_patterns.md` for M expressions and `data_destinations.md` for destination configuration.

---

## Mandatory Rules

### Rule 1: Dataflow Gen2 vs Gen1
Always use **Dataflow Gen2** in Fabric. Gen1 (Power BI Dataflows) is legacy.

| Feature | Gen1 (Legacy) | Gen2 (Fabric) |
|---------|--------------|---------------|
| Destinations | CDM folder only | Lakehouse, Warehouse, KQL DB |
| Staging | Manual | Built-in Staging Lakehouse |
| Compute | Power Query Online | Fabric Spark (via staging) |
| Scale | Limited | Fabric capacity-scaled |
| API type | `DataflowGen1` | `DataflowGen2` |

### Rule 2: Use Staging Lakehouse for Performance
When enabled, Dataflow Gen2 stages data in a Lakehouse using Spark, significantly improving performance for large datasets.

```
Source → Power Query (transform) → Staging Lakehouse → Destination
```

Without staging, data flows through the Power Query engine which is slower for large volumes.

### Rule 3: Mashup Document Structure
Dataflow definitions use a specific mashup document format:

```json
{
    "definition": {
        "parts": [
            {
                "path": "mashup",
                "payload": "<base64-encoded-mashup-content>",
                "payloadType": "InlineBase64"
            }
        ]
    }
}
```

The mashup content is a structured document containing:
- `version` — Always "1.0"
- `queriesMetadata` — Query names, types, and settings
- `queries` — The actual M expressions
- `document` — Global document properties

### Rule 4: M Expressions Must Be Valid Power Query M
Power Query M is a functional language. Key syntax rules:
- **let/in** blocks for query steps
- **each** keyword for row-level functions
- **#"Step Name"** for referencing previous steps
- **Table.*** functions for table operations
- **Text.*** / Number.* / Date.* for type operations

### Rule 5: Destination Must Exist Before Dataflow Runs
If the destination is a Lakehouse table, the Lakehouse must already exist. The Dataflow will create the table if needed, but the Lakehouse item must be present.

---

## Decision Trees

### "When should I use a Dataflow vs Spark Notebook?"
```
├── Simple ETL (filter, rename, merge) → Dataflow Gen2
├── Business user needs to maintain it → Dataflow Gen2
├── Complex transformations (ML, UDFs) → Spark Notebook
├── Very large data (>10M rows) → Spark Notebook (or Dataflow with staging)
├── Need visual/low-code editor → Dataflow Gen2
├── Need Python/Scala code → Spark Notebook
├── Need real-time → EventStream (neither)
└── Need scheduled refresh → Dataflow Gen2 (built-in) or Pipeline + Notebook
```

### "How do I create a Dataflow?"
```
├── 1. Create the Dataflow item
│   └── POST /v1/workspaces/{wsId}/items with type "DataflowGen2"
├── 2. Define the mashup document
│   ├── Write M queries for each output table
│   ├── Configure destination (Lakehouse, Warehouse, etc.)
│   └── Optionally enable staging
├── 3. Push definition
│   └── POST /v1/workspaces/{wsId}/items/{dfId}/updateDefinition
├── 4. Run/refresh the Dataflow
│   └── POST /v1/workspaces/{wsId}/items/{dfId}/jobs/instances?jobType=Pipeline
└── 5. Monitor execution
    └── Poll job status (see monitoring-agent)
```

### "How do I connect to a data source?"
```
├── SQL Server / Azure SQL
│   └── Sql.Database("server.database.windows.net", "dbname")
├── Azure Blob / ADLS
│   └── AzureStorage.Blobs("https://account.blob.core.windows.net/container")
├── SharePoint
│   └── SharePoint.Tables("https://site.sharepoint.com/sites/mysite")
├── Web API / REST
│   └── Web.Contents("https://api.example.com/data")
├── Excel file
│   └── Excel.Workbook(File.Contents("path/file.xlsx"))
├── CSV file
│   └── Csv.Document(File.Contents("path/file.csv"))
├── OData
│   └── OData.Feed("https://services.odata.org/V4/service")
└── Lakehouse Files
    └── Lakehouse.Contents() — browse Lakehouse files
```

---

## API Quick Reference

> **Scopes**: `Dataflow.Read.All`, `Dataflow.ReadWrite.All`, `Dataflow.Execute.All`  
> Service principals and managed identities are supported.

### Core CRUD

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create Dataflow | POST | `/v1/workspaces/{wsId}/dataflows` |
| Get Dataflow | GET | `/v1/workspaces/{wsId}/dataflows/{dfId}` |
| List Dataflows | GET | `/v1/workspaces/{wsId}/dataflows` |
| Update Dataflow | PATCH | `/v1/workspaces/{wsId}/dataflows/{dfId}` |
| Delete Dataflow | DELETE | `/v1/workspaces/{wsId}/dataflows/{dfId}` |
| Get Definition | POST | `/v1/workspaces/{wsId}/dataflows/{dfId}/getDefinition` |
| Update Definition | POST | `/v1/workspaces/{wsId}/dataflows/{dfId}/updateDefinition` |

### Parameters API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Discover Parameters | GET | `/v1/workspaces/{wsId}/dataflows/{dfId}/parameters` |

**Parameter types**: `String`, `Boolean`, `Integer`, `Number`, `DateTime`, `DateTimeZone`, `Date`, `Time`, `Duration`

### Execute / Apply Changes Jobs

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Run On-Demand (Execute) | POST | `/v1/workspaces/{wsId}/dataflows/{dfId}/jobs/instances?jobType=Execute` |
| Run On-Demand (ApplyChanges) | POST | `/v1/workspaces/{wsId}/dataflows/{dfId}/jobs/instances?jobType=ApplyChanges` |
| Get Job Instance | GET | `/v1/workspaces/{wsId}/dataflows/{dfId}/jobs/instances/{jobId}` |
| Create Schedule | POST | `/v1/workspaces/{wsId}/dataflows/{dfId}/jobs/schedule` |
| Update Schedule | PATCH | `/v1/workspaces/{wsId}/dataflows/{dfId}/jobs/schedule/{scheduleId}` |
| Delete Schedule | DELETE | `/v1/workspaces/{wsId}/dataflows/{dfId}/jobs/schedule/{scheduleId}` |

> **Max 20 schedulers** per dataflow. `executeOption`: `SkipApplyChanges` or `ApplyChangesIfNeeded`.

### Execute Query API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Execute Query | POST | `/v1/workspaces/{wsId}/dataflows/{dfId}/executeQuery` |

> Returns data in **Apache Arrow** stream format. Supports custom mashup documents. Long-running operation (LRO).

### Create Dataflow

```python
import requests, base64

API = "https://api.fabric.microsoft.com/v1"

def create_dataflow(ws_id: str, name: str, token: str) -> str:
    """Create an empty Dataflow Gen2 item."""
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/dataflows",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "displayName": name,
            "description": f"Dataflow: {name}"
        }
    )
    resp.raise_for_status()
    return resp.json()["id"]
```

### Push Definition

```python
def push_dataflow_definition(ws_id: str, df_id: str, mashup_content: str, token: str):
    """Push a mashup document to a Dataflow Gen2."""
    payload = base64.b64encode(mashup_content.encode("utf-8")).decode("utf-8")
    
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/items/{df_id}/updateDefinition",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "definition": {
                "parts": [{
                    "path": "mashup",
                    "payload": payload,
                    "payloadType": "InlineBase64"
                }]
            }
        }
    )
    resp.raise_for_status()
    print(f"✅ Dataflow definition updated: {df_id}")
```

### Run Dataflow (Execute with optional parameter overrides)

```python
def run_dataflow(ws_id: str, df_id: str, token: str, params: dict = None):
    """Trigger a Dataflow refresh with optional parameter overrides.
    
    jobType options:
    - "Execute": Run the dataflow (SkipApplyChanges or ApplyChangesIfNeeded)
    - "ApplyChanges": Apply staged changes only
    """
    body = {}
    if params:
        # Override parameters at execution time
        body["executionData"] = {
            "parameters": {name: {"value": val} for name, val in params.items()},
            "executeOption": "ApplyChangesIfNeeded"
        }
    
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/dataflows/{df_id}/jobs/instances?jobType=Execute",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body if body else None
    )
    if resp.status_code == 202:
        location = resp.headers.get("Location")
        print(f"✅ Dataflow triggered. Poll: {location}")
        return location
    else:
        print(f"❌ Failed: {resp.status_code} {resp.text}")
        return None
```

### Discover Parameters

```python
def get_dataflow_parameters(ws_id: str, df_id: str, token: str) -> list:
    """Discover typed parameters in a Dataflow.
    
    Parameter types: String, Boolean, Integer, Number, DateTime, 
                     DateTimeZone, Date, Time, Duration
    """
    resp = requests.get(
        f"{API}/workspaces/{ws_id}/dataflows/{df_id}/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    return resp.json().get("value", [])
```

### Execute Query (Apache Arrow Response)

```python
def execute_query(ws_id: str, df_id: str, token: str, mashup: str = None):
    """Execute a query against a Dataflow and get results in Apache Arrow format.
    
    Returns: LRO location URL to poll for Arrow stream response.
    """
    body = {}
    if mashup:
        body["mashupDocument"] = mashup
    
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/dataflows/{df_id}/executeQuery",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body
    )
    if resp.status_code == 202:
        return resp.headers.get("Location")
    resp.raise_for_status()
```

---

## Dataflow Architecture

```
┌───────────────────────────────────────────┐
│            Dataflow Gen2                   │
│                                            │
│  ┌──────────┐    ┌──────────────────────┐ │
│  │  Source   │ →  │  Power Query M       │ │
│  │ (SQL,CSV, │    │  (filter, rename,    │ │
│  │  API,etc) │    │   merge, transform)  │ │
│  └──────────┘    └──────────┬───────────┘ │
│                              │             │
│                   ┌──────────▼──────────┐  │
│                   │  Staging Lakehouse  │  │
│                   │  (optional, Spark)  │  │
│                   └──────────┬──────────┘  │
│                              │             │
│                   ┌──────────▼──────────┐  │
│                   │   Destination       │  │
│                   │  (Lakehouse table,  │  │
│                   │   Warehouse, KQL)   │  │
│                   └─────────────────────┘  │
└───────────────────────────────────────────┘
```

---

## Dataflow vs Other ETL Options

| Feature | Dataflow Gen2 | Spark Notebook | Pipeline Copy | EventStream |
|---------|--------------|----------------|---------------|-------------|
| Interface | Visual / M code | Code (Python/Scala) | Config-based | Config + code |
| Best for | Moderate ETL | Complex transforms | Simple copy | Real-time |
| Skill level | Business user | Data engineer | Any | Data engineer |
| Scale | Medium | Large | Large | Real-time |
| Scheduling | Built-in | Via Pipeline | Built-in | Continuous |
| Destinations | LH, WH, KQL | LH (Delta) | LH, WH | LH, EH, KQL |

---

## Cross-References

| Topic | Agent | File |
|-------|-------|------|
| Lakehouse as destination | lakehouse-agent | `instructions.md` |
| Pipeline orchestrating Dataflows | orchestrator-agent | `pipelines.md` |
| Semantic Model over Dataflow output | semantic-model-agent | `instructions.md` |
| Monitoring Dataflow runs | monitoring-agent | `instructions.md` |
| Domain model for table design | domain-modeler-agent | `dimensional_modeling.md` |

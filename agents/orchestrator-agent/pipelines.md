# Data Pipelines — Complete Reference

## Overview

Data Pipelines in Fabric are the orchestration engine (similar to Azure Data Factory).
They chain activities (Copy, Notebook, Dataflow, Web, ForEach, IfCondition, Wait, etc.)
and execute them sequentially or in parallel.

---

## Pipeline REST API

**Base**: `https://api.fabric.microsoft.com/v1`  
**Auth**: `az account get-access-token --resource "https://api.fabric.microsoft.com"`

### CRUD Operations

```python
import requests, json, base64, time

API = "https://api.fabric.microsoft.com/v1"
WS_ID = "133c6c70-2e26-4d97-aac1-8ed423dbbf34"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

#### List Pipelines
```python
resp = requests.get(f"{API}/workspaces/{WS_ID}/dataPipelines", headers=headers)
pipelines = resp.json()["value"]
```

#### Create Pipeline (empty)
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/dataPipelines",
    headers=headers,
    json={"displayName": "PL_My_Pipeline", "description": "Ingestion pipeline"}
)
# 201 = sync success, 202 = async → poll x-ms-operation-id
```

#### Create Pipeline (with definition)
```python
pipeline_def = {
    "properties": {
        "activities": [
            # ... activity definitions
        ]
    }
}
payload = base64.b64encode(json.dumps(pipeline_def).encode()).decode()

resp = requests.post(
    f"{API}/workspaces/{WS_ID}/dataPipelines",
    headers=headers,
    json={
        "displayName": "PL_My_Pipeline",
        "definition": {
            "parts": [
                {
                    "path": "pipeline-content.json",
                    "payload": payload,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
)
```

#### Get Pipeline Definition (async)
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/dataPipelines/{pipeline_id}/getDefinition",
    headers=headers
)
if resp.status_code == 202:
    op_id = resp.headers["x-ms-operation-id"]
    # Poll until Succeeded
    for _ in range(24):
        time.sleep(5)
        op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
        if op["status"] == "Succeeded":
            result = requests.get(f"{API}/operations/{op_id}/result", headers=headers).json()
            # Decode parts
            for part in result["definition"]["parts"]:
                content = base64.b64decode(part["payload"]).decode()
                print(f"{part['path']}: {content[:200]}...")
            break
```

#### Update Pipeline Definition
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/dataPipelines/{pipeline_id}/updateDefinition",
    headers=headers,
    json={
        "definition": {
            "parts": [
                {
                    "path": "pipeline-content.json",
                    "payload": payload,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
)
```

#### Run Pipeline
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/items/{pipeline_id}/jobs/instances?jobType=Pipeline",
    headers=headers,
    json={"executionData": {}}
)
# Returns 202 → poll for completion
```

---

## Pipeline Definition Format

The `pipeline-content.json` follows ADF-like structure:

```json
{
    "properties": {
        "activities": [
            {
                "name": "Copy_Sales_Data",
                "type": "Copy",
                "dependsOn": [],
                "policy": {
                    "timeout": "0.12:00:00",
                    "retry": 2,
                    "retryIntervalInSeconds": 30
                },
                "typeProperties": {
                    "source": { ... },
                    "sink": { ... }
                }
            }
        ]
    }
}
```

---

## Activity Types

### Copy Activity
Moves data from source to sink.

```json
{
    "name": "Copy_CSV_to_Lakehouse",
    "type": "Copy",
    "dependsOn": [],
    "policy": {
        "timeout": "0.12:00:00",
        "retry": 2,
        "retryIntervalInSeconds": 30
    },
    "typeProperties": {
        "source": {
            "type": "BlobSource",
            "recursive": true
        },
        "sink": {
            "type": "LakehouseSink",
            "tableActionOption": "Append"
        },
        "enableStaging": false
    }
}
```

### Notebook Activity
Runs a Spark notebook.

```json
{
    "name": "Run_Transform_Notebook",
    "type": "SparkNotebook",
    "dependsOn": [
        {
            "activity": "Copy_CSV_to_Lakehouse",
            "dependencyConditions": ["Succeeded"]
        }
    ],
    "policy": {
        "timeout": "0.12:00:00",
        "retry": 0
    },
    "typeProperties": {
        "notebookId": "86729c39-33a4-454a-8170-0ac363ee809c",
        "parameters": {
            "input_path": {
                "value": "Files/raw/sales",
                "type": "string"
            }
        }
    }
}
```

### ForEach Activity
Iterates over a collection.

```json
{
    "name": "ForEach_Tables",
    "type": "ForEach",
    "dependsOn": [],
    "typeProperties": {
        "isSequential": false,
        "batchCount": 5,
        "items": {
            "value": "@pipeline().parameters.tables",
            "type": "Expression"
        },
        "activities": [
            {
                "name": "Copy_Table",
                "type": "Copy",
                "typeProperties": { ... }
            }
        ]
    }
}
```

### IfCondition Activity
Conditional branching.

```json
{
    "name": "Check_Row_Count",
    "type": "IfCondition",
    "dependsOn": [{"activity": "Copy_Data", "dependencyConditions": ["Succeeded"]}],
    "typeProperties": {
        "expression": {
            "value": "@greater(activity('Copy_Data').output.rowsCopied, 0)",
            "type": "Expression"
        },
        "ifTrueActivities": [ ... ],
        "ifFalseActivities": [ ... ]
    }
}
```

### Wait Activity
Pauses execution for a specified duration.

```json
{
    "name": "Wait_For_Propagation",
    "type": "Wait",
    "dependsOn": [{"activity": "Upload_Files", "dependencyConditions": ["Succeeded"]}],
    "typeProperties": {
        "waitTimeInSeconds": 30
    }
}
```

### Web Activity
Calls an external HTTP endpoint.

```json
{
    "name": "Call_Webhook",
    "type": "WebActivity",
    "dependsOn": [{"activity": "Transform_Data", "dependencyConditions": ["Succeeded"]}],
    "typeProperties": {
        "method": "POST",
        "url": "https://webhook.example.com/notify",
        "body": {
            "status": "complete",
            "pipeline": "@pipeline().Pipeline"
        }
    }
}
```

---

## Pipeline Parameters

```json
{
    "properties": {
        "parameters": {
            "source_folder": {
                "type": "String",
                "defaultValue": "raw/sales"
            },
            "target_schema": {
                "type": "String",
                "defaultValue": "dbo"
            },
            "tables": {
                "type": "Array",
                "defaultValue": ["customers", "orders", "products"]
            }
        },
        "activities": [ ... ]
    }
}
```

Access in expressions: `@pipeline().parameters.source_folder`

---

## Dependency Conditions

| Condition | Meaning |
|-----------|---------|
| `Succeeded` | Previous activity succeeded |
| `Failed` | Previous activity failed |
| `Completed` | Previous activity completed (success or failure) |
| `Skipped` | Previous activity was skipped |

---

## Existing Pipeline Reference

**PL_Load_Finance_Data** (`7fdd5622-9313-4a5f-a769-dccef65a5015`)
- Runs notebook `NB_Load_CSV_to_Delta` (`86729c39-33a4-454a-8170-0ac363ee809c`)
- Cold start on F16: ~2 min `NotStarted`, total ~4 min
- Triggered via API: `POST /items/{id}/jobs/instances?jobType=Pipeline`

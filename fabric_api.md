# Fabric REST API — Patterns & Reference

## Base URL
```
https://api.fabric.microsoft.com/v1
```

## Authentication

Three token scopes used depending on the API:

| Operation | Token Resource |
|-----------|----------------|
| Fabric items (workspaces, reports, models, pipelines) | `https://api.fabric.microsoft.com` |
| OneLake file operations (DFS API) | `https://storage.azure.com` |
| Azure Resource Manager (capacity management) | `https://management.azure.com` |

Acquire via Azure CLI:
```powershell
az account get-access-token --resource "https://api.fabric.microsoft.com" --query accessToken -o tsv
```

In Python:
```python
import subprocess
result = subprocess.run(
    "az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv",
    capture_output=True, text=True, shell=True,
)
token = result.stdout.strip()
```

**Important**: Do NOT use `az rest` from Python `subprocess` — it hangs. Use `requests` library instead.

## Async Operations

Most creation and update operations are **asynchronous** (HTTP 202).

Pattern:
```python
import requests, time

resp = requests.post(url, headers=headers, json=body)

if resp.status_code == 200:
    # Rare — synchronous success
    result = resp.json()

elif resp.status_code == 202:
    # Standard async — poll operation
    op_id = resp.headers.get("x-ms-operation-id")
    for i in range(24):
        time.sleep(5)
        op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
        if op["status"] == "Succeeded":
            # Get result if needed
            result = requests.get(f"{API}/operations/{op_id}/result", headers=headers).json()
            break
        if op["status"] in ("Failed", "Cancelled"):
            raise RuntimeError(op.get("error", {}))
```

## Common Operations

### List Workspace Items
```
GET /v1/workspaces/{wsId}/items?type={type}
```
Types: `Report`, `SemanticModel`, `Lakehouse`, `Notebook`, `DataPipeline`

### Create Item
```
POST /v1/workspaces/{wsId}/items
Body: { "displayName": "...", "type": "Report", "definition": { "parts": [...] } }
```

### Update Item Definition
```
POST /v1/workspaces/{wsId}/items/{itemId}/updateDefinition
Body: { "definition": { "parts": [...] } }
```

### Get Item Definition (async)
```
POST /v1/workspaces/{wsId}/items/{itemId}/getDefinition
→ 202 with operation ID
→ GET /v1/operations/{opId}/result → { "definition": { "parts": [...] } }
```

### Delete Item
```
DELETE /v1/workspaces/{wsId}/items/{itemId}
```

### Run Pipeline
```
POST /v1/workspaces/{wsId}/items/{pipelineId}/jobs/instances?jobType=Pipeline
Body: {"executionData":{}}
```

### Run Notebook
```
POST /v1/workspaces/{wsId}/items/{notebookId}/jobs/instances?jobType=RunNotebook
→ 202 → poll Location header until status == "Completed"
```
> **jobType is `RunNotebook`**, NOT `SparkJob`.

### EventStream Operations
```
# Get EventStream topology (sources, streams, destinations)
GET /v1/workspaces/{wsId}/eventstreams/{esId}/topology

# Update EventStream definition
POST /v1/workspaces/{wsId}/eventstreams/{esId}/updateDefinition
Body: {"definition": {"parts": [...]}}
```
> Custom Endpoint connection string is NOT available via API — get from Fabric portal.

## Definition Parts Format

Every Fabric item definition is an array of `parts`:
```json
{
  "definition": {
    "parts": [
      {
        "path": "report.json",
        "payload": "<base64-encoded-content>",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

Base64 encoding:
```python
import base64, json
payload = base64.b64encode(json.dumps(obj).encode("utf-8")).decode("ascii")
```

## Rate Limits & Tips

- Fabric API has rate limits — add small delays between batch operations
- `getDefinition` is always async (even for small items)
- `updateDefinition` replaces the entire definition — you cannot patch individual parts
- Item names must be unique within a workspace (by type)

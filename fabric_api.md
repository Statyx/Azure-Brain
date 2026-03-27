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

### Python Credential Chain

For robust auth in Python scripts, use a credential chain with MSAL caching:

```python
from azure.identity import AzureCliCredential, InteractiveBrowserCredential, ChainedTokenCredential

credential = ChainedTokenCredential(
    AzureCliCredential(),
    InteractiveBrowserCredential(
        cache_persistence_options=TokenCachePersistenceOptions()
    )
)
token = credential.get_token("https://api.fabric.microsoft.com/.default").token
```

**Order matters**: `AzureCliCredential` first (fast, non-interactive), `InteractiveBrowserCredential` as fallback (pops browser).

**Important**: Do NOT use `az rest` from Python `subprocess` — it hangs. Use `requests` library instead.

## Async Operations

Most creation and update operations are **asynchronous** (HTTP 202).

**CRITICAL**: Always use `allow_redirects=False` on all requests. The `Location` header redirect URL can hang indefinitely on SSL read.

Pattern:
```python
import requests, time

resp = requests.post(url, headers=headers, json=body, allow_redirects=False)

if resp.status_code == 200:
    # Rare — synchronous success
    result = resp.json()

elif resp.status_code == 202:
    # Standard async — poll operation
    op_id = resp.headers.get("x-ms-operation-id")
    for i in range(40):
        time.sleep(3 if i < 10 else 5)
        op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
        if op["status"] == "Succeeded":
            # Get result if needed (skip for updateDefinition)
            result = requests.get(f"{API}/operations/{op_id}/result", headers=headers).json()
            break
        if op["status"] in ("Failed", "Cancelled"):
            raise RuntimeError(op.get("error", {}))
```

> **For `updateDefinition` operations**: Skip the `/result` fetch — just confirm status is "Succeeded". The result endpoint can hang.

## Retry Logic for Transient Errors

Detect and retry transient failures with exponential backoff:

```python
TRANSIENT_PATTERNS = ["429", "503", "timeout", "throttl", "connection"]

def is_transient(error_text):
    return any(p in error_text.lower() for p in TRANSIENT_PATTERNS)

# Retry pattern: 3s × 2^attempt, max 2 retries
for attempt in range(3):
    try:
        resp = requests.post(url, headers=headers, json=body, allow_redirects=False)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 3 * (2 ** attempt)))
            time.sleep(wait)
            continue
        break
    except requests.exceptions.RequestException as e:
        if attempt < 2 and is_transient(str(e)):
            time.sleep(3 * (2 ** attempt))
            continue
        raise
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
- Always use `allow_redirects=False` on all requests (prevents SSL hangs)

## Data Agent Chat Endpoint

Query a Data Agent programmatically (sandbox or production):

```
POST https://api.fabric.microsoft.com/v1/workspaces/{wsId}/aiskills/{agentId}/aiassistant/openai?stage={stage}
```

- `stage`: `sandbox` (draft) or `production` (published)
- Auth: Same Fabric token (`https://api.fabric.microsoft.com/.default`)
- Body: OpenAI-compatible chat format

```python
resp = requests.post(
    f"{API}/workspaces/{ws_id}/aiskills/{agent_id}/aiassistant/openai?stage=sandbox",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={"messages": [{"role": "user", "content": "What is Q1 revenue?"}]},
    allow_redirects=False
)
```

## TMDL Definition Format

Semantic models can be retrieved in TMDL format for schema parsing:

```
POST /v1/workspaces/{wsId}/semanticModels/{modelId}/getDefinition?format=TMDL
→ 202 → poll → GET /operations/{opId}/result
```

Each part is a base64-encoded `.tmdl` file. Descriptions use `///` doc comments (NOT `description` property):

```tmdl
/// Total revenue from all product sales
measure 'Total Revenue' = SUM('FactSales'[Amount])
    formatString: "#,0.00"
```

Parse with:
```python
for part in definition["parts"]:
    content = base64.b64decode(part["payload"]).decode("utf-8")
    # Extract /// comments as descriptions
    for line in content.split("\n"):
        if line.strip().startswith("///"):
            description = line.strip()[3:].strip()
```

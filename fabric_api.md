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

## Data Agent Chat Endpoint (Assistants API)

Data Agents use an **OpenAI Assistants-compatible thread API**, NOT a simple chat endpoint.

Base URL:
```
https://api.fabric.microsoft.com/v1/workspaces/{wsId}/dataAgents/{agentId}/aiassistant/openai
```

> **Also works**: `/aiskills/{agentId}/aiassistant/openai` (legacy alias)

Required params on ALL calls: `stage=sandbox` (or `production`) + `api-version=2024-02-15-preview`

### Full Conversation Flow

```python
import requests, time

base = f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/dataAgents/{agent_id}/aiassistant/openai"
params = {"stage": "sandbox", "api-version": "2024-02-15-preview"}
h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 1. Create thread (Fabric returns same thread per agent/user — IMPORTANT)
thread = requests.post(f"{base}/threads", headers=h, params=params, json={}, timeout=30).json()
thread_id = thread["id"]

# 2. CRITICAL: Delete thread to prevent context overflow (see Thread Management below)
requests.delete(f"{base}/threads/{thread_id}", headers=h, 
                params={"api-version": "2024-02-15-preview"}, timeout=15)  # NO stage param!
thread = requests.post(f"{base}/threads", headers=h, params=params, json={}, timeout=30).json()
thread_id = thread["id"]

# 3. Send message
requests.post(f"{base}/threads/{thread_id}/messages", headers=h, params=params,
              json={"role": "user", "content": "What is Q1 revenue?"}, timeout=30)

# 4. Create assistant + run
asst = requests.post(f"{base}/assistants", headers=h, params=params,
                     json={"model": "irrelevant"}, timeout=30).json()
run = requests.post(f"{base}/threads/{thread_id}/runs", headers=h, params=params,
                    json={"assistant_id": asst["id"]}, timeout=30).json()
run_id = run["id"]

# 5. Poll until completed
while True:
    time.sleep(2)
    status = requests.get(f"{base}/threads/{thread_id}/runs/{run_id}",
                          headers=h, params=params, timeout=30).json()["status"]
    if status in ("completed", "failed"): break

# 6. Get messages (filter by run_id)
msgs = requests.get(f"{base}/threads/{thread_id}/messages",
                    headers=h, params={**params, "limit": 10, "order": "desc"}, timeout=30).json()
answer_msgs = [m for m in msgs["data"] if m.get("run_id") == run_id and m["role"] == "assistant"]

# 7. Get run steps (pipeline trace: fewshots → nl2code → execute → answer)
steps = requests.get(f"{base}/threads/{thread_id}/runs/{run_id}/steps",
                     headers=h, params={**params, "limit": 100}, timeout=30).json()
```

### Thread Management — CRITICAL

**Fabric reuses the same thread per agent/user.** Messages accumulate across runs. After ~50 messages, the thread causes `BadRequest` errors and the agent skips DAX generation entirely (falls back to cached answers).

**Fix**: Delete + recreate the thread before each question:
```python
# DELETE does NOT accept 'stage' param — only api-version
requests.delete(f"{base}/threads/{thread_id}", headers=h,
                params={"api-version": "2024-02-15-preview"}, timeout=15)
# Then POST /threads to get a fresh one
```

### Pipeline Steps (run_steps)

A healthy run produces 6 steps (in reverse chronological order):

| Step | Tool Name | Purpose |
|------|-----------|---------|
| 1 | `analyze.database.fewshots.loading` | Loads few-shot examples |
| 2 | `analyze.database.fewshots.matching` | Matches question to examples |
| 3 | `analyze.database.nl2code` | Generates DAX query |
| 4 | `trace.analyze_semantic_model` | Executes query against model |
| 5 | `analyze.database.execute` | Returns query results |
| 6 | `generate.filename` | Names the output file |

**If only step 1 appears** → thread pollution or agent error. Delete thread and retry.

---

## Extended Token Audience Matrix

Full list of token audiences/scopes by API surface:

| API Surface | Token Audience / Resource | `.default` Scope |
|-------------|--------------------------|------------------|
| Fabric REST API | `https://api.fabric.microsoft.com` | `https://api.fabric.microsoft.com/.default` |
| OneLake DFS | `https://storage.azure.com` | `https://storage.azure.com/.default` |
| Azure Resource Manager | `https://management.azure.com` | `https://management.azure.com/.default` |
| Kusto / Eventhouse | `https://kusto.kusto.windows.net` | `https://kusto.kusto.windows.net/.default` |
| Power BI REST API | `https://analysis.windows.net/powerbi/api` | `https://analysis.windows.net/powerbi/api/.default` |
| SQL (TDS endpoint) | `https://database.windows.net` | `https://database.windows.net/.default` |
| Microsoft Graph | `https://graph.microsoft.com` | `https://graph.microsoft.com/.default` |

> **Fabric Eventhouse** also accepts `{QueryServiceUri}` as token resource (the cluster URI itself). Try cluster URI first, then `https://kusto.kusto.windows.net` as fallback.

## Environment URLs

| Service | URL Pattern |
|---------|-------------|
| Fabric REST API | `https://api.fabric.microsoft.com/v1` |
| Power BI REST API | `https://api.powerbi.com/v1.0/myorg` |
| OneLake DFS | `https://onelake.dfs.fabric.microsoft.com` |
| OneLake Blob | `https://onelake.blob.fabric.microsoft.com` |
| SQL Analytics Endpoint | `*.datawarehouse.fabric.microsoft.com` |
| Kusto Query (Eventhouse) | `https://{guid}.{region}.kusto.fabric.microsoft.com` |
| Semantic Link | `https://api.powerbi.com/v1.0/myorg/groups/{wsId}/datasets/{id}` |
| XMLA Endpoint | `powerbi://api.powerbi.com/v1.0/myorg/{workspace_name}` |
| ARM (Capacity Mgmt) | `https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{cap}` |
| MCP Power BI | `https://api.fabric.microsoft.com/v1/mcp/powerbi` |

## Identity Types

| Identity | Description | Use Case |
|----------|-------------|----------|
| **User** (delegated) | Interactive user login, `az login` | Development, ad-hoc operations |
| **Service Principal** | Entra App Registration with secret/cert | CI/CD, automation, scheduled jobs |
| **Managed Identity** | System/User-assigned MI for Azure resources | Azure Functions, VMs calling Fabric |
| **Workspace Identity** | Fabric workspace-level identity | Cross-workspace, OneLake shortcuts |

### Entra App Registration (for SPN)
1. Portal → App registrations → New
2. Add API permission: `Power BI Service` → `Tenant.ReadWrite.All` (or granular)
3. Admin consent required for tenant-level scopes
4. Authenticate:
```python
from azure.identity import ClientSecretCredential
credential = ClientSecretCredential(tenant_id, client_id, client_secret)
token = credential.get_token("https://api.fabric.microsoft.com/.default").token
```

## Pagination Pattern

All list endpoints use `continuationToken` for pagination:

```python
def list_all_items(workspace_id, item_type, headers):
    """Paginate through all items of a given type."""
    items = []
    url = f"{API}/workspaces/{workspace_id}/items?type={item_type}"
    while url:
        resp = requests.get(url, headers=headers).json()
        items.extend(resp.get("value", []))
        token = resp.get("continuationToken")
        url = f"{API}/workspaces/{workspace_id}/items?type={item_type}&continuationToken={token}" if token else None
    return items
```

> **Note**: Some endpoints (e.g., admin APIs) use `continuationUri` instead — check the response structure.

## Rate Limiting

- **HTTP 429** — Read the `Retry-After` header (seconds) and wait before retrying
- **Batch operations** — Add 200-500ms delay between calls when creating/updating multiple items
- **getDefinition / updateDefinition** — Rate-limited more aggressively; add 1-2s delay between sequential calls
- **Admin APIs** — Separate rate limit pool; may return 429 independently

## LRO Polling Helper (Reusable)

```python
def poll_operation(op_id, headers, timeout_seconds=300, fetch_result=True):
    """Poll a Fabric LRO until completion. Returns result if fetch_result=True."""
    import time
    start = time.time()
    while time.time() - start < timeout_seconds:
        op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
        status = op.get("status")
        if status == "Succeeded":
            if fetch_result:
                return requests.get(f"{API}/operations/{op_id}/result", headers=headers).json()
            return op
        if status in ("Failed", "Cancelled"):
            raise RuntimeError(f"Operation {op_id} {status}: {op.get('error', {})}")
        time.sleep(3)
    raise TimeoutError(f"Operation {op_id} did not complete in {timeout_seconds}s")
```

## CLI Templates (`az rest`)

When using Azure CLI instead of Python, use `az rest` with `--resource` (NOT `--headers`):

```bash
# List workspace items
az rest --method GET \
  --url "https://api.fabric.microsoft.com/v1/workspaces/{wsId}/items?type=Lakehouse" \
  --resource "https://api.fabric.microsoft.com"

# Create item
az rest --method POST \
  --url "https://api.fabric.microsoft.com/v1/workspaces/{wsId}/items" \
  --resource "https://api.fabric.microsoft.com" \
  --body '{"displayName": "MyItem", "type": "Lakehouse"}'

# OneLake listing
az rest --method GET \
  --url "https://onelake.dfs.fabric.microsoft.com/{wsId}?resource=filesystem&recursive=false" \
  --resource "https://storage.azure.com"
```

> **CRITICAL**: Always use `--resource` to set the token audience. `--headers "Authorization=Bearer ..."` bypasses `az`'s token management and can cause auth issues.

## Capacity Management API (ARM)

```bash
# Resume capacity
az rest --method POST \
  --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{cap}/resume?api-version=2023-11-01"

# Suspend capacity
az rest --method POST \
  --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{cap}/suspend?api-version=2023-11-01"

# Check capacity state
az rest --method GET \
  --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{cap}?api-version=2023-11-01" \
  | jq '.properties.state'
```

## Job Execution Types

| Item Type | jobType Parameter | Notes |
|-----------|-------------------|-------|
| Notebook | `RunNotebook` | NOT `SparkJob` |
| Data Pipeline | `Pipeline` | Empty `executionData: {}` |
| Spark Job Definition | `SparkJob` | Only for SparkJobDefinition items |
| Semantic Model Refresh | `enhanced` | For import/DirectQuery refresh |

```
POST /v1/workspaces/{wsId}/items/{itemId}/jobs/instances?jobType={jobType}
```

---

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

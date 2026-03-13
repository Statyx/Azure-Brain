# Data Ingestion — Complete Reference

## Overview

Getting data INTO the Fabric Lakehouse. Three main paths:
1. **OneLake DFS API** — Direct file upload (CSV, Parquet, JSON)
2. **Copy Jobs** — Managed copy from external sources
3. **Shortcuts** — Virtual pointers to external data (no copy)

---

## 1. OneLake DFS API (Direct Upload)

**The proven, working approach for local files.**

### Endpoint
```
https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}/Files/{path}
```

### Auth
```powershell
az account get-access-token --resource "https://storage.azure.com" --query accessToken -o tsv
```

**Token resource**: `https://storage.azure.com` — NOT the Fabric API token!

### 3-Step Upload Protocol

OneLake uses ADLS Gen2 protocol. Files must be uploaded in exactly 3 steps.

#### Python
```python
import requests

STORAGE_TOKEN = "..."  # from az account get-access-token --resource https://storage.azure.com
WS_ID = "133c6c70-2e26-4d97-aac1-8ed423dbbf34"
LH_ID = "f2c42d3b-d402-43e7-b8fb-a9aa395c14e1"
BASE = f"https://onelake.dfs.fabric.microsoft.com/{WS_ID}/{LH_ID}/Files"

headers = {"Authorization": f"Bearer {STORAGE_TOKEN}"}

def upload_file(local_path: str, remote_path: str):
    """Upload a file to OneLake using 3-step ADLS protocol."""
    url = f"{BASE}/{remote_path}"
    
    # Step 1: Create empty file
    resp = requests.put(f"{url}?resource=file", headers=headers)
    assert resp.status_code == 201, f"Create failed: {resp.status_code}"
    
    # Step 2: Append content
    with open(local_path, "rb") as f:
        data = f.read()
    resp = requests.patch(
        f"{url}?action=append&position=0",
        headers={**headers, "Content-Type": "application/octet-stream"},
        data=data,
    )
    assert resp.status_code == 202, f"Append failed: {resp.status_code}"
    
    # Step 3: Flush (commit)
    resp = requests.patch(f"{url}?action=flush&position={len(data)}", headers=headers)
    assert resp.status_code == 200, f"Flush failed: {resp.status_code}"
    
    return len(data)
```

#### PowerShell
```powershell
$storageToken = az account get-access-token --resource "https://storage.azure.com" --query accessToken -o tsv
$wsId = "133c6c70-2e26-4d97-aac1-8ed423dbbf34"
$lhId = "f2c42d3b-d402-43e7-b8fb-a9aa395c14e1"
$base = "https://onelake.dfs.fabric.microsoft.com/$wsId/$lhId/Files"

function Upload-ToOneLake {
    param([string]$LocalPath, [string]$RemotePath)
    
    $uri = "$base/$RemotePath"
    $bytes = [System.IO.File]::ReadAllBytes($LocalPath)
    $h = @{Authorization = "Bearer $storageToken"}
    
    # Create
    Invoke-RestMethod -Uri "$uri`?resource=file" -Method PUT -Headers $h
    
    # Append
    Invoke-RestMethod -Uri "$uri`?action=append&position=0" -Method PATCH `
        -Headers ($h + @{"Content-Type" = "application/octet-stream"}) -Body $bytes
    
    # Flush
    Invoke-RestMethod -Uri "$uri`?action=flush&position=$($bytes.Length)" -Method PATCH -Headers $h
}
```

#### Batch Upload (multiple files)
```python
import os

def upload_folder(local_folder: str, remote_folder: str):
    """Upload all files in a local folder to OneLake."""
    for root, dirs, files in os.walk(local_folder):
        for filename in files:
            local_path = os.path.join(root, filename)
            # Preserve subfolder structure
            relative = os.path.relpath(local_path, local_folder).replace("\\", "/")
            remote_path = f"{remote_folder}/{relative}"
            size = upload_file(local_path, remote_path)
            print(f"  Uploaded {relative} ({size:,} bytes)")
```

### OneLake Directory Listing
```python
def list_files(remote_folder: str):
    """List files in a OneLake directory."""
    url = f"{BASE}/{remote_folder}?resource=filesystem&recursive=true"
    resp = requests.get(url, headers=headers)
    return resp.json().get("paths", [])
```

### Critical Rules
- `position` in flush **MUST** equal exact byte count of uploaded content
- Use `https://storage.azure.com` token (NOT Fabric API token)
- MCP `upload_file` tool returns 400 → **always use DFS API directly**

---

## 2. Copy Jobs

Managed copy operations from external sources into Fabric.

### API Endpoints
```
GET    /v1/workspaces/{wsId}/copyJobs           # List
POST   /v1/workspaces/{wsId}/copyJobs           # Create
GET    /v1/workspaces/{wsId}/copyJobs/{id}      # Get
PATCH  /v1/workspaces/{wsId}/copyJobs/{id}      # Update
DELETE /v1/workspaces/{wsId}/copyJobs/{id}      # Delete
POST   /v1/workspaces/{wsId}/copyJobs/{id}/getDefinition
POST   /v1/workspaces/{wsId}/copyJobs/{id}/updateDefinition
```

### Create Copy Job
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/copyJobs",
    headers=headers,
    json={
        "displayName": "CJ_Import_Sales",
        "description": "Copy sales data from Azure Blob to Lakehouse"
    }
)
```

### Create Copy Job with Definition
```python
import base64, json

copy_def = {
    # Copy job definition structure
    "source": {
        "type": "AzureBlobStorage",
        "connectionId": "<connection-id>",
        "path": "container/folder"
    },
    "destination": {
        "type": "Lakehouse",
        "workspaceId": WS_ID,
        "itemId": LH_ID,
        "path": "Files/raw/sales"
    }
}

payload = base64.b64encode(json.dumps(copy_def).encode()).decode()

resp = requests.post(
    f"{API}/workspaces/{WS_ID}/copyJobs",
    headers=headers,
    json={
        "displayName": "CJ_Import_Sales",
        "definition": {
            "parts": [
                {
                    "path": "copyjob-content.json",
                    "payload": payload,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
)
```

### Required Scopes
- `CopyJob.ReadWrite.All` or `Item.ReadWrite.All`
- Service principals supported ✅

---

## 3. Shortcuts

Virtual references to external data — no data movement.

### Supported Sources
- OneLake (another lakehouse/warehouse)
- Azure Data Lake Storage Gen2
- Amazon S3
- Google Cloud Storage
- Dataverse

### Create via REST API
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/items/{LH_ID}/shortcuts",
    headers=headers,
    json={
        "name": "external_sales",
        "path": "Tables",
        "target": {
            "type": "AdlsGen2",
            "adlsGen2": {
                "connectionId": "<connection-guid>",
                "location": "https://storageaccount.dfs.core.windows.net",
                "subpath": "/container/folder"
            }
        }
    }
)
```

### When to Use Shortcuts vs Copy
| Criterion | Shortcut | Copy Job |
|-----------|----------|----------|
| Data freshness | Real-time | Batch |
| Cross-region cost | Egress charges | One-time copy |
| Transformations needed | No | Yes |
| Data residency | Stays at source | Moved to Fabric |
| Performance | Network dependent | Local after copy |

---

## 4. Supported External Sources for Ingestion

| Source | Recommended Method |
|--------|--------------------|
| Local CSV/Parquet/JSON | OneLake DFS upload → Notebook (CSV→Delta) |
| Azure Blob Storage | Copy Job or Shortcut |
| Azure SQL Database | Copy Activity in Pipeline |
| Azure Data Lake Gen2 | Shortcut (preferred) or Copy Job |
| Amazon S3 | Shortcut or Copy Job |
| REST API | Web Activity → OneLake upload |
| On-premises SQL | On-premises data gateway → Copy Activity |

---

## Common Ingestion Patterns

### Pattern 1: CSV → Lakehouse → Delta Table
```
1. Upload CSV to OneLake (DFS API) → Files/raw/{table}/
2. Run Notebook (Spark) to read CSV → write Delta → Tables/{table}
3. Semantic model auto-discovers Delta tables
```

### Pattern 2: External DB → Lakehouse (Pipeline)
```
1. Create Pipeline with Copy Activity
2. Source = SQL connector, Sink = Lakehouse
3. Schedule pipeline for recurring loads
```

### Pattern 3: External Lake → No-copy read (Shortcut)
```
1. Create ADLS Gen2 shortcut in Lakehouse
2. Data appears as Delta tables (if source is Delta)
3. Zero data movement, real-time access
```

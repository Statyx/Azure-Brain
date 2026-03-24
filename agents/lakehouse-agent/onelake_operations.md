# OneLake Operations — File Upload, Directory Management & DFS API

## OneLake DFS API Fundamentals

OneLake is the unified data lake for Microsoft Fabric. All Lakehouses, Warehouses, and KQL databases store data in OneLake using the Azure Data Lake Storage (ADLS) Gen2 protocol.

**Base URL**: `https://onelake.dfs.fabric.microsoft.com`  
**Token Scope**: `https://storage.azure.com/.default`  
**Auth**: Bearer token (Azure CLI: `az account get-access-token --resource https://storage.azure.com`)

### URL Pattern
```
https://onelake.dfs.fabric.microsoft.com/{workspaceId}/{itemId}/{rootFolder}/{path}
```
- `{workspaceId}` — Workspace GUID  
- `{itemId}` — Lakehouse GUID  
- `{rootFolder}` — `Files` (raw files) or `Tables` (Delta tables)  
- `{path}` — File or folder path within the root

---

## 3-Step File Upload Protocol

Every file upload requires exactly 3 HTTP calls in sequence:

### Step 1: Create Empty File
```http
PUT https://onelake.dfs.fabric.microsoft.com/{wsId}/{lhId}/Files/{path}?resource=file
Authorization: Bearer {storage_token}
```
**Response**: `201 Created`

### Step 2: Append Content
```http
PATCH https://onelake.dfs.fabric.microsoft.com/{wsId}/{lhId}/Files/{path}?action=append&position=0
Authorization: Bearer {storage_token}
Content-Type: application/octet-stream

{file_content_bytes}
```
**Response**: `202 Accepted`

### Step 3: Flush (Commit)
```http
PATCH https://onelake.dfs.fabric.microsoft.com/{wsId}/{lhId}/Files/{path}?action=flush&position={byte_count}
Authorization: Bearer {storage_token}
```
**Response**: `200 OK`

> **CRITICAL**: `position` in Step 3 MUST equal the exact number of bytes uploaded in Step 2. If they don't match, the flush fails silently and the file remains empty.

---

## Python Implementation

### Single File Upload
```python
import requests

ONELAKE = "https://onelake.dfs.fabric.microsoft.com"
WS_ID = "<workspace-guid>"
LH_ID = "<lakehouse-guid>"

def get_storage_token():
    """Get OneLake storage token."""
    import subprocess, json
    result = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://storage.azure.com"],
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)["accessToken"]

def upload_to_onelake(file_path: str, content: bytes, token: str):
    """Upload a file to OneLake Files/ using 3-step protocol."""
    base = f"{ONELAKE}/{WS_ID}/{LH_ID}/Files/{file_path}"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Create
    r1 = requests.put(f"{base}?resource=file", headers=headers)
    r1.raise_for_status()
    
    # Step 2: Append
    r2 = requests.patch(
        f"{base}?action=append&position=0",
        headers={**headers, "Content-Type": "application/octet-stream"},
        data=content
    )
    r2.raise_for_status()
    
    # Step 3: Flush
    r3 = requests.patch(f"{base}?action=flush&position={len(content)}", headers=headers)
    r3.raise_for_status()
    
    print(f"✅ Uploaded {file_path} ({len(content)} bytes)")

# Usage
token = get_storage_token()
with open("data.csv", "rb") as f:
    upload_to_onelake("raw/data.csv", f.read(), token)
```

### Batch File Upload
```python
import os

def upload_directory(local_dir: str, remote_prefix: str, token: str):
    """Upload all files in a local directory to OneLake."""
    for root, dirs, files in os.walk(local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative = os.path.relpath(local_path, local_dir).replace("\\", "/")
            remote_path = f"{remote_prefix}/{relative}"
            
            with open(local_path, "rb") as f:
                content = f.read()
            
            upload_to_onelake(remote_path, content, token)

# Upload all CSVs
upload_directory("data/raw/", "raw", token)
```

### Upload with BOM-Free Encoding
```python
def prepare_csv_content(csv_path: str) -> bytes:
    """Read CSV and return BOM-free UTF-8 bytes."""
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    return content.encode("utf-8")  # No BOM

content = prepare_csv_content("data/customers.csv")
upload_to_onelake("raw/customers.csv", content, token)
```

---

## PowerShell Implementation

### Single File Upload
```powershell
$wsId = "<workspace-guid>"
$lhId = "<lakehouse-guid>"
$token = (az account get-access-token --resource https://storage.azure.com | ConvertFrom-Json).accessToken
$base = "https://onelake.dfs.fabric.microsoft.com/$wsId/$lhId/Files"
$headers = @{ "Authorization" = "Bearer $token" }

function Upload-ToOneLake {
    param([string]$LocalPath, [string]$RemotePath)
    
    $content = [System.IO.File]::ReadAllBytes($LocalPath)
    $url = "$base/$RemotePath"
    
    # Step 1: Create
    Invoke-RestMethod -Uri "$url`?resource=file" -Method PUT -Headers $headers
    
    # Step 2: Append
    Invoke-RestMethod -Uri "$url`?action=append&position=0" -Method PATCH `
        -Headers ($headers + @{ "Content-Type" = "application/octet-stream" }) `
        -Body $content
    
    # Step 3: Flush
    Invoke-RestMethod -Uri "$url`?action=flush&position=$($content.Length)" -Method PATCH -Headers $headers
    
    Write-Host "Uploaded $RemotePath ($($content.Length) bytes)"
}

# Usage
Upload-ToOneLake -LocalPath ".\data.csv" -RemotePath "raw/data.csv"
```

---

## Directory Operations

### Create Directory
```python
def create_directory(path: str, token: str):
    """Create a directory in OneLake."""
    url = f"{ONELAKE}/{WS_ID}/{LH_ID}/Files/{path}?resource=directory"
    r = requests.put(url, headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
```

### List Directory Contents
```python
def list_directory(path: str, token: str):
    """List files and directories under a path."""
    url = f"{ONELAKE}/{WS_ID}/{LH_ID}/Files/{path}?resource=filesystem&recursive=false"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json().get("paths", [])
```

### Delete File
```python
def delete_file(path: str, token: str):
    """Delete a file from OneLake."""
    url = f"{ONELAKE}/{WS_ID}/{LH_ID}/Files/{path}"
    r = requests.delete(url, headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
```

### Read File Content
```python
def read_file(path: str, token: str) -> bytes:
    """Read a file from OneLake."""
    url = f"{ONELAKE}/{WS_ID}/{LH_ID}/Files/{path}"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.content
```

---

## Copy Job API (Bulk Ingestion)

For large data loads from external sources, use the Copy Job API instead of the DFS upload.

```python
def run_copy_job(source_connection_id: str, source_path: str, table_name: str, token: str):
    """Run a Copy Job to load data into a Lakehouse table."""
    fabric_token = get_fabric_token()  # https://api.fabric.microsoft.com/.default
    
    resp = requests.post(
        f"https://api.fabric.microsoft.com/v1/workspaces/{WS_ID}/items/{LH_ID}/jobs/instances?jobType=CopyJob",
        headers={"Authorization": f"Bearer {fabric_token}"},
        json={
            "executionData": {
                "source": {
                    "connectionId": source_connection_id,
                    "relativePath": source_path
                },
                "destination": {
                    "type": "Table",
                    "tableName": table_name,
                    "loadType": "Overwrite"  # or "Append"
                }
            }
        }
    )
    # Returns 202; poll Location header for completion
    return resp.headers.get("Location")
```

---

## Token Reference

| Operation | Scope | Get Token |
|-----------|-------|-----------|
| OneLake DFS (file ops) | `https://storage.azure.com` | `az account get-access-token --resource https://storage.azure.com` |
| Fabric REST API | `https://api.fabric.microsoft.com` | `az account get-access-token --resource https://api.fabric.microsoft.com` |
| Azure Resource Manager | `https://management.azure.com` | `az account get-access-token --resource https://management.azure.com` |

> **Common Mistake**: Using the Fabric API token for OneLake uploads. OneLake requires `storage.azure.com` token.

---

## Best Practices

1. **Always encode as UTF-8 without BOM** — Use `encoding="utf-8-sig"` when reading source files to strip BOM, then write with `"utf-8"`
2. **Create directories before uploading files** — OneLake doesn't auto-create parent directories
3. **Use batch upload for multiple files** — Reduce round trips by preparing all files first
4. **Verify uploads** — After uploading, read back a small sample to confirm
5. **Handle token expiry** — Storage tokens expire after ~60 minutes; refresh on 401
6. **Prefer Shortcuts over copies** — When data is in ADLS Gen2 or another Lakehouse, use Shortcuts (zero data movement)
7. **Raw files → Spark → Delta** — Don't try to write Delta directly via DFS; upload raw files, then use Spark notebooks to create Delta tables

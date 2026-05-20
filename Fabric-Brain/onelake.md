# OneLake DFS API — File Upload Protocol

## URL Formats

### DFS API (file operations)
```
https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{item_id}/Files/{path}
```

### Blob API (alternative for some tools)
```
https://onelake.blob.fabric.microsoft.com/{workspace_id}/{item_id}
```

### ABFS URI (Spark / Notebooks)
```
abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{item_id}/Files/{path}
abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{item_id}/Tables/{table_name}
```

> **ABFS format**: Used in Spark notebooks to access OneLake. Works the same as ADLS Gen2.

### Tables vs Files
- `Files/` — Unstructured storage (CSV, Parquet, images, etc.)
- `Tables/` — Managed Delta Lake tables (created by notebooks/Spark)

## Endpoint
```
https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{item_id}/Files/{path}
```

## Authentication
```powershell
az account get-access-token --resource "https://storage.azure.com" --query accessToken -o tsv
```

**Token resource**: `https://storage.azure.com` (NOT `https://api.fabric.microsoft.com`)

## 3-Step Upload Protocol

OneLake implements the Azure Data Lake Storage Gen2 (ADLS) protocol.
Files must be uploaded in exactly 3 steps:

### Step 1 — Create (PUT)
Creates an empty file placeholder.

```
PUT {base_url}/{folder}/{filename}?resource=file
Authorization: Bearer {storage_token}
```

Response: `201 Created`

### Step 2 — Append (PATCH)
Uploads the file content starting at position 0.

```
PATCH {base_url}/{folder}/{filename}?action=append&position=0
Authorization: Bearer {storage_token}
Content-Type: application/octet-stream
Body: <raw file bytes>
```

Response: `202 Accepted`

### Step 3 — Flush (PATCH)
Commits the upload at the total byte count.

```
PATCH {base_url}/{folder}/{filename}?action=flush&position={total_bytes}
Authorization: Bearer {storage_token}
```

Response: `200 OK`

**CRITICAL**: The `position` in flush MUST equal the exact byte count of the uploaded content.

## Python Example

```python
import requests

storage_token = "..."  # from az account get-access-token --resource https://storage.azure.com
headers = {"Authorization": f"Bearer {storage_token}"}
base = f"https://onelake.dfs.fabric.microsoft.com/{ws_id}/{lh_id}/Files/raw"

def upload_file(local_path: str, remote_folder: str, filename: str):
    url = f"{base}/{remote_folder}/{filename}"
    
    # Step 1: Create
    requests.put(f"{url}?resource=file", headers=headers)
    
    # Step 2: Append
    with open(local_path, "rb") as f:
        data = f.read()
    requests.patch(
        f"{url}?action=append&position=0",
        headers={**headers, "Content-Type": "application/octet-stream"},
        data=data,
    )
    
    # Step 3: Flush
    requests.patch(f"{url}?action=flush&position={len(data)}", headers=headers)
```

## PowerShell Example

```powershell
$storageToken = az account get-access-token --resource "https://storage.azure.com" --query accessToken -o tsv
$base = "https://onelake.dfs.fabric.microsoft.com/$wsId/$lhId/Files/raw"

foreach ($file in Get-ChildItem data/raw -Recurse -Filter *.csv) {
    $subfolder = $file.Directory.Name
    $uri = "$base/$subfolder/$($file.Name)"
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)

    # Create
    Invoke-RestMethod -Uri "$uri`?resource=file" -Method PUT `
        -Headers @{Authorization="Bearer $storageToken"}

    # Append
    Invoke-RestMethod -Uri "$uri`?action=append&position=0" -Method PATCH `
        -Headers @{Authorization="Bearer $storageToken"; "Content-Type"="application/octet-stream"} `
        -Body $bytes

    # Flush
    Invoke-RestMethod -Uri "$uri`?action=flush&position=$($bytes.Length)" -Method PATCH `
        -Headers @{Authorization="Bearer $storageToken"}
}
```

## Folder Structure Convention

```
LH_Finance/
  Files/
    raw/
      finance/
        dim_chart_of_accounts.csv
        dim_cost_centers.csv
        fact_general_ledger.csv
        fact_budgets.csv
        fact_forecasts.csv
        fact_allocations.csv
      business/
        dim_customers.csv
        dim_products.csv
        fact_invoices.csv
        fact_invoice_lines.csv
        fact_payments.csv
  Tables/                ← Created by Notebook (Delta format)
    dim_chart_of_accounts/
    dim_cost_centers/
    ...
```

## Gotchas

1. **MCP `upload_file` does NOT work** — returns HTTP 400. Always use DFS API directly.
2. **Capacity must be running** — OneLake returns 404/empty when capacity is paused.
3. **Token scope is `storage.azure.com`** — not the Fabric API scope.
4. **Folder creation is implicit** — uploading `raw/finance/file.csv` creates `raw/finance/` automatically.
5. **Overwrite**: Re-uploading to the same path replaces the file. No special flag needed.

---

## Listing Files

List files and directories in OneLake using the DFS API:

```bash
# List root of item
az rest --method GET \
  --url "https://onelake.dfs.fabric.microsoft.com/{wsId}/{itemId}?resource=filesystem&recursive=false" \
  --resource "https://storage.azure.com"

# List a subfolder
az rest --method GET \
  --url "https://onelake.dfs.fabric.microsoft.com/{wsId}/{itemId}?resource=filesystem&recursive=false&directory=Files/raw" \
  --resource "https://storage.azure.com"
```

Python:
```python
resp = requests.get(
    f"https://onelake.dfs.fabric.microsoft.com/{ws_id}/{item_id}?resource=filesystem&recursive=false&directory=Files/raw",
    headers={"Authorization": f"Bearer {storage_token}"}
)
paths = resp.json().get("paths", [])
for p in paths:
    print(p["name"], p.get("contentLength", "dir"))
```

## OneLake Shortcuts

Shortcuts are virtual pointers to data in other locations — no data copy.

### Supported Shortcut Targets
| Target | Description |
|--------|-------------|
| OneLake (internal) | Another Lakehouse/Warehouse in the same or different workspace |
| ADLS Gen2 | Azure Data Lake Storage Gen2 account |
| S3 | Amazon S3 bucket |
| GCS | Google Cloud Storage bucket |
| Dataverse | Microsoft Dataverse tables |

### Create a Shortcut via REST API
```python
shortcut_body = {
    "path": "Files/external_data",
    "name": "my_shortcut",
    "target": {
        "oneLake": {
            "workspaceId": "{source_workspace_id}",
            "itemId": "{source_item_id}",
            "path": "Tables/my_table"
        }
    }
}
resp = requests.post(
    f"{API}/workspaces/{ws_id}/items/{lh_id}/shortcuts",
    headers=headers, json=shortcut_body
)
```

### ADLS Gen2 Shortcut
```python
shortcut_body = {
    "path": "Files/adls_data",
    "name": "adls_shortcut",
    "target": {
        "adlsGen2": {
            "location": "https://{account}.dfs.core.windows.net",
            "subpath": "/{container}/{folder}",
            "connectionId": "{connection_id}"  # Fabric connection item
        }
    }
}
```

### List Shortcuts
```
GET /v1/workspaces/{wsId}/items/{itemId}/shortcuts
```

### Delete Shortcut
```
DELETE /v1/workspaces/{wsId}/items/{itemId}/shortcuts/{shortcutPath}/{shortcutName}
```

> **Shortcuts require Workspace Identity** for cross-workspace OneLake shortcuts. Enable in workspace settings.

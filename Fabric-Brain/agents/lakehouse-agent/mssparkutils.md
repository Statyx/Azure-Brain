# mssparkutils — Fabric Notebook Utility Reference

## Overview

`mssparkutils` is Fabric's built-in utility library, available in every Spark notebook without installation. It provides file operations, credential management, notebook orchestration, and environment access.

---

## File System (`mssparkutils.fs`)

### List Files
```python
files = mssparkutils.fs.ls("Files/raw/")
for f in files:
    print(f.name, f.size, f.isDir)

# List Delta tables
tables = mssparkutils.fs.ls("Tables/")
```

### Copy / Move / Delete
```python
# Copy file
mssparkutils.fs.cp("Files/raw/sales.csv", "Files/archive/sales.csv", recurse=False)

# Move file
mssparkutils.fs.mv("Files/raw/sales.csv", "Files/processed/sales.csv")

# Delete file
mssparkutils.fs.rm("Files/temp/scratch.csv", recurse=False)

# Delete folder (recursive)
mssparkutils.fs.rm("Files/temp/", recurse=True)
```

### Create Directory
```python
mssparkutils.fs.mkdirs("Files/raw/2025/03/")
```

### Read / Write Text
```python
# Read small text file
content = mssparkutils.fs.head("Files/raw/config.json", maxBytes=1024)

# Write text content
mssparkutils.fs.put("Files/output/result.txt", "Processing complete", overwrite=True)

# Append
mssparkutils.fs.append("Files/output/log.txt", "Step 1 done\n", createFileIfNotExists=True)
```

### Mount External Storage
```python
# Mount ADLS Gen2
mssparkutils.fs.mount(
    "abfss://container@account.dfs.core.windows.net/folder",
    "/mnt/external",
    {"linkedService": "my_adls_connection"}
)

# Access mounted data
df = spark.read.csv("/mnt/external/data.csv")

# Unmount
mssparkutils.fs.unmount("/mnt/external")
```

---

## Credentials (`mssparkutils.credentials`)

### Get Token
```python
# Fabric API token
token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")

# Storage token
storage_token = mssparkutils.credentials.getToken("https://storage.azure.com")

# Kusto token
kusto_token = mssparkutils.credentials.getToken("https://kusto.kusto.windows.net")

# Graph API token
graph_token = mssparkutils.credentials.getToken("https://graph.microsoft.com")
```

> **This is the preferred way to get tokens inside notebooks** — no need for `azure-identity` or `az login`. Uses the notebook session's identity automatically.

### Get Secret (from Key Vault via Linked Service)
```python
secret = mssparkutils.credentials.getSecret("https://myvault.vault.azure.net/", "my-secret-name")
```

### Get Connection String
```python
conn_str = mssparkutils.credentials.getConnectionStringOrCreds("my_connection_name")
```

---

## Notebook Orchestration (`mssparkutils.notebook`)

### Run Another Notebook
```python
# Synchronous — waits for completion, returns exit value
result = mssparkutils.notebook.run("NB02_SilverTransform", timeoutInSeconds=600)
print(f"NB02 returned: {result}")
```

### Run with Parameters
```python
result = mssparkutils.notebook.run(
    "NB02_SilverTransform",
    timeoutInSeconds=600,
    arguments={"input_schema": "bronze", "output_schema": "silver", "mode": "overwrite"}
)
```

> **Receiving parameters in the called notebook**: Use `%%configure` cell or just read them as notebook parameters that Fabric passes automatically.

### Run Multiple Notebooks in Parallel
```python
from concurrent.futures import ThreadPoolExecutor

notebooks = ["NB01_Bronze", "NB02_Silver", "NB03_Gold"]

def run_nb(name):
    return mssparkutils.notebook.run(name, timeoutInSeconds=600)

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(run_nb, notebooks))
```

### Exit Notebook with Value
```python
# In the called notebook — return a value to the caller
mssparkutils.notebook.exit("success")
# or
mssparkutils.notebook.exit(json.dumps({"rows_processed": 15000, "status": "ok"}))
```

---

## Pipeline-to-Notebook Parameters

### From Pipeline Activity
In a Pipeline's SparkNotebook activity, parameters are passed as:
```json
{
    "type": "SparkNotebook",
    "typeProperties": {
        "notebookId": "{notebookId}",
        "parameters": {
            "source_path": {"value": "Files/raw/sales", "type": "string"},
            "target_table": {"value": "fact_sales", "type": "string"},
            "load_mode": {"value": "overwrite", "type": "string"}
        }
    }
}
```

### Receiving in Notebook
Parameters are auto-injected as notebook variables. Access them directly:
```python
# These variables are automatically created by Fabric when the notebook is called with parameters
# They don't need to be declared — just used

# Direct access (available as global variables)
print(source_path)   # "Files/raw/sales"
print(target_table)  # "fact_sales"
print(load_mode)     # "overwrite"
```

Or use a parameter cell with defaults (for interactive development):
```python
# Parameter cell (tag this cell as "parameters" in the notebook UI)
source_path = "Files/raw/sales"      # default for interactive runs
target_table = "fact_sales"           # overridden by pipeline
load_mode = "overwrite"               # overridden by pipeline
```

---

## Environment (`mssparkutils.env`)

```python
# Get workspace ID
ws_id = mssparkutils.env.getWorkspaceId()

# Get lakehouse ID (default lakehouse)
lh_id = mssparkutils.env.getLakehouseId()

# Get notebook name
nb_name = mssparkutils.env.getNotebookName()

# Get username
user = mssparkutils.env.getUserName()
```

---

## Runtime (`mssparkutils.runtime`)

```python
# Get Spark session context info
context = mssparkutils.runtime.context
print(context)
# Returns: workspace ID, notebook name, session ID, etc.
```

---

## Common Patterns

### End-to-End ETL Notebook with mssparkutils
```python
# Fabric notebook source

# CELL ********************
# Get token for external API call
import requests, json

token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
ws_id = mssparkutils.env.getWorkspaceId()

# CELL ********************
# List raw files
files = mssparkutils.fs.ls("Files/raw/")
csv_files = [f for f in files if f.name.endswith(".csv")]
print(f"Found {len(csv_files)} CSV files to process")

# CELL ********************
# Process each CSV → Delta
for f in csv_files:
    table_name = f.name.replace(".csv", "")
    df = spark.read.option("header", "true").option("inferSchema", "true").csv(f"Files/raw/{f.name}")
    df.write.mode("overwrite").format("delta").saveAsTable(table_name)
    print(f"  ✅ {table_name}: {df.count()} rows")

# CELL ********************
# Return summary
mssparkutils.notebook.exit(json.dumps({"files_processed": len(csv_files), "status": "success"}))
```

---

## Gotchas

1. **`mssparkutils` is not pip-installable** — It's a built-in; never `pip install mssparkutils`
2. **`mssparkutils.fs` paths are relative to the default Lakehouse** — `Files/` and `Tables/` resolve to the bound Lakehouse
3. **No default Lakehouse = `mssparkutils.fs` fails** — Must bind a Lakehouse to the notebook first
4. **`notebook.run()` timeout is in seconds** — 600 = 10 minutes, not milliseconds
5. **`notebook.run()` blocks the calling session** — Use ThreadPoolExecutor for parallel runs
6. **`getToken()` uses the notebook session identity** — No SPN or credential setup needed
7. **Parameter cell must be tagged** — In the Fabric UI, right-click the cell → "Toggle parameter cell"
8. **`notebook.exit()` only accepts strings** — Use `json.dumps()` for structured return values
9. **`fs.rm()` on Tables/ deletes the Delta table** — This is irreversible; use with caution
10. **Mounted paths persist across cells but not across sessions** — Re-mount in each notebook run

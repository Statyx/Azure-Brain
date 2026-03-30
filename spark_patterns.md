# Spark & Lakehouse Patterns — Authoring in Fabric

> Source: [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) — SPARK-AUTHORING-CORE.md

## Lakehouse Creation

### Basic Creation
```python
body = {"displayName": "LH_MyProject", "type": "Lakehouse"}
resp = requests.post(f"{API}/workspaces/{ws_id}/items", headers=h, json=body, allow_redirects=False)
```

### Enable Schemas (Multi-Schema Lakehouse)
```python
body = {
    "displayName": "LH_MyProject",
    "type": "Lakehouse",
    "definition": {
        "parts": [{
            "path": "lakehouse.metadata.json",
            "payload": base64.b64encode(json.dumps({"enableSchemas": True}).encode()).decode(),
            "payloadType": "InlineBase64"
        }]
    }
}
```

> **`enableSchemas: true`** enables multi-schema support — tables can be organized as `schema.table_name` (e.g., `bronze.raw_sales`, `silver.cleaned_sales`). This is ideal for medallion architecture but **cannot be changed after creation**.

### Schema Organization for Medallion
```
LH_MyProject/
  Tables/
    bronze/
      raw_customers/
      raw_orders/
    silver/
      cleaned_customers/
      cleaned_orders/
    gold/
      dim_customers/
      fact_orders/
  Files/
    raw/
      customers.csv
      orders.csv
```

---

## Notebook Management

### Create Notebook with Content
```python
notebook_py = """# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {"name": "synapse_pyspark"},
# META   "dependencies": {}
# META }

# CELL ********************
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

# Read CSV from Files
df = spark.read.option("header", "true").csv("Files/raw/customers.csv")
df.write.mode("overwrite").format("delta").saveAsTable("bronze.raw_customers")
"""

body = {
    "displayName": "NB01_BronzeLoad",
    "type": "Notebook",
    "definition": {
        "parts": [{
            "path": "notebook-content.py",
            "payload": base64.b64encode(notebook_py.encode("utf-8")).decode(),
            "payloadType": "InlineBase64"
        }]
    }
}
resp = requests.post(f"{API}/workspaces/{ws_id}/items", headers=h, json=body, allow_redirects=False)
```

> **CRITICAL**: Do NOT set `"format": "ipynb"` in the definition — causes `InvalidNotebookContent`.

### Default Lakehouse Binding
After creating a notebook, bind it to a default Lakehouse:
```python
# The definition includes a platform config that binds to a lakehouse
# This is set in the notebook's .platform part or via updateDefinition
```

> Notebooks need a default Lakehouse to resolve `Files/` and `Tables/` paths. Without it, `spark.read.csv("Files/...")` fails.

### LRO for Definition APIs
Both `getDefinition` and `updateDefinition` on notebooks are **always async** (HTTP 202). Always poll the operation ID.

---

## Notebook Execution

### Run a Notebook
```python
resp = requests.post(
    f"{API}/workspaces/{ws_id}/items/{nb_id}/jobs/instances?jobType=RunNotebook",
    headers=h, json={"executionData": {}},
    allow_redirects=False
)
op_id = resp.headers.get("x-ms-operation-id")

# Poll until complete
while True:
    op = requests.get(f"{API}/operations/{op_id}", headers=h).json()
    if op["status"] in ("Succeeded", "Failed", "Cancelled"):
        break
    time.sleep(10)
```

### Duplicate Job Prevention
Before starting a new job, check if one is already running:
```python
# List active jobs for an item
resp = requests.get(
    f"{API}/workspaces/{ws_id}/items/{nb_id}/jobs/instances?filter=status eq 'InProgress'",
    headers=h
)
active = resp.json().get("value", [])
if active:
    print(f"Job already running: {active[0]['id']}")
```

### Pool Options

| Pool Type | Warm-up | Best For |
|-----------|---------|----------|
| **Starter Pool** | ~15s | Dev/test, small jobs |
| **Workspace Pool** | ~30-60s | Production, shared across notebooks |
| **Custom Pool** | ~2-5 min | Large jobs, specific node sizes |

> **Starter Pool** (default): Fast start, limited resources. For production workloads, configure a Workspace Pool in workspace settings.

---

## Spark Patterns

### Read from Files → Write to Tables
```python
# Bronze: Raw ingestion
df = spark.read.option("header", "true").option("inferSchema", "true").csv("Files/raw/sales.csv")
df.write.mode("overwrite").format("delta").saveAsTable("bronze.raw_sales")

# Silver: Clean & standardize
df_silver = spark.sql("""
    SELECT
        CAST(sale_id AS BIGINT) AS sale_id,
        CAST(amount AS DECIMAL(18,2)) AS amount,
        TO_DATE(sale_date, 'yyyy-MM-dd') AS sale_date,
        UPPER(TRIM(customer_name)) AS customer_name
    FROM bronze.raw_sales
    WHERE sale_id IS NOT NULL
""")
df_silver.write.mode("overwrite").format("delta").saveAsTable("silver.cleaned_sales")

# Gold: Business aggregations
df_gold = spark.sql("""
    SELECT
        DATE_TRUNC('month', sale_date) AS month,
        customer_name,
        COUNT(*) AS order_count,
        SUM(amount) AS total_revenue
    FROM silver.cleaned_sales
    GROUP BY 1, 2
""")
df_gold.write.mode("overwrite").format("delta").saveAsTable("gold.monthly_revenue")
```

### Delta Table Operations
```python
# Read Delta table
df = spark.read.format("delta").table("bronze.raw_sales")

# Merge / Upsert
from delta.tables import DeltaTable

target = DeltaTable.forName(spark, "silver.dim_customers")
target.alias("t").merge(
    df_new.alias("s"),
    "t.customer_id = s.customer_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

# Optimize (compact small files)
spark.sql("OPTIMIZE silver.cleaned_sales")

# Vacuum (remove old versions)
spark.sql("VACUUM silver.cleaned_sales RETAIN 168 HOURS")
```

---

## Environment Management

### Environment Item Definition
```yaml
# environment.yml (conda format)
dependencies:
  - pip:
    - azure-eventhub==5.11.0
    - requests==2.31.0
```

```yaml
# Setting/Sparkcompute.yml
instancePool: ""
driverCores: 4
driverMemory: 28g
executorCores: 4
executorMemory: 28g
dynamicExecutorAllocation:
  enabled: true
  minExecutors: 1
  maxExecutors: 4
```

### Attach Environment to Notebook
Set the environment in the notebook's metadata or workspace settings.

---

## CI/CD Pipeline Structure

```
deploy.py
├── Create/verify Lakehouse
├── Upload CSVs to OneLake Files/raw/
├── Create notebooks (NB01_Bronze, NB02_Silver, NB03_Gold)
├── Run NB01_Bronze
├── Wait for completion
├── Run NB02_Silver
├── Wait for completion
├── Run NB03_Gold
└── Wait for completion
```

### Infrastructure-as-Code Pattern
```python
# 1. Create Lakehouse (idempotent — check if exists first)
existing = [i for i in list_items(ws_id, "Lakehouse", h) if i["displayName"] == "LH_MyProject"]
if existing:
    lh_id = existing[0]["id"]
else:
    lh_id = create_item(ws_id, "LH_MyProject", "Lakehouse", h)

# 2. Upload data to OneLake Files/
upload_to_onelake(ws_id, lh_id, "raw/sales.csv", local_path)

# 3. Create/update notebooks
create_or_update_notebook(ws_id, "NB01_BronzeLoad", notebook_content, h)

# 4. Run notebooks in sequence
for nb_name in ["NB01_BronzeLoad", "NB02_SilverTransform", "NB03_GoldAggregate"]:
    nb_id = get_item_id(ws_id, nb_name, "Notebook", h)
    run_and_wait(ws_id, nb_id, h)
```

---

## Gotchas

1. **`enableSchemas` cannot be changed after Lakehouse creation** — Plan schema strategy upfront
2. **Notebook `format: "ipynb"`** → `InvalidNotebookContent` — Omit format field entirely
3. **Notebook jobType is `RunNotebook`** — NOT `SparkJob`
4. **Starter Pool has limited resources** — May OOM on large datasets; use Workspace Pool
5. **Default Lakehouse binding required** — Notebook can't resolve `Files/` without it
6. **`getDefinition` on notebooks is always async** — Always poll the operation
7. **F2/F4 capacity cold start** — First notebook run can take 3-5 minutes (Spark pool warm-up)
8. **Delta table names are lowercase** — `saveAsTable("MyTable")` creates `mytable`
9. **`overwrite` mode drops and recreates** — Downstream views/semantic models may break
10. **Concurrent notebook runs share capacity** — Running 5 notebooks in parallel on F16 may OOM
11. **Libraries must be pre-installed** — Use Environment item or `%pip install` (adds startup time)
12. **Spark session isolation** — Each notebook run gets its own SparkSession; no shared state
13. **Files path is case-sensitive** — `Files/Raw/` ≠ `Files/raw/`
14. **VACUUM default retention is 7 days** — Cannot vacuum files newer than `RETAIN` hours

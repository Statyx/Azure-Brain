# Spark Notebooks — Complete Reference

## Overview

Fabric Notebooks run Apache Spark (PySpark) for data transformation.  
Primary use: read raw files from OneLake Files → transform → write Delta tables.

---

## Notebook REST API

### Run Notebook via API
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/items/{notebook_id}/jobs/instances?jobType=SparkJob",
    headers=headers,
    json={"executionData": {}}
)
# Always 202 → poll x-ms-operation-id
```

### Run Notebook with Parameters
```python
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/items/{notebook_id}/jobs/instances?jobType=SparkJob",
    headers=headers,
    json={
        "executionData": {
            "parameters": {
                "input_folder": {"value": "raw/sales", "type": "string"},
                "target_table": {"value": "fact_sales", "type": "string"}
            }
        }
    }
)
```

### CRUD Operations
```python
# List notebooks
resp = requests.get(f"{API}/workspaces/{WS_ID}/items?type=Notebook", headers=headers)

# Get notebook definition (async)
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/items/{notebook_id}/getDefinition",
    headers=headers
)

# Create notebook
resp = requests.post(
    f"{API}/workspaces/{WS_ID}/items",
    headers=headers,
    json={
        "displayName": "NB_My_Transform",
        "type": "Notebook",
        "definition": {
            "format": "ipynb",
            "parts": [
                {
                    "path": "notebook-content.py",
                    "payload": payload_base64,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
)
```

---

## Notebook Content Patterns

### Pattern 1: CSV → Delta Table (Standard ETL)

This is the most common notebook pattern in this project.

```python
# Cell 1: Configuration
lakehouse_path = "abfss://<workspace_id>@onelake.dfs.fabric.microsoft.com/<lakehouse_id>"
raw_path = f"{lakehouse_path}/Files/raw"
tables_path = f"{lakehouse_path}/Tables"

# Cell 2: Read CSVs
df_customers = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load(f"{raw_path}/customers/*.csv")

# Cell 3: Transform
from pyspark.sql.functions import col, to_date, trim, upper

df_clean = df_customers \
    .withColumn("customer_name", trim(upper(col("customer_name")))) \
    .withColumn("created_date", to_date(col("created_date"), "yyyy-MM-dd")) \
    .dropDuplicates(["customer_id"])

# Cell 4: Write Delta
df_clean.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(f"{tables_path}/dim_customers")

print(f"Written {df_clean.count()} rows to dim_customers")
```

### Pattern 2: Multi-Table Batch Load

```python
# Cell 1: Table configuration
tables = [
    {"name": "dim_customers",        "folder": "customers",     "key": "customer_id"},
    {"name": "dim_products",         "folder": "products",      "key": "product_id"},
    {"name": "dim_chart_of_accounts","folder": "chart_accounts","key": "account_id"},
    {"name": "fact_general_ledger",  "folder": "general_ledger","key": "entry_id"},
    {"name": "fact_sales",           "folder": "sales",         "key": "transaction_id"},
]

# Cell 2: Load all tables
for t in tables:
    df = spark.read.format("csv") \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .load(f"{raw_path}/{t['folder']}/*.csv")
    
    df = df.dropDuplicates([t["key"]])
    
    df.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(f"{tables_path}/{t['name']}")
    
    print(f"✓ {t['name']}: {df.count()} rows")
```

### Pattern 3: Incremental Load (Merge/Upsert)

```python
from delta.tables import DeltaTable

# Read new data
df_new = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load(f"{raw_path}/incremental/sales/*.csv")

# Merge into existing Delta table
target = DeltaTable.forPath(spark, f"{tables_path}/fact_sales")

target.alias("t").merge(
    df_new.alias("s"),
    "t.transaction_id = s.transaction_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

print(f"Merged {df_new.count()} records into fact_sales")
```

### Pattern 4: Data Quality Checks

```python
from pyspark.sql.functions import count, when, isnan, isnull

def quality_check(df, table_name: str):
    """Run data quality checks and print report."""
    total = df.count()
    print(f"\n=== Quality Report: {table_name} ({total} rows) ===")
    
    for col_name in df.columns:
        nulls = df.filter(isnull(col_name) | (col(col_name) == "")).count()
        if nulls > 0:
            pct = (nulls / total) * 100
            print(f"  ⚠ {col_name}: {nulls} nulls ({pct:.1f}%)")
    
    dupes = total - df.dropDuplicates().count()
    if dupes > 0:
        print(f"  ⚠ {dupes} duplicate rows")
    
    return total > 0  # passes if non-empty
```

---

## Spark Configuration Tips

### Memory & Performance
```python
# Set shuffle partitions (default 200 is too many for small data)
spark.conf.set("spark.sql.shuffle.partitions", "8")

# Enable adaptive query execution
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Delta optimization
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")
```

### Fabric-Specific Paths
```python
# OneLake path format (replace with your IDs from resource_ids.md)
# abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}

# Shorthand in Fabric notebooks (auto-mounted):
# Files/raw/...     → raw file storage
# Tables/...        → managed Delta tables

# These shortcuts work inside Fabric notebooks:
df = spark.read.csv("Files/raw/customers/*.csv", header=True, inferSchema=True)
df.write.format("delta").mode("overwrite").saveAsTable("dim_customers")
```

---

## Existing Notebook Reference

**NB_Load_CSV_to_Delta** (`86729c39-33a4-454a-8170-0ac363ee809c`)
- Reads CSVs from `Files/raw/` subfolders
- Writes Delta tables to `Tables/`
- 11 tables: dim_* and fact_*
- Called by pipeline `PL_Load_Finance_Data`
- Execution time on F16: ~2 min after Spark starts

---

## Cold Start Warning

On F16 capacity, first notebook run after idle triggers Spark cluster allocation:
- `NotStarted` status for ~2 minutes
- `InProgress` for ~2 minutes  
- Total wall-clock: **~4 minutes**

Subsequent runs while warm: **~1-2 minutes**

# Spark Notebooks — Fabric PySpark Patterns & Notebook Format

## Fabric Notebook Format

Fabric notebooks use a proprietary `.py` format — **not** `.ipynb`. Every notebook deployed via API must follow this format exactly.

### Structure
```python
# Fabric notebook source


# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "<lakehouse-guid>",
# META       "default_lakehouse_name": "<lakehouse-name>",
# META       "default_lakehouse_workspace_id": "<workspace-guid>"
# META     }
# META   }
# META }

# CELL ********************

# Your PySpark code here
df = spark.read.format("csv").option("header", True).load("Files/raw/data.csv")
df.write.format("delta").mode("overwrite").save("Tables/my_table")

# CELL ********************

# Another cell
display(df.limit(10))

# MARKDOWN ********************

# # This is a markdown cell
# With documentation
```

### Format Rules
1. First line: `# Fabric notebook source` (exactly, with 2 blank lines after)
2. Metadata block: Every line prefixed with `# META ` — contains lakehouse binding
3. Code cells: Separator `# CELL ********************`
4. Markdown cells: Separator `# MARKDOWN ********************` — every content line prefixed with `# `
5. No `"format": "ipynb"` in the definition JSON

### Notebook Definition Payload
```python
import base64

notebook_content = read_notebook_py_file()  # The .py file content as string
payload_part = base64.b64encode(notebook_content.encode("utf-8")).decode("utf-8")

definition = {
    "definition": {
        "parts": [
            {
                "path": "notebook-content.py",
                "payload": payload_part,
                "payloadType": "InlineBase64"
            }
        ]
    }
}
```

---

## CSV → Delta Table Pattern

The most common operation: upload CSVs to `Files/raw/`, then convert to Delta tables.

### Single Table
```python
# Read CSV from Files/
df = spark.read.format("csv") \
    .option("header", True) \
    .option("inferSchema", True) \
    .option("encoding", "UTF-8") \
    .load("Files/raw/customers.csv")

# Write as Delta table
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", True) \
    .save("Tables/dim_customers")

print(f"Created dim_customers: {df.count()} rows, {len(df.columns)} columns")
```

### Multi-Table Batch Load
```python
import os

tables_config = {
    "dim_customers": "Files/raw/customers.csv",
    "dim_products": "Files/raw/products.csv",
    "dim_stores": "Files/raw/stores.csv",
    "fact_sales": "Files/raw/sales.csv",
    "fact_inventory": "Files/raw/inventory.csv"
}

for table_name, csv_path in tables_config.items():
    df = spark.read.format("csv") \
        .option("header", True) \
        .option("inferSchema", True) \
        .load(csv_path)
    
    df.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", True) \
        .save(f"Tables/{table_name}")
    
    print(f"✅ {table_name}: {df.count()} rows")
```

### With Explicit Schema (Recommended for Production)
```python
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType

sales_schema = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("product_id", StringType(), False),
    StructField("sale_date", DateType(), False),
    StructField("quantity", IntegerType(), False),
    StructField("amount", DoubleType(), False),
    StructField("store_id", StringType(), True)
])

df = spark.read.format("csv") \
    .option("header", True) \
    .schema(sales_schema) \
    .load("Files/raw/sales.csv")
```

---

## Parquet → Delta Table

```python
# Parquet files preserve schema — simpler than CSV
df = spark.read.format("parquet").load("Files/raw/events/")
df.write.format("delta").mode("overwrite").save("Tables/fact_events")
```

---

## JSON → Delta Table

```python
# Single-line JSON (each line is a JSON object)
df = spark.read.format("json").load("Files/raw/api_responses/")

# Multi-line JSON (entire file is one JSON array)
df = spark.read.format("json") \
    .option("multiLine", True) \
    .load("Files/raw/config.json")

# Nested JSON — flatten before writing
from pyspark.sql.functions import col, explode
df_flat = df.select(
    col("id"),
    col("name"),
    explode(col("items")).alias("item")
).select(
    col("id"),
    col("name"),
    col("item.sku").alias("item_sku"),
    col("item.quantity").alias("item_quantity")
)

df_flat.write.format("delta").mode("overwrite").save("Tables/fact_orders")
```

---

## Incremental Load (Merge / Upsert)

### Delta Merge Pattern
```python
from delta.tables import DeltaTable

# Read new data
df_new = spark.read.format("csv") \
    .option("header", True) \
    .option("inferSchema", True) \
    .load("Files/raw/incremental/customers_update.csv")

# Get existing table
target = DeltaTable.forPath(spark, "Tables/dim_customers")

# Merge: update if exists, insert if new
target.alias("t").merge(
    df_new.alias("s"),
    "t.customer_id = s.customer_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

print(f"Merged {df_new.count()} records into dim_customers")
```

### SCD Type 2 (Slowly Changing Dimension)
```python
from pyspark.sql.functions import current_timestamp, lit

df_new = spark.read.format("csv").option("header", True).load("Files/raw/customers_update.csv")

target = DeltaTable.forPath(spark, "Tables/dim_customers_scd2")

# Mark old records as expired
target.alias("t").merge(
    df_new.alias("s"),
    "t.customer_id = s.customer_id AND t.is_current = true"
).whenMatchedUpdate(set={
    "is_current": lit(False),
    "end_date": current_timestamp()
}).execute()

# Insert new versions
df_insert = df_new.withColumn("is_current", lit(True)) \
    .withColumn("start_date", current_timestamp()) \
    .withColumn("end_date", lit(None).cast("timestamp"))

df_insert.write.format("delta").mode("append").save("Tables/dim_customers_scd2")
```

---

## Data Quality Checks

### Row Count Validation
```python
def validate_load(table_name: str, min_rows: int = 1):
    """Validate that a table has been loaded with expected minimum rows."""
    count = spark.read.format("delta").load(f"Tables/{table_name}").count()
    assert count >= min_rows, f"❌ {table_name}: expected >= {min_rows} rows, got {count}"
    print(f"✅ {table_name}: {count} rows")
    return count

validate_load("dim_customers", min_rows=100)
validate_load("fact_sales", min_rows=1000)
```

### Null Check
```python
from pyspark.sql.functions import col, sum as spark_sum

def check_nulls(table_name: str, key_columns: list):
    """Check for nulls in key columns."""
    df = spark.read.format("delta").load(f"Tables/{table_name}")
    for c in key_columns:
        null_count = df.filter(col(c).isNull()).count()
        if null_count > 0:
            print(f"⚠️ {table_name}.{c}: {null_count} null values")
        else:
            print(f"✅ {table_name}.{c}: no nulls")

check_nulls("fact_sales", ["transaction_id", "customer_id", "amount"])
```

### Duplicate Check
```python
def check_duplicates(table_name: str, key_columns: list):
    """Check for duplicate rows based on key columns."""
    df = spark.read.format("delta").load(f"Tables/{table_name}")
    total = df.count()
    distinct = df.dropDuplicates(key_columns).count()
    dupes = total - distinct
    if dupes > 0:
        print(f"⚠️ {table_name}: {dupes} duplicate rows on {key_columns}")
    else:
        print(f"✅ {table_name}: no duplicates on {key_columns}")
    return dupes

check_duplicates("fact_sales", ["transaction_id"])
```

---

## Running Notebooks via API

### Deploy Notebook
```python
import requests, base64

def deploy_notebook(ws_id: str, notebook_name: str, py_content: str, token: str):
    """Deploy a .py notebook to Fabric workspace."""
    API = "https://api.fabric.microsoft.com/v1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = base64.b64encode(py_content.encode("utf-8")).decode("utf-8")
    
    # Create item
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/items",
        headers=headers,
        json={"displayName": notebook_name, "type": "Notebook"}
    )
    notebook_id = resp.json()["id"]
    
    # Push definition
    requests.post(
        f"{API}/workspaces/{ws_id}/items/{notebook_id}/updateDefinition",
        headers=headers,
        json={
            "definition": {
                "parts": [{
                    "path": "notebook-content.py",
                    "payload": payload,
                    "payloadType": "InlineBase64"
                }]
            }
        }
    )
    return notebook_id
```

### Run Notebook
```python
def run_notebook(ws_id: str, notebook_id: str, token: str):
    """Execute a notebook and wait for completion."""
    API = "https://api.fabric.microsoft.com/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Trigger execution
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/items/{notebook_id}/jobs/instances?jobType=RunNotebook",
        headers=headers
    )
    location = resp.headers.get("Location")
    
    # Poll for completion
    import time
    for _ in range(60):
        status_resp = requests.get(location, headers=headers)
        status = status_resp.json().get("status")
        if status in ("Completed", "Failed", "Cancelled"):
            return status_resp.json()
        time.sleep(10)
    
    raise TimeoutError("Notebook execution timed out")
```

---

## Spark SQL in Notebooks

```python
# Register temp view for SQL queries
df.createOrReplaceTempView("sales_view")

# Run Spark SQL
result = spark.sql("""
    SELECT 
        s.store_id,
        COUNT(*) as transaction_count,
        SUM(s.amount) as total_revenue,
        AVG(s.amount) as avg_transaction
    FROM sales_view s
    GROUP BY s.store_id
    ORDER BY total_revenue DESC
""")

display(result)
```

---

## Tips

1. **`inferSchema` is slow on large files** — Use explicit schema for production loads
2. **`mode("overwrite")` destroys existing data** — Use `merge` for incremental updates
3. **`overwriteSchema` option** — Required when columns change between loads
4. **`display()` function** — Fabric-specific; shows rich table output in notebooks
5. **Default Lakehouse binding** — Set in notebook metadata; allows `Tables/` and `Files/` relative paths
6. **Spark session is pre-configured** — No need to create `SparkSession`; `spark` variable is available
7. **`jobType=RunNotebook`** — Must be exactly this string when triggering via API

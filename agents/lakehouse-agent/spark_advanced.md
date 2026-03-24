# Advanced Spark Patterns for Lakehouse

## SCD Type 2 — Slowly Changing Dimensions

Track historical changes to dimension attributes. Each change creates a new row with validity windows.

### Schema Pattern

```sql
CREATE TABLE dim_customers (
    customer_sk     BIGINT,        -- Surrogate key (auto-increment)
    customer_id     STRING,        -- Business/natural key
    customer_name   STRING,
    region          STRING,
    segment         STRING,
    effective_date  DATE,
    end_date        DATE,          -- NULL = current record
    is_current      BOOLEAN,
    row_hash        STRING         -- Hash of tracked columns for change detection
);
```

### PySpark Implementation

```python
# Fabric notebook source


# CELL ********************
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from datetime import date

def scd_type2_merge(spark, table_path: str, new_data_df, business_key: str, tracked_columns: list):
    """
    Apply SCD Type 2 logic: detect changes, close old records, insert new versions.
    
    Args:
        table_path: Delta table path (e.g., "Tables/dim_customers")
        new_data_df: DataFrame with new/updated records
        business_key: Column name for business key (e.g., "customer_id")
        tracked_columns: Columns to track for changes (e.g., ["region", "segment"])
    """
    today = date.today()
    
    # Generate hash of tracked columns for change detection
    hash_expr = F.md5(F.concat_ws("||", *[F.coalesce(F.col(c).cast("string"), F.lit("NULL")) for c in tracked_columns]))
    
    new_data = new_data_df.withColumn("row_hash", hash_expr)
    
    # Read existing current records
    try:
        existing = spark.read.format("delta").load(table_path).filter(F.col("is_current") == True)
    except Exception:
        # Table doesn't exist yet — initial load
        initial = (new_data
            .withColumn("customer_sk", F.monotonically_increasing_id())
            .withColumn("effective_date", F.lit(today))
            .withColumn("end_date", F.lit(None).cast("date"))
            .withColumn("is_current", F.lit(True))
        )
        initial.write.format("delta").mode("overwrite").save(table_path)
        print(f"✅ Initial load: {initial.count()} records")
        return
    
    # Find changed records (hash mismatch)
    joined = new_data.alias("new").join(
        existing.alias("old"),
        F.col(f"new.{business_key}") == F.col(f"old.{business_key}"),
        "left"
    )
    
    # Changed: existing records where hash differs
    changed = joined.filter(
        F.col("old.row_hash").isNotNull() & 
        (F.col("new.row_hash") != F.col("old.row_hash"))
    ).select("new.*")
    
    # New: records with no existing match
    new_records = joined.filter(F.col(f"old.{business_key}").isNull()).select("new.*")
    
    # Close old versions of changed records
    from delta.tables import DeltaTable
    delta_table = DeltaTable.forPath(spark, table_path)
    
    changed_keys = [row[business_key] for row in changed.select(business_key).collect()]
    
    if changed_keys:
        delta_table.update(
            condition=(F.col(business_key).isin(changed_keys)) & (F.col("is_current") == True),
            set={
                "end_date": F.lit(today),
                "is_current": F.lit(False)
            }
        )
    
    # Insert new versions of changed records + truly new records
    max_sk = spark.read.format("delta").load(table_path).agg(F.max("customer_sk")).collect()[0][0] or 0
    
    to_insert = changed.union(new_records)
    if to_insert.count() > 0:
        window = Window.orderBy(business_key)
        to_insert = (to_insert
            .withColumn("customer_sk", F.row_number().over(window) + F.lit(max_sk))
            .withColumn("effective_date", F.lit(today))
            .withColumn("end_date", F.lit(None).cast("date"))
            .withColumn("is_current", F.lit(True))
        )
        to_insert.write.format("delta").mode("append").save(table_path)
    
    print(f"✅ SCD Type 2: {len(changed_keys)} changed, {new_records.count()} new")


# CELL ********************
# Usage example
new_customers = spark.read.csv("Files/raw/dim_customers_update.csv", header=True)
scd_type2_merge(
    spark, 
    "Tables/dim_customers", 
    new_customers, 
    business_key="customer_id",
    tracked_columns=["customer_name", "region", "segment"]
)
```

---

## Delta Merge / Upsert

Efficiently update existing rows and insert new ones using Delta Lake MERGE.

### Basic Upsert

```python
# CELL ********************
from delta.tables import DeltaTable
from pyspark.sql import functions as F

def delta_upsert(spark, table_path: str, new_data_df, match_columns: list, update_columns: list = None):
    """
    Merge new data into existing Delta table.
    Matching rows are updated; non-matching rows are inserted.
    
    Args:
        table_path: Delta table path
        new_data_df: DataFrame with new/updated records
        match_columns: Columns to match on (composite key)
        update_columns: Columns to update (None = all non-key columns)
    """
    delta_table = DeltaTable.forPath(spark, table_path)
    
    # Build merge condition
    condition = " AND ".join([f"target.{c} = source.{c}" for c in match_columns])
    
    # Determine update columns
    if update_columns is None:
        update_columns = [c for c in new_data_df.columns if c not in match_columns]
    
    update_set = {c: f"source.{c}" for c in update_columns}
    
    (delta_table.alias("target")
        .merge(new_data_df.alias("source"), condition)
        .whenMatchedUpdate(set=update_set)
        .whenNotMatchedInsertAll()
        .execute()
    )
    
    print(f"✅ Upsert complete on {table_path}")


# CELL ********************
# Usage: upsert fact table
new_readings = spark.read.csv("Files/raw/sensor_readings_daily.csv", header=True, inferSchema=True)
delta_upsert(
    spark,
    "Tables/fact_sensor_readings",
    new_readings,
    match_columns=["sensor_id", "timestamp"],
    update_columns=["reading_value", "quality_flag"]
)
```

### Upsert with Delete Detection

```python
# CELL ********************
def delta_full_merge(spark, table_path: str, new_data_df, match_columns: list):
    """
    Full merge: update matches, insert new, soft-delete missing.
    Adds is_deleted flag for records in target but not in source.
    """
    delta_table = DeltaTable.forPath(spark, table_path)
    condition = " AND ".join([f"target.{c} = source.{c}" for c in match_columns])
    
    (delta_table.alias("target")
        .merge(new_data_df.alias("source"), condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .whenNotMatchedBySourceUpdate(set={"is_deleted": F.lit(True)})
        .execute()
    )
```

---

## Deduplication Strategies

### Strategy 1: Drop Exact Duplicates

```python
# CELL ********************
def deduplicate_exact(df, subset_columns=None):
    """Remove exact duplicate rows."""
    before = df.count()
    deduped = df.dropDuplicates(subset_columns)
    after = deduped.count()
    print(f"✅ Dedup: {before} → {after} ({before - after} duplicates removed)")
    return deduped
```

### Strategy 2: Keep Latest by Timestamp (Rank and Filter)

```python
# CELL ********************
from pyspark.sql.window import Window

def deduplicate_keep_latest(df, partition_columns: list, order_column: str):
    """Keep only the latest record per partition key."""
    window = Window.partitionBy(*partition_columns).orderBy(F.col(order_column).desc())
    
    deduped = (df
        .withColumn("_rank", F.row_number().over(window))
        .filter(F.col("_rank") == 1)
        .drop("_rank")
    )
    
    before = df.count()
    after = deduped.count()
    print(f"✅ Dedup (latest): {before} → {after}")
    return deduped


# CELL ********************
# Usage: keep latest sensor reading per sensor per day
readings = spark.read.format("delta").load("Tables/fact_sensor_readings")
clean = deduplicate_keep_latest(
    readings, 
    partition_columns=["sensor_id", "date_key"],
    order_column="timestamp"
)
clean.write.format("delta").mode("overwrite").save("Tables/fact_sensor_readings")
```

### Strategy 3: Dedup on Ingest (Streaming)

```python
# CELL ********************
def deduplicate_streaming(df, id_column: str, watermark_column: str, watermark_delay: str = "10 minutes"):
    """Dedup streaming data using watermark-based state cleanup."""
    return (df
        .withWatermark(watermark_column, watermark_delay)
        .dropDuplicatesWithinWatermark([id_column])
    )
```

---

## Incremental Load Patterns

### Pattern 1: Watermark-Based Incremental

```python
# CELL ********************
def incremental_load_by_watermark(spark, source_path: str, target_table: str, 
                                   watermark_column: str):
    """Load only new records based on max timestamp in target."""
    
    # Get current watermark from target
    try:
        target = spark.read.format("delta").load(f"Tables/{target_table}")
        max_watermark = target.agg(F.max(watermark_column)).collect()[0][0]
        print(f"  Current watermark: {max_watermark}")
    except Exception:
        max_watermark = None
        print("  No existing data — full load")
    
    # Read source with filter
    source = spark.read.csv(source_path, header=True, inferSchema=True)
    
    if max_watermark:
        new_data = source.filter(F.col(watermark_column) > F.lit(max_watermark))
    else:
        new_data = source
    
    new_count = new_data.count()
    print(f"  New records: {new_count}")
    
    if new_count > 0:
        new_data.write.format("delta").mode("append").save(f"Tables/{target_table}")
        print(f"✅ Appended {new_count} records to {target_table}")
    else:
        print(f"ℹ️  No new records for {target_table}")
```

### Pattern 2: Change Data Capture (CDC) from Files

```python
# CELL ********************
def process_cdc_files(spark, cdc_path: str, target_table: str, key_columns: list):
    """
    Process CDC files with operation column (_op: I=insert, U=update, D=delete).
    """
    cdc_df = spark.read.parquet(cdc_path)
    
    inserts = cdc_df.filter(F.col("_op") == "I").drop("_op")
    updates = cdc_df.filter(F.col("_op") == "U").drop("_op")
    deletes = cdc_df.filter(F.col("_op") == "D")
    
    delta_table = DeltaTable.forPath(spark, f"Tables/{target_table}")
    condition = " AND ".join([f"target.{c} = source.{c}" for c in key_columns])
    
    # Apply inserts
    if inserts.count() > 0:
        inserts.write.format("delta").mode("append").save(f"Tables/{target_table}")
    
    # Apply updates
    if updates.count() > 0:
        (delta_table.alias("target")
            .merge(updates.alias("source"), condition)
            .whenMatchedUpdateAll()
            .execute())
    
    # Apply deletes (soft delete)
    if deletes.count() > 0:
        delete_keys = deletes.select(*key_columns)
        (delta_table.alias("target")
            .merge(delete_keys.alias("source"), condition)
            .whenMatchedUpdate(set={"is_deleted": F.lit(True)})
            .execute())
    
    print(f"✅ CDC: {inserts.count()} inserts, {updates.count()} updates, {deletes.count()} deletes")
```

---

## Medallion Architecture Patterns

### Bronze → Silver → Gold Pipeline

```python
# CELL ********************
# Bronze: raw ingestion (schema-on-read, preserve source format)
def load_bronze(spark, source_files: dict):
    """Load raw files into Bronze layer with metadata."""
    for table_name, file_path in source_files.items():
        df = (spark.read
            .option("header", "true")
            .option("inferSchema", "true")
            .csv(f"Files/raw/{file_path}")
            .withColumn("_ingestion_timestamp", F.current_timestamp())
            .withColumn("_source_file", F.lit(file_path))
        )
        df.write.format("delta").mode("overwrite").save(f"Tables/bronze_{table_name}")
        print(f"  Bronze: {table_name} → {df.count()} rows")


# CELL ********************
# Silver: cleansed, deduplicated, type-cast, validated
def transform_silver(spark, table_name: str, transformations: dict):
    """Apply cleaning transformations from Bronze to Silver."""
    df = spark.read.format("delta").load(f"Tables/bronze_{table_name}")
    
    # Apply type casts
    for col_name, target_type in transformations.get("type_casts", {}).items():
        df = df.withColumn(col_name, F.col(col_name).cast(target_type))
    
    # Apply renames
    for old_name, new_name in transformations.get("renames", {}).items():
        df = df.withColumnRenamed(old_name, new_name)
    
    # Drop nulls on key columns
    key_cols = transformations.get("not_null", [])
    if key_cols:
        df = df.dropna(subset=key_cols)
    
    # Deduplicate
    dedup_cols = transformations.get("dedup_on", [])
    if dedup_cols:
        df = df.dropDuplicates(dedup_cols)
    
    df.write.format("delta").mode("overwrite").save(f"Tables/silver_{table_name}")
    print(f"  Silver: {table_name} → {df.count()} rows")


# CELL ********************
# Gold: business-ready aggregates and star schema
def build_gold_fact(spark, fact_name: str, source_table: str, group_by: list, aggregations: dict):
    """Build Gold fact table with aggregations."""
    df = spark.read.format("delta").load(f"Tables/silver_{source_table}")
    
    agg_exprs = []
    for col_name, agg_func in aggregations.items():
        if agg_func == "sum":
            agg_exprs.append(F.sum(col_name).alias(f"total_{col_name}"))
        elif agg_func == "avg":
            agg_exprs.append(F.avg(col_name).alias(f"avg_{col_name}"))
        elif agg_func == "count":
            agg_exprs.append(F.count(col_name).alias(f"count_{col_name}"))
        elif agg_func == "min":
            agg_exprs.append(F.min(col_name).alias(f"min_{col_name}"))
        elif agg_func == "max":
            agg_exprs.append(F.max(col_name).alias(f"max_{col_name}"))
    
    gold = df.groupBy(*group_by).agg(*agg_exprs)
    gold.write.format("delta").mode("overwrite").save(f"Tables/{fact_name}")
    print(f"  Gold: {fact_name} → {gold.count()} rows")
```

---

## Performance Optimization Tips

### 1. Partition Large Tables

```python
# Partition by date for time-series data
df.write.format("delta").partitionBy("year", "month").mode("overwrite").save("Tables/fact_large")
```

> **Warning**: Only partition tables with >1M rows. Over-partitioning small tables hurts performance.

### 2. Z-ORDER for Query Patterns

```sql
OPTIMIZE fact_sensor_readings ZORDER BY (sensor_id, date_key);
```

### 3. V-ORDER for Fabric Optimization

```sql
-- V-ORDER is Fabric-specific and improves Direct Lake performance
OPTIMIZE dim_customers VORDER;
```

### 4. Cache Frequently Used DataFrames

```python
# Cache dimension tables used in multiple joins
dim_sites = spark.read.format("delta").load("Tables/dim_sites").cache()
```

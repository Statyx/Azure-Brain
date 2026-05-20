# Delta Lake Optimization — Performance, Schema Evolution & Maintenance

## Delta Lake in Fabric

Fabric Lakehouses use Delta Lake as the default table format. Delta provides ACID transactions, time travel, schema evolution, and optimized reads. Understanding Delta operations is critical for performant analytics.

---

## OPTIMIZE — File Compaction

Small files (from streaming ingestion or many appends) degrade query performance. `OPTIMIZE` compacts them.

### Basic OPTIMIZE
```python
# Compact all files in a table
spark.sql("OPTIMIZE fact_sales")
```

### OPTIMIZE with Z-ORDER
Z-ordering co-locates related data for faster filtered queries.
```python
# Z-order by frequently filtered columns
spark.sql("OPTIMIZE fact_sales ZORDER BY (customer_id, sale_date)")
```

### When to Z-ORDER
| Column Pattern | Should Z-ORDER? |
|---------------|-----------------|
| Frequently in WHERE clause | ✅ Yes |
| Used in JOIN conditions | ✅ Yes |
| High cardinality (IDs) | ✅ Yes (1-2 columns) |
| Low cardinality (gender, status) | ❌ No (partition instead) |
| Rarely queried | ❌ No |

> **Limit**: Z-ORDER on 1-3 columns max. More columns reduce effectiveness.

---

## V-ORDER — Fabric-Specific Optimization

V-ORDER is a Fabric-specific write-time optimization that arranges data within Parquet files for faster reads in the Fabric engine. It's **enabled by default** in Fabric.

```python
# Explicitly enable V-ORDER (default in Fabric but useful for portable code)
df.write.format("delta") \
    .option("vorder", True) \
    .mode("overwrite") \
    .save("Tables/fact_sales")
```

### V-ORDER vs Z-ORDER
| Feature | V-ORDER | Z-ORDER |
|---------|---------|---------|
| Scope | Within each Parquet file | Across files |
| Purpose | Faster read/decompression | Data skipping |
| When applied | Write time | OPTIMIZE time |
| Cost | Slight write overhead | Heavy computation |
| Use together? | ✅ Yes — complementary | ✅ Yes |

---

## VACUUM — Cleanup Old Files

Delta maintains old file versions for time travel. `VACUUM` removes files older than the retention period.

```python
# Remove files older than 7 days (default)
spark.sql("VACUUM fact_sales")

# Remove files older than 24 hours (minimum)
spark.sql("VACUUM fact_sales RETAIN 24 HOURS")
```

> **Warning**: After VACUUM, time travel queries to versions older than the retention period will fail.

### Maintenance Schedule
```python
def maintain_table(table_name: str, zorder_cols: list = None):
    """Run standard maintenance on a Delta table."""
    
    # 1. Optimize (compact small files)
    if zorder_cols:
        spark.sql(f"OPTIMIZE {table_name} ZORDER BY ({', '.join(zorder_cols)})")
    else:
        spark.sql(f"OPTIMIZE {table_name}")
    
    # 2. Vacuum (cleanup old versions)
    spark.sql(f"VACUUM {table_name} RETAIN 168 HOURS")  # 7 days
    
    # 3. Analyze (update statistics)
    spark.sql(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS")
    
    print(f"✅ Maintained {table_name}")

# Run maintenance
maintain_table("fact_sales", zorder_cols=["sale_date", "store_id"])
maintain_table("dim_customers")
```

---

## Schema Evolution

### Add Columns (Merge Schema)
```python
# New data has extra columns
df_new = spark.read.format("csv").option("header", True).load("Files/raw/sales_v2.csv")

# mergeSchema allows adding new columns
df_new.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", True) \
    .save("Tables/fact_sales")
```

### Overwrite Schema
```python
# Completely replace the schema (dangerous — use with caution)
df_new.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", True) \
    .save("Tables/fact_sales")
```

### ALTER TABLE
```python
# Add column via SQL
spark.sql("ALTER TABLE fact_sales ADD COLUMNS (discount DOUBLE)")

# Rename column
spark.sql("ALTER TABLE fact_sales RENAME COLUMN old_name TO new_name")

# Change column type (limited — only widening allowed)
spark.sql("ALTER TABLE fact_sales ALTER COLUMN quantity TYPE BIGINT")
```

---

## Partitioning

### Create Partitioned Table
```python
df.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("year", "month") \
    .save("Tables/fact_sales_partitioned")
```

### When to Partition

| Scenario | Partition? | Columns |
|----------|-----------|---------|
| Table > 1TB | ✅ Yes | Date-based (year, month) |
| Table < 1GB | ❌ No | Z-ORDER instead |
| Queries always filter by date | ✅ Yes | year, month |
| Queries filter by many columns | ❌ No | Z-ORDER those columns |
| Streaming append table | ✅ Maybe | Date-based if queried by date |

> **Rule of thumb**: Each partition should contain at least 1GB of data. Over-partitioning (too many small partitions) hurts performance.

---

## Time Travel

### Query Historical Versions
```python
# Read a specific version
df_v3 = spark.read.format("delta").option("versionAsOf", 3).load("Tables/fact_sales")

# Read as of a timestamp
df_past = spark.read.format("delta") \
    .option("timestampAsOf", "2024-01-15 10:00:00") \
    .load("Tables/fact_sales")
```

### View Table History
```python
from delta.tables import DeltaTable

dt = DeltaTable.forPath(spark, "Tables/fact_sales")
display(dt.history())  # Shows all versions with timestamps and operations
```

### Restore to Previous Version
```python
spark.sql("RESTORE TABLE fact_sales TO VERSION AS OF 5")
```

---

## Table Properties

### Set Table Properties
```python
spark.sql("""
    ALTER TABLE fact_sales SET TBLPROPERTIES (
        'delta.autoOptimize.optimizeWrite' = 'true',
        'delta.autoOptimize.autoCompact' = 'true',
        'delta.logRetentionDuration' = 'interval 30 days',
        'delta.deletedFileRetentionDuration' = 'interval 7 days'
    )
""")
```

### Recommended Properties for Fabric Tables

| Property | Value | Purpose |
|----------|-------|---------|
| `delta.autoOptimize.optimizeWrite` | `true` | Auto-compact on write |
| `delta.autoOptimize.autoCompact` | `true` | Auto-compact small files |
| `delta.logRetentionDuration` | `interval 30 days` | Keep 30 days of history |
| `delta.deletedFileRetentionDuration` | `interval 7 days` | Keep deleted files 7 days |

---

## Table Cloning

### Shallow Clone (Metadata Only — Fast)
```python
spark.sql("CREATE TABLE fact_sales_test SHALLOW CLONE fact_sales")
```
Use for: testing, experimentation — no data copy.

### Deep Clone (Full Data Copy)
```python
spark.sql("CREATE TABLE fact_sales_backup DEEP CLONE fact_sales")
```
Use for: backups, cross-environment copies.

---

## Performance Patterns

### Read Performance
```python
# Use predicate pushdown — filter early
df = spark.read.format("delta").load("Tables/fact_sales") \
    .filter(col("sale_date") >= "2024-01-01") \
    .filter(col("store_id") == "S001") \
    .select("transaction_id", "amount", "quantity")  # Select only needed columns
```

### Write Performance
```python
# Coalesce before writing to control file count
df.coalesce(10).write.format("delta").mode("overwrite").save("Tables/summary_table")

# Repartition for better parallelism on large writes
df.repartition(50, "store_id").write.format("delta") \
    .mode("overwrite") \
    .partitionBy("store_id") \
    .save("Tables/fact_sales_by_store")
```

### Caching for Repeated Access
```python
# Cache frequently accessed dimension tables
df_products = spark.read.format("delta").load("Tables/dim_products").cache()

# Use in multiple joins
df_sales_enriched = df_sales.join(df_products, "product_id", "left")
df_inventory_enriched = df_inventory.join(df_products, "product_id", "left")
```

---

## Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Many small writes (row by row) | Thousands of tiny files | Batch writes, then OPTIMIZE |
| No VACUUM ever | Storage bloat from old versions | Schedule weekly VACUUM |
| Partitioning by high-cardinality column | Millions of tiny partitions | Remove partition, use Z-ORDER |
| Reading all columns via `SELECT *` | Slow queries, excess I/O | Select only needed columns |
| `inferSchema` on very large CSV | Slow first read | Define explicit schema |
| Overwriting table daily for append data | Destroys history, slow | Use `mode("append")` or merge |

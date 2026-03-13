# Template: CSV to Delta Table Notebook
# Usage: Deploy via Fabric REST API or paste into Fabric Notebook editor
#
# This notebook reads CSV files from OneLake Files/raw/{folder}
# and writes them as Delta tables to Tables/{table_name}

# ── Cell 1: Parameters (tagged as parameter cell) ─────────────
input_folder = "raw"  # Override via pipeline parameter
# ───────────────────────────────────────────────────────────────

# ── Cell 2: Configuration ─────────────────────────────────────
import os
from pyspark.sql.functions import col, trim, to_date, current_timestamp

# Spark tuning for small-to-medium datasets
spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")

raw_path = f"Files/{input_folder}"
tables_path = "Tables"
# ───────────────────────────────────────────────────────────────

# ── Cell 3: Discover and Load ─────────────────────────────────
# Auto-discover subfolders in raw → each subfolder = one table
import subprocess

folders = [
    d for d in os.listdir(f"/lakehouse/default/{raw_path}")
    if os.path.isdir(f"/lakehouse/default/{raw_path}/{d}")
]

print(f"Found {len(folders)} folders to process: {folders}")

results = []
for folder in sorted(folders):
    csv_path = f"{raw_path}/{folder}"
    table_name = folder  # subfolder name = table name
    
    try:
        df = spark.read.format("csv") \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .load(csv_path)
        
        row_count = df.count()
        col_count = len(df.columns)
        
        # Write as Delta table
        df.write.format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(table_name)
        
        results.append({"table": table_name, "rows": row_count, "cols": col_count, "status": "OK"})
        print(f"  ✓ {table_name}: {row_count} rows, {col_count} columns")
        
    except Exception as e:
        results.append({"table": table_name, "rows": 0, "cols": 0, "status": str(e)})
        print(f"  ✗ {table_name}: {e}")

# ───────────────────────────────────────────────────────────────

# ── Cell 4: Summary ───────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Processed {len(results)} tables")
ok = [r for r in results if r['status'] == 'OK']
failed = [r for r in results if r['status'] != 'OK']
print(f"  Succeeded: {len(ok)}")
print(f"  Failed:    {len(failed)}")
total_rows = sum(r['rows'] for r in ok)
print(f"  Total rows: {total_rows:,}")

if failed:
    print("\nFailed tables:")
    for r in failed:
        print(f"  ✗ {r['table']}: {r['status']}")
# ───────────────────────────────────────────────────────────────

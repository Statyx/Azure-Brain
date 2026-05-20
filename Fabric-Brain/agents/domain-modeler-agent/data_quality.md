# Data Quality Validation Framework

## Purpose

Ensure data integrity at every layer of the Fabric stack: Source → Lakehouse → Semantic Model → Report.
Use these patterns after every data load, model deployment, or pipeline run.

---

## Validation Layers

```
Layer 1: Source Validation (CSV/API → Files/)
Layer 2: Transformation Validation (Files/ → Tables/)
Layer 3: Model Validation (Tables/ → Semantic Model)
Layer 4: Report Validation (Semantic Model → Visuals)
Layer 5: Freshness Monitoring (ongoing)
```

---

## Layer 1: Source Validation

### CSV File Checks (Before Upload)

```python
import pandas as pd
import os

def validate_csv_source(file_path: str, expected_columns: list, min_rows: int = 1) -> dict:
    """Validate a CSV file before uploading to OneLake."""
    results = {"file": file_path, "passed": True, "issues": []}
    
    if not os.path.exists(file_path):
        results["passed"] = False
        results["issues"].append(f"File not found: {file_path}")
        return results
    
    df = pd.read_csv(file_path)
    
    # Row count check
    if len(df) < min_rows:
        results["passed"] = False
        results["issues"].append(f"Too few rows: {len(df)} (expected >= {min_rows})")
    
    # Column presence check
    missing = set(expected_columns) - set(df.columns)
    if missing:
        results["passed"] = False
        results["issues"].append(f"Missing columns: {missing}")
    
    # Null check on key columns
    for col in expected_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = null_count / len(df) * 100
            if null_pct > 5:
                results["issues"].append(f"Column '{col}' has {null_pct:.1f}% nulls")
    
    # Duplicate check on ID columns
    id_cols = [c for c in df.columns if c.endswith("_id")]
    for col in id_cols:
        if col in df.columns:
            dup_count = df[col].duplicated().sum()
            if dup_count > 0 and col in expected_columns:
                results["issues"].append(f"Column '{col}' has {dup_count} duplicates")
    
    results["row_count"] = len(df)
    results["column_count"] = len(df.columns)
    return results
```

### Usage

```python
# Validate all dimension files
dims = {
    "dim_sites": ["site_id", "site_name", "region", "country"],
    "dim_sensors": ["sensor_id", "sensor_type", "site_id", "zone_id"],
    "dim_zones": ["zone_id", "zone_name", "site_id"],
}

for table_name, columns in dims.items():
    result = validate_csv_source(f"data/raw/{table_name}.csv", columns)
    status = "✅" if result["passed"] else "❌"
    print(f"{status} {table_name}: {result['row_count']} rows, {len(result['issues'])} issues")
    for issue in result["issues"]:
        print(f"   ⚠️  {issue}")
```

---

## Layer 2: Transformation Validation (Spark Notebook)

### Row Count Reconciliation

```python
# In Spark notebook — run after CSV → Delta transformation
def validate_transformation(table_name: str, csv_path: str):
    """Compare source CSV row count with Delta table row count."""
    csv_df = spark.read.csv(f"Files/raw/{csv_path}", header=True)
    delta_df = spark.read.format("delta").load(f"Tables/{table_name}")
    
    csv_count = csv_df.count()
    delta_count = delta_df.count()
    
    match = csv_count == delta_count
    status = "✅" if match else "❌"
    print(f"{status} {table_name}: CSV={csv_count}, Delta={delta_count}")
    
    if not match:
        diff = csv_count - delta_count
        print(f"   ⚠️  {abs(diff)} rows {'lost' if diff > 0 else 'gained'} during transformation")
    
    return match

# Run for all tables
tables = [
    ("dim_sites", "dim_sites.csv"),
    ("dim_sensors", "dim_sensors.csv"),
    ("dim_zones", "dim_zones.csv"),
    ("fact_sensor_readings", "sensor_readings.csv"),
]

all_pass = all(validate_transformation(t, c) for t, c in tables)
print(f"\n{'✅ All validations passed' if all_pass else '❌ Some validations FAILED'}")
```

### Schema Validation

```python
def validate_schema(table_name: str, expected_schema: dict):
    """Validate Delta table schema matches expectations.
    expected_schema: {"column_name": "data_type", ...}
    """
    df = spark.read.format("delta").load(f"Tables/{table_name}")
    actual = {f.name: f.dataType.simpleString() for f in df.schema.fields}
    
    issues = []
    for col, dtype in expected_schema.items():
        if col not in actual:
            issues.append(f"Missing column: {col}")
        elif actual[col] != dtype:
            issues.append(f"Type mismatch on '{col}': expected {dtype}, got {actual[col]}")
    
    extra = set(actual.keys()) - set(expected_schema.keys())
    if extra:
        issues.append(f"Unexpected columns: {extra}")
    
    status = "✅" if not issues else "❌"
    print(f"{status} {table_name} schema: {len(issues)} issues")
    for issue in issues:
        print(f"   ⚠️  {issue}")
    
    return len(issues) == 0
```

---

## Layer 3: Model Validation (Semantic Model)

### DAX Measure Validation Queries

```python
def validate_dax_measures(ws_id: str, model_id: str, measures: dict, headers: dict):
    """Validate DAX measures return non-blank, reasonable values.
    measures: {"Measure Name": {"min": 0, "max": 1e12, "not_blank": True}, ...}
    """
    results = []
    
    for measure_name, constraints in measures.items():
        query = f'EVALUATE ROW("Value", [{measure_name}])'
        resp = requests.post(
            f"{API}/workspaces/{ws_id}/semanticModels/{model_id}/executeQueries",
            headers=headers,
            json={"queries": [{"query": query}]}
        )
        
        if resp.status_code != 200:
            results.append({"measure": measure_name, "status": "❌", "error": f"HTTP {resp.status_code}"})
            continue
        
        data = resp.json()
        rows = data.get("results", [{}])[0].get("tables", [{}])[0].get("rows", [])
        
        if not rows:
            if constraints.get("not_blank", True):
                results.append({"measure": measure_name, "status": "❌", "error": "BLANK result"})
            continue
        
        value = rows[0].get("[Value]")
        
        # Constraint checks
        issues = []
        if value is None and constraints.get("not_blank", True):
            issues.append("NULL value")
        if value is not None and "min" in constraints and value < constraints["min"]:
            issues.append(f"Below minimum: {value} < {constraints['min']}")
        if value is not None and "max" in constraints and value > constraints["max"]:
            issues.append(f"Above maximum: {value} > {constraints['max']}")
        
        status = "❌" if issues else "✅"
        results.append({"measure": measure_name, "status": status, "value": value, "issues": issues})
    
    # Summary
    passed = sum(1 for r in results if r["status"] == "✅")
    total = len(results)
    print(f"\nMeasure Validation: {passed}/{total} passed")
    for r in results:
        print(f"  {r['status']} {r['measure']}: {r.get('value', 'N/A')} {', '.join(r.get('issues', []))}")
    
    return all(r["status"] == "✅" for r in results)
```

### Relationship Integrity Check

```dax
-- Check for orphaned fact rows (no matching dimension)
EVALUATE
VAR _orphaned = CALCULATETABLE(
    fact_sales,
    ISBLANK(RELATED(dim_customers[customer_name]))
)
RETURN ROW("Orphaned Fact Rows", COUNTROWS(_orphaned))
```

---

## Layer 4: Report Validation

### Post-Deployment Checks

```python
def validate_report_deployment(ws_id: str, report_id: str, headers: dict) -> dict:
    """Validate a deployed report has correct structure."""
    
    # Get definition
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/reports/{report_id}/getDefinition",
        headers=headers
    )
    
    # Poll if async
    if resp.status_code == 202:
        op_id = resp.headers.get("x-ms-operation-id")
        # ... poll pattern ...
    
    definition = resp.json()
    parts = definition.get("definition", {}).get("parts", [])
    part_paths = [p["path"] for p in parts]
    
    checks = {
        "has_report_json": "report.json" in part_paths,
        "has_pbir": "definition.pbir" in part_paths,
        "has_theme": any("theme" in p.lower() for p in part_paths),
    }
    
    # Decode report.json and check structure
    import base64, json
    report_part = next((p for p in parts if p["path"] == "report.json"), None)
    if report_part:
        report_json = json.loads(base64.b64decode(report_part["payload"]))
        sections = report_json.get("sections", [])
        checks["page_count"] = len(sections)
        checks["has_visuals"] = any(
            len(s.get("visualContainers", [])) > 0 for s in sections
        )
        total_visuals = sum(len(s.get("visualContainers", [])) for s in sections)
        checks["total_visuals"] = total_visuals
    
    return checks
```

---

## Layer 5: Freshness Monitoring

### Staleness Detection

```python
def check_data_freshness(ws_id: str, lakehouse_id: str, table_name: str, 
                         max_age_hours: int, headers: dict) -> bool:
    """Check if a Delta table has been updated recently."""
    # Query via SQL Endpoint
    query = f"SELECT MAX(event_datetime) as latest FROM {table_name}"
    # Execute via SQL Endpoint connection...
    
    from datetime import datetime, timedelta
    # ... parse result ...
    if latest < datetime.utcnow() - timedelta(hours=max_age_hours):
        print(f"⚠️  {table_name} is stale: last update {latest} (>{max_age_hours}h ago)")
        return False
    return True
```

### Freshness SLA Table

| Data Layer | Acceptable Staleness | Check Frequency |
|-----------|---------------------|-----------------|
| Streaming KQL tables | < 5 minutes | Every 5 min |
| Daily batch fact tables | < 24 hours | Every hour |
| Dimension tables | < 7 days | Daily |
| Semantic Model (cache) | < 1 hour | Every 30 min |

---

## Complete Validation Pipeline

Run this after every data load or deployment:

```python
def full_validation_pipeline(config: dict):
    """End-to-end data quality validation."""
    print("=" * 60)
    print("DATA QUALITY VALIDATION PIPELINE")
    print("=" * 60)
    
    # Layer 1: Source files
    print("\n📁 Layer 1: Source Validation")
    for table, cols in config["sources"].items():
        validate_csv_source(f"data/raw/{table}.csv", cols)
    
    # Layer 2: Transformations (in Spark notebook context)
    print("\n🔄 Layer 2: Transformation Validation")
    # validate_transformation() calls...
    
    # Layer 3: Semantic Model
    print("\n📊 Layer 3: Semantic Model Validation")
    validate_dax_measures(config["ws_id"], config["model_id"], config["measures"], config["headers"])
    
    # Layer 4: Report
    print("\n📈 Layer 4: Report Validation")
    validate_report_deployment(config["ws_id"], config["report_id"], config["headers"])
    
    # Layer 5: Freshness
    print("\n⏰ Layer 5: Freshness Check")
    for table, max_age in config["freshness_sla"].items():
        check_data_freshness(config["ws_id"], config["lakehouse_id"], table, max_age, config["headers"])
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
```

# Domain Modeler Agent — Known Issues & Pitfalls

## Common Modeling Mistakes

### 1. Inconsistent IDs Across Layers
**Symptom**: KQL query joins fail because `site_id` in KQL is "S001" but in Lakehouse it's "SITE-001".  
**Fix**: Define ID format ONCE in the domain model and enforce everywhere:
```
Convention: site_id = "SITE-{NNN}" → SITE-001, SITE-002, etc.
Used in: dim_sites.csv, SensorReading KQL, Site ontology entity, Semantic Model
```

### 2. Snowflake Schema in Direct Lake
**Symptom**: Power BI Direct Lake mode can't handle multi-level joins.  
**Fix**: Flatten dimensions. Instead of `dim_sensors → dim_equipment → dim_zones → dim_sites`, denormalize:
```
dim_sensors: sensor_id, sensor_name, equipment_id, equipment_name, zone_id, zone_name, site_id, site_name
```
This is intentional in Fabric — Direct Lake works best with flat star schemas.

### 3. Missing Date Dimension
**Symptom**: Time intelligence DAX measures (`SAMEPERIODLASTYEAR`, `DATESMTD`) fail.  
**Fix**: Always include `dim_dates` with a contiguous date range. Mark it as a Date table in the Semantic Model:
```dax
-- In Semantic Model definition
dateTable: dim_dates
dateColumn: date_key
```

### 4. Over-Partitioning Delta Tables
**Symptom**: Thousands of tiny partition folders in `Tables/fact_*/`.  
**Fix**: Only partition tables >1TB. For demo data, never partition. Use Z-ORDER instead.

### 5. KQL Table Missing Timestamp Column
**Symptom**: Time-range filters in KQL dashboards return no data, `| where timestamp > ago(1h)` fails.  
**Fix**: Every KQL streaming table MUST have a `timestamp: datetime` column. It should be the ingestion time or event time.

### 6. Sample Data Not Representative
**Symptom**: Dashboards look flat — all values are the same, no trends visible.  
**Fix**: Use sine waves + noise for time series, weighted distributions for categories:
```python
# BAD: uniform random — boring
value = random.uniform(0, 100)

# GOOD: realistic with daily pattern
hour_angle = (hour / 24) * 2 * math.pi
value = baseline + math.sin(hour_angle) * amplitude + random.gauss(0, noise)
```

### 7. Fact Table Without Proper Grain
**Symptom**: Aggregations double-count or seem wrong.  
**Fix**: Define grain explicitly. One row per X:
- One row per sale transaction ✅
- One row per customer per day ✅ (periodic snapshot)
- Multiple readings per sensor per second where you want per-second ❌ (wrong grain)

### 8. DAX Measures Reference Wrong Table
**Symptom**: `SUM(fact_sales[amount])` returns blank.  
**Fix**: Verify column names match exactly between the Delta table and the Semantic Model definition. Delta column names are case-sensitive.

---

## Cross-Layer Compatibility Issues

| Issue | Where | Fix |
|-------|-------|-----|
| STRING vs string type mismatch | Spark→KQL | Use mapping table: Spark `STRING` = KQL `string` |
| DATE vs datetime | Spark→KQL | KQL only has `datetime` — include time component |
| Null handling | All layers | Define NULL behavior per column; KQL treats nulls differently than Spark |
| Unicode characters | CSV→Spark→KQL | Use UTF-8 without BOM everywhere |
| Timestamp timezone | All layers | Always use UTC (Z suffix) for consistency |

## Scale Guidelines

| Demo Duration | Dimension Rows | Fact Rows | KQL Events | Notes |
|--------------|---------------|-----------|------------|-------|
| 15 min quick | 10-50 per dim | 1,000 | 500/min stream | Minimal |
| 1 hour full | 50-200 per dim | 5,000-10,000 | 1,000/min | Standard |
| Half-day workshop | 200-1000 | 50,000-100,000 | 5,000/min | Need F4+ capacity |
| Production POC | 1,000+ | 1M+ | 10,000+/min | Need F16+ capacity |

> **Trial capacity limits**: Max ~1 concurrent Spark job, limited KQL throughput (~100 events/sec). Keep data small.

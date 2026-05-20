# warehouse-agent — Known Issues & Gotchas

> Warehouse-specific pitfalls. For general Fabric issues see `../../known_issues.md`.

---

## 1. No DROP COLUMN
`ALTER TABLE … DROP COLUMN` is not supported. Recreate the table via CTAS:
```sql
CREATE TABLE dbo.target_new AS
SELECT col1, col2, col4 -- skip col3
FROM dbo.target;

RENAME OBJECT dbo.target TO target_old;
RENAME OBJECT dbo.target_new TO target;
DROP TABLE dbo.target_old;
```

## 2. Write-Write Conflicts — Table-Level Locking
Warehouse uses **snapshot isolation**. Two concurrent **write** transactions on the **same table** will fail — one gets an error. Writes to *different* tables can run concurrently.

**Fix**: Serialize writes to the same table using Pipeline sequential activities.

## 3. MERGE Is Preview-Only
`MERGE INTO` exists but is in **preview** and can fail silently on complex predicates.

**Fix**: Use the DELETE + INSERT pattern:
```sql
BEGIN TRANSACTION;
DELETE FROM dbo.target WHERE key IN (SELECT key FROM dbo.staging);
INSERT INTO dbo.target SELECT * FROM dbo.staging;
COMMIT;
```

## 4. No Temporary Tables
`#temp` and `##global_temp` tables are **not supported**.

**Fix**: Use CTEs, subqueries, or permanent staging tables that you clean up.

## 5. No Cursors
`DECLARE CURSOR` is not available.

**Fix**: Use set-based operations (JOINs, CTEs, window functions).

## 6. Transaction Timeout (~30 min)
Long-running transactions may timeout around 30 minutes.

**Fix**: Break large operations into batches. For massive CTAS, let the engine parallelize — don't wrap in explicit transaction.

## 7. COPY INTO — SAS Token Expiry
SAS tokens used in `COPY INTO` must be valid for the **entire load duration**. A 1-hour load needs a token valid for >1 hour.

**Fix**: Use Managed Identity (workspace identity) where possible, or generate long-lived SAS tokens.

## 8. Cold Start Latency
After capacity pause/resume or long idle, first query can take 30-90 seconds.

**Fix**: Send a lightweight `SELECT 1` as a "warm-up" query before production workloads.

## 9. Lakehouse SQL Endpoint Is Read-Only
You **cannot** INSERT/UPDATE/DELETE through the Lakehouse SQL Endpoint — even from cross-database queries in Warehouse.

**Fix**: Write to Lakehouse via Spark notebooks only. Or use a Pipeline Copy Activity.

## 10. No ALTER TABLE RENAME COLUMN
Column renames require recreating the table via CTAS (same as DROP COLUMN workaround).

## 11. Schema = dbo Only (by Default)
Custom schemas are supported but `COPY INTO` only works with `dbo`. 

**Fix**: Load into `dbo`, then INSERT into custom schema tables.

## 12. V-Order Is Automatic
Tables created via CTAS automatically get V-Order optimization. No manual OPTIMIZE needed (unlike Lakehouse Delta).

---

## Quick-Reference

| Feature | Supported? | Notes |
|---------|-----------|-------|
| INSERT / UPDATE / DELETE | ✅ | Full DML |
| MERGE | ⚠️ | Preview only |
| CTAS | ✅ | Preferred for large transforms |
| COPY INTO | ✅ | Parquet, CSV, Delta from ADLS/Blob |
| Stored Procedures | ✅ | T-SQL only, no CLR |
| Transactions | ✅ | Snapshot isolation, table-level |
| Time Travel | ✅ | `FOR TIMESTAMP AS OF` (7-day retention) |
| Cross-DB Queries | ✅ | Same workspace only |
| DROP COLUMN | ❌ | Use CTAS |
| Temp Tables | ❌ | Use CTEs or staging tables |
| Cursors | ❌ | Use set-based operations |
| Triggers | ❌ | Use Pipeline orchestration |
| Indexes | ❌ | V-Order is automatic |
| Partitioning | ❌ | Automatic micro-partitioning |

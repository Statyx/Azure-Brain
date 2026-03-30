# Warehouse Patterns — SQL DW Authoring in Fabric

> Source: [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) — SQLDW-AUTHORING-CORE.md

## Authoring Capability Matrix

| Capability | Lakehouse SQL EP | Mirrored DB SQL EP | Warehouse |
|------------|-----------------|-------------------|-----------|
| `SELECT` | ✅ | ✅ | ✅ |
| `CREATE TABLE` | ❌ | ❌ | ✅ |
| `INSERT/UPDATE/DELETE` | ❌ | ❌ | ✅ |
| `CREATE VIEW` | ✅ (limited) | ✅ (limited) | ✅ |
| `COPY INTO` | ❌ | ❌ | ✅ |
| `CTAS` | ❌ | ❌ | ✅ |
| Stored Procedures | ❌ | ❌ | ✅ |
| Transactions | ❌ | ❌ | ✅ |
| Time Travel | ❌ | ❌ | ✅ |

> **Lakehouse SQL Endpoint** is read-only — create tables with Spark notebooks, not SQL.

---

## Table DDL

### CREATE TABLE
```sql
CREATE TABLE dbo.fact_sales (
    sale_id         BIGINT NOT NULL,
    product_id      INT NOT NULL,
    customer_id     INT NOT NULL,
    sale_date       DATE NOT NULL,
    quantity        INT,
    unit_price      DECIMAL(18,2),
    total_amount    DECIMAL(18,2)
);
```

### CREATE TABLE AS SELECT (CTAS)
```sql
-- Best pattern for data transformation — highly parallelized
CREATE TABLE dbo.gold_monthly_sales AS
SELECT
    YEAR(sale_date) AS sale_year,
    MONTH(sale_date) AS sale_month,
    product_id,
    SUM(quantity) AS total_quantity,
    SUM(total_amount) AS total_revenue
FROM dbo.fact_sales
GROUP BY YEAR(sale_date), MONTH(sale_date), product_id;
```

> **CTAS** is the preferred Fabric pattern for heavy transformations. It's parallel, creates a new table, and avoids locking issues.

### SELECT INTO
```sql
-- Quick-and-dirty version of CTAS
SELECT product_id, SUM(total_amount) AS revenue
INTO dbo.product_revenue
FROM dbo.fact_sales
GROUP BY product_id;
```

### ALTER TABLE Limitations
```sql
-- ✅ Supported
ALTER TABLE dbo.fact_sales ADD discount DECIMAL(18,2);

-- ❌ NOT supported in Fabric Warehouse
ALTER TABLE dbo.fact_sales DROP COLUMN discount;
ALTER TABLE dbo.fact_sales ALTER COLUMN quantity BIGINT;
```

> **Cannot drop or alter columns** — use CTAS to create a new table without the column, then rename.

---

## Data Ingestion

### COPY INTO (Recommended)
```sql
COPY INTO dbo.fact_sales
FROM 'https://account.dfs.core.windows.net/container/sales/*.parquet'
WITH (
    FILE_TYPE = 'PARQUET',
    CREDENTIAL = (IDENTITY = 'Shared Access Signature', SECRET = '...')
);
```

For CSV:
```sql
COPY INTO dbo.fact_sales
FROM 'https://account.dfs.core.windows.net/container/sales/*.csv'
WITH (
    FILE_TYPE = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CREDENTIAL = (IDENTITY = 'Shared Access Signature', SECRET = '...')
);
```

### OPENROWSET (Query external data without loading)
```sql
SELECT *
FROM OPENROWSET(
    BULK 'https://account.dfs.core.windows.net/container/data.parquet',
    FORMAT = 'PARQUET'
) AS [result];
```

### Ingestion Method Comparison

| Method | Best For | V-Order? | Speed |
|--------|----------|----------|-------|
| COPY INTO | Bulk load from storage | ✅ Auto | ★★★★★ |
| INSERT...SELECT | Small transforms | ✅ Auto | ★★★☆☆ |
| CTAS | Large transforms | ✅ Auto | ★★★★☆ |
| OPENROWSET | Ad-hoc external queries | N/A | ★★★☆☆ |
| Pipeline Copy Activity | Orchestrated ETL | ✅ | ★★★★☆ |

> **V-Order**: Fabric automatically applies V-Order optimization to data written through DML/COPY — no manual step needed.

---

## Transactions

### Snapshot Isolation
Fabric Warehouse uses **snapshot isolation** by default:
- Readers never block writers
- Writers never block readers
- Each transaction sees a consistent snapshot from its start time

### Write-Write Conflicts
Conflicts are detected at the **TABLE level** (not row or page):
```sql
-- Transaction A
BEGIN TRANSACTION;
UPDATE dbo.fact_sales SET discount = 0.1 WHERE sale_id = 1;

-- Transaction B (concurrent, same table → CONFLICT)
BEGIN TRANSACTION;
UPDATE dbo.fact_sales SET discount = 0.2 WHERE sale_id = 2;
-- ❌ One of these will fail with write-write conflict
```

> **Important**: Even if the two transactions touch different rows, they conflict because conflict detection is at the TABLE level.

### Conflict Mitigation Strategies
1. **Partition by table** — Write to different tables, merge later
2. **CTAS instead of UPDATE** — Create a new table, swap
3. **Serialize writes** — Use Pipeline to ensure sequential execution
4. **Small transactions** — Commit frequently to minimize conflict window

### Transaction Example
```sql
BEGIN TRANSACTION;
    DELETE FROM dbo.fact_sales WHERE sale_date < '2020-01-01';
    INSERT INTO dbo.fact_sales_archive SELECT * FROM dbo.fact_sales_staging;
COMMIT;
```

---

## Stored Procedures

### ETL Pattern
```sql
CREATE PROCEDURE dbo.sp_upsert_customers
AS
BEGIN
    -- Fabric: MERGE is in preview, use DELETE + INSERT pattern
    DELETE FROM dbo.dim_customers
    WHERE customer_id IN (SELECT customer_id FROM dbo.staging_customers);

    INSERT INTO dbo.dim_customers
    SELECT * FROM dbo.staging_customers;
END;
```

### CTAS-Based Swap Pattern
Best for large table rebuilds without locking:
```sql
CREATE PROCEDURE dbo.sp_rebuild_gold_sales
AS
BEGIN
    -- 1. Create new table via CTAS
    CREATE TABLE dbo.gold_sales_new AS
    SELECT ...
    FROM dbo.silver_sales
    GROUP BY ...;

    -- 2. Swap using RENAME
    RENAME OBJECT dbo.gold_sales TO gold_sales_old;
    RENAME OBJECT dbo.gold_sales_new TO gold_sales;

    -- 3. Drop old
    DROP TABLE dbo.gold_sales_old;
END;
```

### Cursor Replacement
Cursors are not supported — use set-based operations:
```sql
-- ❌ No cursors in Fabric Warehouse
-- ✅ Use CTAS, window functions, or staged temp tables instead

-- Example: Running total without cursor
SELECT
    sale_date,
    total_amount,
    SUM(total_amount) OVER (ORDER BY sale_date ROWS UNBOUNDED PRECEDING) AS running_total
FROM dbo.fact_sales;
```

---

## Time Travel

Query historical data up to 30 days back:

```sql
-- Query data as it was 7 days ago
SELECT * FROM dbo.fact_sales
FOR TIMESTAMP AS OF '2025-03-20T12:00:00';

-- Compare current vs historical
SELECT 'current' AS version, COUNT(*) AS cnt FROM dbo.fact_sales
UNION ALL
SELECT 'last_week', COUNT(*) FROM dbo.fact_sales
FOR TIMESTAMP AS OF DATEADD(day, -7, GETDATE());
```

> **Retention**: 30 calendar days. Data older than that is not recoverable via time travel.

---

## Warehouse Snapshots

Create named point-in-time snapshots:
```sql
-- Create snapshot (via REST API or UI)
-- Snapshots are separate, queryable copies with their own SQL endpoint
```

---

## Source Control & CI/CD

### Git Integration
Fabric Warehouse supports Git integration:
- Tables, views, stored procedures exported as SQL scripts
- Changes tracked in connected Git repo
- Deployment via sync or deployment pipelines

### SQL Database Projects
For advanced CI/CD:
1. Export warehouse as SQL Database Project (`.sqlproj`)
2. Build/validate locally
3. Deploy via `SqlPackage.exe` or pipeline

---

## Gotchas

1. **Cannot DROP or ALTER columns** — Use CTAS to recreate the table
2. **Write-write conflicts at TABLE level** — Even different rows on same table conflict
3. **MERGE is in preview** — Use DELETE + INSERT pattern for upserts
4. **No clustered indexes** — Fabric Warehouse uses automatic columnar storage optimization
5. **Cursors not supported** — Use set-based operations, window functions
6. **Max 10K tables per warehouse** — Plan schema organization
7. **COPY INTO needs external credential** — SAS or Managed Identity
8. **RENAME OBJECT for table swap** — No `sp_rename` equivalent
9. **Stored procedures can't return result sets to pipelines** — Use Lookup activity with inline SQL
10. **V-Order is automatic** — Don't manually compress or optimize
11. **Lakehouse SQL endpoint is READ-ONLY** — Cannot INSERT/UPDATE/DELETE through it
12. **Time travel max 30 days** — Cannot recover data beyond 30 calendar days
13. **OPENROWSET paths are case-sensitive** — URL must match exactly
14. **No temp tables (#tables)** — Use CTEs or staged permanent tables
15. **Transaction timeout** — Long-running transactions may be killed after ~30 minutes

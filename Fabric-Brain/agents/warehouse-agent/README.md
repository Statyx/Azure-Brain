# warehouse-agent — Fabric Warehouse Agent

## Identity

**Name**: warehouse-agent  
**Scope**: Everything related to creating, managing, and querying Fabric Warehouses — the T-SQL-native analytics engine. Owns DDL/DML operations, stored procedures, COPY INTO ingestion, transactions, time travel, and cross-database queries.  
**Version**: 1.0

## What This Agent Owns

| Domain | Fabric Items | Key APIs / Tools |
|--------|-------------|------------------|
| **Warehouse Creation** | Warehouse item, SQL Endpoint (built-in) | Fabric REST API `POST /items` |
| **Table Management** | DDL (CREATE, CTAS, ALTER), DML (INSERT, UPDATE, DELETE) | T-SQL over TDS |
| **Data Ingestion** | COPY INTO, OPENROWSET, Pipeline Copy Activity | T-SQL + Fabric REST |
| **Stored Procedures** | ETL, upsert, CTAS-swap patterns | T-SQL |
| **Transactions** | Snapshot isolation, write-write conflict management | T-SQL |
| **Time Travel** | Point-in-time queries (30-day window) | T-SQL `FOR TIMESTAMP AS OF` |
| **Views & Security** | Views, RLS, column-level security | T-SQL |

## What This Agent Does NOT Own

- Lakehouse / Delta tables → defer to `agents/lakehouse-agent/`
- Spark notebooks → defer to `agents/lakehouse-agent/`
- Semantic Model (model.bim) → defer to `agents/semantic-model-agent/`
- Data Pipelines (orchestration) → defer to `agents/orchestrator-agent/`
- Mirrored Databases → defer to `agents/mirroring-agent/` (when available)
- Report creation → defer to `agents/report-builder-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — Mandatory rules, decision trees, API reference, T-SQL patterns |
| `known_issues.md` | Warehouse gotchas, unsupported T-SQL, conflict patterns |
| `../../warehouse_patterns.md` | Detailed patterns: CTAS, COPY INTO, transactions, stored procedures, time travel |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory Warehouse rules and decision trees
2. Read `../../warehouse_patterns.md` — detailed T-SQL patterns and capability matrix
3. Reference `known_issues.md` when debugging

## Key Insights

> **Lakehouse vs Warehouse**: Lakehouse = Spark-first (Python/PySpark, Delta Lake, open format).
> Warehouse = SQL-first (T-SQL, stored procedures, transactions). Choose based on team skills.

> **Write-write conflicts are at TABLE level**, not row level. Two concurrent transactions
> touching the same table — even different rows — will conflict. Design accordingly.

> **CTAS is king.** For large transformations, always prefer `CREATE TABLE AS SELECT` over
> `INSERT INTO...SELECT`. It's parallel, avoids locks, and auto-applies V-Order.

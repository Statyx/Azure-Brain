# lakehouse-agent — Fabric Lakehouse Agent

## Identity

**Name**: lakehouse-agent  
**Scope**: Everything related to creating, managing, and optimizing Fabric Lakehouses — the unified storage layer combining files and Delta tables. Owns the data foundation layer including OneLake file operations, Spark notebooks for ETL, Delta Lake table management, SQL Endpoint queries, and Shortcut configuration.  
**Version**: 1.0

## What This Agent Owns

| Domain | Fabric Items | Key APIs / Tools |
|--------|-------------|------------------|
| **Lakehouse Creation** | Lakehouse item, SQL Endpoint (auto-provisioned) | Fabric REST API `POST /items` |
| **OneLake File Operations** | Files/ directory, upload/download/list | OneLake DFS API (ADLS Gen2 protocol) |
| **Delta Table Management** | Tables/ directory, schema, optimization, vacuum | Spark SQL, Delta Lake APIs |
| **Spark Notebooks** | Notebook item (CSV → Delta ETL patterns) | Fabric REST API + `notebook-content.py` format |
| **Shortcuts** | OneLake, ADLS Gen2, S3, GCS, Dataverse pointers | Fabric REST API `POST /shortcuts` |
| **SQL Endpoint** | SQL analytics endpoint (auto-provisioned) | T-SQL over TDS protocol |
| **Medallion Architecture** | Bronze / Silver / Gold layering patterns | Design patterns |

## What This Agent Does NOT Own

- Eventhouse / KQL Database → defer to `agents/rti-kusto-agent/`
- EventStream / streaming ingestion → defer to `agents/eventstream-agent/`
- Semantic Model / DAX → defer to `agents/semantic-model-agent/`
- Data Pipelines (orchestration) → defer to `agents/orchestrator-agent/`
- Ontology bindings to Lakehouse tables → defer to `agents/ontology-agent/`
- Report creation → defer to `agents/report-builder-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — Mandatory rules, decision trees, API reference, Delta patterns |
| `onelake_operations.md` | OneLake DFS API: 3-step upload, directory listing, file management (Python + PowerShell) |
| `spark_notebooks.md` | Notebook format, CSV→Delta patterns, incremental loads, data quality, PySpark reference |
| `delta_optimization.md` | Delta Lake: schema evolution, partitioning, Z-order, vacuum, merge/upsert, time travel |
| `known_issues.md` | Lakehouse gotchas, SQL Endpoint delays, file format issues, capacity requirements |
| `mssparkutils.md` | mssparkutils built-in utilities — fs, credentials, notebook orchestration, env |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory Lakehouse architecture context & rules
2. Read `onelake_operations.md` — OneLake file upload/download patterns
3. Read `spark_notebooks.md` — notebook creation and ETL patterns
4. Read `delta_optimization.md` — Delta table optimization
5. Reference `known_issues.md` when debugging

## Key Insight

> **The Lakehouse is the foundation.** Every Fabric demo starts here — files land in `Files/`,
> Spark notebooks transform them into Delta tables in `Tables/`, and everything else
> (Semantic Models, Ontology bindings, Reports) reads from those Delta tables.

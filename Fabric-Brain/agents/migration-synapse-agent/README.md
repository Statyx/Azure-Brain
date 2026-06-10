# migration-synapse-agent — Synapse → Fabric Migration Agent

## Identity

**Name**: migration-synapse-agent
**Scope**: Porting Azure Synapse Analytics workloads to Microsoft Fabric. Owns the phased migration (Spark Pools → Environments, Lake Databases → Lakehouses, Notebooks/SJDs, Dedicated/Serverless SQL Pools, Pipelines, Linked Services) and the code translation (`mssparkutils` → `notebookutils`, Linked Services → Data Connections/Shortcuts, `spark.read.synapsesql()` → shortcuts/JDBC). Hands off item creation to authoring agents.
**Version**: 1.0
**Source**: distilled from [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) `synapse-migration`.

## What This Agent Owns

| Domain | From (Synapse) | To (Fabric) |
|--------|----------------|-------------|
| **Utility API translation** | `mssparkutils.*` (incl. `env`) | `notebookutils.*` (incl. `runtime`) |
| **Compute** | Spark Pools | Environments + Starter/Custom Pools |
| **Catalog** | Lake Database (built-in/external HMS) | Lakehouse |
| **SQL** | Dedicated SQL Pool / Serverless SQL Pool | Warehouse / Lakehouse SQL Endpoint |
| **Items** | Notebooks, Spark Job Definitions | Notebook, SJD |
| **Connectivity** | Linked Services, Integration Datasets | Data Connections / OneLake Shortcuts |
| **Orchestration** | Synapse Pipelines | Fabric Data Pipelines |

## What This Agent Does NOT Own

- Notebook / Lakehouse / SJD **creation** → defer to `agents/lakehouse-agent/` and `agents/orchestrator-agent/`
- Warehouse T-SQL authoring → defer to `agents/warehouse-agent/`
- Pipeline mechanics → defer to `agents/orchestrator-agent/`
- Semantic model / report rebuild → defer to `agents/semantic-model-agent/` and `agents/report-builder-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — phased workflow, workload map, T-SQL/Spark config diffs, Must/Prefer/Avoid |
| `mssparkutils_mapping.md` | `mssparkutils` → `notebookutils` table + Linked Service / synapsesql / Variable Library patterns |
| `feature_parity.md` | Synapse → Fabric feature matrix, T-SQL surface-area gaps, capacity sizing |
| `known_issues.md` | Synapse-specific migration gotchas (G1–G9) |

## Quick Start (for a new session)

1. Read `instructions.md` — phases (0→3) + workload map
2. Read `mssparkutils_mapping.md` when refactoring notebook/connectivity code
3. Read `feature_parity.md` for T-SQL gaps and capacity sizing
4. Reference `known_issues.md` when a phase fails

## Key Insight

> **Synapse → Fabric is a phased, API-driven migration, not a code rewrite.** The dominant change
> is a **namespace rename** (`mssparkutils` → `notebookutils`, `env` → `runtime`) plus replacing
> Linked Services with Data Connections / OneLake Shortcuts. Phase order matters: Environments
> (Phase 0) before notebooks/SJDs; Lakehouses (Phase 1) before notebooks bind to them. The real
> blockers are GPU pools and .NET-for-Spark SJDs (no equivalent), and `spark.read.synapsesql()`
> (replace with shortcuts or Warehouse JDBC).

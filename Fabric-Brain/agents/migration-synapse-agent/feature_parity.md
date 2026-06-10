# Feature Parity & Capacity Sizing

## Synapse → Fabric — key feature gaps

| Synapse feature | Fabric status | Action |
|---|---|---|
| `spark.read.synapsesql()` | ❌ no equivalent | Replace with JDBC / OneLake shortcut / pipeline |
| Linked Services | ⚠️ redesigned | Data Connections (external) / OneLake Shortcuts (storage) |
| External Hive Metastore | ⚠️ partial | Migrate tables as Shortcuts |
| `mssparkutils.env` | ✅ renamed | `notebookutils.runtime` |
| Dedicated SQL Pool distribution hints | ❌ removed | Drop `HASH`/`ROUND_ROBIN`/`REPLICATE` — auto-distribution |
| PolyBase `CREATE EXTERNAL TABLE` | ⚠️ replaced | `COPY INTO` or Lakehouse external access |
| Result set caching | ❌ not available | Redesign query patterns |
| Workload management (resource classes) | ❌ not available | Use Fabric capacity (CU) |
| GPU Spark pools | ❌ not available | Keep in Synapse / use Azure ML |
| .NET for Spark (C#/F# SJDs) | ❌ not supported | Rewrite in PySpark / keep in Synapse |

## T-SQL surface-area actions
- Remove distribution hints (`WITH (DISTRIBUTION = ...)`).
- Replace `CREATE EXTERNAL TABLE` (PolyBase) with `COPY INTO`.
- Drop result-set-caching and workload-management constructs.
- Delegate Fabric Warehouse T-SQL authoring to `warehouse-agent`.

## Spark config actions
- Replace `spark.read.synapsesql()` (see `mssparkutils_mapping.md`).
- Remove unsupported `%%configure` keys (some are silently ignored — Gotcha G8).
- Move pool-level config / library installs to a Fabric **Environment**.
- Pick the matching Fabric Runtime and re-test (minor Spark version diffs).

## Capacity sizing reference (Synapse pool → Fabric SKU)

| Scenario | Fabric SKU | Pool |
|---|---|---|
| Dev / test | **F8–F16** | Starter Pool |
| Standard production | **F32–F64** | Starter or Custom Pool |
| Enterprise | **F128+** | Custom Pool |

> Use the **Fabric Trial** (free F64, 60 days) for migration validation before committing to a SKU.
> Map Synapse node sizes to Fabric node sizes (Small→XX-Large) by vCore/memory ratio.

# Known Issues — Databricks → Fabric Migration

## 1. `dbutils` raises `NameError`
**Symptom**: `NameError: name 'dbutils' is not defined`.
**Cause**: `dbutils` does not exist in Fabric notebooks.
**Fix**: Replace every call with `notebookutils.*` (see `dbutils_mapping.md`). Never `import dbutils`.

## 2. DBFS paths fail
**Symptom**: Path-not-found / invalid scheme on `dbfs:/...` or `/mnt/...`.
**Cause**: No DBFS in Fabric.
**Fix**: Use OneLake `abfss://workspace@onelake.dfs.fabric.microsoft.com/...` or Lakehouse-relative
`Files/` / `Tables/`. Prefer OneLake Shortcuts for data already in ADLS Gen2.

## 3. Mounts not released between sessions
**Symptom**: Stale mount / mount-point-in-use errors.
**Cause**: Fabric `notebookutils.fs.mount()` is not auto-released on session end.
**Fix**: Pair every `mount()` with `unmount()` in `try/finally`. For persistent/cross-workspace
access, use OneLake Shortcuts instead.

## 4. Unity Catalog 3-level name fails
**Symptom**: Table-not-found on `spark.read.table("catalog.schema.table")`.
**Cause**: Fabric Lakehouse uses 2-level `schema.table`.
**Fix**: Drop the catalog level. Ensure the right Lakehouse is attached as default.

## 5. Governance silently missing
**Symptom**: RLS / column masking / RBAC absent after migration.
**Cause**: Unity Catalog governance does not transfer.
**Fix**: Reconfigure with workspace roles + Lakehouse permissions. Treat as a separate workstream.

## 6. `%pip install` / `dbutils.library.install` not effective in production
**Symptom**: Library missing on scheduled runs, or install ignored.
**Cause**: Runtime library installs are not supported in production.
**Fix**: Create a Fabric Environment with the libraries and attach it to the workspace/notebook.
`dbutils.library.restartPython()` → `notebookutils.session.restartPython()`.

## 7. Widget parameters return nothing
**Symptom**: `dbutils.widgets.get(...)` removed; params not received.
**Cause**: No widget API in Fabric; `notebookutils.runtime.context` does not expose parameter values.
**Fix**: Use a **parameters cell**; pass values via `notebookutils.notebook.run(..., arguments={...})`
or a Pipeline notebook activity's Base parameters. Centralize config via `notebookutils.variableLibrary`.

## 8. Delta Live Tables don't port
**Symptom**: DLT syntax/decorators invalid in Fabric.
**Cause**: No DLT equivalent.
**Fix**: Rewrite DLT datasets as parameterized notebook cells orchestrated by a Fabric Data Pipeline.

## 9. `spark.databricks.*` configs ignored or error
**Symptom**: Behaviour differs; some configs raise errors.
**Cause**: Proprietary Databricks Spark configs.
**Fix**: Remove them. Move valid `spark.conf` to a Fabric Environment.

## 10. GPU Spark pools unsupported
**Symptom**: No GPU node option in Fabric.
**Cause**: GPU-accelerated Spark pools not available.
**Fix**: Migration blocker — keep the workload in Databricks or move to Azure ML.

## 11. MLflow tracking writes to the wrong place
**Symptom**: Experiments not appearing in Fabric.
**Cause**: `mlflow.set_tracking_uri("databricks")` still present, or `set_experiment` uses a path.
**Fix**: Delete `set_tracking_uri`; call `mlflow.set_experiment("name")` with a name, not a path.

## 12. Spark minor-version API warnings
**Symptom**: Deprecated-API warnings / behaviour changes after migration.
**Cause**: Databricks Runtime vs Fabric Runtime Spark minor-version differences.
**Fix**: Pick the matching Fabric Runtime (1.1=3.3, 1.2=3.4, 1.3=3.5) and re-test every notebook.

---

> Issues 13–19 concern **coexistence**, not migration. See `coexistence_interop.md`.
> All are documented Microsoft behaviours observed in the docs on 2026-09-01, **not tenant-verified**.

## 13. `403 Forbidden` creating or testing a OneLake external location
**Symptom**: `403 Forbidden` when Unity Catalog accesses the OneLake path.
**Cause**: The managed identity / service principal has no role on the Fabric workspace, or the workspace has no active capacity assignment.
**Fix**: Grant the identity **Administrator / Member / Contributor** on the target Fabric workspace and confirm capacity is assigned. Check the path ends in `/Files`.
**Source**: Learn `azure/databricks/connect/unity-catalog/cloud-storage/external-locations-onelake` (2026-06-16).

## 14. OneLake external location rejected at creation
**Symptom**: Creation fails on a path that looks correct.
**Cause**: Name-based OneLake paths are rejected — the ID-based (GUID) ABFSS form is mandatory.
**Fix**: Use `abfss://<WorkspaceID>@onelake.dfs.fabric.microsoft.com/<DatabricksStorageID>/Files/`, both GUIDs taken from the Fabric browser URL. A *"skipped file events read"* warning on `Test connection` is expected and is **not** a failure — file event notifications are unsupported on OneLake paths.
**Source**: same as #13.

## 15. Unity Catalog grants do not protect an Azure Databricks Storage item
**Symptom**: A principal with no Unity Catalog grant can still read, write and delete the tables.
**Cause**: Documented by design — any **Member / Contributor / Administrator on the Fabric workspace** holding the Azure Databricks Storage item has full data access, irrespective of Unity Catalog.
**Fix**: No technical fix today. Isolate: a dedicated, restricted Fabric workspace for the storage item, minimal membership, no end users, no other Fabric assets. Treat this as a hard design constraint in any multi-client or multi-market estate, not a footnote.
**Source**: same as #13.

## 16. Federated OneLake query fails or tables are missing in Databricks
**Symptom**: Tables absent from the foreign catalog, or queries fail on some columns.
**Cause**: OneLake catalog federation does not support complex datatypes (array / map / struct), views, materialized views, or columns differing only by case. Only Lakehouse and Warehouse items are supported, and dedicated access mode is not.
**Fix**: Inspect the schema for complex types **before** choosing federation — flatten upstream in Fabric, or use mirroring / a OneLake external location instead. Use standard access mode, DBR 18.0+ / SQL warehouse 2025.40+.
**Source**: Learn `azure/databricks/query-federation/onelake` (2026-08-12).

## 17. Federated read denied despite a SQL permission
**Symptom**: Access denied although *"Read all with SQL analytics endpoint"* was granted.
**Cause**: Databricks reads through the OneLake APIs, not the SQL endpoint — the SQL-only permission is insufficient.
**Fix**: Grant a OneLake read permission (*Read all with Apache Spark* / *Read all OneLake data*) plus Viewer at workspace level. Enable the tenant settings *Service principals can use Fabric APIs*, *Allow apps running outside of Fabric to access data via OneLake*, and *Use short-lived user-delegated SAS tokens*.
**Source**: same as #16.

## 18. Mirrored Unity Catalog is missing tables in Fabric
**Symptom**: Tables visible in Unity Catalog do not appear in the Mirrored Azure Databricks item.
**Cause**: Mirroring filters out materialized views, streaming tables, and external tables that are not Delta format.
**Fix**: Materialize those datasets as Delta tables in Unity Catalog, or reach the underlying storage with a OneLake shortcut. Allow for propagation latency (seconds to several minutes) before concluding a table is missing.
**Source**: Learn `fabric/mirroring/azure-databricks` (2026-05-21).

## 19. Unmanaged Delta in `dbfs:/` blocks every zero-copy pattern
**Symptom**: No shortcut, mirror or federation path works for a subset of tables.
**Cause**: DBFS root is a Microsoft-managed storage account, not addressable via `abfss://` with customer credentials — invisible to shortcuts; and unmanaged non-UC tables fall outside mirroring.
**Fix**: Relocate those tables to an external location (ADLS Gen2, or a OneLake external location) before any interop work. Inventory "unmanaged Delta in DBFS" as its own category during assessment.
**Status**: unconfirmed — reasoned from DBFS root architecture and Rule 2, not tested.

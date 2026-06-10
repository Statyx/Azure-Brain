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

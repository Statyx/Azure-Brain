# `dbutils` → `notebookutils` Mapping

Complete substitution reference for porting Databricks notebook code to Fabric.
`dbutils` is **not available** in Fabric — every call must be replaced.

## File system (`dbutils.fs` → `notebookutils.fs`)

| `dbutils` call | `notebookutils` equivalent | Note |
|---|---|---|
| `dbutils.fs.ls(path)` | `notebookutils.fs.ls(path)` | Direct replacement |
| `dbutils.fs.cp(src, dest)` | `notebookutils.fs.cp(src, dest)` | Direct replacement |
| `dbutils.fs.mv(src, dest)` | `notebookutils.fs.mv(src, dest, create_path, overwrite=False)` | ⚠️ Signature differs |
| `dbutils.fs.rm(path, recurse)` | `notebookutils.fs.rm(path, recurse)` | Direct replacement |
| `dbutils.fs.mkdirs(path)` | `notebookutils.fs.mkdirs(path)` | Direct replacement |
| `dbutils.fs.put(path, contents)` | `notebookutils.fs.put(path, contents)` | Direct replacement |
| `dbutils.fs.head(path, maxBytes)` | `notebookutils.fs.head(path, max_bytes)` | ⚠️ Default differs (Py/Scala 100 KB, R 64 KB) |
| `dbutils.fs.mount(...)` | `notebookutils.fs.mount(source, mountPoint, extraConfigs=None)` | ✅ Supported (Entra default / accountKey / sasToken). Prefer **OneLake Shortcuts** for persistent/cross-workspace |

> ⚠️ Always pair `mount()` with `unmount()` in `try/finally` — Fabric mounts are not released automatically on session end.

```python
# Databricks → Fabric (replace DBFS/mount paths with OneLake-relative paths)
# dbutils.fs.ls("/mnt/bronze/orders/")
notebookutils.fs.ls("Files/bronze/orders/")
# dbutils.fs.cp("/mnt/raw/file.csv", "/mnt/archive/file.csv")
notebookutils.fs.cp("Files/raw/file.csv", "Files/archive/file.csv")
```

## Secrets (`dbutils.secrets` → `notebookutils.credentials`)

| `dbutils` call | `notebookutils` equivalent | Note |
|---|---|---|
| `dbutils.secrets.get(scope, key)` | `notebookutils.credentials.getSecret(keyVaultUrl, secretName)` | Scope → Key Vault URL, key → secret name |

```python
# pwd = dbutils.secrets.get(scope="prod", key="db-password")
pwd = notebookutils.credentials.getSecret("https://myvault.vault.azure.net/", "db-password")
```

## Notebook control flow (`dbutils.notebook` → `notebookutils.notebook`)

| `dbutils` call | `notebookutils` equivalent | Note |
|---|---|---|
| `dbutils.notebook.run(path, timeout, args)` | `notebookutils.notebook.run(name, timeout, args)` | `path` → notebook `name` (relative to workspace) |
| `dbutils.notebook.exit(value)` | `notebookutils.notebook.exit(value)` | Direct replacement |

## Library (`dbutils.library` → Fabric Environments)

| `dbutils` call | Fabric equivalent | Note |
|---|---|---|
| `dbutils.library.install(...)` | **Fabric Environment** item | Not available at runtime |
| `dbutils.library.restartPython()` | `notebookutils.session.restartPython()` | Python/PySpark only |

> Do not use `%pip install` in production notebooks. Move all library management to a Fabric
> Environment attached at workspace or notebook level.

## Data (`dbutils.data`)

| `dbutils` call | Fabric equivalent |
|---|---|
| `dbutils.data.summarize(df)` | `display(df.summary())` or pandas `df.describe()` |

## Widgets (`dbutils.widgets` → parameters cells)

No direct equivalent. Use these patterns:

| Use case | Fabric pattern |
|---|---|
| Param from parent notebook | Mark a cell as **parameters cell** (cell "..." → "Mark cell as parameters"); parent calls `notebookutils.notebook.run("child", arguments={"param": "value"})` — engine inserts an override cell at runtime |
| Pipeline-driven params | Same parameters-cell mechanism; Pipeline notebook activity supplies **Base parameters** |
| Centralized cross-notebook config | `notebookutils.variableLibrary.getLibrary("<name>")` from a Variable Library item (deployment pipelines activate the right value set per stage) |
| Interactive selection | `display()` with input cells / IPython widgets (Python only) |

> `notebookutils.runtime.context` does **not** expose parameter values — it returns execution
> metadata only (workspace/notebook/activity/user IDs, pipeline-vs-interactive flags).

## Unity Catalog namespace → Lakehouse schema

```python
# Databricks (3-level: catalog.schema.table)
# df = spark.read.table("prod.silver.customers")

# Fabric (catalog dropped; Lakehouse context provides it — 2-level)
df = spark.read.table("silver.customers")
```

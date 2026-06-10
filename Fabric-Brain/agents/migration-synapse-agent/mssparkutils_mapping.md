# `mssparkutils` → `notebookutils` & Connectivity Mapping

`mssparkutils` and `notebookutils` share the same API surface in most cases — the **namespace** is
the primary change. The main exception is `env` → `runtime`.

## Namespace rename

| Synapse (`mssparkutils`) | Fabric (`notebookutils`) | Note |
|---|---|---|
| `mssparkutils.fs.*` | `notebookutils.fs.*` | Same API |
| `mssparkutils.notebook.*` | `notebookutils.notebook.*` | Same API |
| `mssparkutils.credentials.*` | `notebookutils.credentials.*` | See Linked Service mapping below |
| `mssparkutils.env.*` | `notebookutils.runtime.*` | ⚠️ Namespace **renamed** |
| `mssparkutils.session.*` | `notebookutils.session.*` | Same API |

### `env` → `runtime`
```python
# Synapse
# workspace = mssparkutils.env.getWorkspaceName()

# Fabric (context dict)
workspace = notebookutils.runtime.context["workspaceName"]
```

## Linked Service → Data Connection / Shortcut / Key Vault

Linked Services have **no direct REST equivalent**. Replace by purpose:

| Linked Service purpose | Fabric replacement |
|---|---|
| External database/service | **Data Connection** (reconfigure credentials + endpoint) |
| ADLS Gen2 / Blob storage mount | **OneLake Shortcut** |
| Secret retrieval | `notebookutils.credentials.getSecret(keyVaultUrl, secretName)` |

```python
# Synapse — Linked Service credential
# conn = mssparkutils.credentials.getConnectionStringOrCreds("MyLinkedService")

# Fabric — Key Vault secret
conn = notebookutils.credentials.getSecret("https://myvault.vault.azure.net/", "my-secret")
```

## `spark.read.synapsesql()` replacement (Gotcha G1)

No Fabric equivalent. Replace with one of:
- **OneLake Shortcut read** — point a Lakehouse shortcut at the data, read via `spark.read.table(...)`.
- **JDBC** — connect to the Fabric Warehouse SQL endpoint.
- **Data Pipeline** — copy activity from the source.

## Dedicated SQL Pool DDL → Fabric Warehouse DDL

```sql
-- Synapse (remove distribution hints + columnstore index clause)
-- CREATE TABLE dbo.Fact (...) WITH (DISTRIBUTION = HASH(id), CLUSTERED COLUMNSTORE INDEX);

-- Fabric Warehouse
CREATE TABLE dbo.Fact (...);
```

## Variable Library for environment promotion

Avoid hardcoded IDs — centralize config in a **Variable Library** item:

```python
# Read config — works in notebooks
lib = notebookutils.variableLibrary.getLibrary("MigrationConfig")
lakehouse_name = lib.lakehouse_name
workspace_id   = lib.workspace_id

# ❌ WRONG — .get() does not exist
# notebookutils.variableLibrary.get("MigrationConfig", "lakehouse_name")
```

- Use **Value Sets** (`valueSets/dev.json`, `valueSets/prod.json`) to promote across environments without code changes.
- Boolean values are returned as **strings** — compare with `.lower() == "true"`, not `bool()`.
- In Data Pipelines, reference via `@pipeline().libraryVariables.<name>` (not `@variables()`).

# Databricks ↔ Fabric Coexistence — Interop Patterns

> **This file is about coexistence, not migration.** The rest of this agent assumes the workload
> moves to Fabric. Most Azure Databricks customers do not move it — they keep Unity Catalog as the
> source of truth and make the two platforms read and write each other's storage. Read this file
> **before** proposing a migration: three of the four patterns below require no change to
> Databricks code at all.

**Status:** documented from primary Microsoft Learn sources (fetched 2026-09-01) —
**not tenant-verified**. Do not present any of these as "verified" until a run proves it.
Pattern A is explicitly flagged **Beta** by Microsoft; re-check before committing to it.

---

## The four patterns

| | Pattern | Direction | Status | Minimum version |
|---|---|---|---|---|
| **A** | Unity Catalog **external location on OneLake** — Databricks stores managed tables in OneLake | Databricks → OneLake (**write**) | ⚠️ **Beta** | DBR **18.1+** or serverless |
| **B** | **OneLake catalog federation** — Databricks queries a Fabric Lakehouse/Warehouse | Fabric → Databricks (**read-only**) | GA | DBR **18.0+**, SQL warehouse 2025.40+ |
| **C** | **Mirrored Azure Databricks** — Fabric reads Unity Catalog | Databricks → Fabric (read) | GA | — |
| **D** | **OneLake shortcut** to Delta already in ADLS Gen2 | Databricks storage → Fabric (read) | GA | — |

A and B are Databricks-side features (configured in Unity Catalog). C and D are Fabric-side.
They compose — a single estate commonly runs C for the existing catalog and A for new output.

---

## A — Databricks writes managed tables into OneLake

Unity Catalog gains an **external location** whose storage type is OneLake. A catalog created with
`MANAGED LOCATION` on it stores its managed tables in OneLake instead of ADLS Gen2.

**Setup order** (all four steps are required):

1. Azure: an **Access Connector for Azure Databricks** (managed identity) or a service principal.
2. Fabric: create an **Azure Databricks Storage** item in the target workspace, and grant the
   identity **Administrator / Member / Contributor** on that workspace.
3. Unity Catalog: `CREATE STORAGE CREDENTIAL` referencing the access connector resource ID.
4. Unity Catalog: `CREATE EXTERNAL LOCATION`, storage type **OneLake**, pointing at the
   **ID-based ABFSS path**.

```text
abfss://<WorkspaceID>@onelake.dfs.fabric.microsoft.com/<DatabricksStorageID>/Files/
```

```sql
CREATE CATALOG my_onelake_catalog
MANAGED LOCATION '<onelake_external_location_path>';

CREATE TABLE my_onelake_catalog.default.my_table (id INT, name STRING);
```

**Prerequisites that are easy to miss:**

- Fabric tenant setting **"Users can create Azure Databricks Storage items"** must be on.
- Target workspace: **"Authenticate with OneLake user-delegated SAS tokens"**
  (Workspace settings → Delegated settings → OneLake settings).
- The Fabric workspace must have an **active capacity assignment** — otherwise `403 Forbidden`.

**Supported UC object types on a OneLake external location:** managed tables (**Delta *and*
Iceberg**), volumes, views, materialized views, streaming tables.

**Known constraints:** name-based paths are rejected at creation (GUIDs only); file event
notifications are not supported on OneLake paths — a *"skipped file events read"* warning during
`Test connection` is expected and does not indicate failure.

> 🚨 **Security caveat — read this before designing a multi-tenant estate.**
> Microsoft documents that **any principal with a non-viewer role (Member, Contributor,
> Administrator) on the Fabric workspace can read, write and delete data in the Azure Databricks
> Storage item — regardless of Unity Catalog grants.** Unity Catalog is *not* the effective
> authorization boundary here. The documented mitigation is organizational, not technical: use a
> **dedicated, restricted Fabric workspace** for the Azure Databricks Storage item, keep the
> member list minimal, and never mix it with user-facing assets. Treat this as a design
> constraint, not a footnote.

---

## B — Databricks reads Fabric (OneLake catalog federation)

A Unity Catalog **connection** of type `onelake` plus a **foreign catalog** bound to one Fabric
data item. Read-only; no copy.

```sql
CREATE CONNECTION <connection-name> TYPE onelake
OPTIONS (workspace '<workspace-id>', credential '<storage-credential-name>');

CREATE FOREIGN CATALOG <catalog-name> USING CONNECTION <connection-name>
OPTIONS (data_item '<data-item-id>', item_type 'Lakehouse');
```

`create_volume_for_lakehouse_files` (default `true`) exposes the Lakehouse `/Files` folder as a
read-only UC **volume** under the `onelake-folders` schema — the path to unstructured data.

**Fabric tenant settings required:** *Service principals can use Fabric APIs*, *Allow apps running
outside of Fabric to access data via OneLake*, *Use short-lived user-delegated SAS tokens*; plus
*Authenticate with OneLake user-delegated SAS tokens* on the workspace.

**Permission trap:** granting **"Read all with SQL analytics endpoint"** is **not sufficient** —
Databricks reads through the OneLake APIs and needs a OneLake read permission
(*Read all with Apache Spark* / *Read all OneLake data*).

**Cross-tenant:** the **service principal** auth method supports Fabric workspaces in a *different*
Azure tenant. This is the only pattern here that crosses a tenant boundary — relevant when the
Databricks estate belongs to a different entity than the Fabric tenant.

**Limitations (all documented):**

- Read-only — `SELECT` only, no writes.
- Only **Fabric Lakehouse and Warehouse** items are supported.
- **Complex datatypes (arrays, maps, structs) are not supported.** This is the constraint that
  most often disqualifies the pattern for semi-structured / API-payload data — check the schema
  before promising it.
- Views and materialized views are not supported.
- Dedicated access mode is not supported (standard access mode only).
- Columns differing only by case (`id` / `ID`) are not supported.
- Connection options (e.g. `workspace`) cannot be updated after creation — recreate.

---

## C — Fabric mirrors Unity Catalog

**No data movement and no replication.** Only the Databricks *catalog structure* is mirrored into
Fabric; the underlying data is reached through **shortcuts**. Fabric creates a *Mirrored Azure
Databricks* item plus an autogenerated **SQL analytics endpoint**, and Power BI can consume it in
**Direct Lake** mode.

Metadata sync (on by default — *"Automatically sync future catalog changes for the selected
schema"*) propagates: schema added, schema deleted, table added, table deleted. Whole catalog is
selected by default; tables and schemas can be excluded.

**Limitations:**

- **Materialized views and streaming tables are not displayed.**
- **External tables that are not Delta format are not displayed.**
- Data changes are not immediate — propagation ranges from a few seconds to several minutes.
- Read-only from Fabric.

---

## D — Shortcut to Delta already in ADLS Gen2

The lowest-friction option when the tables are already external Delta on ADLS Gen2 and catalog
semantics are not needed: a plain OneLake shortcut, no Databricks-side configuration.

> ⚠️ **DBFS root is not shortcut-able.** Tables living only in `dbfs:/` (unmanaged Delta on the
> workspace's default DBFS storage) cannot be reached by a shortcut, because DBFS root is a
> Microsoft-managed storage account not addressable via `abfss://` with customer credentials.
> Such tables must first be moved to an external location (ADLS Gen2 or a OneLake external
> location per pattern A). In an assessment, inventory "unmanaged Delta in DBFS" separately —
> it is the one category that blocks *every* zero-copy pattern here.

---

## Decision tree

### "Databricks is already in place — what do I do?"
```
├── UC managed tables, Fabric must read them       → C (mirroring): no copy, Direct Lake, UC stays authoritative
├── Delta already in ADLS Gen2, no catalog needed  → D (shortcut)
├── Unmanaged Delta in dbfs:/ only                 → ❌ blocked — relocate to an external location first
├── Databricks keeps writing, output lands in OneLake → A (UC external location on OneLake) — Beta + workspace-isolation caveat
├── Databricks must read Fabric-authored data      → B (OneLake catalog federation) — read-only, no complex types
├── The Databricks estate is in another tenant     → B with a service principal (only cross-tenant path here)
└── The workload itself must leave Databricks      → migration (see `instructions.md`)
```

---

## Effect on the migration rules

These patterns do not repeal the migration rules — they change *when* those rules apply.

| Rule in `instructions.md` | Still true when migrating | Under coexistence |
|---|---|---|
| Rule 2 — no DBFS, paths become OneLake | yes | still true, and now DBFS is also the one thing that blocks zero-copy interop |
| Rule 3 — UC 3-level collapses to 2-level | yes | **does not apply** — under C the catalog structure is mirrored, not collapsed |
| `catalog_compute_mapping.md` — "Delta Sharing → OneLake Shortcuts" | yes | incomplete: patterns A and B were not available when that table was written |

---

## Sources

| Pattern | Microsoft Learn | Doc date |
|---|---|---|
| A | `learn.microsoft.com/azure/databricks/connect/unity-catalog/cloud-storage/external-locations-onelake` | updated 2026-06-16 |
| B | `learn.microsoft.com/azure/databricks/query-federation/onelake` | updated 2026-08-12 |
| C | `learn.microsoft.com/fabric/mirroring/azure-databricks` | updated 2026-05-21 |

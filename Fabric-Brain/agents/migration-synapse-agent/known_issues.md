# Known Issues — Synapse → Fabric Migration

Quick-scan gotcha table (from skills-for-fabric `migration-gotchas`), then notes.

| # | Flag ID | Issue | Severity | Blocks? | Resolution |
|---|---------|-------|----------|---------|------------|
| G1 | `SYNAPSESQL_NO_EQUIVALENT` | `spark.read.synapsesql()` has no Fabric equivalent | High | Yes | OneLake shortcut read, Warehouse JDBC, or Data Pipeline |
| G2 | `LIBRARY_VERSION_CONFLICT` | Custom library conflicts with Fabric Runtime | Medium | Maybe | Pin compatible version in Environment, or use Fabric-native alternative |
| G3 | `DELTA_PROTOCOL_MISMATCH` | Delta protocol version incompatibility | High | Yes | Rewrite table with matching `minReaderVersion`/`minWriterVersion` |
| G4 | `SECURITY_MODEL_INCOMPATIBLE` | Managed identity / IP firewall not portable | Medium | Yes | Reconfigure as Workspace Identity + Managed Private Endpoints |
| G5 | `GPU_POOL_UNSUPPORTED` | GPU-accelerated Spark pools unavailable | High | Yes | Blocker — keep in Synapse or use Azure ML |
| G6 | `DOTNET_SPARK_UNSUPPORTED` | .NET for Spark (C#/F# SJDs) unsupported | High | Yes | Blocker — rewrite in PySpark or keep in Synapse |
| G7 | `NULLABLE_POOL_REFERENCE` | `bigDataPool`/`targetBigDataPool` is `null` (not missing) → `NoneType` crash | Medium | No | Use `(x.get("bigDataPool") or {}).get(...)` |
| G8 | `SESSION_CONFIG_IGNORED` | Some `%%configure` keys silently ignored | Low | No | Remove unsupported keys; use Environment for pool-level config |
| G9 | `SHORTCUT_CONNECTION_FAILED` | ADLS shortcut creation fails (connection/permission) | High | Partial | Verify credential type (Key > WorkspaceIdentity > OAuth2) and RBAC |

---

## Notes

### G1 — `spark.read.synapsesql()`
The single most common blocker. Replace with a Lakehouse **shortcut read**, a **JDBC** connection to
the Fabric Warehouse SQL endpoint, or a **Data Pipeline** copy. Never keep the call.

### G3 — Delta protocol mismatch
If a migrated table was written by a newer Delta protocol than the Fabric Runtime supports, reads
fail. Rewrite the table with matching `delta.minReaderVersion` / `delta.minWriterVersion`.

### G4 — Security model
Synapse managed identity and IP firewall rules are not portable. Reconfigure as a **Workspace
Identity** plus **Fabric Managed Private Endpoints**. Plan this as a separate workstream.

### G5 / G6 — Hard blockers
GPU Spark pools and .NET-for-Spark SJDs have **no Fabric equivalent**. Either keep the workload in
Synapse, move to Azure ML (GPU), or rewrite in PySpark (.NET).

### G7 — Null pool reference
The `bigDataPool` field is `null` (not absent) when a notebook has no attached pool. Guard with
`(x.get("bigDataPool") or {}).get(...)` to avoid a `NoneType` crash during inventory.

### G9 — Shortcut connection
ADLS shortcut creation fails on bad credentials/permissions. Credential preference order:
**Key > WorkspaceIdentity > OAuth2**. Verify RBAC on the storage account.

### Phase-order failures
Notebooks/SJDs binding before their Environment (Phase 0) or Lakehouse (Phase 1) exist will fail.
Always execute phases in order: 0 → 1 → 2 → 3.

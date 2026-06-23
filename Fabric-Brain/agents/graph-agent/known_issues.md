# Known Issues & Gotchas — Graph Agent (Graph in Microsoft Fabric, preview)

> Status: **Preview**. Behaviour, regions, and endpoints may change. Re-verify against MS Learn
> (`fabric/graph/*`) and the GraphModel REST reference.

---

## Tenant settings & capacity

| Requirement | Notes |
|-------------|-------|
| **Graph (preview)** tenant setting ON | Required for any Graph Model. Add **Ontology (preview)** for ontology-backed graphs. Wait 5–10 min after enabling. |
| Capacity **F2+** | Sufficient for graph + ontology + ontology MCP server (Learn-confirmed). No separate graph SKU. |
| Capacity **Active** | Resume if paused before push/refresh/query. |
| Region availability | Graph is region-limited (preview) — verify the workspace region against the Graph region list. |

Billing: **10 CU-seconds per CPU-second** of graph uptime (rounded up to minutes); min **100 GB**
graph storage billed as OneLake Cache. Auto-shuts down when idle.

---

## Common issues

### 1. Graph empty / `GraphNotRefreshable: Graph doesn't have valid content`
**Cause**: the Graph Model definition is empty — most often because an **ontology was deployed via
REST** (which doesn't trigger ontology→graph generation; only a UI save does).
**Fix**: build + push the Graph Model definition yourself, then RefreshGraph → `graph_definition_api.md`.

### 2. `ModelValidationError: DataSourceSchemaFetchFailed`
**Cause**: the `dataSources[].path` is wrong — e.g. `/dbo/` added to a non-schema lakehouse, or a
mistyped table.
**Fix**: use the real `row.location` from `GET /workspaces/{ws}/lakehouses/{lh}/tables`.

### 3. `InvalidJobType` on refresh
**Cause**: wrong job type. **Fix**: use `jobType=RefreshGraph` (not `Refresh`).

### 4. `RefreshAlreadyInProgress`
A refresh is already running. **Wait**; don't trigger another. Poll the running job to `Completed`.

### 5. Stale graph after upstream data changes
Graph does **not** auto-refresh. **Fix**: re-run `RefreshGraph` (full re-ingest, costs CU). Batch
data changes before refreshing.

### 6. Can't change the schema
Graph has **no schema evolution**. Adding/removing node/edge types or properties, or changing keys,
requires a **new graph model** + reload. Repoint any Graph Query Sets afterward.

### 7. Edge has no rows after refresh
**Cause**: the edge mapping table's key columns don't match the endpoints' keys (value or **data
type** mismatch). **Fix**: ensure `sourceNodeKeyColumns` / `destinationNodeKeyColumns` exist in the
mapping table and match the node key types exactly.

### 8. Graph Query Set created but empty
**Cause**: queries can't be pushed via API. **Fix**: add GQL in the portal UI.

### 9. Execute Query (beta) endpoint 404
The beta GQL execution endpoint path has shifted during preview. **Fix**: verify against the live
`rest/api/fabric/graphmodel/items` reference; meanwhile use portal Query mode or NL2GQL (Data Agent).

---

## Build order (strict)
```
1. Lakehouse Delta tables exist + populated
2. graphType + dataSources (real OneLake paths) + graphDefinition
3. updateDefinition on the GraphModel item  (ModelValidationError = bad path/binding)
4. RefreshGraph job  → Completed
5. Query (GQL / Graph Query Set / NL2GQL Data Agent)
```
> Never skip the real-path check (step 2) — wrong paths are the #1 push failure.

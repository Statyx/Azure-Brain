# Build & Push a Graph Model Definition via REST (+ the empty-ontology-graph fix)

> Use this when building a **standalone** graph from a Lakehouse via the API, **or** when an
> ontology was deployed via REST and its child Graph Model is **empty** (the ontology→graph
> generation only fires on a UI schema-save). Verified end-to-end on the CCE demo (12 nodes,
> 17 edges). Reference script: `Financial_Platform/src/deploy_graph.py`.

---

## Symptoms of an empty graph

| Symptom | Where |
|---------|-------|
| `The natural language query could not be processed.` | ontology NL2Ontology / MCP |
| `GraphNotRefreshable: Graph doesn't have valid content and cannot be refreshed.` | RefreshGraph job |
| Editor shows **"Build a graph", Nodes(0) Edges(0)** | Graph Model (Model mode) |

**Root cause** (ontology case): `updateDefinition` on the Ontology item does **not** trigger the
ontology→GraphModel generation (a UI save does). No ontology-side job regenerates it (all
`jobType` values return `InvalidJobType`). Fix: build the Graph Model definition yourself and push
it directly.

---

## The five definition parts

### `graphType.json`
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/graphType/1.0.0/schema.json",
  "nodeTypes": [
    { "alias": "<unique-numeric-string>", "labels": ["Estimate"],
      "primaryKeyProperties": ["estimate_id"],
      "properties": [ {"name":"estimate_id","type":"STRING"}, {"name":"estimated_total_eur","type":"FLOAT"} ] }
  ],
  "edgeTypes": [
    { "alias": "<unique>", "labels": ["EstimateInDiscipline"],
      "sourceNodeType": {"alias":"<Estimate-alias>"}, "destinationNodeType": {"alias":"<Discipline-alias>"},
      "properties": [ {"name":"estimate_id","type":"STRING"}, {"name":"discipline_id","type":"STRING"} ] }
  ]
}
```

### `dataSources.json`
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/dataSources/1.0.0/schema.json",
  "dataSources": [
    { "name": "<lakehouseId>_dim_disciplines", "type": "DeltaTable",
      "properties": { "path": "abfss://<wsId>@onelake.dfs.fabric.microsoft.com/<lakehouseId>/Tables/dim_disciplines" } }
  ]
}
```

### `graphDefinition.json`
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/graphDefinition/1.0.0/schema.json",
  "nodeTables": [
    { "nodeTypeAlias": "<Estimate-alias>", "id": "<guid>", "dataSourceName": "<lakehouseId>_fact_estimates",
      "propertyMappings": [ {"propertyName":"estimate_id","sourceColumn":"estimate_id"} ] }
  ],
  "edgeTables": [
    { "edgeTypeAlias": "<edge-alias>", "id": "<guid>", "edgeIdMapping": null,
      "dataSourceName": "<lakehouseId>_fact_estimates",
      "sourceNodeKeyColumns": ["estimate_id"],
      "propertyMappings": [ {"propertyName":"estimate_id","sourceColumn":"estimate_id"},
                            {"propertyName":"discipline_id","sourceColumn":"discipline_id"} ],
      "destinationNodeKeyColumns": ["discipline_id"] }
  ]
}
```

### `stylingConfiguration.json`
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/stylingConfiguration/1.0.0/schema.json",
  "modelLayout": { "positions": {}, "styles": {}, "pan": {"x":0.0,"y":0.0}, "zoomLevel": 1.0 },
  "visualFormat": null, "scenario": "Ontology"
}
```

### `.platform`
`metadata.type = "GraphModel"`, keep the existing displayName.

---

## Mapping a (tabular / ontology) model → graph definition

| Source concept | Graph |
|----------------|-------|
| Entity / key table (name) | `nodeType.labels[0]` |
| Key columns | `nodeType.primaryKeyProperties` |
| Columns | `nodeType.properties` + `nodeTable.propertyMappings` |
| Key table | `dataSource` + `nodeTable.dataSourceName` |
| Relationship / FK (name) | `edgeType.labels[0]` (source→target) |
| FK table | `edgeTable.dataSourceName` |
| Source keys | `edgeTable.sourceNodeKeyColumns` |
| Target FK cols | `edgeTable.destinationNodeKeyColumns` |

Types: `string→STRING`, `int64→INT`, `double→FLOAT`, `datetime→ZONED DATETIME`, `bool→BOOLEAN`.
Aliases are arbitrary unique strings (e.g. a hash of the type name) referenced consistently
between `graphType` and `graphDefinition`.

---

## CRITICAL: real OneLake path

```
GET /workspaces/{ws}/lakehouses/{lh}/tables  →  rows have .location (the abfss URI)
```
- Non-schema lakehouse → `.../Tables/<table>` (**NO `/dbo/`**).
- Schema-enabled → `.../Tables/<schema>/<table>`.
- Host `onelake.dfs.fabric.microsoft.com`.

Wrong path → push fails with `ModelValidationError: DataSourceSchemaFetchFailed` (one per bad table).
**Best practice**: read `row.location` directly instead of constructing the path.

---

## Push + refresh

1. `POST /workspaces/{ws}/items/{graphId}/updateDefinition` with the 5 parts → 202 → poll the op.
   - `op: Failed` + `ModelValidationError` names the failing data sources.
2. `POST /workspaces/{ws}/items/{graphId}/jobs/instances?jobType=RefreshGraph` → poll to `Completed`.
   - jobType is **`RefreshGraph`** (not `Refresh` → `InvalidJobType`). `RefreshAlreadyInProgress` = wait.
3. After ingestion: GQL / NL2Ontology return data. While ingesting: "Graph Model is not ready."

> **Learn an unknown definition format**: `getDefinition` on a *working* graph (even in another
> workspace — cross-workspace getDefinition works) reveals the exact part shapes. This is how the
> format above was reverse-engineered.

---

## Refresh after data changes
The graph does **not** auto-pick new Lakehouse rows. Re-run `RefreshGraph` (full re-ingest, costs CU).

## Cross-references
- `gql_reference.md` — query the graph once populated
- `known_issues.md` — gotchas
- `../ontology-agent/instructions.md` — the ontology that should have generated this graph

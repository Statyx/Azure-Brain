# Graph Model Deployment & GQL — Ontology Graph from the API (preview)

> ⚠️ **Moved.** This workaround is now owned by **`graph-agent`** — canonical reference:
> `../graph-agent/graph_definition_api.md`. Kept here as a legacy pointer for ontology context.


> **Why this file exists.** Deploying a Fabric **Ontology** via the REST API populates the
> entity/relationship schema but does **NOT** generate the child **Graph Model**. Only a
> **UI schema-save** triggers that generation. So an API-deployed ontology has an **empty
> graph** → NL2Ontology and the MCP server return nothing. This file documents the
> **API-only workaround**: build and push the Graph Model definition yourself, then refresh.
>
> Verified end-to-end on the CCE Financial Platform demo (12 entities, 17 relationships).
> Reference implementation: `Financial_Platform/src/deploy_graph.py`.

---

## Symptoms of the empty-graph problem

| Symptom | Where |
|---------|-------|
| `The natural language query could not be processed.` | `mcp_microsoft_fab_search_ontology` (even trivial questions) |
| `GraphNotRefreshable: Graph doesn't have valid content and cannot be refreshed.` | RefreshGraph job |
| Graph editor shows **"Build a graph / Select data from Fabric", Nodes(0) Edges(0)** | Graph Model item (Model mode) |
| `list_ontology_entity_types` works but every query fails | schema read OK, graph empty |

**Root cause**: `updateDefinition` on the Ontology item does not fire the ontology→GraphModel
sync (a UI save does). The child GraphModel is created with empty `graphType/dataSources/graphDefinition`.
There is **no ontology-side job** to regenerate it (all `jobType` values return `InvalidJobType`).

---

## The fix: build the Graph Model definition and push it directly

A Graph Model is a **"Graph in Microsoft Fabric"** item. Push its definition via
`POST /workspaces/{ws}/items/{graphId}/updateDefinition`, then ingest with a
`RefreshGraph` job. Five parts:

### 1. `graphType.json` — logical schema
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/graphType/1.0.0/schema.json",
  "nodeTypes": [
    { "alias": "<unique-numeric-string>", "labels": ["Estimate"],
      "primaryKeyProperties": ["estimate_id"],
      "properties": [ {"name":"estimate_id","type":"STRING"}, {"name":"estimated_total_eur","type":"FLOAT"} ] }
  ],
  "edgeTypes": [
    { "alias": "<unique-numeric-string>", "labels": ["EstimateInDiscipline"],
      "sourceNodeType": {"alias": "<Estimate-alias>"},
      "destinationNodeType": {"alias": "<Discipline-alias>"},
      "properties": [ {"name":"estimate_id","type":"STRING"}, {"name":"discipline_id","type":"STRING"} ] }
  ]
}
```

### 2. `dataSources.json` — one DeltaTable per source table
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/dataSources/1.0.0/schema.json",
  "dataSources": [
    { "name": "<lakehouseId>_dim_disciplines", "type": "DeltaTable",
      "properties": { "path": "abfss://<wsId>@onelake.dfs.fabric.microsoft.com/<lakehouseId>/Tables/dim_disciplines" } }
  ]
}
```

### 3. `graphDefinition.json` — bind types to tables
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/graphDefinition/1.0.0/schema.json",
  "nodeTables": [
    { "nodeTypeAlias": "<Estimate-alias>", "id": "<guid>",
      "dataSourceName": "<lakehouseId>_fact_estimates",
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

### 4. `stylingConfiguration.json`
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphInstance/definition/stylingConfiguration/1.0.0/schema.json",
  "modelLayout": { "positions": {}, "styles": {}, "pan": {"x":0.0,"y":0.0}, "zoomLevel": 1.0 },
  "visualFormat": null, "scenario": "Ontology"
}
```

### 5. `.platform` — `metadata.type = "GraphModel"`, keep the existing displayName.

---

## Mapping an ontology model → graph definition

| Ontology concept | Graph concept |
|------------------|---------------|
| Entity type (name) | `nodeType.labels[0]` = the name |
| Entity key columns | `nodeType.primaryKeyProperties` |
| Entity properties | `nodeType.properties` + `nodeTable.propertyMappings` |
| Entity Lakehouse table | a `dataSource` + `nodeTable.dataSourceName` |
| Relationship (name) | `edgeType.labels[0]` = the name, direction source→target |
| Relationship FK table | `edgeTable.dataSourceName` |
| Relationship source keys | `edgeTable.sourceNodeKeyColumns` |
| Relationship target FK cols | `edgeTable.destinationNodeKeyColumns` |

**Value-type mapping** (Lakehouse/TMSL → Graph): `string→STRING`, `int64→INT`,
`double→FLOAT`, `datetime→ZONED DATETIME`, `bool→BOOLEAN`.

**Aliases** are arbitrary unique strings (e.g. a hash of the type name). They must be
referenced consistently: `nodeTable.nodeTypeAlias` and `edge.sourceNodeType.alias`
point back to a `nodeType.alias`.

---

## CRITICAL: get the real OneLake table path

The dataSource `path` must be the **actual** OneLake location, not a guessed one:

```
GET /workspaces/{ws}/lakehouses/{lh}/tables   →  rows have .location (the abfss URI)
```

- **Non-schema lakehouse** → `.../Tables/<table>` (NO `/dbo/` segment).
- **Schema-enabled lakehouse** → `.../Tables/dbo/<table>` (or other schema).
- Host is `onelake.dfs.fabric.microsoft.com`.

A wrong path (e.g. adding `/dbo/` to a non-schema lakehouse) fails the push with
`ModelValidationError: DataSourceSchemaFetchFailed` — one error per bad table.

> Best practice: read `row.location` directly from the tables API instead of building the path.

---

## Push + refresh sequence

1. `POST /workspaces/{ws}/items/{graphId}/updateDefinition` with the 5 parts.
   - 202 → poll the operation (`Location`/`Operation-Location`). A bad model returns
     `op: Failed` with `ModelValidationError` and the specific failing data sources.
2. `POST /workspaces/{ws}/items/{graphId}/jobs/instances?jobType=RefreshGraph`
   - jobType is **`RefreshGraph`** (NOT `Refresh` → `InvalidJobType`).
   - `RefreshAlreadyInProgress` = a refresh is running; wait, don't re-trigger.
   - Poll `Location` until `Completed`. Ingestion can take a minute or two.
3. After ingestion: NL2Ontology works. While ingesting, the MCP returns
   `The Graph Model is not ready. Please try again later.`

> **Discovering the format from a known-good graph**: `getDefinition` on any *working*
> ontology graph (even in another workspace — cross-workspace getDefinition works) reveals
> the exact part shapes. This is how the format above was reverse-engineered.

---

## GQL query patterns (ISO/IEC 39075)

Node label = entity name, edge label = relationship name (whatever you set in `labels`).
Run in the Graph Model → **Query** mode, or let NL2Ontology generate them.

**Simple list**
```gql
MATCH (d:Discipline) RETURN d.discipline_id, d.discipline_name, d.category
```

**Multi-hop traceability** (one node, many relationships)
```gql
MATCH (e:Estimate {estimate_id: 'EST-BC7792B6'})-[:EstimateInWBS]->(w:WBS),
      (e)-[:EstimateInDiscipline]->(d:Discipline),
      (e)-[:EstimateInCountry]->(c:Country),
      (n:Norm)-[:NormForDiscipline]->(d)
RETURN e.estimate_id, w.wbs_code, d.discipline_name, d.category,
       c.country_name, n.norm_rate_min, n.norm_rate_max
```

**Join two facts via shared dimensions** (reverse edge with `<-[:X]-`)
```gql
MATCH (e:Estimate)-[:EstimateInDiscipline]->(d:Discipline)<-[:BenchmarkInDiscipline]-(b:Benchmark),
      (e)-[:EstimateInCountry]->(c:Country)<-[:BenchmarkInCountry]-(b)
WHERE e.estimated_rate_eur > 2 * b.normalized_rate_eur
RETURN e.estimate_id, d.discipline_id, c.country_code,
       e.estimated_rate_eur, b.normalized_rate_eur
ORDER BY e.estimated_rate_eur DESC
LIMIT 10
```

**Aggregation**
```gql
MATCH (e:Estimate)-[:EstimateInDiscipline]->(d:Discipline)
RETURN d.discipline_id, avg(e.estimated_total_eur) AS avg_total
ORDER BY avg_total DESC
```

---

## Consuming the graph

| Path | How |
|------|-----|
| **MCP server** (agent mode) | `.vscode/mcp.json` HTTP → `.../items/{ontologyId}/ontologyEndpoint`; tools `mcp_microsoft_fab_search_ontology` (NL2Ontology), `mcp_microsoft_fab_list_ontology_entity_types`. Interactive OAuth only. |
| **GQL in the portal** | Open the Graph Model → **Query** mode → paste GQL. |
| **GraphModel REST** | `Execute Query (beta)` operation on the GraphModel item (endpoint path is beta/unstable — verify against the live REST ref). |

---

## Capacity & tenant prerequisites

- **F2+** for Ontology, Graph, Graph Query Set, and the **MCP server** (Learn-confirmed).
  The "Data Agent on ontology needs F64" claim is **unverified** — don't assume it for
  MCP/NL2Ontology demos (F16 is fine). See `known_issues.md`.
- Tenant settings (wait 5–10 min after enabling): **Ontology item (preview)**,
  **Graph (preview)**, **Copilot and Azure OpenAI Service** (NL2Ontology uses the LLM —
  if off, queries fail to translate).
- Capacity must be **Active** (resume if paused) before ingest/query.

---

## Demo checklist

1. Capacity Active; correct tenant signed in.
2. Deploy the ontology (entity types + bindings + relationships + contextualizations).
3. **Build + push the Graph Model definition** (this file) and run `RefreshGraph`.
4. Wait for ingestion → test one `search_ontology` query (warm-up = auth + first-query latency).
5. Start the MCP server in VS Code agent mode for the live NL demo; keep the Graph Model
   **Query** view ready for the GQL visual.
6. Re-run `RefreshGraph` whenever upstream Lakehouse data changes (no auto-refresh).

## Cross-references
- `mcp_ontology.md` — MCP server setup + agent mode
- `relationships_contextualizations.md` — the ontology-side relationship model this graph mirrors
- `graph_queries.md` — broader GQL language reference
- `known_issues.md` — capacity/tenant gotchas, binding validation

# GQL — Graph Query Language Reference (Graph in Microsoft Fabric)

GQL (ISO/IEC 39075) is the standard query language for labeled property graphs. In Fabric it runs
against a **Graph Model** (standalone or ontology-backed). Queries can be saved in a **Graph Query
Set** (created via API, queries added in the UI) or run via the **Execute Query (beta)** API, the
portal **Query** mode, or **NL2GQL** through a graph Data Agent.

---

## Syntax basics

```gql
MATCH (source:NodeLabel)-[:EdgeLabel]->(target:NodeLabel)
WHERE source.prop = 'value'
RETURN source.prop, target.prop
ORDER BY source.prop ASC
LIMIT 10
```

- **Node label** = the node type's label (in an ontology-backed graph, the **entity name**).
- **Edge label** = the edge type's label (in an ontology-backed graph, the **relationship name**).
- Edge direction set when the graph is built (sourceNodeType → destinationNodeType).

| Direction | Meaning |
|-----------|---------|
| `-[:E]->` | outgoing (forward) |
| `<-[:E]-` | incoming (reverse) |
| `-[:E]-`  | undirected (both) |

| Clause | Purpose |
|--------|---------|
| `MATCH` | pattern match |
| `WHERE` | filter |
| `RETURN` | project columns |
| `ORDER BY` | sort |
| `LIMIT` | cap rows |
| `OPTIONAL MATCH` | left-join style (null if no match) |
| aggregations | `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `COLLECT` |

**Multi-pattern join** — comma-separate patterns that share a bound variable:
```gql
MATCH (a:Estimate)-[:EstimateInDiscipline]->(d:Discipline),
      (b:Benchmark)-[:BenchmarkInDiscipline]->(d)
RETURN a.estimate_id, b.benchmark_id, d.discipline_id
```

---

## Pattern examples

### 1-hop
```gql
MATCH (d:Discipline) RETURN d.discipline_id, d.discipline_name, d.category
```
```gql
MATCH (e:Estimate)-[:EstimateInWBS]->(w:WBS)
WHERE w.wbs_code = '50.04.01'
RETURN e.estimate_id, e.estimated_total_eur
```

### Multi-hop (chain patterns through a shared node)
```gql
MATCH (e:Estimate {estimate_id: 'EST-BC7792B6'})-[:EstimateInWBS]->(w:WBS),
      (e)-[:EstimateInDiscipline]->(d:Discipline),
      (e)-[:EstimateInCountry]->(c:Country),
      (n:Norm)-[:NormForDiscipline]->(d)
RETURN e.estimate_id, w.wbs_code, d.discipline_name, d.category,
       c.country_name, n.norm_rate_min, n.norm_rate_max
```

### Join two facts via shared dimensions (reverse edge)
```gql
MATCH (e:Estimate)-[:EstimateInDiscipline]->(d:Discipline)<-[:BenchmarkInDiscipline]-(b:Benchmark),
      (e)-[:EstimateInCountry]->(c:Country)<-[:BenchmarkInCountry]-(b)
WHERE e.estimated_rate_eur > 2 * b.normalized_rate_eur
RETURN e.estimate_id, d.discipline_id, c.country_code,
       e.estimated_rate_eur, b.normalized_rate_eur
ORDER BY e.estimated_rate_eur DESC
LIMIT 10
```

### Aggregation
```gql
MATCH (e:Estimate)-[:EstimateInDiscipline]->(d:Discipline)
RETURN d.discipline_id, avg(e.estimated_total_eur) AS avg_total
ORDER BY avg_total DESC
```
```gql
MATCH (cf:CashflowEntry)-[:CashflowInScenario]->(s:Scenario)
RETURN s.scenario_name, sum(cf.net_cashflow) AS total_net
```

### OPTIONAL MATCH (left join)
```gql
MATCH (e:Estimate)
OPTIONAL MATCH (e)-[:EstimateInDiscipline]->(d:Discipline)
RETURN e.estimate_id, d.discipline_name
```

### Generic traversal templates (any domain)
```gql
-- 3-hop hierarchy
MATCH (a:Parent)-[:HasChild]->(b:Child)-[:HasGrandchild]->(c:Grandchild)
RETURN a.name, b.name, c.name

-- counts per parent
MATCH (p:Parent)-[:HasChild]->(ch:Child)
RETURN p.name, COUNT(ch) AS children ORDER BY children DESC
```

---

## Graph algorithms

Graph in Fabric ships built-in algorithms (paths, centrality, communities) for analytics over the
ingested graph (e.g. shortest path between two nodes, most-connected hubs, community detection).
Use them for influence/criticality analysis and dependency mapping — invoke via GQL/graph engine
once the graph is refreshed.

---

## GQL vs KQL

| Aspect | GQL | KQL |
|--------|-----|-----|
| Source | Graph Model | KQL Database (Eventhouse) |
| Pattern | `MATCH`–`RETURN` (paths) | pipe `\|` (tabular) |
| Best for | relationships, hierarchies, multi-hop | time-series, real-time aggregations |
| Joins | implicit via edges | explicit `join` |
| Multi-hop | native (chain `->`) | nested joins |

- **GQL**: "all estimates under WBS X with their discipline and the applicable norm" (traversal).
- **KQL**: "sensor readings in the last 24h above threshold" (time-series) → `rti-kusto-agent`.

---

## Graph Query Set (saved queries)

```powershell
# Create the item (queries are added in the UI — no API to push query content)
$body = @{ displayName = "CCE_GraphQueries"; type = "GraphQuerySet" } | ConvertTo-Json
Invoke-WebRequest -Uri "$apiBase/workspaces/$WorkspaceId/items" -Method POST -Headers $headers -Body $body
```

> Graph Query Sets can be **created** via API, but **queries are added manually in the portal**.

---

## Execute Query (beta) API

The GraphModel REST surface exposes an `Execute Query (beta)` operation to run GQL programmatically
(returns rows). The exact endpoint path is beta and has shifted during preview — verify against the
live `rest/api/fabric/graphmodel/items` reference before scripting. NL2GQL (Data Agent) and the
portal Query mode are the stable consumption paths meanwhile.

---

## Schema design guidance

- A row of a **key table** → a node; a row of an **FK/mapping table** → an edge.
- Make something a **node type** if you traverse to/through it or group by it; keep it a **property**
  if it's descriptive metadata you only read.
- **Match key column data types** between a node's key and the FK columns used in edges — mismatches
  cause edge-creation failures.
- Keep only properties you query — fewer properties = faster, cheaper graph.
- Schema is **fixed** after build — plan before modeling; structural changes need a new graph.

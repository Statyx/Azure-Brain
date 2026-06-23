# graph-agent — Graph in Microsoft Fabric Agent

## Identity

**Name**: graph-agent
**Scope**: Everything about **Graph in Microsoft Fabric** as a first-class item — the labeled
property graph over OneLake data. Owns the Graph Model definition, GQL querying, graph
algorithms, Graph Query Sets, the Execute Query API, RefreshGraph ingestion, and Data Agents
that use a **graph** as their source (NL2GQL). Works whether the graph is **standalone**
(built directly from a Lakehouse) or **ontology-backed** (generated from an Ontology).
**Version**: 1.0 · **Status**: Preview

## What This Agent Owns

| Domain | Item / Tooling | Key APIs |
|--------|----------------|----------|
| **Graph Model definition** | `graphType` (nodeTypes/edgeTypes), `dataSources`, `graphDefinition` (nodeTables/edgeTables), `stylingConfiguration` | `updateDefinition` / `getDefinition` on the GraphModel item |
| **Standalone graph** | "Build a graph → Select data from Fabric" over Lakehouse Delta tables | GraphModel `Create` + `Update Graph Model Definition` |
| **Ingestion** | `RefreshGraph` job (full re-ingest of bound data) | `POST /items/{graphId}/jobs/instances?jobType=RefreshGraph` |
| **GQL querying** | ISO/IEC 39075 `MATCH`–`RETURN`, multi-hop, aggregations | Graph Query Set (UI) · `Execute Query (beta)` API |
| **Graph algorithms** | paths, centrality, communities | GQL + graph engine |
| **Data Agent (graph source)** | NL2GQL over a graph | Fabric Data Agent with graph data source |

## What This Agent Does NOT Own

- Ontology authoring (entity types, properties, bindings, relationships, contextualizations), NL2Ontology, the **Ontology MCP server** → `agents/ontology-agent/`
- Lakehouse / Delta tables (the graph's source data) → `agents/lakehouse-agent/`
- KQL / Eventhouse time-series → `agents/rti-kusto-agent/`
- Semantic model / Power BI → `agents/semantic-model-agent/`, `agents/report-builder-agent/`

> **Boundary with ontology-agent**: ontology = the *business / semantic* layer (what things
> mean, NL2Ontology). graph = the *storage & traversal* engine (how nodes/edges are stored
> and queried with GQL). An ontology **generates** a Graph Model; this agent owns that Graph
> Model's definition, refresh, and GQL — including the **API-only graph-population workaround**
> when an ontology is deployed via REST (which leaves the graph empty).

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — graph item model, standalone vs ontology-backed, build sequence, GQL rules, anti-patterns |
| `gql_reference.md` | GQL (ISO/IEC 39075) language — syntax, clauses, aggregations, multi-hop, 20+ examples, GQL vs KQL |
| `graph_definition_api.md` | Build + push the Graph Model definition via REST (the empty-graph-after-API workaround), RefreshGraph, OneLake path gotcha |
| `known_issues.md` | Graph-specific gotchas — empty graph, ModelValidationError, RefreshGraph, capacity/regions |

## Quick Start

1. Read `instructions.md` — graph item model + build sequence
2. Building a graph from a Lakehouse, or fixing an empty ontology graph? → `graph_definition_api.md`
3. Writing queries? → `gql_reference.md`
4. Stuck? → `known_issues.md`

## Key Insight

> **The graph is the traversal engine.** Nodes = rows of a key table; edges = rows of an FK
> table mapping source-key → target-key. Once ingested (RefreshGraph), GQL does multi-hop
> joins natively — no SQL joins, no copies, directly on OneLake. An ontology can sit on top
> to add business meaning + NL2Ontology, but the graph works standalone too.

## Cross-References
- `agents/ontology-agent/` — the semantic layer that generates a graph + NL2Ontology + MCP server
- `agents/lakehouse-agent/` — the OneLake Delta tables a graph binds to
- `agents/rti-kusto-agent/` — KQL/time-series (GQL vs KQL boundary)

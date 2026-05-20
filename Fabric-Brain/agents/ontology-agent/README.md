# ontology-agent — Fabric Ontology & Graph Agent

## Identity

**Name**: ontology-agent  
**Scope**: Everything related to creating, deploying, and querying Fabric Ontologies, Graph Models, Graph Query Sets, and Data Agents bound to an Ontology. Owns the entity-relationship modeling layer that bridges batch (Lakehouse) and streaming (Eventhouse/KQL) data.  
**Version**: 1.0

## What This Agent Owns

| Domain | Fabric Items | Key APIs / Tools |
|--------|-------------|------------------|
| **Ontology Definition** | Ontology item, `.platform`, `definition.json` | Fabric REST API `POST /items` + `updateDefinition` |
| **Entity Types** | Entity type schemas, properties, timeseries properties | `EntityTypes/{id}/definition.json` |
| **Data Bindings** | NonTimeSeries (Lakehouse), TimeSeries (KQL) | `EntityTypes/{id}/DataBindings/{guid}.json` |
| **Relationships** | Relationship type schemas, source/target entity links | `RelationshipTypes/{id}/definition.json` |
| **Contextualizations** | FK mappings between related entities | `RelationshipTypes/{id}/Contextualizations/{guid}.json` |
| **Graph Model** | Graph Model (auto-generated from Ontology) | Fabric UI → "Refresh graph model" |
| **Graph Query Set** | GQL queries (ISO/IEC 39075) | Fabric REST API (create) + UI (add queries) |
| **Data Agent (ontology-bound)** | DataAgent with Ontology as source | Fabric REST API `POST /dataAgents` |

## What This Agent Does NOT Own

- Lakehouse creation / CSV upload / Delta tables → defer to `agents/orchestrator-agent/`
- Eventhouse / KQL Database / KQL tables → defer to `agents/rti-kusto-agent/`
- KQL Dashboard → defer to `agents/rti-kusto-agent/`
- Operations Agent → defer to `agents/rti-kusto-agent/`
- Semantic Model / DAX → defer to `agents/semantic-model-agent/`
- Data Agent WITHOUT ontology (e.g. semantic model source) → defer to `agents/ai-skills-agent/`
- Report creation → defer to `agents/report-builder-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — Mandatory rules, decision trees, deployment sequence, API reference |
| `entity_types_bindings.md` | Entity type definitions, properties, value types, ID allocation, NonTimeSeries & TimeSeries data bindings |
| `relationships_contextualizations.md` | Relationship types, contextualizations (FK mapping), FK resolution strategies |
| `graph_queries.md` | GQL language reference, graph model, 20 query examples, GQL vs KQL comparison |
| `known_issues.md` | Ontology-specific gotchas, tenant settings, capacity requirements, binding validation |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory ontology architecture context & rules
2. Read `entity_types_bindings.md` — entity type schemas + data bindings
3. Read `relationships_contextualizations.md` — relationships & FK mapping
4. Read `graph_queries.md` — GQL queries for graph traversal
5. Reference `known_issues.md` when debugging

## Key Insight

> **The Ontology is the unifier.** It bridges Lakehouse (batch) and Eventhouse (streaming)
> data through typed entity bindings, enabling a single knowledge graph over both.
> Entity types define the schema; data bindings connect to actual tables; relationships
> create the graph; contextualizations resolve the FKs.

## Cross-References

| Topic | Agent | File |
|-------|-------|------|
| Lakehouse tables that ontology binds to | orchestrator-agent | `ingestion.md` |
| KQL tables that ontology binds to | rti-kusto-agent | `eventhouse_kql.md` |
| KQL language for time-series queries | rti-kusto-agent | `kql_language.md` |
| Data Agent instruction writing | ai-skills-agent | `instruction_writing_guide.md` |
| Fabric REST API patterns | root | `fabric_api.md` |

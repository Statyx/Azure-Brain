# ontology-agent — Fabric IQ Ontology

## Identity

**Scope:** the new TMDL-based Fabric Ontology experience: governed business context over live
Fabric sources, ontology-agent authoring, Data Agent context, optional graph materialization,
MCP consumption, ALM, and migration from the old experience.

## What this agent owns

| Domain | Current artifact |
| --- | --- |
| Ontology definition | TMDL/TMSL++ parts, Git integration, `getDefinition` / `updateDefinition` |
| Business model | Entities, properties, relationships, metrics, rules, namespaces, inheritance |
| Source grounding | Bindings to Lakehouse, Eventhouse/KQL, Warehouse, SQL, Mirrored DB, semantic models |
| Ontology agent | Discover → draft → validate → preview → apply |
| Data Agent integration | Ontology as governed context over underlying source-native queries |
| MCP | Ontology MCP endpoint and interactive-agent consumption |
| Migration | Old JSON experience → new TMDL experience |

Graph Model definition, refresh, GQL, and Graph Query Sets are owned by `graph-agent`.

## Load order

1. `instructions.md`
2. `new_experience_tmdl.md`
3. `versioning.md` for Git, lineage-safe changes, and promotion
4. `data_agent_context.md` when a Data Agent is involved
5. `mcp_ontology.md` when MCP is involved
6. `migration_old_to_new.md` for old items
7. `known_issues.md`

## Legacy files

The following files document the old ontology experience and must not drive a new project:

- `entity_types_bindings.md`
- `relationships_contextualizations.md`
- `graph_model_deployment.md`
- the old-experience sections of `known_issues.md`

They remain for migration, evidence, and maintenance until the old experience retires.

## Key insight

> Ontology unifies **business meaning and source routing**. It does not force every question
> through a graph. SQL/KQL/DAX remain the normal execution engines; Graph/GQL is an optional,
> selective traversal layer.

## Official sources

- [Ontology overview](https://learn.microsoft.com/fabric/iq/ontology/overview)
- [TMDL ontology definition](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/ontology-definition)
- [Ontology as Data Agent context](https://learn.microsoft.com/fabric/data-science/data-agent-ontology-sources)

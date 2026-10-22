# Migrate Old Ontology Experience to the New TMDL Experience

## Lifecycle

The new TMDL-based experience is the default for new ontology items. The old ontology experience
retires on **January 31, 2027**.

Old experience:

```text
definition.json
EntityTypes/{id}/definition.json
EntityTypes/{id}/DataBindings/{guid}.json
RelationshipTypes/{id}/definition.json
RelationshipTypes/{id}/Contextualizations/{guid}.json
```

New experience:

```text
database.tmdl
model.tmdl
tables/*.tmdl
entities/*.tmdl
entityRelationships.tmdl
relationships.tmdl
metrics/*.tmdl
namespaces/*.tmdl
rules/*.tmdl
```

The Fabric item type is `Ontology` in both generations. Inspect the definition parts; item type
alone cannot identify the generation.

## Supported migration path

Use the banner/action in an old ontology to **create a copy in the new experience**. The original
item remains available, and the new copy receives a new item ID.

The copy carries supported:

- entity types;
- properties and bindings;
- relationship types.

Review and recreate as needed:

- rules;
- Activator alerts;
- downstream consumer connections;
- optional graph materialization scope;
- new metrics, namespaces, inheritance, and reusable properties.

## Migration checklist

1. Inventory every consumer of the old ontology:
   - Fabric Data Agents;
   - dashboards and reports;
   - ontology MCP clients;
   - Graph Models and Graph Query Sets;
   - Foundry or Copilot Studio connections;
   - applications holding the ontology item ID.
2. Create the new-experience copy.
3. Retrieve both definitions and archive a migration diff.
4. Verify copied entities, properties, keys, relationships, and bindings.
5. Generate/reconnect semantic-model metrics where applicable.
6. Add rules, synonyms, namespaces, and inheritance deliberately.
7. Reconnect consumers to the new item ID.
8. For Data Agents, validate source-native SQL/KQL/DAX routing.
9. Materialize and refresh Graph only when traversal is required.
10. Run representative questions and permission tests.
11. Keep the old item read-only during acceptance.
12. Remove the old item only after all consumers are verified.

## Do not translate mechanically

These old rules do not carry forward unchanged:

| Old experience assumption | New experience rule |
| --- | --- |
| Every entity requires `entityIdParts` | Entity can be keyless; `keyProperty` is situational |
| Numeric ID ranges define stable identity | Preserve `lineageTag` |
| `NonTimeSeries` / `TimeSeries` JSON binding files | TMDL backing tables and property backing configurations |
| Contextualization JSON maps each relationship | Entity relationship binds to TOM relationship or junction table |
| Every ontology automatically has an instance graph | Graph materialization is optional and selective |
| Data Agent queries ontology with GQL | Ontology supplies context; Data Agent executes native SQL/KQL/DAX |

## Source

- [What is ontology — migrate from old experience](https://learn.microsoft.com/fabric/iq/ontology/overview#migrate-from-old-experience)

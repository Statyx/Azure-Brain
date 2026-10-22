# New Ontology Experience — TMDL/TMSL++ Authoring

> Current default for new Fabric ontology items. Microsoft documentation calls this the
> **new experience (TMDL-based)**. The old entity-type JSON format is covered only in
> `migration_old_to_new.md` and the legacy companion files.

## Why the model changed

The ontology is now a business-context model aligned with the Analysis Services tabular model.
It combines native TMDL objects with ontology-only TMSL++ extensions:

- native: tables, columns, measures, physical relationships, M expressions, metrics;
- ontology: entities, entity relationships, namespaces, rules, inheritance, reusable properties,
  synonyms, resource links, and source bindings.

The item supports Git integration, Deployment Pipelines, and the public
`getDefinition` / `updateDefinition` APIs.

## Definition layout

| Part | Purpose |
| --- | --- |
| `.platform` | Item metadata; `metadata.type = "Ontology"`, config version `2.0` |
| `database.tmdl` | Database container; compatibility level `1000000` |
| `model.tmdl` | Model plus `ref` statements |
| `tables/{name}.tmdl` | Backing tables, columns, Direct Lake partitions, DAX measures |
| `metrics/{name}.tmdl` | Top-level ontology metrics |
| `relationships.tmdl` | Physical TOM relationships between backing tables |
| `expressions.tmdl` | Shared M expressions such as a Direct Lake source |
| `entities/{namespace}#{name}.tmdl` | Entity types and their properties |
| `entityRelationships.tmdl` | Business relationships between entities |
| `namespaces/{namespace}.tmdl` | Namespace definitions; `default.tmdl` is reserved |
| `rules/{rule}.tmdl` | Natural-language business rules |

The smallest create/update definition can supply `.platform` and `database.tmdl`; the service
can synthesize `model.tmdl` and `namespaces/default.tmdl`. Prefer a full, explicit definition in
source control.

## Minimal skeleton

`database.tmdl`:

```tmdl
database
    compatibilityLevel: 1000000
```

`model.tmdl`:

```tmdl
model Model

ref table dim_sensor
ref entity Sensor
ref namespace default
```

`namespaces/default.tmdl`:

```tmdl
namespace default
    lineageTag: default
```

Use deterministic fake GUIDs in samples and deterministic generated GUIDs in project code.

## Backing tables and entities

`tables/dim_sensor.tmdl`:

```tmdl
table dim_sensor
    lineageTag: a0000000-0000-4000-a000-00000000000a

    column SensorId
        dataType: string
        sourceColumn: SensorId

    column SensorName
        dataType: string
        sourceColumn: SensorName

    partition dim_sensor = entity
        mode: directLake
        source
            entityName: dim_sensor
            schemaName: dbo
            expressionSource: DatabaseQuery
```

`entities/Sensor.tmdl`:

```tmdl
/// A physical sensor that produces operational observations.
entity Sensor
    lineageTag: a0000000-0000-4000-a000-00000000000b
    backingTable: dim_sensor
    keyProperty: SensorId

    property SensorId
        dataType: string
        lineageTag: a0000000-0000-4000-a000-00000000000c
        backingConfiguration
            valueColumn: dim_sensor.SensorId

    property SensorName
        dataType: string
        backingConfiguration
            valueColumn: dim_sensor.SensorName

    synonym probe
    synonym transducer
```

### Identity rules

- `lineageTag` is the stable identity across renames and patches.
- Entity types can be ontology-first and have no `backingTable`.
- Entity types can be keyless; use `keyProperty` for stable instances and graph eligibility.
- A new-experience entity key is not the old `entityIdParts` array.
- A property can use primitive, `Any`, complex, or `TimeSeries<T>` forms.
- Inheritance and reusable properties can have staged tenant rollout; validate on the target
  capacity before depending on them.

## Physical and business relationships

Use `relationships.tmdl` for the physical table relationship:

```tmdl
relationship rel_sensor_equipment
    fromColumn: dim_sensor.EquipmentId
    toColumn: dim_equipment.EquipmentId
```

Use `entityRelationships.tmdl` for business meaning:

```tmdl
entityRelationship SensorInstalledOnEquipment
    lineageTag: a0000000-0000-4000-a000-00000000000d
    fromEntity: Sensor
    toEntity: Equipment
    label: installed on
    backingConfiguration
        relationship: rel_sensor_equipment
```

A business relationship can be:

- backed by a physical TOM relationship; or
- backed by a junction table plus two physical relationships.

This replaces the old per-relationship `Contextualizations/{guid}.json` layout.

## Metrics, rules, and semantic-model alignment

Generating an ontology from a semantic model can bring across:

- tables and columns as entity types and properties;
- model relationships as ontology relationships;
- calculated columns;
- DAX measures as ontology metrics.

The semantic model remains the owner of DAX. Do not duplicate governed calculations as prompt
text or regenerate them independently.

Rules are natural-language business statements linked to entities, properties, and relationships.
Use them for shared governed context, not source-query implementation details.

TMDL round trips currently have limitations for projected/enrichment metric shapes. Retrieve a
working definition and preserve service-emitted parts rather than inventing unsupported keywords.

## Data binding principles

Supported sources include Eventhouse/KQL Database, Lakehouse, Warehouse, SQL Database, Mirrored
Database, Semantic Model, and supported OneLake constructs.

- Data stays in the source.
- Static entity data uses one static binding per entity.
- Time-series properties can use supported Lakehouse/Eventhouse sources.
- Lakehouse static tables must be managed and must not use unsupported Delta column mapping.
- Semantic-model generation requires Read + Build permission.
- When a source changes, validate schema mappings and refresh downstream context/graph as needed.

## Authoring workflow

1. Discover and validate source metadata.
2. Generate from a semantic model or draft with the ontology agent when useful.
3. Review names, synonyms, keys, metrics, rules, and relationships.
4. Preserve lineage tags.
5. `updateDefinition` with TMDL parts.
6. Poll the async operation.
7. `getDefinition` and diff the round trip.
8. Test one native query per bound source.
9. Materialize a graph only if traversal is a required outcome.

## Sources

- [Ontology definition (TMDL/new experience)](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/ontology-definition)
- [Data binding in ontology](https://learn.microsoft.com/fabric/iq/ontology/how-to-bind-data)
- [Generate an ontology from semantic models](https://learn.microsoft.com/fabric/iq/ontology/how-to-generate-from-semantic-models)
- [What is ontology](https://learn.microsoft.com/fabric/iq/ontology/overview)

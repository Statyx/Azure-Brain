# Ontology — Entity Types, Relationships & Data Bindings

## Overview

A Fabric Ontology is a knowledge graph that models domain entities, their properties, and the relationships between them. It bridges **batch data** (Lakehouse) and **streaming data** (KQL Database) through typed data bindings.

## Ontology Definition Structure

The ontology definition is a set of Base64-encoded JSON parts pushed via `updateDefinition`:

```
.platform                                     → metadata + config
definition.json                               → empty ({})
EntityTypes/{id}/definition.json              → entity type schema
EntityTypes/{id}/DataBindings/{guid}.json     → data source binding
RelationshipTypes/{id}/definition.json        → relationship schema
RelationshipTypes/{id}/Contextualizations/{guid}.json → FK mapping
```

## Creating an Ontology

### Step 1: Create the Item
```powershell
$ontologyBody = @{
    displayName = "OilGasRefineryOntology"
    description = "Ontology for entity types, relationships, and telemetry"
    type        = "Ontology"
}
$ontology = Invoke-FabricApi -Method Post `
    -Uri "$FabricApiBase/workspaces/$WorkspaceId/items" `
    -Body $ontologyBody -Token $fabricToken
$ontologyId = $ontology.id
```

### Step 2: Build and Push Definition
Use `updateDefinition` to set entity types, data bindings, relationships, and contextualizations as a single atomic operation.

## Entity Type Definition

```json
{
    "id": "1001",
    "namespace": "usertypes",
    "baseEntityTypeId": null,
    "name": "Refinery",
    "entityIdParts": ["2001"],
    "displayNamePropertyId": "2002",
    "namespaceType": "Custom",
    "visibility": "Visible",
    "properties": [
        {"id": "2001", "name": "RefineryId", "redefines": null, "baseTypeNamespaceType": null, "valueType": "String"},
        {"id": "2002", "name": "RefineryName", "redefines": null, "baseTypeNamespaceType": null, "valueType": "String"},
        {"id": "2003", "name": "Country", "redefines": null, "baseTypeNamespaceType": null, "valueType": "String"}
    ],
    "timeseriesProperties": []
}
```

### Property Value Types
| Type | KQL Equivalent | Description |
|------|---------------|-------------|
| `String` | `string` | Text |
| `BigInt` | `long` | 64-bit integer |
| `Double` | `real` | Double-precision float |
| `DateTime` | `datetime` | Timestamp |
| `Boolean` | `bool` | True/false |

### Timeseries Properties (KQL data)
Entity types that have real-time data include a `timeseriesProperties` array:
```json
{
    "timeseriesProperties": [
        {"id": "4001", "name": "Timestamp", "valueType": "DateTime"},
        {"id": "4002", "name": "ReadingValue", "valueType": "Double"},
        {"id": "4003", "name": "QualityFlag", "valueType": "String"},
        {"id": "4004", "name": "IsAnomaly", "valueType": "Boolean"}
    ]
}
```

## ID Allocation Plan

Use a deterministic ID scheme for maintainability:

| Range | Purpose |
|-------|---------|
| 1001 - 1099 | Entity Type IDs |
| 2001 - 2999 | Property IDs (allocated per entity, 100 per entity) |
| 3001 - 3099 | Relationship Type IDs |
| 4001 - 4099 | Timeseries Property IDs |

### Deterministic GUIDs for Bindings
Generate stable GUIDs from seed strings (enables idempotent re-pushes):
```powershell
function DeterministicGuid([string]$seed) {
    $hash = [System.Security.Cryptography.MD5]::Create().ComputeHash(
        [System.Text.Encoding]::UTF8.GetBytes($seed))
    return ([guid]::new($hash)).ToString()
}

$bindGuid = DeterministicGuid "NonTimeSeries-1001"
$tsBindGuid = DeterministicGuid "TimeSeries-1008"
$ctxGuid = DeterministicGuid "Ctx-3001"
```

## Data Bindings

### NonTimeSeries Binding (Lakehouse)
```json
{
    "id": "{bindGuid}",
    "dataBindingConfiguration": {
        "dataBindingType": "NonTimeSeries",
        "propertyBindings": [
            {"sourceColumnName": "RefineryId", "targetPropertyId": "2001"},
            {"sourceColumnName": "RefineryName", "targetPropertyId": "2002"}
        ],
        "sourceTableProperties": {
            "sourceType": "LakehouseTable",
            "workspaceId": "{workspaceId}",
            "itemId": "{lakehouseId}",
            "sourceTableName": "dimrefinery",
            "sourceSchema": "dbo"
        }
    }
}
```

### TimeSeries Binding (KQL Database)
```json
{
    "id": "{tsBindGuid}",
    "dataBindingConfiguration": {
        "dataBindingType": "TimeSeries",
        "timestampColumnName": "Timestamp",
        "propertyBindings": [
            {"sourceColumnName": "SensorId", "targetPropertyId": "2701"},
            {"sourceColumnName": "Timestamp", "targetPropertyId": "4001"},
            {"sourceColumnName": "ReadingValue", "targetPropertyId": "4002"},
            {"sourceColumnName": "QualityFlag", "targetPropertyId": "4003"},
            {"sourceColumnName": "IsAnomaly", "targetPropertyId": "4004"}
        ],
        "sourceTableProperties": {
            "sourceType": "KustoTable",
            "workspaceId": "{workspaceId}",
            "itemId": "{kqlDatabaseId}",
            "clusterUri": "{kqlClusterUri}",
            "databaseName": "{kqlDatabaseName}",
            "sourceTableName": "SensorReading"
        }
    }
}
```

## Relationships

### Relationship Type Definition
```json
{
    "namespace": "usertypes",
    "id": "3001",
    "name": "RefineryHasProcessUnit",
    "namespaceType": "Custom",
    "source": {"entityTypeId": "1001"},
    "target": {"entityTypeId": "1002"}
}
```

### Contextualization (FK Mapping)
Contextualizations tell the ontology HOW two entities are related by specifying the data binding:

```json
{
    "id": "{ctxGuid}",
    "dataBindingTable": {
        "workspaceId": "{workspaceId}",
        "itemId": "{lakehouseId}",
        "sourceTableName": "dimprocessunit",
        "sourceSchema": "dbo",
        "sourceType": "LakehouseTable"
    },
    "sourceKeyRefBindings": [
        {"sourceColumnName": "RefineryId", "targetPropertyId": "2001"}
    ],
    "targetKeyRefBindings": [
        {"sourceColumnName": "ProcessUnitId", "targetPropertyId": "2101"}
    ]
}
```

### FK Resolution Strategy
When building contextualizations:
1. **Strategy 1**: FK in source entity table (source has a column matching target PK name)
2. **Strategy 2**: FK in target entity table (target has a column matching source PK name — for "parent has children" relationships)
3. Try exact name match first, then pattern match (e.g., `FromProcessUnitId`, `PerformedByEmployeeId`)

## Part Assembly for updateDefinition

```powershell
$parts = @()

# .platform
$parts += @{ path = ".platform"; payload = (ToBase64 $platformJson); payloadType = "InlineBase64" }

# definition.json (always empty)
$parts += @{ path = "definition.json"; payload = (ToBase64 "{}"); payloadType = "InlineBase64" }

# Entity types + their bindings
foreach ($et in $entityTypes) {
    $parts += @{ path = "EntityTypes/$($et.id)/definition.json"; ... }
    $parts += @{ path = "EntityTypes/$($et.id)/DataBindings/$bindGuid.json"; ... }
    if ($et.timeseriesTable) {
        $parts += @{ path = "EntityTypes/$($et.id)/DataBindings/$tsBindGuid.json"; ... }
    }
}

# Relationships + contextualizations
foreach ($rel in $relationships) {
    $parts += @{ path = "RelationshipTypes/$($rel.id)/definition.json"; ... }
    $parts += @{ path = "RelationshipTypes/$($rel.id)/Contextualizations/$ctxGuid.json"; ... }
}

# Build payload manually (PS 5.1 ConvertTo-Json crashes with large payloads)
$partsJson = ($parts | ForEach-Object { '{"path":"' + $_.path + '","payload":"' + $_.payload + '","payloadType":"InlineBase64"}' }) -join ','
$bodyStr = '{"definition":{"parts":[' + $partsJson + ']}}'

# Push
Invoke-WebRequest -Uri "$apiBase/workspaces/$WorkspaceId/items/$OntologyId/updateDefinition" `
    -Method POST -Headers $headers -Body $bodyStr
```

## Typical Part Counts

| Ontology Size | Entity Types | Relationships | Total Parts |
|---------------|-------------|---------------|-------------|
| Small (5 entities) | ~15 parts | ~10 parts | ~27 |
| Medium (13 entities) | ~30 parts | ~30 parts | ~62 |
| Large (25+ entities) | ~55 parts | ~50+ parts | ~107+ |

The Oil & Gas Refinery ontology has **59 parts** (13 entity types + 15 relationships + bindings + contextualizations + platform + definition.json).

## Graph Model

The Graph Model is **auto-generated** from the Ontology when you click "Refresh graph model" in the preview. It can also be created programmatically as a separate Fabric item, but typically the ontology handles this.

## Generate Ontology from Semantic Model

In the Fabric UI:
1. Open the Semantic Model
2. Ribbon → "Generate Ontology"
3. Name the ontology
4. Creates entity types from tables, with initial relationships

Then customize: rename entity types, verify keys, configure relationship contextualizations.

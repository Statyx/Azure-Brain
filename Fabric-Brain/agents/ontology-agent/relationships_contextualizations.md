# Relationships & Contextualizations

---

## Overview

Relationships define **how entity types are connected** in the ontology graph. Contextualizations tell the ontology **how to resolve those connections** by specifying the FK columns in the source data.

```
Relationship Type   = "Refinery has ProcessUnit"  (schema)
Contextualization   = "join dimprocessunit.RefineryId → dimrefinery.RefineryId"  (data)
```

---

## Relationship Type Definition

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

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique relationship type ID (range 3001–3099) |
| `namespace` | string | Always `"usertypes"` |
| `name` | string | Descriptive name (convention: `SourceVerbTarget`) |
| `namespaceType` | string | Always `"Custom"` |
| `source.entityTypeId` | string | ID of the source entity type |
| `target.entityTypeId` | string | ID of the target entity type |

### Naming Convention

Use `{Source}{Verb}{Target}` pattern:
- `RefineryHasProcessUnit` — parent-child
- `EquipmentHasSensor` — composition
- `EmployeeAssignedToShift` — assignment
- `MaintenanceTaskPerformedBy` — action
- `SafetyIncidentReportedBy` — attribution
- `ChemicalUsedInProcessUnit` — usage

---

## Contextualization (FK Mapping)

A contextualization tells the ontology which data binding table contains the FK and how to resolve it.

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

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deterministic GUID (use `DeterministicGuid("Ctx-{relationshipId}")`) |
| `dataBindingTable` | object | The table that contains the FK column(s) |
| `sourceKeyRefBindings` | array | Columns that reference the **source** entity's key |
| `targetKeyRefBindings` | array | Columns that reference the **target** entity's key |

### How it Works

For a relationship `Refinery → ProcessUnit`:
- `dataBindingTable` = `dimprocessunit` (the target's table, which contains the FK)
- `sourceKeyRefBindings` = `RefineryId` column → maps to Refinery's `entityIdParts` property
- `targetKeyRefBindings` = `ProcessUnitId` column → maps to ProcessUnit's `entityIdParts` property

The contextualization says: *"In the `dimprocessunit` table, `RefineryId` links to the Refinery entity, and `ProcessUnitId` identifies the ProcessUnit entity."*

---

## FK Resolution Strategies

When building contextualizations, you need to determine **which table contains the FK**.

### Strategy 1: FK in Target Table (Most Common)

The **target entity's table** has a column referencing the source entity's key.

**Example**: `RefineryHasProcessUnit`
- Target table: `dimprocessunit` has a `RefineryId` column
- `dataBindingTable` → `dimprocessunit`

```
dimrefinery:         RefineryId | RefineryName | ...
dimprocessunit:      ProcessUnitId | ProcessUnitName | RefineryId | ...
                                                       ↑ FK to dimrefinery
```

### Strategy 2: FK in Source Table

The **source entity's table** has a column referencing the target entity's key.

**Example**: If `MaintenanceTask` table has an `EquipmentId` column:
- Source table: `dimmaintenancetask` has `EquipmentId`
- `dataBindingTable` → `dimmaintenancetask`

### Strategy 3: Pattern Matching for FK Column Names

When the FK column doesn't exactly match the target key name, look for patterns:
- `FromProcessUnitId` → maps to `ProcessUnitId`
- `PerformedByEmployeeId` → maps to `EmployeeId`
- `ReportedByEmployeeId` → maps to `EmployeeId`

**Rule**: Always verify the actual column name in the source table before building the contextualization.

---

## File Path for Contextualizations

```
RelationshipTypes/3001/definition.json                    ← relationship schema
RelationshipTypes/3001/Contextualizations/{ctxGuid}.json  ← FK mapping
```

Each relationship has exactly **one** contextualization (one FK resolution).

---

## Example: Oil & Gas Refinery Relationships

### 15 Relationships

| ID | Name | Source → Target | FK Location |
|----|------|----------------|-------------|
| 3001 | RefineryHasProcessUnit | Refinery → ProcessUnit | `dimprocessunit.RefineryId` |
| 3002 | ProcessUnitHasEquipment | ProcessUnit → Equipment | `dimequipment.ProcessUnitId` |
| 3003 | EquipmentHasSensor | Equipment → Sensor | `dimsensor.EquipmentId` |
| 3004 | SensorGeneratesReading | Sensor → SensorReading | `SensorReading.SensorId` (KQL) |
| 3005 | EmployeeAssignedToShift | Employee → Shift | `dimshift.EmployeeId` |
| 3006 | ShiftInProcessUnit | Shift → ProcessUnit | `dimshift.ProcessUnitId` |
| 3007 | MaintenanceTaskOnEquipment | MaintenanceTask → Equipment | `dimmaintenancetask.EquipmentId` |
| 3008 | MaintenanceTaskPerformedBy | MaintenanceTask → Employee | `dimmaintenancetask.PerformedByEmployeeId` |
| 3009 | SafetyIncidentInProcessUnit | SafetyIncident → ProcessUnit | `dimsafetyincident.ProcessUnitId` |
| 3010 | SafetyIncidentReportedBy | SafetyIncident → Employee | `dimsafetyincident.ReportedByEmployeeId` |
| 3011 | ChemicalUsedInProcessUnit | ChemicalCompound → ProcessUnit | `dimchemicalcompound.ProcessUnitId` |
| 3012 | EnvironmentalReadingBySensor | EnvironmentalReading → Sensor | `EnvironmentalReading.SensorId` (KQL) |
| 3013 | ProductionBatchInProcessUnit | ProductionBatch → ProcessUnit | `dimproductionbatch.ProcessUnitId` |
| 3014 | QualityTestOnBatch | QualityTest → ProductionBatch | `dimqualitytest.BatchId` |
| 3015 | QualityTestPerformedBy | QualityTest → Employee | `dimqualitytest.PerformedByEmployeeId` |

---

## Building Contextualizations Step by Step

### Step 1: Identify the Relationship
```
RefineryHasProcessUnit: Refinery (1001) → ProcessUnit (1002)
```

### Step 2: Find the FK Column
Look at the target table (`dimprocessunit`). Does it have a column matching the source key (`RefineryId`)? 
- **Yes** → strategy 1, `dataBindingTable` = `dimprocessunit`

### Step 3: Build the Contextualization JSON
```json
{
    "id": "DeterministicGuid('Ctx-3001')",
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

### Step 4: Verify
- `sourceColumnName` in `sourceKeyRefBindings` must exist in `dimprocessunit`
- `targetPropertyId` "2001" must be in entity type 1001's `entityIdParts`
- `sourceColumnName` in `targetKeyRefBindings` must exist in `dimprocessunit`
- `targetPropertyId` "2101" must be in entity type 1002's `entityIdParts`

---

## Common Contextualization Patterns

### Parent-Child (1:N)
```
Refinery → ProcessUnit
dataBindingTable: child table (dimprocessunit)
sourceKeyRefBindings: parent FK column (RefineryId) → parent key property
targetKeyRefBindings: child PK column (ProcessUnitId) → child key property
```

### Assignment (N:M via dimension)
```
Employee → Shift
dataBindingTable: assignment table (dimshift)
sourceKeyRefBindings: employee FK column (EmployeeId) → employee key property
targetKeyRefBindings: shift PK column (ShiftId) → shift key property
```

### Action Attribution
```
MaintenanceTask → Employee (PerformedBy)
dataBindingTable: task table (dimmaintenancetask)
sourceKeyRefBindings: task PK column (TaskId) → task key property
targetKeyRefBindings: employee FK column (PerformedByEmployeeId) → employee key property
```

> **Note**: For "PerformedBy" or "ReportedBy" patterns, the FK column name often has a prefix. Always check the actual column name.

---

## Relationship Direction in Graph

The direction matters for GQL queries:

```gql
-- Forward direction (as defined)
MATCH (r:Refinery)-[:RefineryHasProcessUnit]->(pu:ProcessUnit)

-- Reverse direction (traversing backwards)
MATCH (pu:ProcessUnit)<-[:RefineryHasProcessUnit]-(r:Refinery)

-- Undirected (either direction)
MATCH (r:Refinery)-[:RefineryHasProcessUnit]-(pu:ProcessUnit)
```

**Convention**: Define relationships from parent → child or source → target. Use forward direction in standard queries.

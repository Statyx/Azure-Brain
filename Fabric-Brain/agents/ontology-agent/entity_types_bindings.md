kusto-agent# Entity Types & Data Bindings

---

## Entity Type Definition

An entity type is the schema for a class of domain objects (e.g., Refinery, Sensor, Employee).

### Full Structure

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
        {"id": "2003", "name": "Country", "redefines": null, "baseTypeNamespaceType": null, "valueType": "String"},
        {"id": "2004", "name": "Capacity", "redefines": null, "baseTypeNamespaceType": null, "valueType": "BigInt"}
    ],
    "timeseriesProperties": []
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique entity type ID (e.g., `"1001"`) |
| `namespace` | string | Always `"usertypes"` for custom types |
| `name` | string | Entity type name (e.g., `"Refinery"`) |
| `entityIdParts` | string[] | Property IDs that form the unique key — **MANDATORY** |
| `displayNamePropertyId` | string | Property ID shown as display label |
| `namespaceType` | string | Always `"Custom"` |
| `visibility` | string | `"Visible"` or `"Hidden"` |
| `properties` | array | List of property definitions |
| `timeseriesProperties` | array | Timeseries property definitions (for streaming data) |

### Property Value Types

| Value Type | KQL Equivalent | SQL Equivalent | Description |
|-----------|---------------|----------------|-------------|
| `String` | `string` | `nvarchar` | Text |
| `BigInt` | `long` | `bigint` | 64-bit integer |
| `Double` | `real` | `float` | Double-precision float |
| `DateTime` | `datetime` | `datetime2` | Timestamp |
| `Boolean` | `bool` | `bit` | True/false |

### Property Definition

```json
{
    "id": "2001",
    "name": "RefineryId",
    "redefines": null,
    "baseTypeNamespaceType": null,
    "valueType": "String"
}
```

- `id` — unique property ID within the entity type
- `name` — property name (must match source column name for bindings)
- `valueType` — one of the value types above

---

## Timeseries Properties

Entity types with real-time (streaming) data include `timeseriesProperties`. These map to columns in a KQL table.

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

**Rules**:
- Timeseries properties use a separate ID range (4001+) from regular properties (2001+)
- One timeseries property must be `DateTime` — this is the timestamp column
- An entity can have BOTH `properties` (static/batch) and `timeseriesProperties` (streaming)

---

## ID Allocation Plan

Use deterministic, range-based IDs for reproducibility:

| Range | Purpose | Example |
|-------|---------|---------|
| 1001 – 1099 | Entity Type IDs | `1001` = Refinery, `1002` = ProcessUnit |
| 2001 – 2099 | Properties for entity 1001 | `2001` = RefineryId, `2002` = RefineryName |
| 2101 – 2199 | Properties for entity 1002 | `2101` = ProcessUnitId, `2102` = ProcessUnitName |
| 2201 – 2299 | Properties for entity 1003 | ... |
| 3001 – 3099 | Relationship Type IDs | `3001` = RefineryHasProcessUnit |
| 4001 – 4099 | Timeseries Property IDs | `4001` = Timestamp, `4002` = ReadingValue |

**Convention**: Entity `100N` gets properties in range `2{N-1}01 – 2{N-1}99` (zero-padded).

---

## Data Bindings

Data bindings connect entity type properties to actual table columns in Lakehouse or KQL databases.

### NonTimeSeries Binding (Lakehouse)

Binds entity properties to a Lakehouse Delta table (batch/dimension/fact data):

```json
{
    "id": "{bindGuid}",
    "dataBindingConfiguration": {
        "dataBindingType": "NonTimeSeries",
        "propertyBindings": [
            {"sourceColumnName": "RefineryId", "targetPropertyId": "2001"},
            {"sourceColumnName": "RefineryName", "targetPropertyId": "2002"},
            {"sourceColumnName": "Country", "targetPropertyId": "2003"},
            {"sourceColumnName": "Capacity", "targetPropertyId": "2004"}
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

**Key fields**:
- `id` — deterministic GUID (use `DeterministicGuid("NonTimeSeries-{entityTypeId}")`)
- `dataBindingType` — `"NonTimeSeries"`
- `propertyBindings` — maps source column → target property by ID
- `sourceType` — `"LakehouseTable"`
- `sourceTableName` — exact Delta table name in the Lakehouse
- `sourceSchema` — always `"dbo"` for Lakehouse

### TimeSeries Binding (KQL Database)

Binds timeseries properties to a KQL table (streaming/real-time data):

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

**Key fields**:
- `id` — deterministic GUID (use `DeterministicGuid("TimeSeries-{entityTypeId}")`)
- `dataBindingType` — `"TimeSeries"`
- `timestampColumnName` — column name used as the timestamp axis
- `sourceType` — `"KustoTable"`
- `clusterUri` — the Eventhouse `queryServiceUri` (get from Eventhouse properties)
- `databaseName` — KQL database display name

### Dual Bindings

An entity type can have **both** NonTimeSeries and TimeSeries bindings. Example: `Sensor` entity has:
- NonTimeSeries → `dimsensor` (Lakehouse) — static properties (name, type, thresholds)
- TimeSeries → `SensorReading` (KQL) — real-time readings (value, timestamp, anomaly)

This is the key power of the Ontology: **one entity spans both batch and streaming data**.

---

## Deterministic GUIDs

Generate stable GUIDs from seed strings for idempotent re-pushes:

```powershell
function DeterministicGuid([string]$seed) {
    $hash = [System.Security.Cryptography.MD5]::Create().ComputeHash(
        [System.Text.Encoding]::UTF8.GetBytes($seed))
    return ([guid]::new($hash)).ToString()
}

# Usage
$bindGuid   = DeterministicGuid "NonTimeSeries-1001"   # Refinery Lakehouse binding
$tsBindGuid = DeterministicGuid "TimeSeries-1008"       # SensorReading KQL binding
$ctxGuid    = DeterministicGuid "Ctx-3001"              # RefineryHasProcessUnit contextualization
```

**Why**: If you re-push the same definition, deterministic GUIDs prevent duplicate bindings. The same seed always produces the same GUID.

---

## File Path for Bindings

Bindings are stored under the entity type in the definition:

```
EntityTypes/1001/DataBindings/{nonTimeSeriesGuid}.json   ← Lakehouse binding
EntityTypes/1001/DataBindings/{timeSeriesGuid}.json      ← KQL binding (if applicable)
```

An entity with both binding types will have **two** files under `DataBindings/`.

---

## Creating the Ontology Item

```powershell
# Step 1: Create the item
$ontologyBody = @{
    displayName = "MyDomainOntology"
    description = "Ontology for entity types, relationships, and telemetry"
    type        = "Ontology"
} | ConvertTo-Json

$ontology = Invoke-WebRequest -Uri "$apiBase/workspaces/$WorkspaceId/items" `
    -Method POST -Headers $headers -Body $ontologyBody
$ontologyId = ($ontology.Content | ConvertFrom-Json).id

# Step 2: Build parts array (see instructions.md for full pattern)
# Step 3: Push via updateDefinition
```

---

## Example: Oil & Gas Refinery Entities

| ID | Entity Type | entityIdParts | Key Properties | Timeseries? |
|----|-------------|--------------|----------------|-------------|
| 1001 | Refinery | RefineryId | RefineryName, Country, Capacity | No |
| 1002 | ProcessUnit | ProcessUnitId | ProcessUnitName, UnitType, DesignCapacity | No |
| 1003 | Equipment | EquipmentId | EquipmentName, EquipmentType, Status, InstallDate | No |
| 1004 | Sensor | SensorId | SensorName, SensorType, Unit, MinThreshold, MaxThreshold | No |
| 1005 | Employee | EmployeeId | FullName, Role, Department, HireDate | No |
| 1006 | MaintenanceTask | TaskId | TaskType, Status, Priority, ScheduledDate, CompletedDate | No |
| 1007 | Shift | ShiftId | ShiftDate, ShiftType, StartTime, EndTime | No |
| 1008 | SensorReading | (timeseries) | SensorId | **Yes** (Timestamp, ReadingValue, QualityFlag, IsAnomaly) |
| 1009 | SafetyIncident | IncidentId | IncidentType, Severity, IncidentDate, Description | No |
| 1010 | ChemicalCompound | ChemicalId | ChemicalName, HazardClass, StorageTemp | No |
| 1011 | EnvironmentalReading | (timeseries) | SensorId | **Yes** (ReadingType, ReadingValue, Timestamp) |
| 1012 | ProductionBatch | BatchId | BatchNumber, ProductType, StartDate, EndDate | No |
| 1013 | QualityTest | TestId | TestType, Result, TestDate | No |

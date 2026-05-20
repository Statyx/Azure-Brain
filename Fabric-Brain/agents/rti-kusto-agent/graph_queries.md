# GQL — Graph Query Language Reference

## Overview

GQL (Graph Query Language) is the ISO/IEC 39075 standard for querying property graphs. In Fabric, GQL queries run against the **Graph Model** generated from an Ontology. Queries are stored in a **Graph Query Set** item.

> **API Limitation**: Graph Query Sets cannot be created or updated via API. Queries must be added manually in the Fabric UI.

## GQL Syntax

### Basic Pattern
```gql
MATCH (source:EntityType)-[:RELATIONSHIP_TYPE]->(target:EntityType)
RETURN source, target
```

### Direction
- `->` — outgoing edge
- `<-` — incoming edge
- `-` — undirected (matches both)

### Key Clauses
| Clause | Purpose | Example |
|--------|---------|---------|
| `MATCH` | Pattern match on graph | `MATCH (r:Refinery)` |
| `WHERE` | Filter conditions | `WHERE r.Country = "USA"` |
| `RETURN` | Select output columns | `RETURN r.Name, r.Country` |
| `ORDER BY` | Sort results | `ORDER BY r.Name ASC` |
| `LIMIT` | Restrict rows | `LIMIT 10` |
| `GROUP BY` | Aggregate | (used with `COUNT`, `SUM`, etc.) |

### Aggregation Functions
- `COUNT(x)` — Count elements
- `SUM(x)` — Sum numeric values
- `AVG(x)` — Average
- `MIN(x)`, `MAX(x)` — Min/max
- `COLLECT(x)` — Collect into list

---

## Graph Schema — Oil & Gas Refinery Example

### 13 Node Types (Entity Types)
```
Refinery, ProcessUnit, Equipment, Sensor, SensorReading,
Employee, MaintenanceTask, Shift, SafetyIncident,
ChemicalCompound, EnvironmentalReading, ProductionBatch, QualityTest
```

### 15 Edge Types (Relationships)
```
RefineryHasProcessUnit       : Refinery → ProcessUnit
ProcessUnitHasEquipment      : ProcessUnit → Equipment
EquipmentHasSensor           : Equipment → Sensor
SensorGeneratesReading       : Sensor → SensorReading
EmployeeAssignedToShift      : Employee → Shift
ShiftInProcessUnit           : Shift → ProcessUnit
MaintenanceTaskOnEquipment   : MaintenanceTask → Equipment
MaintenanceTaskPerformedBy   : MaintenanceTask → Employee
SafetyIncidentInProcessUnit  : SafetyIncident → ProcessUnit
SafetyIncidentReportedBy     : SafetyIncident → Employee
ChemicalUsedInProcessUnit    : ChemicalCompound → ProcessUnit
EnvironmentalReadingBySensor : EnvironmentalReading → Sensor
ProductionBatchInProcessUnit : ProductionBatch → ProcessUnit
QualityTestOnBatch           : QualityTest → ProductionBatch
QualityTestPerformedBy       : QualityTest → Employee
```

---

## Query Examples

### Basic Queries

#### 1. List All Refineries
```gql
MATCH (r:Refinery)
RETURN r.RefineryName, r.Country, r.Capacity
```

#### 2. Process Units for a Refinery
```gql
MATCH (r:Refinery)-[:RefineryHasProcessUnit]->(pu:ProcessUnit)
WHERE r.RefineryName = "Houston Refinery"
RETURN pu.ProcessUnitName, pu.UnitType, pu.DesignCapacity
```

#### 3. Equipment in a Process Unit
```gql
MATCH (pu:ProcessUnit)-[:ProcessUnitHasEquipment]->(eq:Equipment)
WHERE pu.ProcessUnitName = "Crude Distillation Unit"
RETURN eq.EquipmentName, eq.EquipmentType, eq.Status, eq.InstallDate
```

#### 4. Sensors on Equipment
```gql
MATCH (eq:Equipment)-[:EquipmentHasSensor]->(s:Sensor)
WHERE eq.EquipmentName = "CDU Heat Exchanger"
RETURN s.SensorName, s.SensorType, s.Unit, s.MinThreshold, s.MaxThreshold
```

#### 5. Employee Shift Assignments
```gql
MATCH (e:Employee)-[:EmployeeAssignedToShift]->(sh:Shift)
RETURN e.FullName, e.Role, sh.ShiftDate, sh.ShiftType, sh.StartTime, sh.EndTime
ORDER BY sh.ShiftDate DESC
LIMIT 20
```

#### 6. Maintenance History for Equipment
```gql
MATCH (mt:MaintenanceTask)-[:MaintenanceTaskOnEquipment]->(eq:Equipment)
RETURN eq.EquipmentName, mt.TaskType, mt.Status, mt.Priority, mt.ScheduledDate, mt.CompletedDate
ORDER BY mt.ScheduledDate DESC
```

#### 7. Safety Incidents by Process Unit
```gql
MATCH (si:SafetyIncident)-[:SafetyIncidentInProcessUnit]->(pu:ProcessUnit)
RETURN pu.ProcessUnitName, si.IncidentType, si.Severity, si.IncidentDate, si.Description
ORDER BY si.IncidentDate DESC
```

#### 8. Chemicals Used in Process Units
```gql
MATCH (cc:ChemicalCompound)-[:ChemicalUsedInProcessUnit]->(pu:ProcessUnit)
RETURN pu.ProcessUnitName, cc.ChemicalName, cc.HazardClass, cc.StorageTemp
```

#### 9. Production Batches with Quality Tests
```gql
MATCH (pb:ProductionBatch)-[:ProductionBatchInProcessUnit]->(pu:ProcessUnit),
      (qt:QualityTest)-[:QualityTestOnBatch]->(pb)
RETURN pu.ProcessUnitName, pb.BatchNumber, pb.ProductType, qt.TestType, qt.Result, qt.TestDate
ORDER BY qt.TestDate DESC
```

#### 10. Environmental Readings by Sensor
```gql
MATCH (er:EnvironmentalReading)-[:EnvironmentalReadingBySensor]->(s:Sensor)
RETURN s.SensorName, er.ReadingType, er.ReadingValue, er.Timestamp
ORDER BY er.Timestamp DESC
LIMIT 50
```

### Advanced Queries

#### 11. Full Equipment Hierarchy (3-hop path)
```gql
MATCH (r:Refinery)-[:RefineryHasProcessUnit]->(pu:ProcessUnit)-[:ProcessUnitHasEquipment]->(eq:Equipment)
RETURN r.RefineryName, pu.ProcessUnitName, eq.EquipmentName, eq.Status
ORDER BY r.RefineryName, pu.ProcessUnitName
```

#### 12. Equipment → Sensors → Latest Readings (4-hop)
```gql
MATCH (eq:Equipment)-[:EquipmentHasSensor]->(s:Sensor)-[:SensorGeneratesReading]->(sr:SensorReading)
WHERE eq.Status = "Running"
RETURN eq.EquipmentName, s.SensorName, sr.ReadingValue, sr.Timestamp, sr.IsAnomaly
ORDER BY sr.Timestamp DESC
LIMIT 100
```

#### 13. Anomalous Sensor Readings
```gql
MATCH (eq:Equipment)-[:EquipmentHasSensor]->(s:Sensor)-[:SensorGeneratesReading]->(sr:SensorReading)
WHERE sr.IsAnomaly = true
RETURN eq.EquipmentName, s.SensorName, s.SensorType, sr.ReadingValue, sr.Timestamp, sr.QualityFlag
ORDER BY sr.Timestamp DESC
```

#### 14. Maintenance Tasks with Assigned Employees
```gql
MATCH (mt:MaintenanceTask)-[:MaintenanceTaskOnEquipment]->(eq:Equipment),
      (mt)-[:MaintenanceTaskPerformedBy]->(e:Employee)
WHERE mt.Status = "Pending"
RETURN eq.EquipmentName, mt.TaskType, mt.Priority, mt.ScheduledDate, e.FullName, e.Role
ORDER BY mt.Priority, mt.ScheduledDate
```

#### 15. Safety Incidents with Reporters
```gql
MATCH (si:SafetyIncident)-[:SafetyIncidentInProcessUnit]->(pu:ProcessUnit),
      (si)-[:SafetyIncidentReportedBy]->(e:Employee)
WHERE si.Severity = "High"
RETURN pu.ProcessUnitName, si.IncidentType, si.IncidentDate, si.Description, e.FullName
ORDER BY si.IncidentDate DESC
```

#### 16. Equipment Needing Maintenance (Overdue)
```gql
MATCH (mt:MaintenanceTask)-[:MaintenanceTaskOnEquipment]->(eq:Equipment)
WHERE mt.Status = "Overdue"
RETURN eq.EquipmentName, eq.EquipmentType, mt.TaskType, mt.Priority, mt.ScheduledDate
ORDER BY mt.ScheduledDate
```

#### 17. Shift Coverage by Process Unit
```gql
MATCH (e:Employee)-[:EmployeeAssignedToShift]->(sh:Shift)-[:ShiftInProcessUnit]->(pu:ProcessUnit)
RETURN pu.ProcessUnitName, sh.ShiftDate, sh.ShiftType, COUNT(e) AS StaffCount
ORDER BY sh.ShiftDate DESC, pu.ProcessUnitName
```

#### 18. Quality Test Results per Product Type
```gql
MATCH (qt:QualityTest)-[:QualityTestOnBatch]->(pb:ProductionBatch)
RETURN pb.ProductType, qt.TestType, COUNT(qt) AS TestCount,
       SUM(CASE WHEN qt.Result = "Pass" THEN 1 ELSE 0 END) AS Passed,
       SUM(CASE WHEN qt.Result = "Fail" THEN 1 ELSE 0 END) AS Failed
```

#### 19. Cross-Domain: Employee Workload (Maintenance + Shifts + Quality)
```gql
MATCH (e:Employee)
OPTIONAL MATCH (mt:MaintenanceTask)-[:MaintenanceTaskPerformedBy]->(e)
OPTIONAL MATCH (e)-[:EmployeeAssignedToShift]->(sh:Shift)
RETURN e.FullName, e.Role,
       COUNT(DISTINCT mt) AS MaintenanceTasks,
       COUNT(DISTINCT sh) AS ShiftsAssigned
ORDER BY MaintenanceTasks DESC
```

#### 20. Full Refinery Overview (All Entity Counts)
```gql
MATCH (r:Refinery)-[:RefineryHasProcessUnit]->(pu:ProcessUnit)
OPTIONAL MATCH (pu)-[:ProcessUnitHasEquipment]->(eq:Equipment)
OPTIONAL MATCH (eq)-[:EquipmentHasSensor]->(s:Sensor)
RETURN r.RefineryName,
       COUNT(DISTINCT pu) AS ProcessUnits,
       COUNT(DISTINCT eq) AS Equipment,
       COUNT(DISTINCT s) AS Sensors
ORDER BY r.RefineryName
```

---

## GQL vs KQL

| Aspect | GQL | KQL |
|--------|-----|-----|
| Data source | Graph Model (Ontology) | KQL Database (Eventhouse) |
| Query pattern | MATCH-RETURN (path-based) | Pipe model (tabular) |
| Best for | Relationships, hierarchies, connected data | Time-series, aggregations, real-time |
| API creation | ❌ Manual UI only | ✅ Kusto REST mgmt API |
| Item type | GraphQuerySet | N/A (queries in dashboard/agent) |

## Creating a Graph Query Set

Graph Query Sets can be created as Fabric items, but **queries must be added via the UI**:

```powershell
# Create the item
$gqsBody = @{
    displayName = "RefineryGraphQueries"
    description = "GQL queries for graph traversal"
    type        = "GraphQLApi"  # Note: actual type may vary
} | ConvertTo-Json
# Then open in Fabric UI to add queries
```

> **Known Limitation**: As of 2025, there is no public API to push individual GQL queries into a Graph Query Set. You must use the Fabric portal to create and edit queries.

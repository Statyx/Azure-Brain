# Eventhouse & KQL Database

## Architecture

```
Eventhouse (container)
└── KQL Database (auto-created, same name as Eventhouse)
    ├── SensorReading (table)
    ├── EquipmentAlert (table)
    ├── ProcessMetric (table)
    ├── PipelineFlow (table)
    └── TankLevel (table)
```

## Creating an Eventhouse

```powershell
$eventhouseBody = @{
    displayName = "RefineryTelemetryEH"
    type        = "Eventhouse"
    description = "Eventhouse for sensor telemetry streaming data"
}
$eventhouse = Invoke-FabricApi -Method Post `
    -Uri "$FabricApiBase/workspaces/$WorkspaceId/items" `
    -Body $eventhouseBody -Token $fabricToken
$eventhouseId = $eventhouse.id
```

The KQL Database is auto-provisioned with the Eventhouse. To find it:
```powershell
$kqlDatabases = Invoke-FabricApi -Method Get `
    -Uri "$FabricApiBase/workspaces/$WorkspaceId/kqlDatabases" -Token $fabricToken
$kqlDb = $kqlDatabases.value | Where-Object { $_.displayName -eq "RefineryTelemetryEH" }
$kqlDbId = $kqlDb.id

# Get query service URI from Eventhouse properties
$ehDetail = Invoke-FabricApi -Method Get `
    -Uri "$FabricApiBase/workspaces/$WorkspaceId/eventhouses/$eventhouseId" -Token $fabricToken
$queryServiceUri = $ehDetail.properties.queryServiceUri
```

## Kusto REST Management API

All table operations use the Kusto mgmt endpoint, NOT the Fabric REST API.

**Endpoint**: `{QueryServiceUri}/v1/rest/mgmt`

**Headers**:
```json
{
    "Authorization": "Bearer {kustoToken}",
    "Content-Type": "application/json; charset=utf-8"
}
```

**Body format**:
```json
{
    "db": "RefineryTelemetryEH",
    "csl": ".create-merge table SensorReading (SensorId:string, Timestamp:datetime, ReadingValue:real)"
}
```

## Creating KQL Tables

Use `.create-merge table` (idempotent — creates if new, merges schema if exists):

```
.create-merge table SensorReading
    (SensorId:string, EquipmentId:string, RefineryId:string,
     Timestamp:datetime, ReadingValue:real, MeasurementUnit:string,
     SensorType:string, QualityFlag:string, IsAnomaly:bool)

.create-merge table EquipmentAlert
    (AlertId:string, SensorId:string, EquipmentId:string, RefineryId:string,
     Timestamp:datetime, AlertType:string, Severity:string,
     ReadingValue:real, ThresholdValue:real, Message:string, IsAcknowledged:bool)

.create-merge table ProcessMetric
    (ProcessUnitId:string, RefineryId:string, Timestamp:datetime,
     ThroughputBPH:real, InletTemperatureF:real, OutletTemperatureF:real,
     PressurePSI:real, FeedRateBPH:real, YieldPercent:real, EnergyConsumptionMMBTU:real)

.create-merge table PipelineFlow
    (PipelineId:string, RefineryId:string, Timestamp:datetime,
     FlowRateBPH:real, PressurePSI:real, TemperatureF:real,
     ViscosityCp:real, IsFlowNormal:bool)

.create-merge table TankLevel
    (TankId:string, RefineryId:string, Timestamp:datetime,
     LevelBarrels:real, LevelPercent:real, TemperatureF:real,
     ProductId:string, IsOverflow:bool)
```

## Data Ingestion

### Inline Ingestion (small datasets, <64KB per batch)
```
.ingest inline into table SensorReading with (format='csv') <|
SN001,EQ001,REF001,2025-12-01T01:00:00,450.2,DegF,Temperature,Good,false
SN002,EQ001,REF001,2025-12-01T01:00:00,510.0,PSI,Pressure,Good,false
```

### Batch Ingestion Pattern (PowerShell)
```powershell
$batchSize = 50  # Kusto inline limit ~64KB per command
for ($i = 0; $i -lt $rows.Count; $i += $batchSize) {
    $batch = $rows[$i..([Math]::Min($i + $batchSize - 1, $rows.Count - 1))]
    $inlineData = $batch -join "`n"
    $cmd = ".ingest inline into table SensorReading with (format='csv') <|`n$inlineData"
    Invoke-KustoMgmt -Command $cmd
}
```

### Enrichment Pattern
Raw telemetry (SensorTelemetry.csv) often needs enrichment by joining with dimension tables:
```powershell
# Build lookup from dimension CSVs
$sensorLookup = @{}
Import-Csv "DimSensor.csv" | ForEach-Object {
    $sensorLookup[$_.SensorId] = @{
        EquipmentId = $_.EquipmentId
        SensorType  = $_.SensorType
        MinRange    = [double]$_.MinRange
        MaxRange    = [double]$_.MaxRange
    }
}
# Enrich each row before ingestion
foreach ($row in $rawData) {
    $sensor = $sensorLookup[$row.SensorId]
    $isAnomaly = ($value -lt $sensor.MinRange -or $value -gt $sensor.MaxRange)
    # Build enriched CSV line...
}
```

## Kusto Token Acquisition (PowerShell)

```powershell
# Try multiple resources in order (Fabric Eventhouse accepts various scopes)
$tokenResources = @($QueryServiceUri, "https://kusto.kusto.windows.net",
                      "https://help.kusto.windows.net", "https://api.fabric.microsoft.com")
foreach ($resource in $tokenResources) {
    try {
        $kustoToken = (Get-AzAccessToken -ResourceUrl $resource).Token
        break
    } catch { continue }
}
```

## Waiting for Database Ready

After Eventhouse creation, the KQL database may take time to provision:
```powershell
for ($wait = 1; $wait -le 6; $wait++) {
    try {
        Invoke-KustoMgmt -Command ".show database" | Out-Null
        break  # Ready
    } catch {
        Start-Sleep -Seconds 15  # Not ready yet
    }
}
```

## KQL Data Types

| KQL Type | Description | Example |
|----------|-------------|---------|
| `string` | Text | `"SN001"` |
| `datetime` | Timestamp | `2025-12-01T01:00:00` |
| `real` | Float/double | `450.2` |
| `long` | 64-bit integer | `550000` |
| `bool` | Boolean | `true`/`false` |
| `int` | 32-bit integer | `42` |
| `decimal` | High-precision decimal | `3.14159` |
| `timespan` | Duration | `1h`, `30m`, `15s` |
| `dynamic` | JSON/array | `{"key": "value"}` |
| `guid` | GUID | `00000000-0000-0000-0000-000000000000` |

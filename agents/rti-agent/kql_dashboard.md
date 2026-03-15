# KQL Dashboard (Real-Time Intelligence)

## Overview

A KQL Dashboard (type `KQLDashboard`) is a Fabric item that displays real-time visualizations from KQL database data. It uses a JSON definition format following the `RealTimeDashboard.json` schema.

## Creating a KQL Dashboard

### Step A: Create the Item

```powershell
$createBody = @{
    displayName = "RefineryTelemetryDashboard"
    type        = "KQLDashboard"
    description = "Real-Time Intelligence dashboard for telemetry monitoring"
} | ConvertTo-Json -Depth 5

$response = Invoke-WebRequest `
    -Uri "$apiBase/workspaces/$WorkspaceId/items" `
    -Method POST -Headers $headers -Body $createBody -UseBasicParsing

$dashboardId = ($response.Content | ConvertFrom-Json).id
```

### Step B: Upload Definition

```powershell
$updateBody = @{
    definition = @{
        parts = @(
            @{
                path        = "RealTimeDashboard.json"
                payload     = $dashJsonBase64
                payloadType = "InlineBase64"
            }
        )
    }
} | ConvertTo-Json -Depth 10

# Try type-specific endpoint first, then generic fallback
foreach ($endpoint in @(
    "$apiBase/workspaces/$WorkspaceId/kqlDashboards/$dashboardId/updateDefinition",
    "$apiBase/workspaces/$WorkspaceId/items/$dashboardId/updateDefinition"
)) {
    try {
        Invoke-WebRequest -Uri $endpoint -Method POST -Headers $headers -Body $updateBody -UseBasicParsing
        break  # Success
    } catch { continue }
}
```

## Dashboard Definition Schema

```json
{
    "$schema": "https://dataexplorer.azure.com/static/d/schema/20/dashboard.json",
    "schema_version": "20",
    "title": "Dashboard Name",
    "autoRefresh": {
        "enabled": true,
        "defaultInterval": "30s",
        "minInterval": "30s"
    },
    "dataSources": [
        {
            "id": "{guid}",
            "name": "RefineryTelemetryEH",
            "clusterUri": "{queryServiceUri}",
            "database": "RefineryTelemetryEH",
            "kind": "manual-kusto",
            "scopeId": "KustoDatabaseResource"
        }
    ],
    "pages": [
        {
            "id": "{guid}",
            "name": "Refinery Overview"
        }
    ],
    "tiles": [ /* see Tile Structure below */ ],
    "parameters": []
}
```

## Tile Structure

Each tile is an object with:

```json
{
    "id": "{guid}",
    "title": "Sensor Readings Over Time",
    "query": "SensorReading\n| summarize AvgReading = avg(ReadingValue) by bin(Timestamp, 15m), SensorType\n| order by Timestamp asc",
    "layout": { "x": 0, "y": 0, "width": 12, "height": 6 },
    "pageId": "{pageId}",
    "visualType": "line",
    "dataSourceId": "{dataSourceId}",
    "visualOptions": {
        "xColumn": { "type": "infer" },
        "yColumns": { "type": "infer" },
        "yAxisMinimumValue": { "type": "infer" },
        "yAxisMaximumValue": { "type": "infer" },
        "seriesColumns": { "type": "infer" },
        "hideLegend": false,
        "crossFilterDisabled": false,
        "hideTileTitle": false,
        "multipleYAxes": {
            "base": { "id": "-1", "columns": [], "yAxisScale": "linear" },
            "additional": []
        }
    },
    "usedParamVariables": []
}
```

## Visual Types

| Type | Use Case | KQL Pattern |
|------|----------|-------------|
| `line` | Time-series trends | `summarize ... by bin(Timestamp, interval)` |
| `bar` / `barchart` | Categorical comparison | `summarize ... by Category` |
| `pie` | Distribution / proportion | `summarize count() by Category` |
| `table` | Detailed records | `project col1, col2 \| take 100` |
| `map` | Geographical data | Must have `Latitude`, `Longitude` columns |
| `area` | Cumulative trends | Same as line, stacked optional |
| `scatter` | Correlation | Two numeric columns |
| `column` | Vertical bars | Similar to bar |

## Layout Grid

The dashboard uses a 24-column grid:
- `x`: Column position (0-23)
- `y`: Row position (0+, each unit ~50px)
- `width`: Columns wide (1-24)
- `height`: Rows tall (typically 5-6)

### Example 2x3 Layout
```
Row 0:  [Tile 1: x=0  w=12 h=6] [Tile 2: x=12 w=6  h=6] [Tile 3: x=18 w=6  h=6]
Row 6:  [Tile 4: x=0  w=8  h=6] [Tile 5: x=8  w=8  h=6] [Tile 6: x=16 w=8  h=6]
Row 12: [Tile 7: x=0  w=8  h=5] [Tile 8: x=8  w=8  h=5] [Tile 9: x=16 w=8  h=5]
Row 17: [Tile 10: x=0 w=12 h=5] [Tile 11: x=12 w=6 h=5] [Tile 12: x=18 w=6 h=5]
```

## Example Tiles (Oil & Gas Refinery)

### 1. Sensor Readings Over Time (line)
```kql
SensorReading
| summarize AvgReading = avg(ReadingValue) by bin(Timestamp, 15m), SensorType
| order by Timestamp asc
```

### 2. Equipment Alerts by Severity (pie)
```kql
EquipmentAlert
| summarize Count = count() by Severity
| order by Count desc
```

### 3. Top Sensors by Reading Count (table)
```kql
SensorReading
| summarize Readings = count(),
            AvgValue = round(avg(ReadingValue), 2),
            MinValue = round(min(ReadingValue), 2),
            MaxValue = round(max(ReadingValue), 2)
    by SensorId, SensorType, MeasurementUnit
| top 20 by Readings desc
```

### 4. Anomaly Detections (table)
```kql
SensorReading
| where IsAnomaly == true
| project Timestamp, SensorId, SensorType, ReadingValue, MeasurementUnit, QualityFlag, EquipmentId
| order by Timestamp desc
| take 100
```

### 5. Process Unit Throughput (line)
```kql
ProcessMetric
| summarize AvgThroughput = avg(ThroughputBPH), AvgYield = avg(YieldPercent)
    by bin(Timestamp, 1h), ProcessUnitId
| order by Timestamp asc
```

### 6. Current Tank Levels (table)
```kql
TankLevel
| summarize arg_max(Timestamp, *) by TankId
| project TankId, Timestamp, LevelBarrels, LevelPercent, TemperatureF, ProductId, IsOverflow
| order by LevelPercent desc
```

### 7. Map with Static Data
```kql
datatable(Name:string, Latitude:real, Longitude:real, City:string, Capacity:long) [
    "Gulf Coast Refinery", 29.7604, -95.3698, "Houston", 550000,
    "North Sea Refinery",  56.0234,  -3.7135, "Grangemouth", 550000
]
| project Name, Latitude, Longitude, City, Capacity
```

## Tenant Setting Required

The **"Create Real-Time dashboards"** tenant setting must be enabled in Admin Portal > Tenant settings > Real-Time Intelligence. Without this, the API returns `FeatureNotAvailable`.

## Handling Existing Dashboard

If the dashboard name already exists, the API returns an error with `ItemDisplayNameAlreadyInUse`. Look up the existing item and update its definition instead:

```powershell
$allItems = (Invoke-RestMethod -Uri "$apiBase/workspaces/$WorkspaceId/items" -Headers $headers).value
$existing = $allItems | Where-Object { $_.displayName -eq $DashboardName -and $_.type -eq 'KQLDashboard' }
$dashboardId = $existing.id
# Then proceed with updateDefinition...
```

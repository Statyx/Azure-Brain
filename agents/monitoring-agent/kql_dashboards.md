# KQL Operational Dashboards — Queries for Monitoring Fabric

## Overview

When Fabric streams data via EventStream to an Eventhouse, you can build KQL-based operational dashboards that monitor both the business data AND the infrastructure health. This file provides KQL query templates for common monitoring scenarios.

---

## Data Ingestion Monitoring

### Ingestion Rate Over Time
```kql
// Events ingested per minute over the last hour
SensorReading
| where timestamp > ago(1h)
| summarize EventCount = count() by bin(timestamp, 1m)
| render timechart with (title="Ingestion Rate (events/min)")
```

### Ingestion Lag Detection
```kql
// Detect ingestion lag: difference between event time and current time
SensorReading
| where timestamp > ago(10m)
| extend IngestionLagSeconds = datetime_diff('second', now(), timestamp)
| summarize 
    AvgLag = avg(IngestionLagSeconds),
    MaxLag = max(IngestionLagSeconds),
    P95Lag = percentile(IngestionLagSeconds, 95)
    by bin(timestamp, 1m)
| render timechart with (title="Ingestion Lag (seconds)")
```

### Data Gap Detection
```kql
// Find gaps in data ingestion (no events for more than 60 seconds)
SensorReading
| where timestamp > ago(1h)
| summarize LastEvent = max(timestamp) by bin(timestamp, 1m)
| sort by timestamp asc
| extend PreviousEvent = prev(timestamp)
| extend GapSeconds = datetime_diff('second', timestamp, PreviousEvent)
| where GapSeconds > 60
| project timestamp, GapSeconds
```

### Events Per Source
```kql
// Distribution of events by source (sensor, site, etc.)
SensorReading
| where timestamp > ago(1h)
| summarize EventCount = count() by site_id
| sort by EventCount desc
| render barchart with (title="Events by Site")
```

---

## Data Quality Monitoring

### Anomaly Detection
```kql
// Detect value anomalies using statistical boundaries
SensorReading
| where timestamp > ago(24h)
| summarize 
    AvgValue = avg(value),
    StdValue = stdev(value)
    by sensor_id
| join kind=inner (
    SensorReading
    | where timestamp > ago(1h)
) on sensor_id
| where value > AvgValue + 3 * StdValue or value < AvgValue - 3 * StdValue
| project timestamp, sensor_id, value, AvgValue, StdValue,
    Deviation = round((value - AvgValue) / StdValue, 2)
| sort by abs(Deviation) desc
| take 50
```

### Quality Score Distribution
```kql
// Percentage of "Good" vs "Bad" quality readings
SensorReading
| where timestamp > ago(1h)
| summarize 
    TotalCount = count(),
    GoodCount = countif(quality == "Good"),
    BadCount = countif(quality == "Bad")
| extend 
    GoodPct = round(100.0 * GoodCount / TotalCount, 1),
    BadPct = round(100.0 * BadCount / TotalCount, 1)
```

### Null/Missing Value Check
```kql
// Check for null or empty values in key columns
SensorReading
| where timestamp > ago(1h)
| summarize 
    TotalRows = count(),
    NullSensorId = countif(isempty(sensor_id)),
    NullValue = countif(isnull(value)),
    NullTimestamp = countif(isnull(timestamp))
| extend 
    HasIssues = NullSensorId > 0 or NullValue > 0 or NullTimestamp > 0
```

### Duplicate Detection
```kql
// Find duplicate events (same sensor + timestamp)
SensorReading
| where timestamp > ago(1h)
| summarize Count = count() by sensor_id, timestamp
| where Count > 1
| sort by Count desc
| take 20
```

---

## Equipment & Asset Monitoring

### Last Known Value Per Sensor
```kql
// Current state: latest reading from each sensor
SensorReading
| summarize arg_max(timestamp, *) by sensor_id
| project sensor_id, site_id, zone_id, value, unit, quality, LastSeen = timestamp
| extend MinutesSinceLastReading = datetime_diff('minute', now(), LastSeen)
| sort by MinutesSinceLastReading desc
```

### Silent Sensors (No Recent Data)
```kql
// Sensors that haven't reported in the last 10 minutes
SensorReading
| summarize LastSeen = max(timestamp) by sensor_id, site_id
| where LastSeen < ago(10m)
| extend SilentMinutes = datetime_diff('minute', now(), LastSeen)
| sort by SilentMinutes desc
```

### Threshold Violations
```kql
// Readings that exceed min/max thresholds
// (Assumes thresholds are in a separate table or known values)
let Thresholds = datatable(sensor_type: string, min_threshold: real, max_threshold: real) [
    "Temperature", 15.0, 85.0,
    "Pressure", 0.5, 10.0,
    "Vibration", 0.0, 25.0,
    "Humidity", 20.0, 90.0
];
SensorReading
| where timestamp > ago(1h)
| lookup Thresholds on $left.unit == $right.sensor_type
| where value < min_threshold or value > max_threshold
| project timestamp, sensor_id, site_id, value, unit, min_threshold, max_threshold,
    ViolationType = iff(value < min_threshold, "Below Min", "Above Max")
| sort by timestamp desc
```

---

## Alert Pattern Monitoring

### Alert Frequency by Type
```kql
EquipmentAlert
| where timestamp > ago(24h)
| summarize AlertCount = count() by alert_type, bin(timestamp, 1h)
| render timechart with (title="Alerts per Hour by Type")
```

### Critical Alert Spike Detection
```kql
// Detect when critical alerts exceed normal rate
EquipmentAlert
| where timestamp > ago(24h)
| where severity >= 4
| summarize Count = count() by bin(timestamp, 15m)
| extend AvgRate = avg_of(Count)  // Use moving average in practice
| where Count > 10  // Threshold: more than 10 critical alerts in 15 min
```

### Top Alerting Equipment
```kql
EquipmentAlert
| where timestamp > ago(7d)
| summarize 
    TotalAlerts = count(),
    CriticalAlerts = countif(severity >= 4),
    AvgSeverity = avg(severity)
    by equipment_id
| sort by CriticalAlerts desc
| take 10
| render barchart with (title="Top 10 Alerting Equipment")
```

---

## Operational Dashboard Tiles

### Tile 1: Real-Time KPIs (Single Values)
```kql
// Events in last 5 minutes
SensorReading | where timestamp > ago(5m) | count

// Active sensors
SensorReading | where timestamp > ago(5m) | summarize dcount(sensor_id)

// Active sites
SensorReading | where timestamp > ago(5m) | summarize dcount(site_id)

// Avg quality percentage
SensorReading | where timestamp > ago(5m) | summarize round(100.0 * countif(quality == "Good") / count(), 1)
```

### Tile 2: Throughput Gauge
```kql
// Events per second (current rate)
SensorReading
| where timestamp > ago(1m)
| count
| extend EventsPerSecond = Count / 60.0
```

### Tile 3: System Health Summary
```kql
// Overall system health score
let TotalSensors = toscalar(SensorReading | where timestamp > ago(1h) | summarize dcount(sensor_id));
let ActiveSensors = toscalar(SensorReading | where timestamp > ago(5m) | summarize dcount(sensor_id));
let BadReadings = toscalar(SensorReading | where timestamp > ago(5m) | summarize countif(quality == "Bad"));
let TotalReadings = toscalar(SensorReading | where timestamp > ago(5m) | count);
print 
    ActiveSensorPct = round(100.0 * ActiveSensors / TotalSensors, 1),
    DataQualityPct = round(100.0 * (TotalReadings - BadReadings) / TotalReadings, 1),
    OverallHealth = iff(
        ActiveSensors * 1.0 / TotalSensors > 0.95 and BadReadings * 1.0 / TotalReadings < 0.05,
        "Healthy", "Degraded"
    )
```

---

## Time-Based Patterns

### Hourly Heatmap Data
```kql
// Average readings by hour of day and day of week (heatmap data)
SensorReading
| where timestamp > ago(7d)
| extend HourOfDay = hourofday(timestamp), DayOfWeek = dayofweek(timestamp) / 1d
| summarize AvgValue = avg(value) by HourOfDay, DayOfWeek
| sort by DayOfWeek asc, HourOfDay asc
```

### Rolling Averages
```kql
// 1-hour rolling average per sensor
SensorReading
| where timestamp > ago(24h)
| summarize AvgValue = avg(value) by sensor_id, bin(timestamp, 1h)
| order by sensor_id, timestamp asc
| serialize 
| extend RollingAvg = row_cumsum(AvgValue) / row_number()
```

---

## Dashboard Setup Pattern

When building a KQL Dashboard for monitoring, structure tiles in this order:

```
Row 1: KPI Cards
┌─────────────┬──────────────┬──────────────┬──────────────┐
│ Total Events│ Active Sensor│ Data Quality │ Alert Count  │
│   (5 min)   │   Count      │     %        │  (Critical)  │
└─────────────┴──────────────┴──────────────┴──────────────┘

Row 2: Time Series
┌──────────────────────────────────────────────────────────┐
│ Ingestion Rate (events/min) — timechart                  │
└──────────────────────────────────────────────────────────┘

Row 3: Distribution
┌───────────────────────────┬──────────────────────────────┐
│ Events by Site (bar)      │ Alerts by Type (pie)         │
└───────────────────────────┴──────────────────────────────┘

Row 4: Alerts & Issues
┌──────────────────────────────────────────────────────────┐
│ Recent Critical Alerts (table)                           │
└──────────────────────────────────────────────────────────┘

Row 5: Details
┌──────────────────────────────────────────────────────────┐
│ Silent Sensors / Threshold Violations (table)            │
└──────────────────────────────────────────────────────────┘
```

---

## Tips

1. **Use `ago()` for relative time** — Dashboards should always use relative time ranges, not absolute dates
2. **`bin()` for time aggregation** — Group by time windows: `bin(timestamp, 1m)`, `bin(timestamp, 5m)`, `bin(timestamp, 1h)`
3. **`render` for visualization** — `timechart`, `barchart`, `piechart`, `table`
4. **`arg_max` for latest value** — `summarize arg_max(timestamp, *) by sensor_id` gets the most recent reading
5. **`dcount` for distinct counting** — More efficient than `count(distinct ...)`
6. **Auto-refresh** — KQL Dashboards support auto-refresh intervals (30s, 1m, 5m)
7. **Parameters** — Use dashboard parameters for site_id, time_range filters

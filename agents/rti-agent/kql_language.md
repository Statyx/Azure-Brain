# KQL (Kusto Query Language) Reference

## Overview

KQL is the query language for Azure Data Explorer, Fabric Eventhouses, and KQL Databases. It is optimized for:
- **Time-series analytics** (sensor data, logs, telemetry)
- **Anomaly detection** (outliers, threshold violations)
- **Streaming aggregation** (real-time dashboards)
- **Text search and parsing** (log analytics)

KQL uses a **pipe model**: data flows left-to-right through operators.

```kql
TableName
| where Timestamp > ago(1h)
| summarize count() by bin(Timestamp, 5m)
| render timechart
```

## Core Operators

### Filtering
```kql
// where — filter rows
SensorReading | where IsAnomaly == true
SensorReading | where Timestamp > ago(24h)
SensorReading | where SensorType in ("Temperature", "Pressure")
SensorReading | where ReadingValue between (100 .. 500)
SensorReading | where MeasurementUnit !contains "PSI"
SensorReading | where SensorId startswith "SN0"
SensorReading | where isnotempty(QualityFlag)
```

### Projection
```kql
// project — select and rename columns
SensorReading | project Timestamp, SensorId, Value = ReadingValue

// project-away — remove columns
SensorReading | project-away QualityFlag, IsAnomaly

// extend — add computed columns
SensorReading | extend IsHigh = ReadingValue > 500
SensorReading | extend Hour = hourofday(Timestamp)
```

### Aggregation
```kql
// summarize — group and aggregate
SensorReading
| summarize AvgReading = avg(ReadingValue),
            MaxReading = max(ReadingValue),
            Count = count()
    by SensorType, bin(Timestamp, 1h)

// Common aggregation functions:
// count(), countif(), dcount(), dcountif()
// sum(), sumif(), avg(), avgif()
// min(), max(), percentile(), percentiles()
// arg_max(Timestamp, *) — row with max value
// arg_min(Timestamp, *) — row with min value
// make_list(), make_set() — collect into array
// stdev(), variance()
```

### Sorting and Limiting
```kql
// order by / sort by
SensorReading | order by Timestamp desc

// top — N rows with ordering
SensorReading | top 10 by ReadingValue desc

// take / limit — N rows (unordered)
SensorReading | take 100
```

### Joining
```kql
// join — combine tables
SensorReading
| join kind=inner (
    EquipmentAlert | project SensorId, AlertType, Severity
) on SensorId

// Join kinds: inner, leftouter, rightouter, fullouter, semi, anti, leftanti, rightanti
// Default is innerunique

// lookup — optimized equi-join (right table is small)
SensorReading
| lookup DimSensor on SensorId
```

### Union
```kql
// union — combine multiple tables
SensorReading | union EquipmentAlert | where Timestamp > ago(1h)
```

## Time-Series Functions

### Time Binning
```kql
// bin() — round timestamps to intervals
SensorReading | summarize avg(ReadingValue) by bin(Timestamp, 5m)
SensorReading | summarize count() by bin(Timestamp, 1h)
SensorReading | summarize max(ReadingValue) by bin(Timestamp, 1d)
```

### Time Functions
```kql
ago(1h)          // 1 hour ago
ago(7d)          // 7 days ago
now()            // current timestamp
datetime(2025-12-01)  // specific date

// Extract parts
hourofday(Timestamp)   // 0-23
dayofweek(Timestamp)   // 0d-6d (Sunday=0)
monthofyear(Timestamp) // 1-12
startofday(Timestamp)
startofweek(Timestamp)
startofmonth(Timestamp)

// Arithmetic
Timestamp + 1h
Timestamp - 30m
datetime_diff('hour', EndTime, StartTime)
```

### Time-Series Analysis
```kql
// make-series — create evenly-spaced time series
SensorReading
| make-series AvgReading = avg(ReadingValue) on Timestamp from ago(7d) to now() step 1h by SensorId

// series_decompose — trend + seasonality + residual
SensorReading
| make-series Reading = avg(ReadingValue) on Timestamp from ago(7d) to now() step 1h
| extend (baseline, seasonal, trend, residual) = series_decompose(Reading)

// series_outliers — detect anomalies in a series
SensorReading
| make-series Reading = avg(ReadingValue) on Timestamp from ago(7d) to now() step 1h
| extend outliers = series_outliers(Reading)

// series_stats — statistics for a series
SensorReading
| make-series Reading = avg(ReadingValue) on Timestamp from ago(7d) to now() step 1h
| extend (min_val, min_idx, max_val, max_idx, avg_val, stdev_val, variance_val) = series_stats(Reading)
```

## String Functions

```kql
// String operations
| where Name contains "pump"          // case-insensitive
| where Name contains_cs "Pump"       // case-sensitive
| where Name startswith "REF"
| where Name endswith "_v2"
| where Name matches regex @"SN\d{3}"
| where Name has "critical"           // word-boundary match

// Manipulation
| extend Lower = tolower(Name)
| extend Upper = toupper(Name)
| extend Trimmed = trim(" ", Name)
| extend Sub = substring(Name, 0, 3)
| extend Concat = strcat(FirstName, " ", LastName)
| extend Replaced = replace_string(Name, "old", "new")

// Parsing
| parse Message with "Temperature: " Temp:real " degrees"
| parse-where Message with "Alert: " AlertType " on " Equipment
```

## Aggregation Patterns for Dashboards

### Latest Value per Entity
```kql
SensorReading
| summarize arg_max(Timestamp, *) by SensorId
| project SensorId, Timestamp, ReadingValue, SensorType
```

### Trend Over Time
```kql
SensorReading
| summarize AvgReading = avg(ReadingValue) by bin(Timestamp, 15m), SensorType
| order by Timestamp asc
```

### Count by Category
```kql
EquipmentAlert
| summarize Count = count() by Severity
| order by Count desc
```

### Threshold Violations
```kql
SensorReading
| where IsAnomaly == true
| project Timestamp, SensorId, SensorType, ReadingValue, QualityFlag
| order by Timestamp desc
| take 100
```

### Unacknowledged Items
```kql
EquipmentAlert
| where IsAcknowledged == false
| project Timestamp, AlertId, SensorId, AlertType, Severity, Message
| order by Timestamp desc
```

## Render Operators (for dashboards)

```kql
// Line chart
| render timechart

// Bar chart
| render barchart

// Pie chart
| render piechart

// Scatter
| render scatterchart

// Table (default)
| render table

// Area chart
| render areachart

// Column chart
| render columnchart

// Stacked area
| render stackedareachart

// Map (with Latitude/Longitude columns)
| render map
```

## Management Commands

```kql
// Show tables
.show tables

// Show table schema
.show table SensorReading schema as json

// Show database
.show database

// Create/merge table (idempotent)
.create-merge table SensorReading (SensorId:string, Timestamp:datetime, ReadingValue:real)

// Drop table
.drop table SensorReading

// Alter table (add column)
.alter-merge table SensorReading (NewColumn:string)

// Inline ingestion
.ingest inline into table SensorReading with (format='csv') <|
SN001,2025-12-01T01:00:00,450.2

// Show ingestion failures
.show ingestion failures

// Show row count
SensorReading | count

// Clear table data (keep schema)
.clear table SensorReading data
```

## Useful Patterns

### Anomaly Detection
```kql
SensorReading
| where Timestamp > ago(24h)
| summarize AvgReading = avg(ReadingValue), StdDev = stdev(ReadingValue) by SensorId
| extend LowerBound = AvgReading - 3 * StdDev, UpperBound = AvgReading + 3 * StdDev
| join kind=inner (
    SensorReading | where Timestamp > ago(1h)
) on SensorId
| where ReadingValue < LowerBound or ReadingValue > UpperBound
```

### Moving Average
```kql
SensorReading
| where SensorId == "SN001"
| order by Timestamp asc
| extend MovingAvg = avg(ReadingValue, 10)  // 10-row window
```

### Delta / Rate of Change
```kql
SensorReading
| where SensorId == "SN001"
| order by Timestamp asc
| extend PrevValue = prev(ReadingValue)
| extend Delta = ReadingValue - PrevValue
| where abs(Delta) > 50  // Sudden changes
```

### Time-to-Resolution
```kql
EquipmentAlert
| where isnotempty(AcknowledgedTimestamp)
| extend TimeToAck = datetime_diff('minute', todatetime(AcknowledgedTimestamp), Timestamp)
| summarize AvgTimeToAck = avg(TimeToAck) by Severity
```

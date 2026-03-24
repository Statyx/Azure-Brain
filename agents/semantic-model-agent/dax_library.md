# Multi-Domain DAX Measure Library

## Purpose

Ready-to-use DAX measure patterns organized by industry domain. Each measure includes the formula, required columns, and usage notes.

---

## Universal Measures (All Domains)

### Time Intelligence

```dax
// Year-to-Date
[YTD Sales] =
CALCULATE(
    [Total Revenue],
    DATESYTD('Calendar'[Date])
)

// Previous Year Same Period
[PY Sales] =
CALCULATE(
    [Total Revenue],
    SAMEPERIODLASTYEAR('Calendar'[Date])
)

// Year-over-Year Growth %
[YoY Growth %] =
VAR CurrentValue = [Total Revenue]
VAR PreviousValue = [PY Sales]
RETURN
IF(
    PreviousValue <> 0,
    DIVIDE(CurrentValue - PreviousValue, PreviousValue),
    BLANK()
)

// Month-to-Date
[MTD Sales] =
CALCULATE(
    [Total Revenue],
    DATESMTD('Calendar'[Date])
)

// Moving Average (3 months)
[3M Moving Avg] =
AVERAGEX(
    DATESINPERIOD('Calendar'[Date], MAX('Calendar'[Date]), -3, MONTH),
    [Total Revenue]
)

// Rolling 12-Month Total
[R12M Total] =
CALCULATE(
    [Total Revenue],
    DATESINPERIOD('Calendar'[Date], MAX('Calendar'[Date]), -12, MONTH)
)
```

### Ranking & Comparison

```dax
// Dynamic Top N
[Rank] =
RANKX(
    ALLSELECTED('Product'[ProductName]),
    [Total Revenue], , DESC, DENSE
)

// % of Grand Total
[% of Total] =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], REMOVEFILTERS('Product'))
)

// % of Parent (within category)
[% of Category] =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], REMOVEFILTERS('Product'[ProductName]))
)

// Cumulative Total
[Cumulative Revenue] =
CALCULATE(
    [Total Revenue],
    FILTER(
        ALL('Calendar'[Date]),
        'Calendar'[Date] <= MAX('Calendar'[Date])
    )
)
```

---

## Retail & E-Commerce

### Revenue & Sales

```dax
// Gross Revenue
[Gross Revenue] =
SUMX(
    'Sales',
    'Sales'[Quantity] * 'Sales'[UnitPrice]
)

// Net Revenue (after discounts and returns)
[Net Revenue] =
[Gross Revenue] - [Total Discounts] - [Total Returns]

// Average Order Value
[AOV] =
DIVIDE(
    [Net Revenue],
    DISTINCTCOUNT('Sales'[OrderId])
)

// Average Selling Price
[ASP] =
DIVIDE(
    [Net Revenue],
    SUM('Sales'[Quantity])
)

// Revenue per Square Foot (brick-and-mortar)
[Rev per SqFt] =
DIVIDE(
    [Net Revenue],
    SUM('Store'[SquareFootage])
)
```

### Customer Metrics

```dax
// Customer Count
[Customer Count] =
DISTINCTCOUNT('Sales'[CustomerId])

// New Customers (first purchase in period)
[New Customers] =
COUNTROWS(
    FILTER(
        VALUES('Customer'[CustomerId]),
        CALCULATE(
            MIN('Sales'[OrderDate]),
            ALL('Calendar')
        ) >= MIN('Calendar'[Date])
        &&
        CALCULATE(
            MIN('Sales'[OrderDate]),
            ALL('Calendar')
        ) <= MAX('Calendar'[Date])
    )
)

// Repeat Purchase Rate
[Repeat Rate] =
VAR CustomersWithMultipleOrders =
    COUNTROWS(
        FILTER(
            VALUES('Sales'[CustomerId]),
            CALCULATE(DISTINCTCOUNT('Sales'[OrderId])) > 1
        )
    )
RETURN
DIVIDE(CustomersWithMultipleOrders, [Customer Count])

// Customer Lifetime Value (simplified)
[CLV Estimate] =
[AOV] * [Avg Orders per Customer] * [Avg Customer Lifespan Years]

// Average Orders per Customer
[Avg Orders per Customer] =
DIVIDE(
    DISTINCTCOUNT('Sales'[OrderId]),
    [Customer Count]
)

// Cart Abandonment Rate
[Abandonment Rate] =
DIVIDE(
    COUNTROWS(FILTER('Cart', 'Cart'[Status] = "Abandoned")),
    COUNTROWS('Cart')
)
```

### Inventory

```dax
// Inventory Turnover
[Inventory Turnover] =
DIVIDE(
    [COGS],
    AVERAGE('Inventory'[StockValue])
)

// Days of Supply
[Days of Supply] =
DIVIDE(
    SUM('Inventory'[QuantityOnHand]),
    DIVIDE([Total Units Sold], 30)
)

// Stockout Rate
[Stockout Rate] =
DIVIDE(
    COUNTROWS(FILTER('Inventory', 'Inventory'[QuantityOnHand] = 0)),
    COUNTROWS('Inventory')
)

// Sell-Through Rate
[Sell-Through %] =
DIVIDE(
    SUM('Sales'[Quantity]),
    SUM('Inventory'[QuantityReceived])
)
```

---

## Manufacturing & IoT

### Production Metrics

```dax
// Overall Equipment Effectiveness (OEE)
[OEE] =
[Availability] * [Performance] * [Quality]

// Availability
[Availability] =
DIVIDE(
    SUM('Production'[ActualRunTimeMinutes]),
    SUM('Production'[PlannedRunTimeMinutes])
)

// Performance
[Performance] =
DIVIDE(
    SUM('Production'[ActualOutput]),
    SUM('Production'[TheoreticalMaxOutput])
)

// Quality (First Pass Yield)
[Quality] =
DIVIDE(
    SUM('Production'[GoodUnits]),
    SUM('Production'[TotalUnitsProduced])
)

// Cycle Time
[Avg Cycle Time (sec)] =
DIVIDE(
    SUM('Production'[ActualRunTimeMinutes]) * 60,
    SUM('Production'[TotalUnitsProduced])
)

// Defect Rate (PPM)
[Defect PPM] =
DIVIDE(
    SUM('Production'[DefectiveUnits]),
    SUM('Production'[TotalUnitsProduced])
) * 1000000
```

### Sensor & IoT

```dax
// Sensor Uptime %
[Sensor Uptime %] =
DIVIDE(
    COUNTROWS(FILTER('SensorReading', NOT(ISBLANK('SensorReading'[Value])))),
    COUNTROWS('SensorReading')
)

// Average Sensor Reading
[Avg Reading] =
AVERAGE('SensorReading'[Value])

// Sensor Alert Count
[Alert Count] =
COUNTROWS(
    FILTER(
        'SensorReading',
        'SensorReading'[Value] > RELATED('Sensor'[UpperThreshold])
        || 'SensorReading'[Value] < RELATED('Sensor'[LowerThreshold])
    )
)

// Mean Time Between Failures (MTBF)
[MTBF (hours)] =
DIVIDE(
    SUM('Equipment'[TotalOperatingHours]),
    COUNTROWS(FILTER('Incident', 'Incident'[Type] = "Failure"))
)

// Mean Time to Repair (MTTR)
[MTTR (hours)] =
AVERAGE('Incident'[RepairDurationHours])
```

---

## Healthcare

### Patient Metrics

```dax
// Patient Volume
[Patient Count] =
DISTINCTCOUNT('Encounter'[PatientId])

// Average Length of Stay (ALOS)
[ALOS (days)] =
AVERAGE('Encounter'[LengthOfStayDays])

// Readmission Rate (30-day)
[30-Day Readmission Rate] =
VAR Discharges =
    COUNTROWS(FILTER('Encounter', 'Encounter'[Type] = "Inpatient"))
VAR Readmissions =
    COUNTROWS(
        FILTER(
            'Encounter',
            'Encounter'[IsReadmission] = TRUE()
            && 'Encounter'[DaysSincePriorDischarge] <= 30
        )
    )
RETURN
DIVIDE(Readmissions, Discharges)

// Bed Occupancy Rate
[Bed Occupancy %] =
DIVIDE(
    SUM('Census'[OccupiedBeds]),
    SUM('Census'[AvailableBeds])
)

// ED Wait Time
[Avg ED Wait (min)] =
AVERAGE('EDVisit'[WaitTimeMinutes])
```

### Financial (Healthcare)

```dax
// Revenue per Patient
[Rev per Patient] =
DIVIDE(
    [Total Revenue],
    [Patient Count]
)

// Cost per Case
[Cost per Case] =
DIVIDE(
    SUM('Cost'[TotalCost]),
    DISTINCTCOUNT('Encounter'[EncounterId])
)

// Payer Mix
[Payer Mix %] =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], REMOVEFILTERS('Payer'[PayerType]))
)

// Denial Rate
[Denial Rate] =
DIVIDE(
    COUNTROWS(FILTER('Claim', 'Claim'[Status] = "Denied")),
    COUNTROWS('Claim')
)
```

---

## Energy & Utilities

### Consumption

```dax
// Total Energy Consumption (kWh)
[Total kWh] =
SUM('Meter'[ConsumptionKWh])

// Peak Demand (kW)
[Peak Demand kW] =
MAXX(
    'Meter',
    'Meter'[DemandKW]
)

// Energy Cost
[Energy Cost] =
SUMX(
    'Meter',
    'Meter'[ConsumptionKWh] * RELATED('Tariff'[RatePerKWh])
)

// Consumption per Degree Day (weather normalization)
[kWh per HDD] =
DIVIDE(
    [Total kWh],
    SUM('Weather'[HeatingDegreeDays])
)

// Load Factor
[Load Factor] =
DIVIDE(
    AVERAGE('Meter'[DemandKW]),
    MAX('Meter'[DemandKW])
)
```

### Renewable & Sustainability

```dax
// Renewable Energy %
[Renewable %] =
DIVIDE(
    CALCULATE([Total kWh], 'Source'[Type] IN {"Solar", "Wind", "Hydro"}),
    [Total kWh]
)

// Carbon Emissions (tCO2e)
[Carbon Emissions] =
SUMX(
    'Meter',
    'Meter'[ConsumptionKWh] * RELATED('Source'[EmissionFactorKgCO2PerKWh]) / 1000
)

// Carbon Intensity
[Carbon Intensity (kg/unit)] =
DIVIDE(
    [Carbon Emissions] * 1000,
    SUM('Production'[TotalUnitsProduced])
)
```

---

## Financial Services

### Portfolio Metrics

```dax
// Total Assets Under Management
[AUM] =
SUM('Position'[MarketValue])

// Weighted Average Return
[Weighted Return] =
SUMX(
    'Position',
    'Position'[MarketValue] / [AUM] * 'Position'[ReturnPct]
)

// Sharpe Ratio (simplified, annualized)
[Sharpe Ratio] =
DIVIDE(
    [Weighted Return] - [Risk Free Rate],
    [Portfolio StdDev]
)

// Net Asset Value per Share
[NAV per Share] =
DIVIDE(
    [AUM] - SUM('Fund'[TotalLiabilities]),
    SUM('Fund'[SharesOutstanding])
)
```

### Risk & Compliance

```dax
// Non-Performing Loan Rate
[NPL Rate] =
DIVIDE(
    CALCULATE(SUM('Loan'[OutstandingBalance]), 'Loan'[DaysOverdue] > 90),
    SUM('Loan'[OutstandingBalance])
)

// Provision Coverage Ratio
[Coverage Ratio] =
DIVIDE(
    SUM('Loan'[ProvisionAmount]),
    CALCULATE(SUM('Loan'[OutstandingBalance]), 'Loan'[DaysOverdue] > 90)
)

// Capital Adequacy (simplified)
[CAR %] =
DIVIDE(
    SUM('Capital'[TierOneCapital]) + SUM('Capital'[TierTwoCapital]),
    SUM('Asset'[RiskWeightedValue])
)

// Fraud Detection Rate
[Fraud Rate] =
DIVIDE(
    COUNTROWS(FILTER('Transaction', 'Transaction'[IsFraud] = TRUE())),
    COUNTROWS('Transaction')
)
```

---

## HR & Workforce

```dax
// Headcount
[Headcount] =
COUNTROWS(FILTER('Employee', 'Employee'[Status] = "Active"))

// Turnover Rate (annualized)
[Turnover Rate] =
DIVIDE(
    COUNTROWS(FILTER('Employee', 'Employee'[TerminationDate] <> BLANK())),
    AVERAGE('Snapshot'[ActiveEmployees])
)

// Revenue per Employee
[Rev per Employee] =
DIVIDE(
    [Total Revenue],
    [Headcount]
)

// Absence Rate
[Absence Rate] =
DIVIDE(
    SUM('Absence'[DaysAbsent]),
    SUM('WorkCalendar'[WorkingDays]) * [Headcount]
)

// Training Hours per Employee
[Training Hours per FTE] =
DIVIDE(
    SUM('Training'[Hours]),
    [Headcount]
)

// Gender Pay Gap
[Gender Pay Gap %] =
VAR MaleAvg = CALCULATE(AVERAGE('Employee'[Salary]), 'Employee'[Gender] = "Male")
VAR FemaleAvg = CALCULATE(AVERAGE('Employee'[Salary]), 'Employee'[Gender] = "Female")
RETURN
DIVIDE(MaleAvg - FemaleAvg, MaleAvg)
```

---

## Measure Naming Conventions

| Pattern | Example | When to Use |
|---------|---------|------------|
| `Total [Noun]` | Total Revenue | Additive measures (SUM) |
| `Avg [Noun]` | Avg Order Value | Average measures |
| `[Noun] Count` | Customer Count | Count measures |
| `[Noun] %` | Turnover Rate | Ratio/percentage measures |
| `YTD [Noun]` | YTD Sales | Year-to-date |
| `PY [Noun]` | PY Sales | Prior year comparison |
| `[Noun] Rank` | Product Rank | Ranking measures |
| `[Noun] per [Noun]` | Rev per Employee | Intensity/per-unit measures |

> **Rule**: Always create a base measure (`Total Revenue = SUM(Sales[Amount])`) before building derived measures on top. **NEVER** reference column aggregations directly in complex measures.

---

## Cross-References

- [Semantic Model Agent Instructions](instructions.md) — Naming conventions, star schema patterns
- [Report Builder Performance](../report-builder-agent/performance.md) — DAX performance optimization
- [Domain Modeler Agent](../domain-modeler-agent/instructions.md) — Dimensional modeling for each domain

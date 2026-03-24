# Dimensional Modeling — Star Schema Patterns & Conventions

## Star Schema Fundamentals

A star schema has one or more **fact tables** at the center, surrounded by **dimension tables**. Facts contain measures (numeric values to aggregate). Dimensions contain descriptive attributes for slicing and filtering.

```
          dim_dates
              │
dim_customers─┼─fact_sales─dim_products
              │
          dim_stores
```

---

## Dimension Table Patterns

### Standard Dimension
```sql
-- Lakehouse Delta table definition
CREATE TABLE dim_customers (
    customer_id     STRING      NOT NULL,   -- Primary key (business key)
    customer_name   STRING      NOT NULL,
    email           STRING,
    segment         STRING,                  -- e.g., "Enterprise", "SMB", "Consumer"
    region          STRING,
    city            STRING,
    country         STRING,
    created_date    DATE        NOT NULL,
    is_active       BOOLEAN     DEFAULT true
);
```

### Date Dimension (Universal)
Every model should include a date dimension. This is the most reused dimension.
```sql
CREATE TABLE dim_dates (
    date_key        DATE        NOT NULL,   -- 2024-01-15
    year            INT         NOT NULL,   -- 2024
    quarter         INT         NOT NULL,   -- 1
    month           INT         NOT NULL,   -- 1
    month_name      STRING      NOT NULL,   -- "January"
    week            INT         NOT NULL,   -- 3
    day_of_week     INT         NOT NULL,   -- 2 (Monday=1)
    day_name        STRING      NOT NULL,   -- "Monday"
    is_weekend      BOOLEAN     NOT NULL,
    is_holiday      BOOLEAN     DEFAULT false,
    fiscal_year     INT,
    fiscal_quarter  INT
);
```

### Generate Date Dimension in Python
```python
import pandas as pd

def generate_date_dimension(start="2023-01-01", end="2025-12-31"):
    dates = pd.date_range(start, end)
    df = pd.DataFrame({
        "date_key": dates.date,
        "year": dates.year,
        "quarter": dates.quarter,
        "month": dates.month,
        "month_name": dates.strftime("%B"),
        "week": dates.isocalendar().week.values,
        "day_of_week": dates.dayofweek + 1,
        "day_name": dates.strftime("%A"),
        "is_weekend": dates.dayofweek >= 5,
        "is_holiday": False,
        "fiscal_year": dates.year,
        "fiscal_quarter": dates.quarter
    })
    return df
```

### Slowly Changing Dimension (SCD Type 2)
For dimensions that change over time and you need historical tracking:
```sql
CREATE TABLE dim_customers_scd2 (
    surrogate_key   BIGINT      NOT NULL,   -- Auto-generated surrogate
    customer_id     STRING      NOT NULL,   -- Business key
    customer_name   STRING      NOT NULL,
    segment         STRING,
    region          STRING,
    is_current      BOOLEAN     NOT NULL,   -- true = active version
    start_date      TIMESTAMP   NOT NULL,
    end_date        TIMESTAMP               -- NULL = current record
);
```

### Role-Playing Dimension
Same dimension used in multiple roles (e.g., date used as order_date, ship_date):
```
fact_orders.order_date → dim_dates.date_key (role: "Order Date")
fact_orders.ship_date  → dim_dates.date_key (role: "Ship Date")
```
In Semantic Model, create two relationships with different roles and use USERELATIONSHIP() in DAX.

### Junk Dimension
Combines multiple low-cardinality flags/indicators into one dimension:
```sql
CREATE TABLE dim_transaction_flags (
    flag_key        INT         NOT NULL,
    is_online       BOOLEAN,
    is_promotional  BOOLEAN,
    payment_method  STRING,     -- "Cash", "Card", "Digital"
    order_priority  STRING      -- "High", "Medium", "Low"
);
```

---

## Fact Table Patterns

### Transaction Fact
One row per discrete event or transaction. Most common.
```sql
CREATE TABLE fact_sales (
    transaction_id  STRING      NOT NULL,
    customer_id     STRING      NOT NULL,   -- FK → dim_customers
    product_id      STRING      NOT NULL,   -- FK → dim_products
    store_id        STRING      NOT NULL,   -- FK → dim_stores
    sale_date       DATE        NOT NULL,   -- FK → dim_dates
    quantity        INT         NOT NULL,
    unit_price      DOUBLE      NOT NULL,
    discount_pct    DOUBLE      DEFAULT 0,
    total_amount    DOUBLE      NOT NULL,
    cost            DOUBLE,
    margin          DOUBLE
);
```

### Periodic Snapshot Fact
State captured at regular intervals (daily inventory, monthly balance):
```sql
CREATE TABLE fact_daily_inventory (
    snapshot_date   DATE        NOT NULL,   -- FK → dim_dates
    product_id      STRING      NOT NULL,   -- FK → dim_products
    warehouse_id    STRING      NOT NULL,   -- FK → dim_warehouses
    quantity_on_hand INT        NOT NULL,
    quantity_on_order INT       DEFAULT 0,
    reorder_point   INT
);
```

### Accumulating Snapshot Fact
Tracks the lifecycle of a process with multiple milestones:
```sql
CREATE TABLE fact_order_lifecycle (
    order_id        STRING      NOT NULL,
    order_date      DATE,       -- Milestone 1
    payment_date    DATE,       -- Milestone 2
    ship_date       DATE,       -- Milestone 3
    delivery_date   DATE,       -- Milestone 4
    return_date     DATE,       -- Milestone 5 (optional)
    days_to_ship    INT,
    days_to_deliver INT,
    order_amount    DOUBLE
);
```

### Factless Fact
Records events with no measures — pure tracking:
```sql
CREATE TABLE fact_attendance (
    student_id      STRING      NOT NULL,
    class_id        STRING      NOT NULL,
    attendance_date DATE        NOT NULL,
    was_present     BOOLEAN     NOT NULL
);
-- Measure: COUNT of rows, COUNTROWS where was_present = true
```

---

## KQL Table Design for Streaming

KQL tables mirror fact tables but are optimized for time-series ingestion:

```kql
.create table SensorReading (
    sensor_id: string,
    site_id: string,
    zone_id: string,
    value: real,
    unit: string,
    quality: string,
    timestamp: datetime
)

// Retention policy
.alter table SensorReading policy retention 
```
{ "SoftDeletePeriod": "365.00:00:00", "Recoverability": "Enabled" }
```

// Ingestion mapping for EventStream JSON
.create-or-alter table SensorReading ingestion json mapping "SensorReadingMapping"
```
[
    {"column": "sensor_id", "path": "$.sensor_id", "datatype": "string"},
    {"column": "site_id", "path": "$.site_id", "datatype": "string"},
    {"column": "zone_id", "path": "$.zone_id", "datatype": "string"},
    {"column": "value", "path": "$.value", "datatype": "real"},
    {"column": "unit", "path": "$.unit", "datatype": "string"},
    {"column": "quality", "path": "$.quality", "datatype": "string"},
    {"column": "timestamp", "path": "$.timestamp", "datatype": "datetime"}
]
```
```

---

## Ontology Entity Design

Map dimension tables to ontology entity types:

```yaml
entity_types:
  - name: Site
    external_id: site_id
    properties:
      - name: site_name (type: String)
      - name: address (type: String)
      - name: latitude (type: Double)
      - name: longitude (type: Double)
    bindings:
      kql_database: EventhouseDB
      kql_table: SensorReading
      kql_key: site_id

  - name: Sensor
    external_id: sensor_id
    properties:
      - name: sensor_type (type: String)
      - name: unit (type: String)
      - name: min_threshold (type: Double)
      - name: max_threshold (type: Double)
    bindings:
      kql_database: EventhouseDB
      kql_table: SensorReading
      kql_key: sensor_id

relationships:
  - name: SensorBelongsToSite
    from: Sensor
    to: Site
    via_kql: "SensorReading | distinct sensor_id, site_id"
```

---

## DAX Measure Templates

### Standard Measures (Every Model)
```dax
// Additive measures
Total Revenue = SUM(fact_sales[total_amount])
Total Quantity = SUM(fact_sales[quantity])
Total Cost = SUM(fact_sales[cost])
Transaction Count = COUNTROWS(fact_sales)
Avg Transaction Value = AVERAGE(fact_sales[total_amount])

// Margin
Gross Margin = [Total Revenue] - [Total Cost]
Margin % = DIVIDE([Gross Margin], [Total Revenue], 0)
```

### Time Intelligence
```dax
// Year-over-year
Revenue YoY = 
    CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_dates[date_key]))

Revenue YoY Growth % = 
    DIVIDE([Total Revenue] - [Revenue YoY], [Revenue YoY], 0)

// Month-to-date
Revenue MTD = 
    CALCULATE([Total Revenue], DATESMTD(dim_dates[date_key]))

// Year-to-date
Revenue YTD = 
    CALCULATE([Total Revenue], DATESYTD(dim_dates[date_key]))

// Rolling 30 days
Revenue Rolling 30D = 
    CALCULATE(
        [Total Revenue],
        DATESINPERIOD(dim_dates[date_key], MAX(dim_dates[date_key]), -30, DAY)
    )
```

### IoT / Sensor Measures
```dax
Avg Reading = AVERAGE(fact_readings[value])
Max Reading = MAX(fact_readings[value])
Min Reading = MIN(fact_readings[value])
Reading Count = COUNTROWS(fact_readings)

Out of Range Count = 
    COUNTROWS(
        FILTER(fact_readings, 
            fact_readings[value] < fact_readings[min_threshold] ||
            fact_readings[value] > fact_readings[max_threshold]
        )
    )

Anomaly Rate % = 
    DIVIDE([Out of Range Count], [Reading Count], 0)
```

---

## Best Practices

1. **Start with the grain** — Define it clearly before anything else
2. **Conformed dimensions** — Use the same dim_dates, dim_geography across all facts
3. **Additive measures only in fact tables** — Non-additive calculations go in DAX
4. **Don't normalize dimensions** — Star schema, not snowflake (Fabric Direct Lake works best with flat tables)
5. **Include surrogate keys only if SCD is needed** — Business keys work for most demo scenarios
6. **Keep dimensions small** — A few hundred to a few thousand rows is ideal for demos
7. **Keep facts realistic** — Use proper cardinality: many facts per dimension member

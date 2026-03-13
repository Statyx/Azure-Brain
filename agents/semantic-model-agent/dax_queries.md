# DAX Queries — Testing, Validation & Debugging

## Overview

DAX queries let you test measures, validate model structure, and debug data issues
**without** building a report. Use them after deployment to verify the model works.

---

## DAX Query Syntax

```dax
// Basic query
EVALUATE
    table_or_expression

// With DEFINE for ad-hoc measures
DEFINE
    MEASURE table[MeasureName] = expression
EVALUATE
    expression

// With ORDER BY
EVALUATE
    expression
ORDER BY column [ASC|DESC]
```

---

## Validation Queries

### 1. Check Table Row Counts

```dax
EVALUATE
ROW(
    "dim_customers", COUNTROWS(dim_customers),
    "dim_products", COUNTROWS(dim_products),
    "dim_chart_of_accounts", COUNTROWS(dim_chart_of_accounts),
    "dim_cost_centers", COUNTROWS(dim_cost_centers),
    "fact_general_ledger", COUNTROWS(fact_general_ledger),
    "fact_budgets", COUNTROWS(fact_budgets),
    "fact_forecasts", COUNTROWS(fact_forecasts),
    "fact_allocations", COUNTROWS(fact_allocations),
    "fact_invoices", COUNTROWS(fact_invoices),
    "fact_invoice_lines", COUNTROWS(fact_invoice_lines),
    "fact_payments", COUNTROWS(fact_payments)
)
```

### 2. Verify Measures Return Values

```dax
EVALUATE
ROW(
    "Total Revenue", [Total Revenue],
    "Total COGS", [Total COGS],
    "Gross Profit", [Gross Profit],
    "Gross Margin %", [Gross Margin %],
    "EBITDA", [EBITDA],
    "Net Income", [Net Income],
    "Total Invoices", [Total Invoices],
    "DSO", [DSO],
    "Budget Amount", [Budget Amount],
    "Variance Amount", [Variance Amount]
)
```

### 3. Check Relationship Integrity

```dax
// Find orphan keys in fact_general_ledger (account_id not in dim)
EVALUATE
FILTER(
    SELECTCOLUMNS(
        fact_general_ledger,
        "account_id", fact_general_ledger[account_id]
    ),
    NOT(fact_general_ledger[account_id] IN VALUES(dim_chart_of_accounts[account_id]))
)
```

```dax
// Find orphan customer_id in fact_invoices
EVALUATE
FILTER(
    SELECTCOLUMNS(fact_invoices, "customer_id", fact_invoices[customer_id]),
    NOT(fact_invoices[customer_id] IN VALUES(dim_customers[customer_id]))
)
```

### 4. Verify Column Distinct Counts

```dax
EVALUATE
ROW(
    "Accounts", DISTINCTCOUNT(dim_chart_of_accounts[account_id]),
    "Cost Centers", DISTINCTCOUNT(dim_cost_centers[cost_center_id]),
    "Customers", DISTINCTCOUNT(dim_customers[customer_id]),
    "Products", DISTINCTCOUNT(dim_products[product_id]),
    "GL Entries", DISTINCTCOUNT(fact_general_ledger[entry_id]),
    "Invoices", DISTINCTCOUNT(fact_invoices[invoice_id])
)
```

---

## Debugging Queries

### 5. Revenue by Account Type (Validate CALCULATE filter)

```dax
EVALUATE
SUMMARIZECOLUMNS(
    dim_chart_of_accounts[account_type],
    "Total", SUM(fact_general_ledger[amount]),
    "Count", COUNTROWS(fact_general_ledger)
)
ORDER BY dim_chart_of_accounts[account_type]
```

### 6. Budget vs Actual by Cost Center

```dax
EVALUATE
ADDCOLUMNS(
    VALUES(dim_cost_centers[cost_center_name]),
    "Actual", CALCULATE(SUM(fact_general_ledger[amount])),
    "Budget", CALCULATE(SUM(fact_budgets[amount])),
    "Variance", CALCULATE(SUM(fact_general_ledger[amount])) - CALCULATE(SUM(fact_budgets[amount]))
)
ORDER BY [Variance] DESC
```

### 7. Top 10 Customers by Invoice Amount

```dax
EVALUATE
TOPN(
    10,
    ADDCOLUMNS(
        VALUES(dim_customers[customer_name]),
        "Total Invoiced", CALCULATE(SUM(fact_invoices[total_amount_eur]))
    ),
    [Total Invoiced], DESC
)
```

### 8. Monthly Revenue Trend

```dax
EVALUATE
ADDCOLUMNS(
    SUMMARIZE(fact_general_ledger, fact_general_ledger[entry_date]),
    "Revenue", CALCULATE(
        SUM(fact_general_ledger[amount]),
        dim_chart_of_accounts[account_type] = "Revenue"
    )
)
ORDER BY fact_general_ledger[entry_date]
```

### 9. Invoice Aging Analysis

```dax
EVALUATE
SUMMARIZECOLUMNS(
    fact_invoices[status],
    "Count", COUNTROWS(fact_invoices),
    "Total Amount", SUM(fact_invoices[total_amount_eur]),
    "Avg Amount", AVERAGE(fact_invoices[total_amount_eur])
)
```

### 10. Detect Duplicate Keys

```dax
// Find duplicate entry_ids in fact_general_ledger
EVALUATE
FILTER(
    ADDCOLUMNS(
        VALUES(fact_general_ledger[entry_id]),
        "Occurrences", CALCULATE(COUNTROWS(fact_general_ledger))
    ),
    [Occurrences] > 1
)
```

---

## Ad-Hoc Measure Testing

### Test a New Measure Before Adding to model.bim

```dax
DEFINE
    MEASURE fact_general_ledger[Revenue MoM Growth] = 
        VAR CurrentMonth = [Total Revenue]
        VAR PriorMonth = CALCULATE(
            [Total Revenue],
            DATEADD(dim_calendar[Date], -1, MONTH)
        )
        RETURN DIVIDE(CurrentMonth - PriorMonth, PriorMonth, 0)

EVALUATE
ADDCOLUMNS(
    VALUES(dim_calendar[Month]),
    "Revenue", [Total Revenue],
    "MoM Growth", [Revenue MoM Growth]
)
ORDER BY dim_calendar[Month]
```

### Test with Specific Filter Context

```dax
EVALUATE
{
    CALCULATE([Total Revenue], dim_cost_centers[region] = "Europe"),
    CALCULATE([Total Revenue], dim_cost_centers[region] = "Americas"),
    CALCULATE([Total Revenue], dim_cost_centers[region] = "Asia-Pacific")
}
```

---

## Performance Analysis Queries

### Measure Execution Timing

```dax
// Use with DAX Studio for timing
EVALUATE
ROW(
    "Revenue", [Total Revenue],
    "GP", [Gross Profit],
    "EBITDA", [EBITDA],
    "DSO", [DSO]
)
```

### Check Model Size (row counts per table)

```dax
EVALUATE
UNION(
    ROW("Table", "dim_customers", "Rows", COUNTROWS(dim_customers)),
    ROW("Table", "dim_products", "Rows", COUNTROWS(dim_products)),
    ROW("Table", "dim_chart_of_accounts", "Rows", COUNTROWS(dim_chart_of_accounts)),
    ROW("Table", "dim_cost_centers", "Rows", COUNTROWS(dim_cost_centers)),
    ROW("Table", "fact_general_ledger", "Rows", COUNTROWS(fact_general_ledger)),
    ROW("Table", "fact_budgets", "Rows", COUNTROWS(fact_budgets)),
    ROW("Table", "fact_forecasts", "Rows", COUNTROWS(fact_forecasts)),
    ROW("Table", "fact_invoices", "Rows", COUNTROWS(fact_invoices)),
    ROW("Table", "fact_invoice_lines", "Rows", COUNTROWS(fact_invoice_lines)),
    ROW("Table", "fact_payments", "Rows", COUNTROWS(fact_payments)),
    ROW("Table", "fact_allocations", "Rows", COUNTROWS(fact_allocations))
)
```

---

## Running DAX Queries via REST API

Currently, Fabric REST API does not have a direct "execute DAX query" endpoint 
for semantic models like XMLA does. Options:

### Option 1: DAX Studio (Desktop)
Connect to: `powerbi://api.powerbi.com/v1.0/myorg/CDR - Demo Finance Fabric`  
Database: `SM_Finance`

### Option 2: XMLA Endpoint (Programmatic)
```python
# Requires: pip install azure-identity adomdclient
# Connection string format:
# Provider=MSOLAP;Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace};
# Initial Catalog={model_name};Integrated Security=ClaimsToken
```

### Option 3: Power BI REST API (Execute Queries)
```python
resp = requests.post(
    f"https://api.powerbi.com/v1.0/myorg/datasets/{model_id}/executeQueries",
    headers=headers,
    json={
        "queries": [{"query": "EVALUATE ROW(\"Rev\", [Total Revenue])"}],
        "serializerSettings": {"includeNulls": True}
    }
)
result = resp.json()
```

Note: This requires Power BI REST API scope (`https://analysis.windows.net/powerbi/api`),
not the Fabric API scope.

# DAX Measures — Complete Reference

## Overview

DAX (Data Analysis Expressions) measures are calculations defined in the semantic model.
They execute at query time and respond to filter context from slicers, visuals, and report pages.

---

## Measure Syntax in model.bim

Measures live inside a table's `measures` array:

```json
{
  "name": "Total Revenue",
  "expression": "CALCULATE(SUM(fact_general_ledger[amount]), dim_chart_of_accounts[account_type] = \"Revenue\")",
  "formatString": "#,0.00",
  "annotations": [
    {"name": "PBI_FormatHint", "value": "{\"currencyCulture\":\"en-US\"}"}
  ]
}
```

### Format Strings

| Type | Format | Example Output |
|------|--------|----------------|
| Currency | `#,0.00` | 1,234,567.89 |
| Currency (no decimals) | `#,0` | 1,234,568 |
| Percentage | `0.0%;-0.0%;0.0%` | 45.3% |
| Integer | `#,0` | 1,234 |
| Decimal (2) | `#,0.00` | 1,234.57 |
| Date | `yyyy-MM-dd` | 2025-03-15 |

### Annotations for Formatting

```json
"annotations": [
  {"name": "PBI_FormatHint", "value": "{\"currencyCulture\":\"en-US\"}"}
]
```

---

## DAX Function Categories

### Aggregation Functions

```dax
// Basic aggregations
SUM(table[column])
AVERAGE(table[column])
MIN(table[column])
MAX(table[column])
COUNT(table[column])
COUNTROWS(table)
DISTINCTCOUNT(table[column])

// Conditional aggregation
SUMX(table, expression)
AVERAGEX(table, expression)
COUNTX(table, expression)
```

### Filter Functions

```dax
// Core filter function — modifies filter context
CALCULATE(expression, filter1, filter2, ...)

// Filter helpers
FILTER(table, condition)
ALL(table_or_column)         -- removes all filters
ALLEXCEPT(table, column)     -- removes all filters except specified
REMOVEFILTERS(table_or_column)
KEEPFILTERS(filter_expression)
VALUES(column)               -- distinct values respecting filters
HASONEVALUE(column)          -- true if single value in context
SELECTEDVALUE(column, default)
```

### Logic & Conditional

```dax
IF(condition, true_result, false_result)
SWITCH(expression, value1, result1, ..., default)
AND(cond1, cond2)  -- or use &&
OR(cond1, cond2)   -- or use ||
NOT(condition)
ISBLANK(value)
COALESCE(value1, value2, ...)
BLANK()
```

### Math Functions

```dax
DIVIDE(numerator, denominator, alternate_result)  -- safe division
ABS(number)
ROUND(number, decimals)
INT(number)
MOD(number, divisor)
POWER(base, exponent)
SQRT(number)
```

### Time Intelligence

```dax
// Year-to-Date
TOTALYTD(expression, dates_column)
DATESYTD(dates_column)

// Previous periods
PREVIOUSMONTH(dates_column)
PREVIOUSQUARTER(dates_column)
PREVIOUSYEAR(dates_column)
SAMEPERIODLASTYEAR(dates_column)

// Period-over-period
DATEADD(dates_column, number_of_intervals, interval)
// interval: DAY, MONTH, QUARTER, YEAR

// Running totals
DATESINPERIOD(dates_column, end_date, -intervals, interval_type)

// First/Last dates
FIRSTDATE(dates_column)
LASTDATE(dates_column)
STARTOFMONTH(dates_column)
ENDOFMONTH(dates_column)
STARTOFYEAR(dates_column)
ENDOFYEAR(dates_column)
```

### Table Functions

```dax
SUMMARIZE(table, group_col1, group_col2, "Name", expression)
SUMMARIZECOLUMNS(group_col1, group_col2, "Name", expression)
ADDCOLUMNS(table, "Name", expression)
SELECTCOLUMNS(table, "Name", expression)
UNION(table1, table2)
INTERSECT(table1, table2)
EXCEPT(table1, table2)
CROSSJOIN(table1, table2)
TOPN(n, table, order_expression, order_direction)
GENERATE(table, table_expression)
ROW("Column1", value1, "Column2", value2)
DATATABLE("Col1", STRING, "Col2", INTEGER, {{val1, val2}})
```

### Text Functions

```dax
CONCATENATE(text1, text2)   -- or use &
FORMAT(value, format_string)
LEFT(text, num_chars)
RIGHT(text, num_chars)
MID(text, start, length)
LEN(text)
UPPER(text)
LOWER(text)
TRIM(text)
SUBSTITUTE(text, old_text, new_text)
SEARCH(find_text, within_text, start_pos, not_found_value)
CONTAINSSTRING(within_text, find_text)
```

---

## Finance Measure Patterns (Production-Proven)

### P&L Measures (9)

```dax
// Revenue
Total Revenue = 
CALCULATE(
    SUM(fact_general_ledger[amount]),
    dim_chart_of_accounts[account_type] = "Revenue"
)

// Cost of Goods Sold
Total COGS = 
CALCULATE(
    SUM(fact_general_ledger[amount]),
    dim_chart_of_accounts[account_type] = "COGS"
)

// Gross Profit
Gross Profit = [Total Revenue] - [Total COGS]

// Gross Margin %
Gross Margin % = DIVIDE([Gross Profit], [Total Revenue], 0)

// Operating Expenses
Operating Expenses = 
CALCULATE(
    SUM(fact_general_ledger[amount]),
    dim_chart_of_accounts[account_type] = "OpEx"
)

// EBITDA
EBITDA = [Total Revenue] - [Total COGS] - [Operating Expenses]

// EBITDA Margin %
EBITDA Margin % = DIVIDE([EBITDA], [Total Revenue], 0)

// Net Income (all types)
Net Income = SUM(fact_general_ledger[amount])

// Year-to-Date Revenue
YTD Revenue = TOTALYTD([Total Revenue], dim_calendar[Date])
```

### Budget Measures (5)

```dax
Budget Amount = SUM(fact_budgets[amount])

Actual Amount = SUM(fact_general_ledger[amount])

Variance Amount = [Actual Amount] - [Budget Amount]

Variance % = DIVIDE([Variance Amount], [Budget Amount], 0)

Material Variance = 
IF(
    AND(ABS([Variance Amount]) > 50000, ABS([Variance %]) > 0.10),
    [Variance Amount],
    BLANK()
)
```

### Forecast Measures (2)

```dax
Forecast Amount = SUM(fact_forecasts[amount])

Forecast Accuracy = 
1 - ABS(
    DIVIDE(
        [Actual Amount] - [Forecast Amount],
        [Forecast Amount],
        0
    )
)
```

### Accounts Receivable / DSO Measures (7)

```dax
Total Invoices = SUM(fact_invoices[total_amount_eur])

Paid Invoices = 
CALCULATE(
    SUM(fact_invoices[total_amount_eur]),
    fact_invoices[status] = "Paid"
)

Unpaid Invoices = 
CALCULATE(
    SUM(fact_invoices[total_amount_eur]),
    fact_invoices[status] IN {"Issued", "Overdue"}
)

Total AR = [Unpaid Invoices]

DSO = DIVIDE([Total AR], [Total Revenue], 0) * 365

Overdue Invoices Amount = 
CALCULATE(
    SUM(fact_invoices[total_amount_eur]),
    fact_invoices[status] = "Overdue"
)

Overdue Invoices Count = 
CALCULATE(
    COUNTROWS(fact_invoices),
    fact_invoices[status] = "Overdue"
)
```

### Payment Measures (3)

```dax
Total Payments = SUM(fact_payments[payment_amount_eur])

Collection Rate = DIVIDE([Total Payments], [Total Invoices], 0)

Avg Days to Pay = AVERAGE(fact_payments[days_overdue])
```

---

## Advanced DAX Patterns

### Year-over-Year Growth
```dax
Revenue YoY Growth = 
VAR CurrentYear = [Total Revenue]
VAR PriorYear = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_calendar[Date]))
RETURN
    DIVIDE(CurrentYear - PriorYear, PriorYear, 0)
```

### Rolling 12-Month Average
```dax
Rolling 12M Avg Revenue = 
AVERAGEX(
    DATESINPERIOD(dim_calendar[Date], LASTDATE(dim_calendar[Date]), -12, MONTH),
    [Total Revenue]
)
```

### Running Total
```dax
Running Total Revenue = 
CALCULATE(
    [Total Revenue],
    FILTER(
        ALL(dim_calendar[Date]),
        dim_calendar[Date] <= MAX(dim_calendar[Date])
    )
)
```

### Rank
```dax
Customer Revenue Rank = 
RANKX(ALL(dim_customers), [Total Invoices],, DESC, Dense)
```

### Dynamic Currency Formatting
```dax
Revenue Display = 
VAR Value = [Total Revenue]
RETURN
    SWITCH(
        TRUE(),
        ABS(Value) >= 1000000, FORMAT(Value / 1000000, "#,0.0") & "M",
        ABS(Value) >= 1000,    FORMAT(Value / 1000, "#,0.0") & "K",
        FORMAT(Value, "#,0")
    )
```

### Parent-Child Hierarchy (Chart of Accounts)
```dax
Account Path = 
PATH(dim_chart_of_accounts[account_id], dim_chart_of_accounts[parent_account_id])

Account Depth = PATHLENGTH([Account Path])

Account Level 1 = LOOKUPVALUE(
    dim_chart_of_accounts[account_name],
    dim_chart_of_accounts[account_id],
    PATHITEM([Account Path], 1)
)
```

---

## Measure Best Practices

1. **Always use DIVIDE()** instead of `/` — handles division by zero
2. **Use variables (VAR/RETURN)** for readability and performance
3. **Name measures with spaces** — `Total Revenue` not `Total_Revenue`
4. **Add format strings** — every measure needs one
5. **Place measures on the primary fact table** — typically `fact_general_ledger`
6. **Use CALCULATE() for context modification** — not nested FILTER()
7. **Avoid SUMX when SUM suffices** — iterator functions are slower
8. **Test with DAX queries** before deploying (see `dax_queries.md`)

# Semantic Model — Deployment & Structure

## Deployment Flow

1. Build `model.bim` (TMSL JSON) locally
2. Base64-encode it (InlineBase64 payload)
3. `POST /workspaces/{wsId}/items` with type `SemanticModel`
4. Include TWO parts: `definition.pbism` + `model.bim`
5. Poll async `x-ms-operation-id` until Succeeded

## definition.pbism — STRICT FORMAT

**Only accepted format** (any other properties cause ERROR):
```json
{"version": "1.0"}
```

❌ `datasetReference`, `connections`, `connectionString` etc. → **all rejected by API**

## model.bim Structure (TMSL)

```json
{
  "compatibilityLevel": 1604,
  "model": {
    "name": "SM_Finance",
    "defaultMode": "directLake",
    "culture": "en-US",
    "tables": [...],
    "relationships": [...],
    "expressions": [...],
    "roles": [],
    "annotations": []
  }
}
```

### Direct Lake Mode

- `defaultMode: "directLake"` at model level
- NO `"mode"` property on individual partitions — Direct Lake doesn't use it
- Tables reference Delta tables in the Lakehouse via M expression (each table partition)

### Table Template

```json
{
  "name": "fact_general_ledger",
  "columns": [
    {
      "name": "entry_id",
      "dataType": "string",
      "sourceColumn": "entry_id",
      "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    },
    {
      "name": "debit_amount_eur",
      "dataType": "decimal",
      "sourceColumn": "debit_amount_eur",
      "formatString": "#,0.00",
      "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    }
  ],
  "partitions": [
    {
      "name": "fact_general_ledger",
      "source": {
        "type": "entity",
        "expression": "DatabaseQuery",
        "entityName": "fact_general_ledger",
        "schemaName": "dbo",
        "expressionSource": "DatabaseQuery"
      }
    }
  ]
}
```

### Relationship Template

```json
{
  "name": "auto_rel_gl_to_accounts",
  "fromTable": "fact_general_ledger",
  "fromColumn": "account_id",
  "toTable": "dim_chart_of_accounts",
  "toColumn": "account_id",
  "crossFilteringBehavior": "oneDirection"
}
```

All relationships are Many-to-One (from fact to dim).  
`crossFilteringBehavior: "oneDirection"` (dim → fact only).

### M Expression (Data Source)

```json
{
  "name": "DatabaseQuery",
  "kind": "m",
  "expression": [
    "let",
    "    database = Sql.Database(\"eenhbexk3...\", \"LH_Finance\")",
    "in",
    "    database"
  ]
}
```

The expression references the Lakehouse SQL analytics endpoint.

## 11 Tables

| Table | Type | Key Column | Rows (approx) |
|-------|------|-----------|----------------|
| dim_chart_of_accounts | Dim | account_id | 150 |
| dim_cost_centers | Dim | cost_center_id | 13 |
| dim_customers | Dim | customer_id | 500 |
| dim_products | Dim | product_id | 50 |
| fact_general_ledger | Fact | entry_id | 50,000 |
| fact_budgets | Fact | budget_id | 2,000 |
| fact_forecasts | Fact | forecast_id | 6,000 |
| fact_allocations | Fact | allocation_id | 65 |
| fact_invoices | Fact | invoice_id | 8,000 |
| fact_invoice_lines | Fact | line_id | 20,000 |
| fact_payments | Fact | payment_id | 7,000 |

## 11 Relationships

```
dim_chart_of_accounts → fact_general_ledger   (account_id)
dim_chart_of_accounts → fact_budgets          (account_id)
dim_chart_of_accounts → fact_forecasts        (account_id)
dim_cost_centers      → fact_general_ledger   (cost_center_id)
dim_cost_centers      → fact_budgets          (cost_center_id)
dim_cost_centers      → fact_forecasts        (cost_center_id)
dim_cost_centers      → fact_allocations      (to_cost_center_id)
dim_customers         → fact_invoices         (customer_id)
dim_products          → fact_invoice_lines    (product_id)
fact_invoices         → fact_invoice_lines    (invoice_id)
fact_invoices         → fact_payments         (invoice_id)
```

## 26 DAX Measures (on fact_general_ledger)

### P&L (9)
| Measure | DAX Logic |
|---------|-----------|
| Total Revenue | `CALCULATE(SUM(actuals[amount]), accounts[account_type]="Revenue")` |
| Total COGS | `CALCULATE(SUM(actuals[amount]), accounts[account_type]="COGS")` |
| Gross Profit | `[Total Revenue] - [Total COGS]` |
| Gross Margin % | `DIVIDE([Gross Profit], [Total Revenue], 0)` |
| Operating Expenses | `CALCULATE(SUM(actuals[amount]), accounts[account_type]="OpEx")` |
| EBITDA | `[Total Revenue] - [Total COGS] - [Operating Expenses]` |
| EBITDA Margin % | `DIVIDE([EBITDA], [Total Revenue], 0)` |
| Net Income | All account types combined |
| YTD Revenue | `TOTALYTD([Total Revenue], dim_calendar[Date])` |

### Budget (5)
| Measure | DAX Logic |
|---------|-----------|
| Budget Amount | `SUM(budget[amount])` |
| Actual Amount | `SUM(actuals[amount])` |
| Variance Amount | `[Actual Amount] - [Budget Amount]` |
| Variance % | `DIVIDE([Variance Amount], [Budget Amount], 0)` |
| Material Variance | `IF(ABS>50K AND ABS%>10%, [Variance Amount], BLANK())` |

### Forecast (2)
| Measure | DAX Logic |
|---------|-----------|
| Forecast Amount | `SUM(forecasts[amount])` |
| Forecast Accuracy | `1 - ABS(DIVIDE([Actual]-[Forecast], [Forecast], 0))` |

### AR/DSO (7)
| Measure | DAX Logic |
|---------|-----------|
| Total Invoices | `SUM(invoices[total_amount_eur])` |
| Paid Invoices | `CALCULATE(..., status="Paid")` |
| Unpaid Invoices | `CALCULATE(..., status IN {"Issued","Overdue"})` |
| Total AR | Same as Unpaid Invoices |
| DSO | `DIVIDE([Total AR], [Total Revenue], 0) * 365` |
| Overdue Invoices Amount | `CALCULATE(..., status="Overdue")` |
| Overdue Invoices Count | `CALCULATE(COUNTROWS...)` |

### Payments (3)
| Measure | DAX Logic |
|---------|-----------|
| Total Payments | `SUM(payments[payment_amount_eur])` |
| Collection Rate | `DIVIDE([Total Payments], [Total Invoices], 0)` |
| Avg Days to Pay | `AVERAGE(payments[days_overdue])` |

## API Call to Deploy

```python
import base64, json, requests

bim = json.dumps(model_bim)
bim_b64 = base64.b64encode(bim.encode()).decode()
pbism_b64 = base64.b64encode(b'{"version": "1.0"}').decode()

body = {
    "displayName": "SM_Finance",
    "type": "SemanticModel",
    "definition": {
        "parts": [
            {"path": "definition.pbism",  "payload": pbism_b64, "payloadType": "InlineBase64"},
            {"path": "model.bim",         "payload": bim_b64,   "payloadType": "InlineBase64"},
        ]
    }
}

resp = requests.post(f"{API}/workspaces/{WS_ID}/items", headers=headers, json=body)
# Returns 202 → poll x-ms-operation-id
```

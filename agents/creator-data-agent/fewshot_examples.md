# Few-Shot Examples — Writing Effective Q&A Pairs

Few-shot examples are the **single most impactful** way to improve Data Agent accuracy. They teach the agent how to translate natural language questions into correct queries.

---

## Why Few-Shots Matter

- Without few-shots: agent guesses query patterns → ~50-60% accuracy
- With 5+ few-shots: agent mimics proven patterns → ~80-90% accuracy
- With 10-15 targeted few-shots: agent handles variations → ~90-95% accuracy

---

## Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/fewShots/1.0.0/schema.json",
  "fewShots": [
    {
      "id": "unique-uuid-here",
      "question": "Natural language question",
      "query": "DAX or SQL query that answers it"
    }
  ]
}
```

Each example needs:
- **id**: A unique UUID (use `str(uuid.uuid4())` in Python)
- **question**: How a user would naturally ask this
- **query**: The exact DAX/SQL/KQL that produces the correct answer

---

## Query Language by Data Source

| Data Source Type | Query Language | Example |
|-----------------|---------------|---------|
| `semantic_model` | DAX (`EVALUATE`) | `EVALUATE ROW("Revenue", [Total Revenue])` |
| `lakehouse-tables` | Spark SQL | `SELECT SUM(amount) FROM fact_gl` |
| `data_warehouse` | T-SQL | `SELECT TOP 10 * FROM dbo.fact_gl` |
| `kusto` | KQL | `SalesTable \| summarize sum(Amount)` |

---

## Best Practices for Writing Few-Shots

### 1. Cover All Query Patterns

Aim for at least one example per pattern:

| Pattern | Example Question | Example Query (DAX) |
|---------|-----------------|---------------------|
| **Simple aggregation** | "What is the total revenue?" | `EVALUATE ROW("Total Revenue", [Total Revenue])` |
| **Filtered aggregation** | "What is Q2 revenue?" | `EVALUATE CALCULATETABLE(ROW("Revenue", [Total Revenue]), dim_calendar[quarter] = "Q2")` |
| **Ranking / Top N** | "Top 5 customers by revenue" | `EVALUATE TOPN(5, SUMMARIZE(fact_general_ledger, dim_customers[customer_name], "Revenue", [Total Revenue]), [Revenue], DESC)` |
| **Comparison** | "Revenue vs COGS by quarter" | `EVALUATE SUMMARIZE(dim_calendar, dim_calendar[quarter], "Revenue", [Total Revenue], "COGS", [COGS])` |
| **Time series** | "Monthly revenue trend" | `EVALUATE SUMMARIZE(dim_calendar, dim_calendar[period_month], "Revenue", [Total Revenue])` |
| **Ratio / Percentage** | "Gross margin by product" | `EVALUATE ADDCOLUMNS(SUMMARIZE(dim_products, dim_products[category]), "Margin", [Gross Margin %])` |
| **Variance** | "Budget vs actual by cost center" | `EVALUATE SUMMARIZE(dim_cost_centers, dim_cost_centers[cost_center_name], "Budget", [Budget Amount], "Actual", [Actual Amount], "Variance", [Budget Variance %])` |
| **Conditional** | "Which cost centers exceeded budget?" | `EVALUATE FILTER(ADDCOLUMNS(SUMMARIZE(dim_cost_centers, dim_cost_centers[cost_center_name], "Variance", [Budget Variance %]), "Exceeded", [Variance] > 0), [Exceeded])` |

### 2. Use Natural Phrasing

Write questions the way real users ask them, not how a developer would:

| Good (Natural) | Bad (Technical) |
|----------------|-----------------|
| "What's our revenue this year?" | "SELECT SUM revenue from GL" |
| "Which products are most profitable?" | "TOPN products by gross margin measure" |
| "How is marketing spending vs budget?" | "Filter budget variance where cost_center = marketing" |
| "Show me the P&L" | "EVALUATE P&L summary using GL measures" |

### 3. Match Your Instruction Terminology

If your instructions say "Use **Revenue** not sales", your few-shot questions should use "revenue":

```json
{
  "question": "What is the total revenue?",     // ✅ matches terminology
  "query": "EVALUATE ROW(\"Total Revenue\", [Total Revenue])"
},
{
  "question": "What are total sales?",           // ✅ also good — teaches synonym handling
  "query": "EVALUATE ROW(\"Total Revenue\", [Total Revenue])"
}
```

### 4. Include Edge Cases

```json
{
  "question": "Revenue for last month",
  "query": "EVALUATE CALCULATETABLE(ROW(\"Revenue\", [Total Revenue]), DATESINPERIOD(dim_calendar[date], TODAY(), -1, MONTH))"
},
{
  "question": "Year over year growth",
  "query": "EVALUATE ROW(\"Current Year\", [Total Revenue], \"Prior Year\", CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_calendar[date])), \"Growth %\", DIVIDE([Total Revenue] - CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_calendar[date])), CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_calendar[date]))))"
}
```

---

## Example: Complete fewshots.json for Finance

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/fewShots/1.0.0/schema.json",
  "fewShots": [
    {
      "id": "f001",
      "question": "What is the total revenue?",
      "query": "EVALUATE ROW(\"Total Revenue\", [Total Revenue])"
    },
    {
      "id": "f002",
      "question": "What is the gross margin percentage?",
      "query": "EVALUATE ROW(\"Gross Margin %\", [Gross Margin %])"
    },
    {
      "id": "f003",
      "question": "Show revenue by quarter",
      "query": "EVALUATE SUMMARIZE(dim_calendar, dim_calendar[quarter], \"Revenue\", [Total Revenue])"
    },
    {
      "id": "f004",
      "question": "Top 5 customers by revenue",
      "query": "EVALUATE TOPN(5, SUMMARIZE(fact_general_ledger, dim_customers[customer_name], \"Revenue\", [Total Revenue]), [Revenue], DESC)"
    },
    {
      "id": "f005",
      "question": "Budget vs actual for marketing",
      "query": "EVALUATE CALCULATETABLE(ROW(\"Budget\", [Budget Amount], \"Actual\", [Actual Amount], \"Variance %\", [Budget Variance %]), dim_cost_centers[cost_center_name] = \"Marketing\")"
    },
    {
      "id": "f006",
      "question": "What is the DSO?",
      "query": "EVALUATE ROW(\"DSO (Days)\", [DSO])"
    },
    {
      "id": "f007",
      "question": "Revenue trend by month",
      "query": "EVALUATE SUMMARIZE(dim_calendar, dim_calendar[period_month], \"Revenue\", [Total Revenue])"
    },
    {
      "id": "f008",
      "question": "Which cost centers exceeded their budget?",
      "query": "EVALUATE FILTER(ADDCOLUMNS(SUMMARIZE(dim_cost_centers, dim_cost_centers[cost_center_name], \"Variance\", [Budget Variance %]), \"Exceeded\", [Variance] > 0), [Exceeded])"
    },
    {
      "id": "f009",
      "question": "EBITDA by quarter",
      "query": "EVALUATE SUMMARIZE(dim_calendar, dim_calendar[quarter], \"EBITDA\", [EBITDA])"
    },
    {
      "id": "f010",
      "question": "Revenue by product category",
      "query": "EVALUATE SUMMARIZE(dim_products, dim_products[category], \"Revenue\", [Total Revenue])"
    }
  ]
}
```

---

## Generating UUIDs in Python

```python
import uuid

# For each few-shot example
example_id = str(uuid.uuid4())
# e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

For simplicity during development, sequential IDs like `"f001"`, `"f002"` work too — the API accepts any unique string.

---

## How Many Examples?

| Count | Quality Impact |
|-------|---------------|
| 0 | Agent guesses everything — inconsistent |
| 3–5 | Covers basic patterns — decent baseline |
| 8–12 | Covers most query types — good quality |
| 15–20 | Covers edge cases + synonyms — excellent |
| 25+ | Diminishing returns — focus on instruction quality instead |

**Sweet spot**: 10–15 examples covering the 8 query patterns above.

---

## Validating Few-Shots

Before deploying, test each query independently:

1. Open the semantic model in Fabric portal
2. Go to "New query" (DAX query view)
3. Paste each `query` value and run it
4. Verify it returns correct results
5. Fix any measure name mismatches

**Common failures:**
- Measure name doesn't match model.bim → `[Total Revenue]` vs `[TotalRevenue]`
- Table alias wrong → `dim_calendar` vs `Calendar`
- Column name case mismatch → `customer_name` vs `CustomerName`

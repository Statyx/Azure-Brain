# Relationships — Star Schema Design & Rules

## Overview

Fabric semantic models use a star schema: dimension tables connected to fact tables
via Many-to-One relationships. Relationships enable filter context propagation,
which is the foundation of how DAX measures respond to slicers and visuals.

---

## Relationship Definition in model.bim

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

### Properties

| Property | Description | Values |
|----------|-------------|--------|
| `name` | Unique relationship identifier | `auto_rel_{from}_{to}` convention |
| `fromTable` | The "many" side (facts) | Fact table name |
| `fromColumn` | FK column on many side | Column name |
| `toTable` | The "one" side (dimensions) | Dimension table name |
| `toColumn` | PK column on one side | Column name |
| `crossFilteringBehavior` | Filter direction | `oneDirection` or `bothDirections` |

### Cross-Filter Behavior

| Value | Meaning | Use When |
|-------|---------|----------|
| `oneDirection` | Dim → Fact only (recommended) | Standard star schema |
| `bothDirections` | Both directions | Bridge tables, M2M patterns |

**Best practice:** Always use `oneDirection` unless you have a specific reason for bi-directional.
Bi-directional filtering can cause ambiguity and performance issues.

---

## Star Schema Pattern

```
                    ┌─────────────────────┐
                    │ dim_chart_of_accounts│
                    │  (account_id PK)     │
                    └──────────┬──────────┘
                               │ 1
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼ *                    ▼ *                    ▼ *
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│fact_general_  │  │ fact_budgets  │  │fact_forecasts │
│ledger         │  │               │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
        ▲ *                                    
        │                                      
        │ 1                                    
┌───────────────┐     ┌───────────────┐  ┌───────────────┐
│dim_cost_centers│────▶│ fact_budgets  │  │fact_forecasts │
│               │  1  *│               │  *│               │
└───────────────┘     └───────────────┘  └───────────────┘

        ┌───────────────┐
        │ dim_customers  │
        │  (customer_id) │
        └──────┬────────┘
               │ 1
               ▼ *
        ┌───────────────┐     ┌───────────────┐
        │ fact_invoices  │────▶│fact_invoice_  │
        │               │  1  *│lines          │
        └──────┬────────┘     └───────┬───────┘
               │ 1                    ▲ *
               ▼ *                    │ 1
        ┌───────────────┐     ┌───────────────┐
        │ fact_payments  │     │ dim_products   │
        └───────────────┘     └───────────────┘
```

---

## Finance Model Relationships (11 total)

```json
[
  {
    "name": "auto_rel_gl_to_accounts",
    "fromTable": "fact_general_ledger",
    "fromColumn": "account_id",
    "toTable": "dim_chart_of_accounts",
    "toColumn": "account_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_budgets_to_accounts",
    "fromTable": "fact_budgets",
    "fromColumn": "account_id",
    "toTable": "dim_chart_of_accounts",
    "toColumn": "account_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_forecasts_to_accounts",
    "fromTable": "fact_forecasts",
    "fromColumn": "account_id",
    "toTable": "dim_chart_of_accounts",
    "toColumn": "account_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_gl_to_costcenters",
    "fromTable": "fact_general_ledger",
    "fromColumn": "cost_center_id",
    "toTable": "dim_cost_centers",
    "toColumn": "cost_center_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_budgets_to_costcenters",
    "fromTable": "fact_budgets",
    "fromColumn": "cost_center_id",
    "toTable": "dim_cost_centers",
    "toColumn": "cost_center_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_forecasts_to_costcenters",
    "fromTable": "fact_forecasts",
    "fromColumn": "cost_center_id",
    "toTable": "dim_cost_centers",
    "toColumn": "cost_center_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_allocations_to_costcenters",
    "fromTable": "fact_allocations",
    "fromColumn": "to_cost_center_id",
    "toTable": "dim_cost_centers",
    "toColumn": "cost_center_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_invoices_to_customers",
    "fromTable": "fact_invoices",
    "fromColumn": "customer_id",
    "toTable": "dim_customers",
    "toColumn": "customer_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_invoicelines_to_products",
    "fromTable": "fact_invoice_lines",
    "fromColumn": "product_id",
    "toTable": "dim_products",
    "toColumn": "product_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_invoicelines_to_invoices",
    "fromTable": "fact_invoice_lines",
    "fromColumn": "invoice_id",
    "toTable": "fact_invoices",
    "toColumn": "invoice_id",
    "crossFilteringBehavior": "oneDirection"
  },
  {
    "name": "auto_rel_payments_to_invoices",
    "fromTable": "fact_payments",
    "fromColumn": "invoice_id",
    "toTable": "fact_invoices",
    "toColumn": "invoice_id",
    "crossFilteringBehavior": "oneDirection"
  }
]
```

---

## Relationship Design Rules

### Rule 1: Always Many-to-One
- `fromTable` = Many side (fact tables)
- `toTable` = One side (dimension tables, or parent in fact-to-fact)
- The "one" side must have unique values in the join column

### Rule 2: No Ambiguous Paths
- There must be **only one active path** between any two tables
- If multiple paths exist (e.g., date dimension used for both order_date and ship_date):
  - Make one relationship **active** (default)
  - Make others **inactive**: add `"isActive": false`
  - Use `USERELATIONSHIP()` in DAX to activate the inactive one

```json
{
  "name": "rel_orders_order_date",
  "fromTable": "fact_orders",
  "fromColumn": "order_date",
  "toTable": "dim_calendar",
  "toColumn": "date",
  "crossFilteringBehavior": "oneDirection"
}
// Active by default (isActive not specified = true)

{
  "name": "rel_orders_ship_date",
  "fromTable": "fact_orders",
  "fromColumn": "ship_date",
  "toTable": "dim_calendar",
  "toColumn": "date",
  "isActive": false,
  "crossFilteringBehavior": "oneDirection"
}
```

```dax
// DAX to use inactive relationship
Shipped Revenue = 
CALCULATE(
    [Total Revenue],
    USERELATIONSHIP(fact_orders[ship_date], dim_calendar[date])
)
```

### Rule 3: Referential Integrity
- Every FK value in the fact should exist in the dimension
- Orphan rows (FK not in dim) won't be filterable
- Use DAX queries to detect orphans (see `dax_queries.md`)

### Rule 4: Naming Convention
- Name: `auto_rel_{fromTable_short}_{toTable_short}`
- Or: `rel_{meaningfulDescription}`
- Be consistent across the model

### Rule 5: Avoid Bi-Directional Unless Required
- Bi-directional filters propagate in both directions
- Can cause:
  - Ambiguous paths
  - Unexpected filter results
  - Performance degradation
- Only use for: bridge tables, many-to-many patterns

---

## Common Relationship Patterns

### Pattern: Role-Playing Dimension

When a fact table has multiple date columns pointing to the same calendar dimension:

```json
// Active: Order Date
{"fromTable": "fact_sales", "fromColumn": "order_date", "toTable": "dim_calendar", "toColumn": "date"}

// Inactive: Ship Date
{"fromTable": "fact_sales", "fromColumn": "ship_date", "toTable": "dim_calendar", "toColumn": "date", "isActive": false}

// Inactive: Due Date
{"fromTable": "fact_sales", "fromColumn": "due_date", "toTable": "dim_calendar", "toColumn": "date", "isActive": false}
```

### Pattern: Fact-to-Fact (via shared dimension)

Don't create direct fact-to-fact relationships unless there's a parent-child hierarchy.
Instead, use shared dimensions to create indirect connections.

Exception: `fact_invoices` → `fact_invoice_lines` is a valid parent-child pattern.

### Pattern: Bridge Table (Many-to-Many)

For many-to-many relationships, create a bridge table:

```
dim_customers ←1:*— bridge_customer_segments —*:1→ dim_segments
```

Both relationships use `"crossFilteringBehavior": "bothDirections"`.

---

## Validation Checklist

Before deploying relationships:

- [ ] Every fact table has at least one relationship to a dimension
- [ ] All relationships are Many-to-One (fromTable=many, toTable=one)
- [ ] No ambiguous paths between any two tables
- [ ] Cross-filtering is `oneDirection` unless specifically needed
- [ ] Join columns have matching data types
- [ ] Names follow consistent convention
- [ ] Orphan key detection queries pass (see `dax_queries.md`)

# Visual Catalog — All Visual Types, Projections & prototypeQuery

---

## Visual Type Reference

| Visual | `visualType` value | Projection Buckets | prototypeQuery? | Notes |
|--------|-------------------|-------------------|:---:|-------|
| KPI Card (new) | `cardVisual` | `Data` | YES | **NOT** `card` (deprecated) |
| Card (old) | `card` | `Values` | YES | Deprecated — avoid |
| Clustered Bar | `clusteredBarChart` | `Category` + `Y` | YES | Horizontal bars |
| Clustered Column | `clusteredColumnChart` | `Category` + `Y` | YES | Vertical bars |
| Stacked Bar | `stackedBarChart` | `Category` + `Y` + `Series` | YES | |
| Stacked Column | `stackedColumnChart` | `Category` + `Y` + `Series` | YES | |
| Line Chart | `lineChart` | `Category` + `Y` | YES | |
| Area Chart | `areaChart` | `Category` + `Y` | YES | |
| Line & Column | `lineClusteredColumnComboChart` | `Category` + `Y` + `Y2` | YES | |
| Donut Chart | `donutChart` | `Category` + `Y` | YES | |
| Pie Chart | `pieChart` | `Category` + `Y` | YES | |
| Table | `tableEx` | `Values` | YES | |
| Matrix | `matrix` | `Rows` + `Columns` + `Values` | YES | |
| Slicer | `slicer` | `Values` | YES | Filter visual |
| Textbox | `textbox` | none | **NO** | Static text, no data binding |
| Shape | `shape` | none | **NO** | Decorative |
| Image | `image` | none | **NO** | |
| KPI | `kpi` | `Indicator` + `TrendAxis` + `Goals` | YES | |
| Gauge | `gauge` | `Y` + `MinValue` + `MaxValue` + `TargetValue` | YES | |
| Treemap | `treemap` | `Group` + `Values` | YES | |
| Waterfall | `waterfallChart` | `Category` + `Y` + `Breakdown` | YES | |
| Scatter | `scatterChart` | `X` + `Y` + `Size` + `Details` | YES | |
| Map | `map` | `Category` + `Size` | YES | |
| Filled Map | `filledMap` | `Location` + `Values` | YES | |

**CRITICAL PITFALL**: `card` (old) vs `cardVisual` (new). Always use `cardVisual` with `Data` bucket.

---

## Projections — Data Binding

Projections tell the visual which measures/columns to display.

### Card Visual (KPI)
```json
"projections": {
  "Data": [
    {"queryRef": "fact_general_ledger.Total Revenue"}
  ]
}
```

### Bar / Column / Line / Area / Donut Charts
```json
"projections": {
  "Category": [
    {"queryRef": "dim_cost_centers.region"}
  ],
  "Y": [
    {"queryRef": "fact_general_ledger.Total Revenue"}
  ]
}
```
> **Single-color problem**: Without `Series`, all bars use the same Fluent 2 blue.
> To get multi-colored bars, add the category column to `Series` too — see below.

### Colored Bar Charts (Multi-Color per Category)
```json
"projections": {
  "Category": [{"queryRef": "dim_cost_centers.region"}],
  "Y": [{"queryRef": "fact_general_ledger.Total Revenue"}],
  "Series": [{"queryRef": "dim_cost_centers.region"}]
}
```
**Why**: Adding the same column to both `Category` and `Series` makes PBI assign a different Fluent 2 theme color to each bar. Without this, a single-measure bar chart renders all bars in the first theme color (#118DFF blue).

**Important**: When using this pattern, hide the legend (it duplicates axis labels):
```json
"objects": {
  "legend": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
}
```

> `dataPoint.colorByCategory: true` does NOT work when deploying via API. See `known_issues.md` Issue #13.

### Stacked Charts (with Series)
```json
"projections": {
  "Category": [{"queryRef": "dim_calendar.fiscal_year"}],
  "Y": [{"queryRef": "fact_general_ledger.Total Revenue"}],
  "Series": [{"queryRef": "dim_cost_centers.region"}]
}
```

### Combo Chart (Line & Column)
```json
"projections": {
  "Category": [{"queryRef": "dim_calendar.fiscal_year"}],
  "Y": [{"queryRef": "fact_general_ledger.Total Revenue"}],
  "Y2": [{"queryRef": "fact_general_ledger.Gross Margin %"}]
}
```

### Table
```json
"projections": {
  "Values": [
    {"queryRef": "dim_cost_centers.region"},
    {"queryRef": "fact_general_ledger.Total Revenue"},
    {"queryRef": "fact_general_ledger.Total Expenses"}
  ]
}
```

### Matrix
```json
"projections": {
  "Rows": [{"queryRef": "dim_cost_centers.region"}],
  "Columns": [{"queryRef": "dim_calendar.fiscal_year"}],
  "Values": [{"queryRef": "fact_general_ledger.Total Revenue"}]
}
```

### Slicer
```json
"projections": {
  "Values": [
    {"queryRef": "dim_calendar.fiscal_year"}
  ]
}
```

---

## prototypeQuery — MANDATORY for Data Visuals

Without `prototypeQuery`, visuals render as empty containers. No error message.

### Full Structure
```json
{
  "Version": 2,
  "From": [
    {"Name": "<alias>", "Entity": "<table_name>", "Type": 0}
  ],
  "Select": [
    // Measure or Column references
  ],
  "OrderBy": [
    // Optional sorting
  ]
}
```

### From Clause
```json
{"Name": "f", "Entity": "fact_general_ledger", "Type": 0}
```
- `Name`: Short alias (typically single letter: `f`, `d`, `c`, etc.)
- `Entity`: Exact table name from semantic model
- `Type`: Always `0` (table)

### Select — Measure Reference
```json
{
  "Measure": {
    "Expression": {"SourceRef": {"Source": "f"}},
    "Property": "Total Revenue"
  },
  "Name": "fact_general_ledger.Total Revenue",
  "NativeReferenceName": "Total Revenue"
}
```

### Select — Column Reference
```json
{
  "Column": {
    "Expression": {"SourceRef": {"Source": "d"}},
    "Property": "region"
  },
  "Name": "dim_cost_centers.region",
  "NativeReferenceName": "region"
}
```

### OrderBy — Descending by Measure
```json
{
  "Direction": 2,
  "Expression": {
    "Measure": {
      "Expression": {"SourceRef": {"Source": "f"}},
      "Property": "Total Revenue"
    }
  }
}
```
- `Direction`: `1` = Ascending, `2` = Descending

---

## Complete Visual Examples

### Example 1: KPI Card — Total Revenue

```json
{
  "name": "card_total_revenue",
  "layouts": [{"id": 0, "position": {"x": 30, "y": 60, "z": 1, "width": 390, "height": 120}}],
  "singleVisual": {
    "visualType": "cardVisual",
    "projections": {
      "Data": [{"queryRef": "fact_general_ledger.Total Revenue"}]
    },
    "prototypeQuery": {
      "Version": 2,
      "From": [{"Name": "f", "Entity": "fact_general_ledger", "Type": 0}],
      "Select": [{
        "Measure": {
          "Expression": {"SourceRef": {"Source": "f"}},
          "Property": "Total Revenue"
        },
        "Name": "fact_general_ledger.Total Revenue",
        "NativeReferenceName": "Total Revenue"
      }]
    },
    "drillFilterOtherVisuals": true,
    "objects": {
      "outline": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
      "calloutValue": [{"properties": {
        "fontSize": {"expr": {"Literal": {"Value": "27D"}}},
        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#252423'"}}}}}
      }}],
      "categoryLabel": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
    },
    "vcObjects": {
      "title": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": {"expr": {"Literal": {"Value": "'Total Revenue'"}}},
        "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#616161'"}}}}}
      }}],
      "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
      "border": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#c7c8ce'"}}}}},
        "radius": {"expr": {"Literal": {"Value": "8L"}}}
      }}],
      "dropShadow": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#cccccc'"}}}}},
        "preset": {"expr": {"Literal": {"Value": "'Custom'"}}},
        "shadowBlur": {"expr": {"Literal": {"Value": "5L"}}},
        "shadowDistance": {"expr": {"Literal": {"Value": "4L"}}},
        "transparency": {"expr": {"Literal": {"Value": "85L"}}}
      }}]
    }
  },
  "howCreated": "Copilot"
}
```

### Example 2: Clustered Bar Chart — Revenue by Region (Multi-Colored)

```json
{
  "name": "bar_revenue_region",
  "layouts": [{"id": 0, "position": {"x": 30, "y": 325, "z": 2, "width": 595, "height": 185}}],
  "singleVisual": {
    "visualType": "clusteredBarChart",
    "projections": {
      "Category": [{"queryRef": "dim_cost_centers.region"}],
      "Y": [{"queryRef": "fact_general_ledger.Total Revenue"}],
      "Series": [{"queryRef": "dim_cost_centers.region"}]
    },
    "prototypeQuery": {
      "Version": 2,
      "From": [
        {"Name": "d", "Entity": "dim_cost_centers", "Type": 0},
        {"Name": "f", "Entity": "fact_general_ledger", "Type": 0}
      ],
      "Select": [
        {
          "Column": {
            "Expression": {"SourceRef": {"Source": "d"}},
            "Property": "region"
          },
          "Name": "dim_cost_centers.region",
          "NativeReferenceName": "region"
        },
        {
          "Measure": {
            "Expression": {"SourceRef": {"Source": "f"}},
            "Property": "Total Revenue"
          },
          "Name": "fact_general_ledger.Total Revenue",
          "NativeReferenceName": "Total Revenue"
        }
      ],
      "OrderBy": [{
        "Direction": 2,
        "Expression": {
          "Measure": {
            "Expression": {"SourceRef": {"Source": "f"}},
            "Property": "Total Revenue"
          }
        }
      }]
    },
    "drillFilterOtherVisuals": true,
    "objects": {
      "categoryAxis": [{"properties": {"fontSize": {"expr": {"Literal": {"Value": "10D"}}}}}],
      "valueAxis": [{"properties": {"fontSize": {"expr": {"Literal": {"Value": "10D"}}}}}],
      "legend": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
    },
    "vcObjects": {
      "title": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": {"expr": {"Literal": {"Value": "'Revenue by Region'"}}},
        "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#252423'"}}}}}
      }}],
      "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
      "border": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#c7c8ce'"}}}}},
        "radius": {"expr": {"Literal": {"Value": "8L"}}}
      }}],
      "dropShadow": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#cccccc'"}}}}},
        "preset": {"expr": {"Literal": {"Value": "'Custom'"}}},
        "shadowBlur": {"expr": {"Literal": {"Value": "5L"}}},
        "shadowDistance": {"expr": {"Literal": {"Value": "4L"}}},
        "transparency": {"expr": {"Literal": {"Value": "85L"}}}
      }}]
    }
  },
  "howCreated": "Copilot"
}
```

> **Key patterns**: `Series` added for multi-color, legend hidden, Fluent 2 structural colors (#252423 title, #c7c8ce border, #cccccc shadow, 8L radius).

### Example 3: Line Chart — Revenue Trend by Month

```json
{
  "name": "line_revenue_trend",
  "layouts": [{"id": 0, "position": {"x": 655, "y": 325, "z": 3, "width": 595, "height": 185}}],
  "singleVisual": {
    "visualType": "lineChart",
    "projections": {
      "Category": [{"queryRef": "dim_calendar.month_name"}],
      "Y": [{"queryRef": "fact_general_ledger.Total Revenue"}]
    },
    "prototypeQuery": {
      "Version": 2,
      "From": [
        {"Name": "c", "Entity": "dim_calendar", "Type": 0},
        {"Name": "f", "Entity": "fact_general_ledger", "Type": 0}
      ],
      "Select": [
        {
          "Column": {
            "Expression": {"SourceRef": {"Source": "c"}},
            "Property": "month_name"
          },
          "Name": "dim_calendar.month_name",
          "NativeReferenceName": "month_name"
        },
        {
          "Measure": {
            "Expression": {"SourceRef": {"Source": "f"}},
            "Property": "Total Revenue"
          },
          "Name": "fact_general_ledger.Total Revenue",
          "NativeReferenceName": "Total Revenue"
        }
      ]
    },
    "drillFilterOtherVisuals": true,
    "objects": {},
    "vcObjects": {
      "title": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": {"expr": {"Literal": {"Value": "'Revenue Trend'"}}}
      }}]
    }
  },
  "howCreated": "Copilot"
}
```

### Example 4: Textbox — Dashboard Title

```json
{
  "name": "title_textbox",
  "layouts": [{"id": 0, "position": {"x": 30, "y": 10, "z": 0, "width": 1220, "height": 40}}],
  "singleVisual": {
    "visualType": "textbox",
    "drillFilterOtherVisuals": true,
    "objects": {
      "general": [{"properties": {
        "paragraphs": [{
          "textRuns": [{
            "value": "Finance Performance Dashboard",
            "textStyle": {
              "fontFamily": "Segoe UI",
              "fontSize": "14pt",
              "fontWeight": "bold"
            }
          }],
          "horizontalTextAlignment": "left"
        }]
      }}]
    },
    "vcObjects": {}
  },
  "howCreated": "Copilot"
}
```

---

## Measure Name Matching — EXACT Match Required

| Model Definition | Visual Reference | Works? |
|:---:|:---:|:---:|
| `Total Revenue` | `Total Revenue` | YES |
| `Total Revenue` | `Total_Revenue` | **NO** |
| `Total Revenue` | `total revenue` | **NO** |
| `Gross Margin %` | `Gross Margin %` | YES |
| `Gross Margin %` | `Gross Margin` | **NO** |

Always verify against `model.bim` or via DAX `EVALUATE` query before using in visuals.

---

## Available Finance Measures (from SM_Finance)

For the complete list with DAX code, see `agents/semantic-model-agent/dax_measures.md`.

### Quick Reference (26 measures)

**P&L (9)**: Total Revenue, Total COGS, Gross Profit, Gross Margin %, Total Operating Expenses, EBITDA, EBITDA Margin %, Net Income, Net Margin %

**Budget (5)**: Budget Amount, Budget Variance, Budget Variance %, Forecast Amount, Forecast Variance

**AR / DSO (7)**: Total Invoiced, Total Collected, Outstanding AR, DSO, Overdue Amount, Overdue %, Average Collection Days

**Payments (3)**: Total Payments, On-Time Payment Rate, Average Payment Delay Days

---

## Python: Visual Builder Helpers

```python
import json, secrets

def make_visual_id(prefix: str = "") -> str:
    """Generate unique 20-char hex ID for visual name."""
    return prefix + secrets.token_hex(10)

def make_measure_select(alias: str, table: str, measure: str) -> dict:
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Source": alias}},
            "Property": measure
        },
        "Name": f"{table}.{measure}",
        "NativeReferenceName": measure
    }

def make_column_select(alias: str, table: str, column: str) -> dict:
    return {
        "Column": {
            "Expression": {"SourceRef": {"Source": alias}},
            "Property": column
        },
        "Name": f"{table}.{column}",
        "NativeReferenceName": column
    }

def make_from(alias: str, table: str) -> dict:
    return {"Name": alias, "Entity": table, "Type": 0}

def make_card(name, x, y, w, h, table, measure, title, alias="f"):
    """Build a complete card visual config dict."""
    return {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 1, "width": w, "height": h}}],
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": f"{table}.{measure}"}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [make_from(alias, table)],
                "Select": [make_measure_select(alias, table, measure)]
            },
            "drillFilterOtherVisuals": True,
            "objects": {
                "outline": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "calloutValue": [{"properties": {"fontSize": {"expr": {"Literal": {"Value": "27D"}}}}}],
                "categoryLabel": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}}
                }}],
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "border": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E0E0E0'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "4L"}}}
                }}]
            }
        },
        "howCreated": "Copilot"
    }
```

# Pages & Layout — Canvas Grid System

> **See also**: `dashboard_design_guide.md` for comprehensive design principles, typography scale, color system, and setup checklist.

---

## Design Principles (Quick Reference)

1. **F-Pattern reading**: KPIs top-left → charts middle → detail tables bottom
2. **One story per page**: Each page answers ONE business question
3. **Consistent grid**: All visuals align to the column system below — no arbitrary positioning
4. **White space matters**: Minimum 10px gap between visuals; don't fill every pixel
5. **5-second rule**: User understands the main message within 5 seconds

---

## Standard Canvas

| Property | Value | Notes |
|----------|-------|-------|
| Width | 1280 px | 16:9 aspect ratio |
| Height | 720 px | Standard HD |
| `displayOption` | `1` | Fit to page |

All visual coordinates are relative to this 1280×720 grid.

---

## Margin & Spacing Rules

| Rule | Value |
|------|-------|
| Left/right margin | 30 px |
| Top margin | 10 px |
| Gap between columns | 20 px |
| Gap between rows | 10–15 px |
| Usable width | 1220 px (1280 − 30 − 30) |

---

## Column Systems

### 3-Column Layout (KPI Cards)
```
Usable: 1220 px
Columns: 3
Gap: 20 px
Column width: (1220 - 2×20) / 3 = 390 px (rounded)

x positions:  30  |  440  |  850
```

### 2-Column Layout (Charts)
```
Usable: 1220 px
Columns: 2
Gap: 30 px
Column width: (1220 - 30) / 2 = 595 px

x positions:  30  |  655
```

### Full-Width Layout
```
x: 30, width: 1220
```

---

## Recommended Heights

| Element | Height | Notes |
|---------|--------|-------|
| Title bar (textbox) | 40 px | Dashboard heading |
| KPI Card | 120 px | Minimum for readable calloutValue |
| Small Chart | 185 px | |
| Medium Chart | 250 px | More detail / labels |
| Large Chart | 350 px | Complex charts, tables |
| Slicer | 40–60 px | Dropdown style |
| Table / Matrix | 200–350 px | Depends on row count |

**CRITICAL**: Card height must be ≥ 120px when `calloutValue.fontSize: 27D`, otherwise values clip.

---

## Dashboard Templates

### Template A: Executive Overview (6 KPIs + 4 Charts)

```
y=10    [─────────── Title Bar (1220×40) ───────────]

y=60    [ KPI 1 (390×120) ] [ KPI 2 (390×120) ] [ KPI 3 (390×120) ]

y=190   [ KPI 4 (390×120) ] [ KPI 5 (390×120) ] [ KPI 6 (390×120) ]

y=325   [ Chart 1 (595×185) ]    [ Chart 2 (595×185) ]

y=525   [ Chart 3 (595×185) ]    [ Chart 4 (595×185) ]

Total: 710 px → fits in 720 canvas
```

Visual coordinates:
| Visual | x | y | width | height |
|--------|---|---|-------|--------|
| Title | 30 | 10 | 1220 | 40 |
| KPI 1 | 30 | 60 | 390 | 120 |
| KPI 2 | 440 | 60 | 390 | 120 |
| KPI 3 | 850 | 60 | 390 | 120 |
| KPI 4 | 30 | 190 | 390 | 120 |
| KPI 5 | 440 | 190 | 390 | 120 |
| KPI 6 | 850 | 190 | 390 | 120 |
| Chart 1 | 30 | 325 | 595 | 185 |
| Chart 2 | 655 | 325 | 595 | 185 |
| Chart 3 | 30 | 525 | 595 | 185 |
| Chart 4 | 655 | 525 | 595 | 185 |

### Template B: KPI Row + One Large Chart

```
y=10    [─────────── Title Bar (1220×40) ───────────]

y=60    [ KPI 1 (390×120) ] [ KPI 2 (390×120) ] [ KPI 3 (390×120) ]

y=195   [──────────── Large Chart (1220×350) ────────────]

y=560   [──────── Slicer Row (1220×50) ────────]
```

### Template C: Table/Matrix Focus

```
y=10    [─────────── Title Bar (1220×40) ───────────]

y=60    [ KPI 1 (295×120) ] [ KPI 2 (295×120) ] [ KPI 3 (295×120) ] [ KPI 4 (295×120) ]

y=195   [──────────── Table or Matrix (1220×510) ────────────]
```

4-column for KPI row:
```
Column width: (1220 - 3×20) / 4 = 290 px (rounded to 295)
x positions:  30  |  335  |  640  |  945
Widths: 295 each (last one: 285 to fit)
```

---

## Multi-Page Reports

### Adding Pages

Each page is a `section` in the `sections[]` array:

```python
sections = [
    make_section("Overview", "Executive Overview", overview_visuals),
    make_section("Revenue", "Revenue Analysis", revenue_visuals),
    make_section("Budget", "Budget vs Actual", budget_visuals),
    make_section("AR", "Accounts Receivable", ar_visuals),
]
```

### Page Naming Rules
- `name`: Internal identifier — no spaces, no special characters, unique per report
- `displayName`: User-visible tab name — spaces OK, unicode OK
- `config`: Must contain `{"name": "<name>"}` stringified — name must match the `name` field

### Page Order
Pages appear in the order they occur in `sections[]`. First page is shown by default.
The `activeSectionIndex` in report config controls which page opens first (0-based).

---

## Z-Index Stacking

The `z` property controls visual overlap order:
- `z: 0` — Background elements (shapes, images)
- `z: 1` — Standard visuals (cards, charts)
- `z: 2+` — Overlapping elements
- Higher `z` = on top

---

## Python: Layout Helpers

```python
def kpi_row_3col(y: int, measures: list[tuple[str, str, str]], table: str = "fact_general_ledger"):
    """Generate 3 KPI cards in a row.
    
    Args:
        y: Y position of the row
        measures: List of (measure_name, title, visual_id) tuples
    """
    x_positions = [30, 440, 850]
    visuals = []
    for i, (measure, title, vid) in enumerate(measures):
        visuals.append(make_card(vid, x_positions[i], y, 390, 120, table, measure, title))
    return visuals

def chart_row_2col(y: int, chart1_config: dict, chart2_config: dict):
    """Position two chart configs side by side."""
    chart1_config["layouts"][0]["position"].update({"x": 30, "y": y, "width": 595, "height": 185})
    chart2_config["layouts"][0]["position"].update({"x": 655, "y": y, "width": 595, "height": 185})
    return [chart1_config, chart2_config]

def full_width(y: int, height: int, config: dict):
    """Position a visual full-width."""
    config["layouts"][0]["position"].update({"x": 30, "y": y, "width": 1220, "height": height})
    return config
```

---

## Finance Dashboard — RPT_Finance_Dashboard (5 Pages)

Uses the **Copilot standard layout** matching the working `Finance_Report` in the same workspace. Light theme with drop shadows, accent bars on cards.

### Standard Page Layout (Copilot Style)

```
┌────────────────────────────────────────────────────────────────┐
│ Header bar (shape)     h=80          [Slicer1] [Slicer2]      │  y=0
│ Page Title (textbox)   z=2                                     │  y=20
├──────────────────────────────┬─────────────────────────────────┤
│ Card 1  (w=595, h=112)      │ Card 2   (w=595, h=112)        │  y=100
├──────────────────────────────┬─────────────────────────────────┤
│ Chart 1 (w=595, h=224)      │ Chart 2  (w=595, h=224)        │  y=222
├──────────────────────────────┬─────────────────────────────────┤
│ Chart 3 (w=595, h=224)      │ Chart 4  (w=595, h=224)        │  y=456
└──────────────────────────────┴─────────────────────────────────┘
```

Grid: x=40 (left col), x=645 (right col), w=595 each

| Element | x | y | z | w×h | Notes |
|---------|---|---|---|-----|-------|
| Header shape | 0 | 0 | 1 | 1280×80 | fill=off, outline=off, dropShadow=on |
| Page title | 40 | 20 | 2 | 620×40 | Segoe UI 14pt bold |
| Slicer 1 | 840 | 0 | 2 | 212×72 | Dropdown mode |
| Slicer 2 | 1068 | 0 | 2 | 212×72 | Dropdown mode |
| Card left | 40 | 100 | 1 | 595×112 | cardVisual with accentBar |
| Card right | 645 | 100 | 1 | 595×112 | cardVisual with accentBar |
| Chart TL | 40 | 222 | 1 | 595×224 | Any axis chart |
| Chart TR | 645 | 222 | 1 | 595×224 | Any axis chart |
| Chart BL | 40 | 456 | 1 | 595×224 | Any axis chart |
| Chart BR | 645 | 456 | 1 | 595×224 | Any axis chart |

### vcObjects (standard for all visuals)

```json
"vcObjects": {
  "dropShadow": [{"properties": {"show": "true", "color": "#A6ADC6", "preset": "Custom", "shadowSpread": "0L", "shadowBlur": "5L", "angle": "90L", "shadowDistance": "4L", "transparency": "85L"}}],
  "background": [{"properties": {"show": "true"}}],
  "border": [{"properties": {"show": "true", "color": "#E0E0E0", "radius": "4L"}}],
  "title": [{"properties": {"show": "true", "text": "'Chart Title'"}}]
}
```

### Card objects (standard)

```json
"objects": {
  "accentBar": [{"properties": {"color": "#118DFF"}, "selector": {"metadata": "table.Measure"}}],
  "outline": [{"properties": {"show": "false"}}],
  "layout": [{"properties": {"maxTiles": "10L"}}]
}
```

### Slicer objects (standard)

```json
"objects": {
  "data": [{"properties": {"mode": "Dropdown"}}],
  "header": [{"properties": {"show": "true", "fontFamily": "Segoe UI", "textSize": "9L"}}],
  "selection": [{"properties": {"selectAllCheckboxEnabled": "true"}}]
}
```

### Page 1: Financial Performance Overview (10 visuals)
| Slicers | period_month, fiscal_year |
| Cards | Total Revenue, Net Income |
| Charts | Gross Profit by Fiscal Year (bar), EBITDA by Month (line), Gross Margin % by Fiscal Year (bar), Net Income by Month (line) |

### Page 2: P&L Analysis (10 visuals)
| Slicers | period_month, fiscal_year |
| Cards | Total Revenue, Total COGS |
| Charts | Revenue vs COGS by Month (clustered column, 2 measures), Margin Trends (line, 2 measures), Revenue by Sub-Category (bar), OpEx by Cost Center (bar) |

### Page 3: Budget vs Actuals Analysis (10 visuals)
| Slicers | cost_center_name, fiscal_year |
| Cards | Budget Amount, Actual Amount |
| Charts | Budget vs Actual by Account (bar, 2 measures), Variance by Account (bar), Variance % by Month (line), Variance by Cost Center (bar) |

### Page 4: Cash Flow & Receivables (10 visuals)
| Slicers | region, fiscal_year |
| Cards | Total AR, DSO |
| Charts | AR by Customer (bar), Invoices by Status (donut), Overdue by Customer (bar), Paid vs Unpaid by Region (column, 2 measures) |

### Page 5: Product Profitability Analysis (9 visuals)
| Slicers | category (1 slicer only) |
| Cards | Gross Profit, Gross Margin % |
| Charts | Revenue by Product (bar), Revenue vs COGS Trend (line, 2 measures), Gross Profit by Category (bar), Gross Profit Trend (line) |

### Generation Script

The report is generated by `temp/rebuild_report.py` using the exact visual format from the Copilot-generated Finance_Report reference. Deploy with:
```bash
python temp/rebuild_report.py          # Generate report.json
python src/deploy_report.py --from-file report.json  # Deploy to Fabric
```

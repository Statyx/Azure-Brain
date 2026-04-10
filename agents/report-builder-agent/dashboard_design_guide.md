# Dashboard Design Guide — Layout, Typography & Setup Best Practices

This file is the **definitive reference** for building professional, readable, and consistent Power BI dashboards via API. It codifies layout principles, typography rules, color usage, and page setup standards.

---

## 1. Design Principles

### The 5-Second Rule
A user should understand the dashboard's main message within 5 seconds of looking at it. This means:
- **KPIs first** — Place the most important numbers at the top-left (F-pattern reading)
- **Progressive detail** — Summary metrics → charts → detail tables, top to bottom
- **One story per page** — Each page answers ONE business question

### Visual Hierarchy (Top → Bottom)
```
1. Page title           — Establishes context ("What am I looking at?")
2. KPI cards (row)      — Key numbers with trend indicators
3. Primary charts       — Visual patterns, comparisons, trends
4. Secondary charts     — Supporting detail, breakdowns
5. Tables / matrices    — Granular data for drill-down
6. Slicers / filters    — User controls (top or side)
```

### The Inverted Pyramid
- **Top of page**: Most aggregated, broadest data (total revenue, overall margin)
- **Middle**: Segmented data (by region, by product, by period)
- **Bottom**: Most detailed data (individual transactions, line items)

---

## 2. Layout Grid System

### Canvas Standard
| Property | Value |
|----------|-------|
| Width | 1280 px |
| Height | 720 px |
| Aspect ratio | 16:9 |
| `displayOption` | `1` (Fit to page) |

### Spacing Rules
| Rule | Value | Why |
|------|-------|-----|
| Page margins (left/right) | 30 px | Prevents content from touching edges |
| Top margin | 10 px | Compact — title bar starts immediately |
| Column gap | 20 px | Clear separation without wasting space |
| Row gap | 10–15 px | Tight vertical rhythm |
| Usable width | 1220 px | 1280 − 30 − 30 |

### Alignment Rules
- **Always align** visuals to the grid — no arbitrary x/y values
- **Consistent widths** within a row — all KPIs same width, all charts same width
- **Consistent heights** within a row — mixed heights create visual noise
- **Left-align text** in cards and titles (Western languages read left-to-right)

### White Space
- White space is **not wasted space** — it aids readability and focus
- Minimum 10px gap between any two visuals
- Don't fill every pixel — a crowded page overwhelms users
- Use `background: transparent` for spacer areas if needed

---

## 3. Typography System

### Font Stack
Power BI supports limited fonts via API. Use this hierarchy:

| Priority | Font | Use Case |
|----------|------|----------|
| 1st | **Segoe UI** | Default for all dashboard text — designed for screens |
| 2nd | **Segoe UI Semibold** | Emphasis text, card values |
| 3rd | **DIN** | Numeric-heavy displays (alternative to Segoe UI) |
| Fallback | **Arial** | Safe fallback if Segoe unavailable |

> **Rule**: Use ONE font family per dashboard. Segoe UI for everything. Differentiate via weight and size, not font family.

### Font Size Scale (Modular Scale)
Use a consistent type scale based on functional roles:

| Role | Size | Weight | Where Used |
|------|------|--------|------------|
| Page title | 14pt / `14D` | Bold | Title textbox at top of page |
| Section heading | 12pt / `12D` | Semibold | Visual group labels |
| Visual title | 11pt / `11D` | Regular or Semibold | `vcObjects.title.fontSize` |
| KPI callout value | 27pt / `27D` | Semibold | `objects.calloutValue.fontSize` — **CRITICAL: never use default** |
| KPI label | 10pt / `10D` | Regular | Category label below KPI value |
| Axis labels | 10pt / `10D` | Regular | Chart `categoryAxis` / `valueAxis` |
| Data labels | 9pt / `9D` | Regular | Chart `labels.fontSize` |
| Legend | 10pt / `10D` | Regular | `legend.fontSize` |
| Table header | 11pt / `11D` | Semibold | Table column headers |
| Table body | 10pt / `10D` | Regular | Table cell values |
| Tooltip | 10pt / `10D` | Regular | Tooltip body text |
| Slicer items | 10pt / `10D` | Regular | Dropdown/list items |

### Typography Implementation in JSON

#### Page Title (Textbox)
```python
"objects": {
    "general": [{"properties": {
        "paragraphs": [{
            "textRuns": [{
                "value": "Finance Overview",
                "textStyle": {
                    "fontFamily": "Segoe UI",
                    "fontSize": "14pt",
                    "fontWeight": "bold",
                    "color": "#333333"
                }
            }],
            "horizontalTextAlignment": "left"
        }]
    }}]
}
```

#### Visual Title
```python
"vcObjects": {
    "title": [{"properties": {
        "show":      _lit("true"),
        "text":      _lit("'Revenue by Region'"),
        "fontSize":  _lit("11D"),
        "fontColor": _color("#333333"),
        "fontFamily": _lit("'Segoe UI'"),
    }}]
}
```

#### KPI Card Value
```python
"objects": {
    "calloutValue": [{"properties": {
        "fontSize":   _lit("27D"),
        "fontFamily": _lit("'Segoe UI Semibold'"),
        "color":      _color("#333333"),
    }}],
}
```

### Typography Anti-Patterns
| Don't | Why | Do Instead |
|-------|-----|------------|
| Use more than 2 font families | Creates visual chaos | Segoe UI + Segoe UI Semibold |
| Use font sizes below 9pt | Unreadable on most screens | Minimum 9pt for any text |
| Use ALL CAPS for long text | Hard to read | Use bold weight for emphasis |
| Leave default card font size | Values clip or are too large | Always set `calloutValue.fontSize: 27D` |
| Mix pt sizes without a scale | Inconsistent hierarchy | Use the modular scale above |

---

## 4. Color System

### Microsoft Fluent 2 Palette (Active Standard)

This is the standard palette for all new reports. PBI assigns these colors automatically to data series in charts.

| Index | Name | Hex | Auto-assigned to |
|:---:|-------|-----|-------|
| 1 | Blue | `#118DFF` | 1st series |
| 2 | Navy | `#12239E` | 2nd series |
| 3 | Orange | `#E66C37` | 3rd series |
| 4 | Purple | `#6B007B` | 4th series |
| 5 | Pink | `#E044A7` | 5th series |
| 6 | Violet | `#744EC2` | 6th series |
| 7 | Gold | `#D9B300` | 7th series |
| 8 | Red | `#D64550` | 8th series |

### Structural Colors

| Element | Color | Hex |
|---------|-------|-----|
| Primary text | Dark charcoal | `#252423` |
| Visual titles / labels | Medium gray | `#616161` |
| Page background | White | `#FFFFFF` |
| Card background | White | `#FFFFFF` |
| Background panel | Near-white | `#F6F6F6` |
| Border | Cool gray | `#c7c8ce` |
| Shadow | Light gray | `#cccccc` |
| Accent bar | Fluent Blue | `#118DFF` |
| Separator line | Cool gray | `#c7c8ce` |
| Positive | Green | `#70AD47` |
| Warning | Amber | `#FFC000` |
| Negative | Red | `#D64550` |

### Color Rules
1. **Maximum 6 colors** in any single chart — beyond 6, use "Other" bucket
2. **Consistent meaning** — same color = same semantic throughout all pages
3. **Sufficient contrast** — WCAG AA minimum (4.5:1 for text, 3:1 for graphics)
4. **No pure black text** — Use `#252423` (softer on eyes, still high contrast)
5. **Color is not the only indicator** — Pair with icons, labels, or patterns for accessibility
6. **Avoid red/green only** — ~8% of men have color vision deficiency; add shapes or labels

### Multi-Color Bar/Scatter Charts (CRITICAL)
To get a different color per category in bar charts (instead of all bars being the same blue):
- Add the **same category column** to the `Series` projection bucket alongside `Category`
- This forces PBI to treat each category value as a separate series → different Fluent 2 colors
- Hide the legend (it duplicates the axis labels): `"legend": [{"properties": {"show": _lit("false")}}]`
- **Do NOT use** `dataPoint.colorByCategory: true` — this does not work when deploying via API
- See `known_issues.md` Issue #13 for details

### Conditional Formatting Colors
For variance/performance indicators:
```python
# Positive variance (green)
_color("#70AD47")
# Negative variance (red)  
_color("#D64550")
# Neutral / on target
_color("#616161")
```

---

## 5. Page Layout Templates

### Template: Executive Overview
**Purpose**: High-level KPIs + trend overview. First page of any dashboard.

```
┌──────────────────────────────────────────────────────┐
│ [Title: "Finance Overview"]           y=10, h=40     │
├──────────┬──────────┬──────────┬─────────────────────┤
│ KPI 1    │ KPI 2    │ KPI 3    │     y=60, h=120     │
├──────────┴──────────┴──────────┤                     │
│ KPI 4    │ KPI 5    │ KPI 6    │     y=190, h=120    │
├──────────────────┬─────────────┤                     │
│ Trend Chart      │ Pie/Donut  │     y=325, h=185    │
├──────────────────┼─────────────┤                     │
│ Bar Chart        │ Map/Table  │     y=525, h=185    │
└──────────────────┴─────────────┘                     │
```

Key decisions:
- 6 KPIs in 2 rows of 3 (390px wide each)
- 4 charts in 2×2 grid (595px wide each)
- Total vertical: 710px — fits in 720px canvas

### Template: Analysis Deep-Dive
**Purpose**: Detailed breakdown with filtering. Interior pages.

```
┌──────────────────────────────────────────────────────┐
│ [Title + Slicers]                     y=10, h=50     │
├──────────┬──────────┬──────────┬─────────────────────┤
│ KPI 1    │ KPI 2    │ KPI 3    │     y=70, h=100     │
├──────────────────────────────────────────────────────┤
│ [Primary Chart — Full Width]          y=180, h=250   │
├──────────────────┬───────────────────────────────────┤
│ Secondary Chart  │ Secondary Chart    y=445, h=200   │
└──────────────────┴───────────────────────────────────┘
```

Key decisions:
- Slicers in title row to save vertical space
- 3 KPIs (shorter at 100px — no calloutValue, just card)
- One dominant chart to anchor the analysis
- Two supporting charts at bottom

### Template: Table-Centric
**Purpose**: Line-item detail, drill-down data, export-friendly.

```
┌──────────────────────────────────────────────────────┐
│ [Title]                               y=10, h=40     │
├──────────┬──────────┬──────────┬──────┬──────────────┤
│ KPI 1    │ KPI 2    │ KPI 3    │ KPI 4│ y=60, h=100  │
├──────────────────────────────────────────────────────┤
│ [Slicer Row]                          y=170, h=50    │
├──────────────────────────────────────────────────────┤
│                                                      │
│             Table / Matrix                           │
│             (Full Width)              y=230, h=480   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 6. Dashboard Setup Checklist

When creating a **new dashboard from scratch**, follow this checklist:

### Pre-Build
- [ ] Identify the **target audience** (executive, analyst, operational)
- [ ] List the **top 5 questions** the dashboard must answer
- [ ] Verify all **measures exist** in the semantic model (`model.bim`)
- [ ] Choose a **page template** per page (Overview, Analysis, Table)
- [ ] Define the **color assignments** (which measure = which color)

### Report.json Setup
- [ ] Set `layoutOptimization: 0` (integer, not string)
- [ ] Set canvas `width: 1280`, `height: 720`
- [ ] Include `theme: "CY26SU02"` and `resourcePackages` with base theme
- [ ] Set `activeSectionIndex: 0`
- [ ] Include `config` with `themeCollection.baseTheme`

### Per Page
- [ ] Unique `section.name` (no spaces, no special characters)
- [ ] Human-readable `section.displayName`
- [ ] `section.config` = `json.dumps({"name": "<internalName>"})`
- [ ] `section.filters` = `"[]"` (stringified)
- [ ] Width = 1280, Height = 720

### Per Visual
- [ ] Unique visual ID (guid or descriptive slug)
- [ ] Position on grid (x, y, width, height aligned to layout system)
- [ ] `prototypeQuery` with `Version: 2`, `From`, `Select` — **MANDATORY**
- [ ] `config` is `json.dumps(...)` (stringified, not embedded)
- [ ] Correct measure/column names (exact match to model, case-sensitive)
- [ ] Card `calloutValue.fontSize: 27D` (never leave default)
- [ ] Card height ≥ 120px

### Deployment
- [ ] Build `definition.pbir` using V2 schema with XMLA connection string
- [ ] Include base theme as a separate part (`StaticResources/SharedResources/BaseThemes/CY26SU02.json`)
- [ ] Deploy via POST (create) or POST updateDefinition (update)
- [ ] Poll async operation until Succeeded
- [ ] Verify with `getDefinition` round-trip

---

## 7. Responsive Design Considerations

### Display Contexts
Power BI reports may be viewed on:
- **Desktop** (1920×1080+) — full experience
- **Web browser** (varies) — "Fit to page" scales the 1280×720 canvas
- **Mobile app** — separate mobile layout (not covered by API yet)
- **Embedded / Teams** — similar to web, may be narrower

### Best Practices for Multi-Context
- Design at **1280×720** as the canonical size
- Use `displayOption: 1` (Fit to page) — canvas scales proportionally
- Avoid text smaller than **9pt** — won't be readable when scaled down
- Test that KPI card values don't clip at smaller viewport sizes
- Keep critical content in the **top-left quadrant** (visible without scrolling on mobile)

---

## 8. Navigation & Multi-Page Design

### Page Naming Convention
| Page | Internal Name | Display Name |
|------|--------------|--------------|
| Page 1 | `overview` | Finance Overview |
| Page 2 | `pnl_analysis` | P&L Analysis |
| Page 3 | `budget_analysis` | Budget Analysis |
| Page 4 | `cash_flow` | Cash Flow |
| Page 5 | `monthly_trends` | Monthly Trends |

### Navigation Sidebar Pattern
If using a navigation sidebar (like MF_Finance):
- Sidebar width: 160px (reduces usable content width to 1060px)
- Place at x=0, full height (720px)
- Use dark background (`#2D2D2D`) with white text
- Active page indicator: accent color bar or highlight
- Each nav item is a button or textbox with bookmark/page navigation action

### Page Flow
- **Page 1**: Always the executive overview — broadest, most aggregated
- **Pages 2–4**: Analytical deep-dives, one topic each
- **Last page**: Most detailed or specialized view

---

## 9. Accessibility Checklist

- [ ] All visuals have descriptive titles (not "Chart 1")
- [ ] Color contrast meets WCAG AA (4.5:1 text, 3:1 graphics)
- [ ] Information is not conveyed by color alone
- [ ] Font sizes ≥ 9pt everywhere
- [ ] Tab order follows logical reading flow (top-left to bottom-right)
- [ ] Alt text on images and shapes (if any)
- [ ] Avoid using only red/green to indicate good/bad

---

## Cross-References

- Grid coordinates & column systems → `pages_layout.md`
- Expression language & vcObjects → `themes_styling.md`
- Visual type catalog & prototypeQuery patterns → `visual_catalog.md`
- Known issues & gotchas → `known_issues.md`
- Report JSON structure → `report_structure.md`

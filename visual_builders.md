# Visual Builders — Expression Language & Styling

## PBI Expression Helpers

Power BI config JSON uses a verbose expression language for property values.
These patterns appear hundreds of times — helper functions are essential.

### Literal Values
```json
{ "expr": { "Literal": { "Value": "true" } } }
{ "expr": { "Literal": { "Value": "false" } } }
{ "expr": { "Literal": { "Value": "27D" } } }         // number (D suffix)
{ "expr": { "Literal": { "Value": "0L" } } }          // integer (L suffix)
{ "expr": { "Literal": { "Value": "'#FF0000'" } } }   // string (single-quoted)
{ "expr": { "Literal": { "Value": "'Custom'" } } }    // string enum
```

Type suffixes:
- `D` = double/decimal (e.g., `"27D"` for font size 27pt)
- `L` = long/integer (e.g., `"4L"` for shadow distance 4px)
- `'...'` = string literal (single quotes inside the JSON string)

### Color Values
```json
{ "solid": { "color": { "expr": { "Literal": { "Value": "'#A6ADC6'" } } } } }
```

### Source References
```json
{ "SourceRef": { "Source": "f" } }  // reference to alias "f" in From clause
```

### Measure Expression
```json
{
  "Measure": {
    "Expression": { "SourceRef": { "Source": "f" } },
    "Property": "Total Revenue"
  }
}
```

### Column Expression
```json
{
  "Column": {
    "Expression": { "SourceRef": { "Source": "d" } },
    "Property": "region"
  }
}
```

## Python Helper Functions

```python
def _lit(value: str) -> dict:
    """Wrap a raw literal: 'true', '27D', "'#FF0000'", etc."""
    return {"expr": {"Literal": {"Value": value}}}

def _color(hex_color: str) -> dict:
    """Solid color property."""
    return {"solid": {"color": _lit(f"'{hex_color}'")}}

def _source_ref(alias: str) -> dict:
    return {"SourceRef": {"Source": alias}}

def _measure_expr(alias: str, prop: str) -> dict:
    return {"Measure": {"Expression": _source_ref(alias), "Property": prop}}

def _column_expr(alias: str, prop: str) -> dict:
    return {"Column": {"Expression": _source_ref(alias), "Property": prop}}
```

## Container Styling (vcObjects)

Every visual container can have title, drop shadow, background, and border.
This goes in `singleVisual.vcObjects` (NOT `singleVisual.objects`).

```python
def make_vc_objects(title_text=None):
    vc = {}

    if title_text:
        vc["title"] = [{"properties": {
            "show": _lit("true"),
            "text": _lit(f"'{title_text}'"),  # single-quoted string
        }}]

    vc["dropShadow"] = [{"properties": {
        "show":          _lit("true"),
        "color":         _color("#A6ADC6"),
        "preset":        _lit("'Custom'"),
        "shadowSpread":  _lit("0L"),
        "shadowBlur":    _lit("5L"),
        "angle":         _lit("90L"),
        "shadowDistance": _lit("4L"),
        "transparency":  _lit("85L"),
    }}]

    vc["background"] = [{"properties": {"show": _lit("true")}}]

    vc["border"] = [{"properties": {
        "show":   _lit("true"),
        "color":  _color("#E0E0E0"),
        "radius": _lit("4L"),
    }}]

    return vc
```

## Visual-Specific Objects

### Card (calloutValue)
```python
"objects": {
    "outline":       [{"properties": {"show": _lit("false")}}],
    "calloutValue":  [{"properties": {"fontSize": _lit("27D")}}],   # MUST set explicitly
    "categoryLabel": [{"properties": {"show": _lit("false")}}],
}
```

**CRITICAL**: Default `calloutValue` font size is enormous. Set to `27D` (27pt) or smaller
to prevent values from being clipped in card containers.

Recommended card height: 120px minimum.

### Chart (axis objects)
```python
"objects": {
    "categoryAxis": [{"properties": {"showAxisTitle": _lit("true")}}],
    "valueAxis":    [{"properties": {"showAxisTitle": _lit("true")}}],
}
```

### Textbox (general paragraphs)
```python
"objects": {
    "general": [{"properties": {
        "paragraphs": [{
            "textRuns": [{
                "value": "Dashboard Title",
                "textStyle": {
                    "fontFamily": "Segoe UI",
                    "fontSize": "14pt",
                    "fontWeight": "bold",
                },
            }],
            "horizontalTextAlignment": "left",
        }],
    }}],
}
```

## Table Alias Builder

When a visual references multiple tables, each needs a unique alias:

```python
def build_aliases(tables: list[str]) -> tuple[dict, list]:
    alias_map = {}
    from_list = []
    for t in tables:
        if t not in alias_map:
            alias_map[t] = chr(ord("a") + len(alias_map))
            from_list.append({"Name": alias_map[t], "Entity": t, "Type": 0})
    return alias_map, from_list
```

## Layout Grid Patterns

Standard 1280×720 canvas:

### 3-Column KPI Row
```
Margins: 30px left/right, 20px gaps
Column width: 390px
x positions: 30 / 440 / 850
```

### 2-Column Chart Row
```
Column width: 595px
x positions: 30 / 655
```

### Recommended Heights
| Element | Height |
|---------|--------|
| Title bar | 40px |
| KPI Card | 120px |
| Chart | 185px |
| Spacing between rows | 10-15px |

### Full Dashboard Template
```
y=10:   Title (h=40)
y=60:   KPI Row 1 (h=120)
y=190:  KPI Row 2 (h=120)
y=325:  Chart Row 1 (h=185)
y=525:  Chart Row 2 (h=185)
        Total: 710px (fits in 720 canvas)
```

## Multi-Measure Chart Builder

For charts with multiple measures on the Y-axis (e.g., Budget vs Actual, Revenue vs COGS):

```python
def make_multi_chart(x, y, z, w, h, vis_type, title,
                     cat_table, cat_col, measures, top_n=12):
    """Chart with one category column and multiple measures.
    measures: list of (table, measure_name) tuples.
    
    Example:
        make_multi_chart(155, 182, 2000, 560, 245, "clusteredColumnChart",
            "Budget vs Actual by Month", "fact_budgets", "period_month",
            [("fact_budgets", "Budget Amount"), ("fact_budgets", "Actual Amount")])
    """
    cat_ref = f"{cat_table}.{cat_col}"
    proj_y = [{"queryRef": f"{t}.{m}"} for t, m in measures]
    proj = {"Category": [{"queryRef": cat_ref}], "Y": proj_y}
    
    # From clause: include all unique tables
    alias_map = {cat_table: "c"}
    from_list = [{"Name": "c", "Entity": cat_table, "Type": 0}]
    for t, m in measures:
        if t not in alias_map:
            a = chr(ord("a") + len(alias_map))
            alias_map[t] = a
            from_list.append({"Name": a, "Entity": t, "Type": 0})
    
    # Binding: list all measure indices
    binding = {
        "Primary": {"Groupings": [{"Projections": [0]}]},
        "Values": [{"Projections": list(range(1, len(measures) + 1))}],
        "DataReduction": {"DataVolume": 4, "Primary": {"Top": {"Count": top_n}}},
        "Version": 1
    }
```

**Key rules for multi-measure visuals:**
- Each measure needs its table in `From` with a unique alias
- `Projections` index 0 = category, 1..N = measures
- `Binding.Values.Projections` must list all measure indices: `[1, 2, 3]`
- `legend.show` should be `true` to distinguish measures
- Works with: `clusteredColumnChart`, `lineChart`, `clusteredBarChart`, `stackedColumnChart`

## Report Design Best Practices — Common Mistakes

### NEVER use raw ID/code columns for chart labels
When dimension tables have both a code/ID column (e.g., `level1`, `country_code`, `discipline_id`)
and a human-readable description column (e.g., `description`, `country_name`, `discipline_name`),
**ALWAYS use the description column** for chart axes and scatter categories.

**Bad** (renders as meaningless numbers):
```python
_bar("b1", ..., "dim_wbs", "level1", ...)         # Shows "10", "20", "30"...
_scatter("sc1", ..., "dim_wbs", "level1", ...)     # Dots labeled "60", "80"...
```

**Good** (renders as readable text):
```python
_bar("b1", ..., "dim_wbs", "description", ...)     # Shows "Site Preparation", "Civil Works"...
_scatter("sc1", ..., "dim_wbs", "description", ...) # Dots labeled "Electrical Systems"...
```

**Rule**: Before building any chart, check the dimension table columns.
Pick the column with the highest semantic value for the end user.
Codes belong in tooltips or detail tables, not in axes or legends.

### Scatter plot outlier awareness
When a scatter chart has one point far from the cluster, it compresses all other
data points into a narrow band, making the chart hard to read.
Mitigations:
- Use `description` labels so the outlier is identifiable at a glance
- Consider logarithmic scales if variance is extreme
- Add a visual-level TopN filter to exclude outliers if needed

### Slicer display names
Slicer dropdown mode shows the raw column `NativeReferenceName` as a header inside the slicer.
To avoid showing `country_name` or `discipline_name` to the user:
- Set `vcObjects.title` with a friendly label ("Pays", "Discipline")
- **Hide the inner header** via `objects.header = [{"properties": {"show": false}}]`
- This removes the redundant raw column name while keeping the clean title

```python
"objects": {
    "data":   [{"properties": {"mode": _lit("'Dropdown'")}}],
    "header": [{"properties": {"show": _lit("false")}}],  # hide raw column name
},
"vcObjects": {"title": [{"properties": {
    "show": _lit("true"),
    "text": _lit("'Pays'"),  # clean user-facing label
}}]},
```

## Sidebar Navigation Pattern (Dark Theme)

The MF_Finance report uses a dark sidebar (140px) with navigation labels:

```python
# Theme colors
C_SIDEBAR  = "#071222"   # sidebar background
C_HEADER   = "#0F2440"   # header bar
C_CARD_BG  = "#162D50"   # card backgrounds
C_CHART_BG = "#132743"   # chart backgrounds
C_BORDER   = "#1E3456"   # border color
C_ACCENT   = "#1E90FF"   # active nav, data points
C_WHITE    = "#FFFFFF"    # primary text
C_GREY     = "#8899BB"   # labels, subtitles
```

Each page replicates the sidebar with the active page highlighted (blue shape + bold white text).
Content area starts at x=155 to leave room for the sidebar.

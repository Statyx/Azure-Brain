# Themes & Styling — Expression Language, Colors, Python Helpers

---

## PBI Expression Language

Power BI config JSON uses a verbose expression language for property values.
These patterns appear hundreds of times — helper functions are essential.

### Literal Values

```json
{"expr": {"Literal": {"Value": "true"}}}         // boolean true
{"expr": {"Literal": {"Value": "false"}}}        // boolean false
{"expr": {"Literal": {"Value": "27D"}}}          // number (D suffix = double/decimal)
{"expr": {"Literal": {"Value": "0L"}}}           // integer (L suffix = long)
{"expr": {"Literal": {"Value": "'#FF0000'"}}}    // string (single-quoted inside JSON string)
{"expr": {"Literal": {"Value": "'Custom'"}}}     // string enum
```

### Type Suffix Reference

| Suffix | Type | Example | Meaning |
|--------|------|---------|---------|
| `D` | double/decimal | `"27D"` | 27pt font size |
| `L` | long/integer | `"4L"` | 4px distance |
| `'...'` | string | `"'#A6ADC6'"` | Color hex string |
| none | boolean | `"true"` | Boolean value |

### Color Value
```json
{"solid": {"color": {"expr": {"Literal": {"Value": "'#A6ADC6'"}}}}}
```

### Source Reference
```json
{"SourceRef": {"Source": "f"}}   // reference to alias in From clause
```

---

## Python Helper Functions

```python
def _lit(value: str) -> dict:
    """Wrap a raw literal: 'true', '27D', \"'#FF0000'\", etc."""
    return {"expr": {"Literal": {"Value": value}}}

def _color(hex_color: str) -> dict:
    """Solid color property. hex_color includes #, e.g. '#FF0000'."""
    return {"solid": {"color": _lit(f"'{hex_color}'")}}

def _source_ref(alias: str) -> dict:
    return {"SourceRef": {"Source": alias}}

def _measure_expr(alias: str, prop: str) -> dict:
    return {"Measure": {"Expression": _source_ref(alias), "Property": prop}}

def _column_expr(alias: str, prop: str) -> dict:
    return {"Column": {"Expression": _source_ref(alias), "Property": prop}}

def _bool(val: bool) -> dict:
    return _lit("true" if val else "false")

def _int(val: int) -> dict:
    return _lit(f"{val}L")

def _float(val: float) -> dict:
    return _lit(f"{val}D")

def _str(val: str) -> dict:
    return _lit(f"'{val}'")
```

---

## Container Styling (vcObjects)

`vcObjects` = container-level styling. Goes in `singleVisual.vcObjects`.
This controls the visual's frame: title, background, border, shadow.

### Title
```python
"title": [{"properties": {
    "show":      _lit("true"),
    "text":      _lit("'My Visual Title'"),
    "fontSize":  _lit("12D"),           # optional
    "fontColor": _color("#333333"),      # optional
    "bold":      _lit("true"),           # optional
}}]
```

### Drop Shadow
```python
"dropShadow": [{"properties": {
    "show":          _lit("true"),
    "color":         _color("#A6ADC6"),
    "preset":        _lit("'Custom'"),
    "shadowSpread":  _lit("0L"),
    "shadowBlur":    _lit("5L"),
    "angle":         _lit("90L"),
    "shadowDistance": _lit("4L"),
    "transparency":  _lit("85L"),
}}]
```

### Background
```python
"background": [{"properties": {
    "show":         _lit("true"),
    "color":        _color("#FFFFFF"),    # optional - defaults to white
    "transparency": _lit("0L"),           # optional - 0=opaque, 100=transparent
}}]
```

### Border
```python
"border": [{"properties": {
    "show":   _lit("true"),
    "color":  _color("#E0E0E0"),
    "radius": _lit("4L"),          # corner radius in px
    "width":  _lit("1L"),          # optional border width
}}]
```

### Full vcObjects Builder
```python
def make_vc_objects(title_text=None, shadow=True, background=True, border=True):
    vc = {}
    
    if title_text:
        vc["title"] = [{"properties": {
            "show": _lit("true"),
            "text": _lit(f"'{title_text}'"),
        }}]
    
    if shadow:
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
    
    if background:
        vc["background"] = [{"properties": {"show": _lit("true")}}]
    
    if border:
        vc["border"] = [{"properties": {
            "show":   _lit("true"),
            "color":  _color("#E0E0E0"),
            "radius": _lit("4L"),
        }}]
    
    return vc
```

---

## Visual-Specific Objects (objects)

`objects` = visual-type-specific formatting. Goes in `singleVisual.objects`.

### Card (cardVisual)
```python
"objects": {
    "outline":       [{"properties": {"show": _lit("false")}}],
    "calloutValue":  [{"properties": {"fontSize": _lit("27D")}}],
    "categoryLabel": [{"properties": {"show": _lit("false")}}],
}
```

**CRITICAL**: Default `calloutValue` font size is enormous. Always set to `27D` (27pt).
Card height must be ≥ 120px to avoid clipping.

### Chart Axes
```python
"objects": {
    "categoryAxis": [{"properties": {
        "showAxisTitle": _lit("true"),
        "fontSize":      _lit("10D"),     # optional
    }}],
    "valueAxis": [{"properties": {
        "showAxisTitle": _lit("true"),
        "fontSize":      _lit("10D"),     # optional
    }}],
}
```

### Chart Legend
```python
"objects": {
    "legend": [{"properties": {
        "show":     _lit("true"),
        "position": _lit("'Top'"),         # Top, Bottom, Left, Right
        "fontSize": _lit("10D"),
    }}],
}
```

### Chart Data Labels
```python
"objects": {
    "labels": [{"properties": {
        "show":     _lit("true"),
        "fontSize": _lit("10D"),
        "color":    _color("#333333"),
    }}],
}
```

### Textbox (paragraphs)
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
                }
            }],
            "horizontalTextAlignment": "left"
        }]
    }}]
}
```

---

## Base Theme

The base theme file is required for proper rendering. Current project uses `CY26SU02`.

### In report.json
```json
{
  "theme": "CY26SU02",
  "resourcePackages": [{
    "resourcePackage": {
      "name": "SharedResources",
      "type": 2,
      "items": [{"type": 202, "path": "BaseThemes/CY26SU02.json", "name": "CY26SU02"}],
      "disabled": false
    }
  }]
}
```

### In report config (stringified)
```json
{
  "themeCollection": {
    "baseTheme": {
      "name": "CY26SU02",
      "version": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
      "type": 2
    }
  }
}
```

### In API parts
```json
{
  "path": "StaticResources/SharedResources/BaseThemes/CY26SU02.json",
  "payload": "<base64-encoded-theme-json>",
  "payloadType": "InlineBase64"
}
```

### Getting the Theme File
Extract from an existing report via `getDefinition`:
```python
for part in result["definition"]["parts"]:
    if "BaseThemes" in part["path"]:
        theme_b64 = part["payload"]
        theme_json = json.loads(base64.b64decode(theme_b64))
        break
```

---

## Color Palette — Finance Dashboard

Recommended colors for finance visuals:

| Purpose | Color | Hex |
|---------|-------|-----|
| Primary (Revenue) | Blue | `#4472C4` |
| Secondary (Expenses) | Red | `#ED7D31` |
| Positive (Profit) | Green | `#70AD47` |
| Warning (Budget Over) | Orange | `#FFC000` |
| Negative (Loss) | Dark Red | `#C00000` |
| Neutral | Gray | `#A5A5A5` |
| Background | White | `#FFFFFF` |
| Border | Light Gray | `#E0E0E0` |
| Shadow | Blue Gray | `#A6ADC6` |
| Text | Dark Gray | `#333333` |

---

## Table Alias Builder

When a visual references multiple tables, each needs a unique alias:

```python
def build_aliases(tables: list[str]) -> tuple[dict, list]:
    """Build alias map and From clause for prototypeQuery.
    
    Returns:
        alias_map: {"fact_general_ledger": "f", "dim_calendar": "d", ...}
        from_list: [{"Name": "f", "Entity": "fact_general_ledger", "Type": 0}, ...]
    """
    alias_map = {}
    from_list = []
    for t in tables:
        if t not in alias_map:
            alias_map[t] = chr(ord("a") + len(alias_map))
            from_list.append({"Name": alias_map[t], "Entity": t, "Type": 0})
    return alias_map, from_list
```

### Common Aliases in Finance Model
| Table | Alias |
|-------|-------|
| `fact_general_ledger` | `f` or `a` |
| `dim_calendar` | `c` or `b` |
| `dim_cost_centers` | `d` or `c` |
| `dim_accounts` | `e` or `d` |
| `fact_budget` | `g` or `e` |
| `fact_ar_invoices` | `h` or `f` |

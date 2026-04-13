# Themes & Styling — Expression Language, Colors, Typography, Python Helpers

> **See also**: `dashboard_design_guide.md` for complete design system, layout templates, and setup checklist.

---

## Typography Quick Reference

Use **ONE font family** (Segoe UI) and differentiate via size and weight only.

| Role | Size | Weight | JSON Value |
|------|------|--------|------------|
| Page title | 14pt | Bold | `"14D"` |
| Visual title | 11pt | Regular | `"11D"` |
| KPI callout | 27pt | Semibold | `"27D"` — **never leave default** |
| Axis / Legend / Labels | 10pt | Regular | `"10D"` |
| Data labels | 9pt | Regular | `"9D"` |
| Table header | 11pt | Semibold | `"11D"` |
| Table body | 10pt | Regular | `"10D"` |

**Minimum readable size**: 9pt. Never go below this.

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
    "color":         _color("#cccccc"),     # Fluent 2: light gray shadow
    "preset":        _lit("'Custom'"),
    "shadowBlur":    _lit("5L"),
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
    "color":  _color("#c7c8ce"),    # Fluent 2: cool gray border
    "radius": _lit("8L"),          # corner radius in px (8px for modern look)
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
            "color":         _color("#cccccc"),
            "preset":        _lit("'Custom'"),
            "shadowBlur":    _lit("5L"),
            "shadowDistance": _lit("4L"),
            "transparency":  _lit("85L"),
        }}]
    
    if background:
        vc["background"] = [{"properties": {"show": _lit("true")}}]
    
    if border:
        vc["border"] = [{"properties": {
            "show":   _lit("true"),
            "color":  _color("#c7c8ce"),
            "radius": _lit("8L"),
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
    "calloutValue":  [{"properties": {
        "fontSize": _lit("14D"),
        "color":    _color("#252423"),
    }}],
    "categoryLabel": [{"properties": {"show": _lit("true")}}],
}
```

**CRITICAL**: Card height must be ≥ **120px** for `14D` and ≥ 130px for `27D`.
Category label clips at 100px with 14D — the title (22px) + value (25px) + categoryLabel (18px) + padding = 99px with zero margin.

### Slicer (dropdown mode)
```python
"objects": {
    "data": [{"properties": {
        "mode":                    _lit("'Dropdown'"),
        "isInvertedSelectionMode": _lit("false"),
    }}],
    "header": [{"properties": {"show": _lit("false")}}],
    "selection": [{"properties": {
        "selectAllCheckboxEnabled": _lit("false"),
        "singleSelect":            _lit("false"),
    }}],
}
```

**vcObjects for slicers (MANDATORY — must match card/chart styling):**
```python
"vcObjects": {
    "title": [{"properties": {
        "show":      _lit("true"),
        "text":      _lit("'Filter Label'"),
        "fontSize":  _lit("10D"),           # slightly smaller than card title (11D)
        "fontColor": _color("#616161"),      # subtle gray
    }}],
    "visualHeader":        [{"properties": {"show": _lit("false")}}],
    "visualHeaderTooltip": [{"properties": {"show": _lit("false")}}],
    "background":          [{"properties": {"show": _lit("true")}}],
    "border":              [{"properties": {"show": _lit("false")}}],
    "dropShadow": [{"properties": {
        "show":          _lit("true"),
        "color":         _color("#cccccc"),
        "preset":        _lit("'Custom'"),
        "shadowBlur":    _lit("5L"),
        "shadowDistance": _lit("4L"),
        "transparency":  _lit("85L"),
    }}],
}
```

**Key slicer styling rules:**
1. **Hide PBI header** (`objects.header.show: false`) — use vcObjects.title instead
2. **Title font 10D** (not 11D like cards) — slicers are secondary UI, slightly smaller
3. **Title color #616161** — lighter gray, not the dark #252423 used for chart titles
4. **Height must be 75px** with title — title takes 22px inside the visual
5. **Background + shadow** — without them, slicers look like floating orphans
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

## Color Palette — Microsoft Fluent 2 (Active Standard)

This is Microsoft's default modern palette used by Power BI. Use this palette for all new reports.

### Theme Data Colors (8 series, auto-assigned by PBI)

| Index | Name | Hex | Usage |
|:---:|-------|-----|-------|
| 1 | Blue | `#118DFF` | Primary series, accent, action |
| 2 | Navy | `#12239E` | Secondary series |
| 3 | Orange | `#E66C37` | Tertiary series |
| 4 | Purple | `#6B007B` | Fourth series |
| 5 | Pink | `#E044A7` | Fifth series |
| 6 | Violet | `#744EC2` | Sixth series |
| 7 | Gold | `#D9B300` | Seventh series |
| 8 | Red | `#D64550` | Eighth series, negative variance |

### Structural Colors (applied in vcObjects / objects)

| Element | Color | Hex |
|---------|-------|-----|
| Primary text | Dark charcoal | `#252423` |
| Visual title / labels | Medium gray | `#616161` |
| Border | Cool gray | `#c7c8ce` |
| Shadow | Light gray | `#cccccc` |
| Accent bar | Fluent Blue | `#118DFF` |
| Background panel | Near-white | `#F6F6F6` |
| Page background | White | `#FFFFFF` |
| Separator line | Cool gray | `#c7c8ce` |
| Positive | Green | `#70AD47` |
| Warning | Amber | `#FFC000` |
| Negative | Red | `#D64550` |

### Migration Note: Previous Palettes
Earlier iterations used Fashion colors (deep teal/coral), then Competitive Marketing (#01B8AA teal). The Fluent 2 palette above is the current standard as of 2026-04. Always use it for new reports.

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

---

## Decorative Elements — Accent Bar, Separator, Background Panel

These `basicShape` visuals add professional polish that differentiates API-built reports from default ones.

### Accent Bar (top-of-page brand stripe)
A 5px-tall colored bar across the full 1280px width at y=0. Sets the brand tone.

```python
def _accent_bar(name, y=0, color="#118DFF"):
    """Thin colored accent bar across top of page."""
    return {
        "x": 0, "y": y, "z": 0, "width": 1280, "height": 5,
        "config": json.dumps({
            "name": name,
            "layouts": [{"id": 0, "position": {"x": 0, "y": y, "z": 0, "width": 1280, "height": 5}}],
            "singleVisual": {"visualType": "basicShape", "objects": {
                "line": [{"properties": {"show": _lit("false")}}],
                "fill": [{"properties": {
                    "fillColor": _color(color),
                    "transparency": _lit("0L"),
                }}],
            }},
        }), "filters": "[]",
    }
```

### Separator (section divider)
A 2px-tall line at 30px margin, 1220px wide. Use between visual groups to create sections.

```python
def _separator(name, y):
    return {
        "x": 30, "y": y, "z": 0, "width": 1220, "height": 2,
        "config": json.dumps({
            "name": name,
            "layouts": [{"id": 0, "position": {"x": 30, "y": y, "z": 0, "width": 1220, "height": 2}}],
            "singleVisual": {"visualType": "basicShape", "objects": {
                "line": [{"properties": {"show": _lit("false")}}],
                "fill": [{"properties": {
                    "fillColor": _color("#c7c8ce"),
                    "transparency": _lit("0L"),
                }}],
            }},
        }), "filters": "[]",
    }
```

### Background Panel (visual grouping)
A subtle #F6F6F6 rectangle placed BEHIND a group of visuals (z=0). Groups related KPIs visually.

```python
def _bg_panel(name, x, y, w, h, color="#F6F6F6"):
    return {
        "x": x, "y": y, "z": 0, "width": w, "height": h,
        "config": json.dumps({
            "name": name,
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h}}],
            "singleVisual": {"visualType": "basicShape", "objects": {
                "line": [{"properties": {"show": _lit("false")}}],
                "fill": [{"properties": {
                    "fillColor": _color(color),
                    "transparency": _lit("0L"),
                }}],
            }},
        }), "filters": "[]",
    }
```

**Important**: Decorative elements use `z: 0` so they sit behind data visuals (z ≥ 1). The `line` property is hidden so only the fill shows.

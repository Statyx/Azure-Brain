# Themes, Styling & PBIR Expressions

> Everything you need to write valid colors, theme files, container styling, and PBIR literal expressions.

---

## 1. PBIR Literal Expressions — Cheatsheet

In `visual.json` / `page.json`, **every property value** is wrapped in an expression envelope. The CLI is the canonical encoder:

```powershell
powerbi-report-author expr encode --kind <kind> <value>
```

### All kinds and their shapes

| Kind | CLI | Result inside a property | Notes |
|---|---|---|---|
| string | `expr encode --kind string "My Title"` | `{"expr":{"Literal":{"Value":"'My Title'"}}}` | Value padded with single quotes |
| number (float / double) | `expr encode --kind number "100"` | `{"expr":{"Literal":{"Value":"100D"}}}` | Suffix `D` |
| integer | `expr encode --kind integer "12"` | `{"expr":{"Literal":{"Value":"12L"}}}` | Suffix `L` |
| bool | `expr encode --kind bool "true"` | `{"expr":{"Literal":{"Value":"true"}}}` | No quoting |
| hex color | `expr encode --kind color "#118DFF"` | `{"solid":{"color":{"expr":{"Literal":{"Value":"'#118DFF'"}}}}}` | Wraps in `solid.color` |
| theme color | `expr encode --kind themeColor "1" --percent -10` | `{"solid":{"color":{"expr":{"ThemeDataColor":{"ColorId":1,"Percent":-10}}}}}` | `ColorId` 1-based; `Percent` darkens/lightens |

### Examples in context

#### Show a title with custom text and color

```json
"visualContainerObjects": {
  "title": [{
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" }}},
      "text": { "expr": { "Literal": { "Value": "'Total Revenue'" }}},
      "fontColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#333333'" }}}}},
      "fontSize": { "expr": { "Literal": { "Value": "11D" }}},
      "bold": { "expr": { "Literal": { "Value": "true" }}}
    }
  }]
}
```

#### Bind a card's callout to a theme color

For `cardVisual`, the **callout text** (number/label) lives on the `value` object — not `cardCalloutArea` (which controls the surrounding rectangle: padding, background, corner radius).

```json
"objects": {
  "value": [{
    "properties": {
      "fontColor": { "solid": { "color": { "expr": { "ThemeDataColor": { "ColorId": 1, "Percent": 0 }}}}}
    }
  }]
}
```

### Common encoding mistakes

| Mistake | Why it breaks | Fix |
|---|---|---|
| `"#118DFF"` (no quotes around hex) | Parser expects a quoted string literal | `"'#118DFF'"` |
| `"100"` (no suffix) | Treated as string `"100"`, not a double | `"100D"` (number) or `"100L"` (integer) |
| Forgetting `solid.color` wrapper for colors | Color properties expect a `solid` brush, not a raw literal | Use `expr encode --kind color` |
| Setting `Percent: 0` on every theme color | OK, but verbose | Set `Percent` only when shading is needed |

---

## 2. Visual-Container Objects (VCOs)

VCOs are the 16 styling layers shared by **all** visual types. They live in `visual.json.visual.visualContainerObjects` (not `objects`).

| VCO | Use for |
|---|---|
| `general` | x/y/width/height/altText (rarely override; position lives in `visual.position`) |
| `title` | Visual title (text, font, color, alignment) |
| `subTitle` | Optional subtitle |
| `background` | Container fill color + transparency |
| `border` | Border on/off, color, radius, width |
| `divider` | Divider line between sections (cards) |
| `dropShadow` | Soft shadow (color, `shadowBlur`, `position`, `preset`) |
| `padding` | Inner spacing between border and visual |
| `spacing` | Outer spacing margins |
| `stylePreset` | Apply a named preset from the theme |
| `visualHeader` | Header bar with ⋯ menu (show/hide, font, fill) |
| `visualHeaderTooltip` | Tooltip shown on header hover |
| `visualLink` | Click-through URL or page navigation |
| `visualTooltip` | Tooltip when hovering data points |
| `lockAspect` | Maintain aspect ratio on resize |

Source of truth: [`cli_knowledge/vcos/<vco>.json`](cli_knowledge/vcos/) — each file lists every property, its type, and `displayName`.

### Why not put everything under `objects`?

`objects` is reserved for **visual-type-specific** properties (`labels` on a chart, `value` / `cardCalloutArea` on a card, `valueAxis` on a bar chart, …). VCOs are the cross-cutting concerns that exist on every visual.

### Pattern: drop-shadowed card with title

```json
"visualContainerObjects": {
  "background": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" }}}, "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#FFFFFF'" }}}}}, "transparency": { "expr": { "Literal": { "Value": "0L" }}} }}],
  "border": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" }}} }}],
  "dropShadow": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" }}}, "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#000000'" }}}}}, "transparency": { "expr": { "Literal": { "Value": "92L" }}}, "shadowBlur": { "expr": { "Literal": { "Value": "8L" }}}, "preset": { "expr": { "Literal": { "Value": "'BottomRight'" }}}, "position": { "expr": { "Literal": { "Value": "'Outer'" }}} }}],
  "title": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" }}}, "text": { "expr": { "Literal": { "Value": "'Total Revenue'" }}}, "fontSize": { "expr": { "Literal": { "Value": "11D" }}} }}]
}
```

---

## 3. Theme Files

Themes are **plain JSON** (no PBIR `expr` wrappers). Path:

```
StaticResources/SharedResources/BaseThemes/<themeName>.json
```

### Minimal theme

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/theme/2.140.0/schema.json",
  "name": "AzureBrainLight",
  "dataColors": ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7", "#744EC2", "#D9B300", "#D64550"],
  "background": "#FFFFFF",
  "foreground": "#333333",
  "tableAccent": "#118DFF"
}
```

| Field | Purpose |
|---|---|
| `name` | Referenced from `report.json.themeCollection.baseTheme.name` |
| `dataColors[]` | The 8 colors used by `ThemeDataColor`. ColorId is **1-based** in PBIR. |
| `background` / `foreground` | Page-level defaults |
| `tableAccent` | Header tint for tables |
| `visualStyles` | Per-visual-type overrides (advanced) |

### Per-visual style overrides

```json
"visualStyles": {
  "*": {
    "*": {
      "title": [{ "fontSize": 11, "fontFamily": "Segoe UI Semibold", "fontColor": { "solid": { "color": "#333333" }}}],
      "background": [{ "color": { "solid": { "color": "#FFFFFF" }}, "transparency": 0 }]
    }
  },
  "cardVisual": {
    "*": {
      "value": [{ "fontSize": 27, "fontFamily": "Segoe UI Semibold" }]
    }
  }
}
```

Inside `visualStyles` values are plain JSON, **not** wrapped in `expr.Literal`. Use `powerbi-report-author theme encode --kind <kind> <value>` if uncertain.

### Theme color shading

The shading algorithm matches Power BI's `ThemeDataColor.Percent`. To preview the resulting hex:

```powershell
powerbi-report-author theme shade-color "#118DFF" -10
```

returns the darkened hex.

---

## 4. Color Strategy (Tones)

Pick **one** tone for the report; rebuild the theme to match.

| Tone | Background | Foreground | Accent #1 | Mood |
|---|---|---|---|---|
| **Bright Light** | `#FFFFFF` | `#1F2A37` | `#0078D4` | Operational, clean, default office |
| **Soft Pastel** | `#F4F6F8` | `#2D3748` | `#5B8DEF` | Friendly, approachable, narrative reports |
| **High Contrast** | `#FFFFFF` | `#000000` | `#0F62FE` | Accessibility, regulated industries |
| **Dark Mode** | `#1A1F2C` | `#E5E7EB` | `#36B5FF` | Executive, NOC dashboards, modern |
| **Earthy Warm** | `#FBF7F2` | `#3D2C1E` | `#C2570C` | Brand-driven, sustainability, retail |

Each tone's full 8-color `dataColors[]` palette lives in [`dashboard_design_guide.md`](dashboard_design_guide.md).

**Dark mode checklist** (mandatory if `background` is dark):
- Text uses `foreground` (light), never default black
- All `dropShadow.color` is black with very high transparency (90+)
- Borders use a mid grey (#3A3F4B) not pure white
- Sparingly use color: 1 accent + 1 alert + neutral grey is enough
- Test contrast — every `dataColor` must meet WCAG AA against the dark background

---

## 5. Common Styling Patterns

### A. KPI Cards (uniform row)

| Property | Value |
|---|---|
| `background.color` | `#FFFFFF` (light) / theme `card.color` (dark) |
| `border.show` | `false` |
| `dropShadow.show` | `true`, `shadowBlur` 8, `transparency` 92, `preset: 'BottomRight'`, `position: 'Outer'` |
| `title.show` | `true`, `fontSize` 11, `bold` true |
| `value.fontSize` *(cardVisual)* | `27D` (numbers ≥ 100) or `36D` (large dashboards) — callout text lives on `value`, **not** `cardCalloutArea` |
| Position | `height = 120`, equal `width` across the row |

### B. Chart Containers

- `border.show: false`
- `dropShadow.show: false` (charts already have visual mass)
- `title.show: true, fontSize: 11`
- `padding: 8` to keep axis labels off the border

### C. Slicers

- `border.show: false`
- `background.show: true`, light fill matching tone
- `title.show: true` when filtering by a non-obvious field
- Min height `75px` when title is shown — otherwise it overlaps the value

### D. Section dividers

Use a thin rectangle visual (`shape` of `rectangle` type), `height: 1`, fill `#E5E7EB` (light) or `#2A2F3A` (dark), full page width.

---

## 6. Cross-References

- Property catalog → [`cli_knowledge/vcos/`](cli_knowledge/vcos/), [`cli_knowledge/visuals/<type>/objects/`](cli_knowledge/visuals/)
- Tone palettes (full color lists) → [`dashboard_design_guide.md`](dashboard_design_guide.md)
- Page grid (where to place things) → [`pages_layout.md`](pages_layout.md)
- Visual selection by use case → [`visual_catalog.md`](visual_catalog.md)
- Known styling issues → [`known_issues.md`](known_issues.md)

# Layout Patterns — Reusable PPTX Components

## Multi-Slide Architecture

Use `new_slide()` to create slides in order. Each call updates the global `slide` reference.

```python
# Pattern: global slide reference
slide = None
def new_slide():
    global slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    return slide
```

### Recommended Slide Order
| # | Type | Header/Footer | Background |
|---|------|--------------|------------|
| 0 | Title | None | Dark (`DARK`) + teal accent bar |
| 1 | Use Case | `slide_header()` + `slide_footer()` | White (default) |
| 2 | Solution | `slide_header()` + `slide_footer()` | White (default) |
| 3 | Architecture | `slide_header()` + `slide_footer()` | White (default) |

## Title Slide (Image Background — Preferred)

The approved pattern uses a full-bleed background image with dark overlay, NOT solid color.

```
┌──────────────────────────────────────────────────────────────┐
│ ═══ accent bar (0.05") ═══                                   │
│                                                              │
│ [Background IMAGE: dark tech/data visual]                    │
│ [Semi-transparent overlay: #0A0E1A @ 45% opacity]            │
│                                                              │
│    Contextual Title (38pt bold white Segoe UI Semibold)      │
│    e.g. "Validation des Estimations\n                        │
│          de Coûts de Construction"                           │
│                                                              │
│    Subtitle · Describes what it does (14pt light blue)       │
│    ───── accent bar (3.0" × 0.04") ─────                    │
│                                                              │
│    Clément Droinat (14pt bold white)                         │
│    Solution Engineer, Data & Analytics (11pt gray)           │
└──────────────────────────────────────────────────────────────┘
```

### Rules
- Title must be CONTEXTUAL — describe the project/analysis, NOT generic slogans
- NO project name/complex name, NO country, NO submission date on title
- Background: `assets/title_bg.jpg` + dark overlay at 45% opacity
- Fallback if no image: navy `#1B1F3B` (NOT black)
- Overlay transparency via XML: `a:srgbClr > a:alpha val="45000"`

```python
# Image background + overlay
slide.shapes.add_picture(str(bg_path), 0, 0, prs.slide_width, prs.slide_height)
overlay = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
overlay.fill.solid()
overlay.fill.fore_color.rgb = RGBColor(0x0A, 0x0E, 0x1A)
# Set 45% opacity via XML
sp_pr = overlay._element.find(qn('p:spPr'))
solid_fill = sp_pr.find(qn('a:solidFill'))
srgb = solid_fill.find(qn('a:srgbClr'))
alpha = etree.SubElement(srgb, qn('a:alpha'))
alpha.set('val', '45000')
overlay.line.fill.background()
```

## Title Slide (Dark Background — Legacy)

Use when no background image available. Navy `#0F172A`, NOT black.

```
┌──────────────────────────────────────────────────────────────┐
│ ═══ teal accent bar (0.05") ═══                             │
│                                          DARK (#0F172A)     │
│ [Fabric icon]  Microsoft Fabric (16pt bold white)           │
│                                                              │
│                                                              │
│    Bring your data into the era of AI (40pt white)          │
│                                                              │
│    Project Name — Subtitle (18pt teal)                      │
│    ───── teal bar (2.5" × 0.04") ─────                     │
│                                                              │
│    Clément Droinat (14pt bold white)                        │
│    Solution Engineer, Data & Analytics (11pt gray)          │
└──────────────────────────────────────────────────────────────┘
```

Key: No `slide_header()`/`slide_footer()`. Full-bleed `rect(0, 0, W, H, DARK)`.

## Content Slide Structure (13.333" × 7.5" Widescreen)

```
┌──────────────────────────────────────────────────────────────┐
│ ═══ teal accent bar (0.06" tall) ═══                        │
│                                                              │
│ [Fabric icon]  Project Title                                 │
│                Subtitle · Description                        │
│ ─── separator line ───                                       │
│                                                              │
│ ┌───────┐  → ┌──────────────────────────────────┐  → ┌─────┐│
│ │Sources│    │ Microsoft Fabric          OneLake │    │Users││
│ │(dashed│    │ ┌──────┐→┌──────┐→┌──────┐→┌────┐│    │     ││
│ │ box)  │    │ │Ingest│ │Store │ │Serve │ │Use ││    │     ││
│ │       │    │ │      │ │      │ │      │ │    ││    │     ││
│ │       │    │ └──────┘ └──────┘ └──────┘ └────┘│    │     ││
│ └───────┘    └──────────────────────────────────┘    └─────┘│
│                                                              │
│ ─── footer (gray bar) :: icons credit · generator · project ─│
└──────────────────────────────────────────────────────────────┘
```

## Component Card

A white rounded rectangle with icon + text + optional badge below.

```
┌──────────────────────────────┐
│ [icon]  Name (8pt bold)      │  card_h = 0.58"
│         Description (6pt)    │
└──────────────────────────────┘
  [ badge label (6.5pt) ]         badge below card

icon: 0.32" × 0.32" at (card_left + 0.06", card_top + 0.12")
text: starts at card_left + 0.42"
name: top + 0.04", 8pt Segoe UI Bold
desc: top + 0.23", 6pt Segoe UI, GRAY_600
badge: top + card_h + 0.04", centered
```

### Naming Conventions (critical for fit)
| Item Type | Prefix | Example |
|-----------|--------|---------|
| Pipeline | `PL_` | `PL_CCE_Setup` |
| Notebook | `NB_` | `NB_Setup_LH` |
| Lakehouse | `LH_` | `LH_CCE_Ref` |
| Semantic Model | `SM_` | `SM_CCE` |
| Report | `RPT_` | `RPT_CCE` |
| Data Agent | _(name)_ | `CCE_Advisor` |

## Detail Pills (Delta Tables / Measures)

Small colored pills inside a zone listing specific artifacts:

```python
# Delta table pills in STORE zone
for i, table_name in enumerate(tables):
    y = start_y + Inches(i * 0.2)
    sh = rect(zone_left + Inches(0.1), y, zone_w - Inches(0.2), Inches(0.17),
              GREEN_50, GREEN_200, Pt(0.5))
    # text: 6pt Consolas, centered, zone accent color
```

- Height: `0.17"` per pill, `0.2"` spacing (including gap)
- Font: `6pt Consolas` (monospace for technical names)
- Colors: match parent zone triad
- Guard: check `y + 0.18"` stays inside zone bottom

## Step Circles

Numbered circles between zones showing data flow order:

```
 ①        ②        ③        ④
  →        →        →        →
DFS API  writes   Direct   Report
Upload   Delta    Lake     + AI
```

- Size: `0.28"` oval, green fill (`STEP_BG`), green border (`STEP_BD`)
- Number: `9pt Segoe UI Bold`, centered, `STEP_FG` color
- Arrow: `18pt "→"` in `GRAY_400`
- Label: `6.5pt` two-line text below arrow

## Zone Template

Each inner zone follows this structure:

```python
rect(z_left, Z_T, Z_W, Z_H, COLOR_50, COLOR_200, Pt(1))           # zone box
text(z_left + 0.08", Z_T + 0.06", ...)                              # zone header
component(z_left + 0.06", Z_T + 0.35", Z_W - 0.12", ...)          # first component
# optional: trigger label between components
component(z_left + 0.06", Z_T + 1.55", Z_W - 0.12", ...)          # second component
# optional: detail pills
```

## Badge Types

| Badge | Background | Foreground | Border | Used For |
|-------|-----------|------------|--------|----------|
| Data Factory | PURPLE_50 | PURPLE_700 | PURPLE_200 | Pipeline items |
| Data Engineering | GREEN_50 | GREEN_700 | GREEN_200 | Notebook, Lakehouse |
| Semantic Model | AMBER_50 | AMBER_700 | AMBER_200 | Semantic model items |
| Power BI | ROSE_50 | ROSE_700 | ROSE_200 | Reports, dashboards |
| Data Source | SLATE_50 | SLATE_700 | SLATE_200 | External sources |
| Data Agent | GREEN_50 | GREEN_700 | GREEN_200 | AI agents |

## Dashed Box Pattern (Sources / Users)

Used for external entities outside the Fabric zone:

```python
rect(left, top, width, height, SLATE_50, SLATE_200, Pt(1), dash=True)
```

- `dash=True` sets `line.dash_style = 2` (dashed border)
- Interior: component cards stacked vertically with 0.8" spacing
- Bottom: summary text (row counts, descriptions) in `GRAY_400, 7pt`

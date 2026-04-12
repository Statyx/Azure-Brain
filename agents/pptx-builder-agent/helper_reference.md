# Helper Function Reference — `_build_pptx.py`

Complete catalog of reusable helper functions for PPTX generation. These are defined in `_build_pptx.py` and operate on a global `slide` variable set by `new_slide()`.

---

## Core Setup

### `new_slide()`
Creates a blank slide, sets it as the global `slide` reference, applies light gray background.
```python
def new_slide():
    global slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG  # #F8FAFC
    return slide
```

### `icon(name) → str | None`
Returns the path to a pre-rendered PNG icon, or `None` if not found.
```python
def icon(name):
    p = PNG_DIR / f"{name}.png"
    return str(p) if p.exists() else None
```

---

## Drawing Primitives

### `rect(left, top, w, h, fill, border, border_w, radius, dash) → Shape`
Rounded (or square) rectangle with optional border and dash style.
- `fill`: `RGBColor` for background
- `border`: `RGBColor` or `None` (transparent line)
- `radius=True`: uses `MSO_SHAPE.ROUNDED_RECTANGLE` with `adjustments[0] = 0.06`
- `dash=True`: sets `line.dash_style = 2` (evenly spaced dashes)
- Always disables shadow via `sh.shadow.inherit = False`

### `text(left, top, w, h, txt, sz, bold, color, align, anchor) → TextBox`
Single-paragraph text box. Default: `9pt, Segoe UI, left-aligned, top-anchored`.
- `anchor`: `MSO_ANCHOR.TOP` (default) or `MSO_ANCHOR.MIDDLE` for vertical centering

### `multitext(left, top, w, h, lines, align) → TextBox`
Multi-paragraph text box. `lines` is a list of `(text, size, bold, color)` tuples.
- Each paragraph gets `space_after = Pt(4)`
- Use for bullet lists, multi-line descriptions, persona lists

### `pic(name, left, top, size) → Picture | None`
Inserts a PNG icon. Returns `None` if the icon file doesn't exist. Default `size = Inches(0.42)`.

---

## Architecture Components

### `step_circle(left, top, num)`
Green numbered circle for data flow ordering.
- Size: `0.28"` oval
- Colors: `STEP_BG` fill, `STEP_BD` border (1.5pt), `STEP_FG` text
- Font: `9pt Segoe UI Bold`, centered

### `arrow_label(left, top, label)`
Arrow character (`→` at 18pt) with optional 2-line label below.
- Arrow color: `GRAY_400`
- Label: `6.5pt Segoe UI`, `GRAY_600`, center-aligned
- Typical labels: `"DFS API\nUpload"`, `"writes\nDelta"`, `"Direct\nLake"`, `"Report\n+ AI"`

### `badge(left, top, label, bg, fg, bd, w)`
Small colored label badge, typically placed below a component card.
- Height: `0.18"`, default width: `1.05"`
- Font: `6.5pt Segoe UI Bold`, centered
- Colors are zone-specific triads (see Color System below)

### `component(left, top, w, icon_name, name, desc, badge_*, icon_size) → card_h`
Full component card: white rounded rect + icon + name + description + optional badge.
- Card height: `0.58"` (fixed)
- Icon: `0.32"` at `(+0.06", +0.12")` from card top-left
- Name: `8pt Segoe UI Bold` at `+0.42"` from left, `+0.04"` from top
- Description: `6pt Segoe UI` in `GRAY_600` at `+0.23"` from top
- Badge: positioned `+0.04"` below the card

---

## Slide Furniture

### `slide_header(title, subtitle)`
Standard header for all content slides:
1. Teal accent bar at top (`0.06"` tall)
2. Fabric icon (`0.55"`) at top-left
3. Title text (`20pt bold`) next to icon
4. Optional subtitle (`10pt gray`) below title
5. Separator line (`0.01"` tall, `SLATE_200`)

### `slide_footer()`
Standard footer bar:
- Light gray bar at bottom (`0.4"` tall, `SLATE_50`)
- Credits text: `6.5pt GRAY_400` — icons attribution, generator name, project label

---

## Composite Components

### `info_card(left, top, w, h, title_txt, items, bg, bd, fg, icon_name)`
Rounded card with title + bullet list. Used on Solution and Use Case slides.
- Title: `11pt bold` in `fg` color, optional icon to the left
- Items: list of strings, rendered as `"• {item}"` in `8.5pt GRAY_600`
- Typical size: `3.9" × 2.5"` (Solution) or `2.8" × 1.7"` (I/O cards)

---

## Color System — Complete Reference

### Tailwind-Inspired Triads (50/200/700 = background/border/text)

| Name | 50 (bg) | 200 (border) | 700 (text) | Usage |
|------|---------|-------------|-----------|-------|
| PURPLE | `#FAF5FF` | `#E9D5FF` | `#7C3AED` | Ingest & Transform zone |
| GREEN | `#F0FDF4` | `#BBF7D0` | `#15803D` | Store zone, Data Engineering |
| AMBER | `#FFFBEB` | `#FDE68A` | `#B45309` | Serve zone |
| CYAN | `#ECFEFF` | `#A5F3FC` | `#0E7890` | Consume zone |
| BLUE | `#EFF6FF` | `#BFDBFE` | `#1D40AF` | Business Users, Input cards |
| ROSE | `#FFF1F2` | `#FECDD3` | `#BE123C` | Power BI items |
| SLATE | `#F8FAFC` | `#E2E8F0` | `#334155` | External Sources, neutral |
| RED | `#FEF2F2` | `#FECACA` | `#B91C1C` | Pain points / alert section |

### Special Colors

| Name | Hex | Usage |
|------|-----|-------|
| `WHITE` | `#FFFFFF` | Card backgrounds |
| `BG` | `#F8FAFC` | Slide background (light gray) |
| `DARK` | `#0F172A` | Title slide background (navy) |
| `GRAY_600` | `#475569` | Description text |
| `GRAY_400` | `#94A3B8` | Subtle text, arrows |
| `TEAL_700` | `#0F766E` | Fabric zone border, header text |
| `TEAL_500` | `#14B8A6` | Accent bars, subtitle text |
| `STEP_BG` | `#DCFCE7` | Step circle fill |
| `STEP_FG` | `#166534` | Step circle number text |
| `STEP_BD` | `#4ADE80` | Step circle border |

---

## Layout Constants — Architecture Slide

```python
M       = Inches(0.3)     # page margin
SRC_W   = Inches(1.6)     # sources column width
USR_W   = Inches(1.9)     # users column width
GAP     = Inches(0.45)    # gap between major columns
FAB_L   = M + SRC_W + GAP # fabric zone left edge (computed)
FAB_W   = SLIDE_W - FAB_L - USR_W - GAP - M
FAB_T   = Inches(1.2)     # fabric zone top
FAB_H   = Inches(5.6)     # fabric zone height
Z_T     = FAB_T + Inches(0.55)  # inner zone top
Z_H     = FAB_H - Inches(0.75)  # inner zone height
ARROW_W = Inches(0.42)    # space for step circle + arrow
N_ZONES = 4               # Ingest, Store, Serve, Consume
Z_W     = (FAB_W - Inches(0.35) - (N_ZONES-1)*ARROW_W) / N_ZONES
```

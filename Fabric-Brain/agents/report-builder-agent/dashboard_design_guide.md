# Dashboard Design Guide

> The design bible: tones, typography, color, layout principles, and the five dashboard archetypes. **Format-agnostic** — applies equally to PBIR and any future format.

---

## 1. Five Archetypes

Every dashboard answers one of five primary user intents. Pick **one** archetype per page; mix archetypes only across pages, never within a page.

| Archetype | User intent | Reading time | Density |
|---|---|---|---|
| **Executive Summary** | *"Give me the headline."* | 5 seconds | Sparse |
| **Operational Monitor** | *"What's happening now? Is anything broken?"* | 10–30 seconds | Medium-high |
| **Analytical Canvas** | *"Let me explore. I'll drill, slice, ask questions."* | Minutes | High |
| **Narrative Story** | *"Walk me through the insight."* | 1–3 min, sequential | Sparse |
| **Comparative Benchmark** | *"How does X compare to Y?"* | 30 seconds | Medium |

Layouts and visual mixes per archetype are in [`pages_layout.md`](pages_layout.md) and [`visual_catalog.md`](visual_catalog.md).

---

## 2. The 5-Second Rule

A reader should grasp the page's primary message in 5 seconds. Implications:
- **KPIs at the top-left** (F-pattern reading)
- **One headline per page** — a single title that names the question being answered
- **Progressive detail** — KPI → trend → breakdown → drill table, top to bottom
- **One story per page** — if there are two stories, split into two pages

---

## 3. Visual Hierarchy

```
1. Page title          — establishes context ("what am I looking at?")
2. KPI cards (row)     — key numbers, ideally with delta vs target/period
3. Primary chart       — the headline pattern (trend / comparison / split)
4. Secondary chart(s)  — supporting detail
5. Table / matrix      — granular data for drill
6. Slicers             — user controls (top bar or left sidebar)
```

**Inverted pyramid by aggregation level**: most aggregated at top, most granular at bottom.

---

## 4. Tones (Color Strategy)

Pick one tone per report. Every visual inherits the tone's palette via the theme file ([`themes_styling.md`](themes_styling.md)).

### Bright Light (default office)
- Background `#FFFFFF`, Foreground `#1F2A37`
- Accents: `#0078D4 #107C10 #C42B1C #FF8C00 #5C2D91 #008272 #B4A0FF #767676`
- Use for: operational reports, finance, HR, supply chain.

### Soft Pastel (friendly narrative)
- Background `#F4F6F8`, Foreground `#2D3748`
- Accents: `#5B8DEF #6FCF97 #F2994A #EB5757 #BB6BD9 #56CCF2 #F2C94C #828282`
- Use for: customer success, brand reports, narrative storytelling.

### High Contrast (accessibility, regulated)
- Background `#FFFFFF`, Foreground `#000000`
- Accents: `#0F62FE #198038 #DA1E28 #FA4D56 #6929C4 #1192E8 #B28600 #525252`
- Use for: audit, compliance, healthcare, government.

### Dark Mode (executive, NOC)
- Background `#1A1F2C`, Foreground `#E5E7EB`
- Accents: `#36B5FF #57D9A3 #FFAB48 #FF7185 #B68AFF #58D2D2 #FFE15D #9CA3AF`
- Use for: real-time monitors, exec dashboards, NOC, IoT.

### Earthy Warm (brand-driven)
- Background `#FBF7F2`, Foreground `#3D2C1E`
- Accents: `#C2570C #5F8B4C #B45253 #D9A05B #7C5C42 #2F6B7E #B89F65 #6E5849`
- Use for: sustainability, retail, hospitality, lifestyle brands.

### Tone selection checklist
- [ ] One tone selected
- [ ] Theme file built with the tone's palette
- [ ] All visual fills resolved via `ThemeDataColor` (not hard-coded hex) when possible
- [ ] Foreground reaches WCAG AA contrast against background
- [ ] If dark mode: dark-mode checklist from [`themes_styling.md`](themes_styling.md) verified

---

## 5. Typography

### Font stack

| Priority | Font | Use |
|---|---|---|
| 1 | **Segoe UI** | Default for all dashboard text |
| 2 | **Segoe UI Semibold** | Emphasis, card values |
| 3 | **DIN** | Numeric-heavy displays (alternative) |
| Fallback | **Arial** | Safe fallback |

**Rule**: one font family per report. Differentiate via weight and size, never family.

### Scale

| Role | Size | Weight | Where |
|---|---|---|---|
| Page title | 14pt | Bold | Top-of-page textbox |
| Section heading | 12pt | Semibold | Group label |
| Visual title | 11pt | Regular or Semibold | `visualContainerObjects.title.fontSize` |
| KPI callout value | 27pt | Semibold | `objects.value.fontSize` *(cardVisual)* |
| KPI label | 10pt | Regular | Below the KPI value |
| Axis labels | 10pt | Regular | `categoryAxis.fontSize` / `valueAxis.fontSize` |
| Data labels | 9pt | Regular | `labels.fontSize` |
| Legend | 10pt | Regular | `legend.fontSize` |
| Table header | 11pt | Semibold | `columnHeaders.fontSize` |
| Table body | 10pt | Regular | `values.fontSize` |
| Tooltip | 10pt | Regular | `visualTooltip` |
| Slicer items | 10pt | Regular | `slicerSettings.fontSize` |

**Always** set `value.fontSize` on `cardVisual` — the schema default is enormous and clips at any sensible width. (Note: `cardCalloutArea` controls the rectangle, **not** the text — see `cli_knowledge/visuals/cardVisual/objects/`.)

---

## 6. The 1280 × 720 Grid (8 px rhythm)

| Rule | Value |
|---|---|
| Canvas | 1280 × 720 (`displayOption: FitToPage`) |
| Side margins | 30 px |
| Top margin | 10 px |
| Bottom margin | 20 px |
| Inter-column gap | 20 px |
| Inter-row gap | 10–15 px |
| Usable area | 1220 × 690 |
| Grid unit | 8 px (all sizes are multiples of 8 where possible) |

**KPI card minimum height: 120 px** (otherwise callout numbers clip).  
**Slicer minimum height with title: 75 px** (otherwise title overlaps value).

See [`pages_layout.md`](pages_layout.md) for full layout templates per archetype.

---

## 7. White Space

White space is **content**, not waste.
- Minimum 10 px gap between any two visuals.
- Do not fill every pixel — readers need breathing room.
- Group related visuals tightly (8-10 px gaps); separate unrelated groups widely (20-30 px gaps).
- A page with 5 well-spaced visuals always reads better than 10 cramped ones.

---

## 8. Color Use Discipline

| Rule | Why |
|---|---|
| One accent color per page | Multiple accents fight for attention |
| Categorical colors only when categories differ qualitatively | "Region A vs B" yes; "Q1 vs Q2" no — use the same color |
| Sequential colors for ordinal data | Heatmaps, intensity, score |
| Diverging colors for signed values | Variance, gain/loss, sentiment |
| Red = bad, Green = good — only with cultural context | In finance, red can mean "negative", in retail "luxury" |
| Grey is a color | Use neutral grey for context data so accent pops |
| Match `dropShadow.color` to background | Black shadow on dark bg = invisible mass; use 92+ transparency |

---

## 9. Page Setup Checklist

Before declaring a page done:

- [ ] Title textbox at top, 1220×40, page-name visible
- [ ] Tone applied via theme
- [ ] All visuals snap to the 8 px grid
- [ ] All KPI cards same height (120) and same width within a row
- [ ] All chart visuals same height within a row
- [ ] No off-canvas visuals (x+width ≤ 1250, y+height ≤ 710)
- [ ] One archetype per page (no mixing)
- [ ] Page-level filters set if scope differs from report-level
- [ ] Slicers (if any) anchored top or left, not floating
- [ ] Page tested at FitToPage on a 1366×768 laptop (smallest realistic screen)

---

## 10. Anti-Patterns (Avoid These)

| Anti-pattern | Why it hurts | Replacement |
|---|---|---|
| 3D pie chart | Distorts angle perception | Donut with ≤ 6 slices, or bar chart |
| Truncated Y-axis on bar chart | Exaggerates difference deceptively | Either zero-baseline or call attention with annotation |
| 8-color palette on one chart | Eye can't separate more than 5-6 hues | Group into "top N + Other" |
| Multiple fonts | Cognitive load, looks unprofessional | One family + weights |
| Rainbow palette for ordinal data | No perceptual order | Sequential single-hue gradient |
| Tiny callout numbers in cards | Defeats the point of a KPI | Always set `value.fontSize: 27D+` on cardVisual |
| Visuals touching the edge | Looks unfinished | Respect the 30 px side margin |
| Two visuals showing the same data differently | Reader picks the worse one | Pick one — the one matching the question |
| Action button without target | Frustrates the user | Always bind `action` to a page navigation or bookmark |

---

## 11. From Screenshot to PBIR — Mini-Workflow

If the user gives a screenshot, decode it before generating:

1. **Tone**: dark or light? primary accent hue?
2. **Archetype**: one headline number row? trend? grid of small multiples? sidebar? → match to section 1.
3. **Visual inventory**: enumerate each rectangle, label it with a visual type from [`visual_catalog.md`](visual_catalog.md).
4. **Grid**: measure pixel ratios → snap to 1280 × 720 with 8 px rhythm.
5. **Typography**: estimate title size, KPI size, body size — match to section 5 scale.
6. **Generate** the PBIR folder, validate, deploy.
7. **Compare** the deployed report to the screenshot — adjust spacing/colors as needed.

---

## 12. Cross-References

- Mandatory agent rules → [`instructions.md`](instructions.md)
- PBIR folder anatomy → [`report_structure.md`](report_structure.md)
- Visual selection per archetype → [`visual_catalog.md`](visual_catalog.md)
- Grid + page layouts → [`pages_layout.md`](pages_layout.md)
- Expression encoding + VCO usage → [`themes_styling.md`](themes_styling.md)
- Property lookups → [`cli_knowledge/`](cli_knowledge/)
- Known issues → [`known_issues.md`](known_issues.md)

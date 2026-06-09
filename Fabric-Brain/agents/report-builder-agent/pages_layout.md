# Pages & Layout — PBIR

> Canvas dimensions, grid system, and ready-to-use page layouts per dashboard archetype.

---

## 1. Page Structure on Disk

```
pages/
├─ pages.json
└─ <pageId>/
   ├─ page.json
   ├─ filters.json          # optional, page-scoped filters
   └─ visuals/
      └─ <visualId>/
         ├─ visual.json
         ├─ filters.json    # optional, visual-scoped filters
         └─ mobile.json     # optional, mobile layout overrides
```

`pageId` is the page's internal name (no spaces, no special chars: `overview`, `cash_flow`, `pnl_q2`).  
`visualId` is a UUID (`uuidgen` in PowerShell: `[guid]::NewGuid().ToString('N').Substring(0,16)`).

---

## 2. `pages.json` (Page Index)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
  "activePageName": "overview",
  "pageOrder": ["overview", "pnl", "cash_flow", "trends"]
}
```

- `pageOrder[]` defines the tab order in the report viewer.
- Every entry must match an existing `pages/<id>/page.json` folder.
- `activePageName` is the page shown on first open.

---

## 3. `page.json` (Page Metadata)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
  "name": "overview",
  "displayName": "Overview",
  "displayOption": "FitToPage",
  "height": 720,
  "width": 1280,
  "visualInteractions": [],
  "objects": {}
}
```

### Canvas sizing

| Use case | Width × Height | Notes |
|---|---|---|
| **Standard 16:9** | 1280 × 720 | Default; renders crisp on most screens |
| **Wide 16:9 HD** | 1920 × 1080 | Use only if you have data density to fill it |
| **Mobile portrait** | 320 × 568 | Defined in `mobile.json` per visual, not page-level |
| **Letter (print)** | 816 × 1056 | Set `displayOption: "ActualSize"` |

### `displayOption`

| Value | Behaviour |
|---|---|
| `"FitToPage"` (default) | Scales to fit the browser window, preserving aspect ratio |
| `"ActualSize"` | Renders pixel-perfect — scroll bars appear if window is smaller |
| `"FitToWidth"` | Scales to fit width; height scrolls |

### Page-level `objects`

Page objects style the canvas itself. Use sparingly:

| Object | Purpose |
|---|---|
| `background` | Page background color / image |
| `displayArea` | Inner padding around all visuals |
| `outspace` | Color outside the canvas (when `FitToPage` shows letterboxing) |
| `pageInformation` | Title, type, hidden flag |
| `pageRefresh` | Auto-refresh interval (for `realTimeLineChart` pages) |
| `pageSize` | Width / height (mirror of `width`/`height` top-level) |
| `filterSortOrder` | Order of filters in the filter pane |

Values use the same PBIR expression envelopes as visuals (see [`themes_styling.md`](themes_styling.md)).

---

## 4. The 1280 × 720 Grid

### Margins & Gutters

| Edge | Padding |
|---|---|
| Left | 30 px |
| Right | 30 px |
| Top | 10 px (title bar starts immediately) |
| Bottom | 20 px |
| Between columns | 20 px |
| Between rows | 10–15 px |

Usable area: **1220 × 690** (after side margins and top/bottom padding).

### 12-column system

`12 × 100 - 20 × 11 = 980` doesn't fit 1220, so we use simpler ratios:

| Layout | Column widths (px) |
|---|---|
| **6 KPI cards** | `200 + 20 + 200 + 20 + 200 + 20 + 200 + 20 + 200 + 20 + 200 = 1320` → shrink to `190`: `190×6 + 20×5 = 1240` ✓ |
| **4 KPI cards** | `285 × 4 + 20 × 3 = 1200` ✓ |
| **3 + 1 split** | `390 × 3 + 20 × 2 + 20 + 30 = 1230 - extras = 1240` → use `400 + 20 + 400 + 20 + 400 + 20 + 0 = 1260` |
| **Sidebar + content** | sidebar `220` + gap `20` + content `980` = `1220` ✓ |
| **Two-column 50/50** | `600 + 20 + 600 = 1220` ✓ |
| **Three-column 33/33/33** | `393 + 20 + 393 + 20 + 393 = 1219` ✓ |

Rule of thumb: **divide 1220 by N visuals in a row, subtract 20·(N-1)/N for gaps**.

### Standard heights

| Element | Height (px) |
|---|---|
| Page title row | 50 |
| KPI card row | **120** (mandatory minimum for `cardVisual` callout) |
| Slicer row | 75 (when `vcObjects.title.show = true`) |
| Chart (compact) | 240 |
| Chart (standard) | 320 |
| Chart (hero) | 480 |
| Table / matrix | 260 (header + 8 rows × 28) — scale up |
| Separator line | 1 |

---

## 5. Archetype Layout Templates

Match each layout to the archetype defined in [`dashboard_design_guide.md`](dashboard_design_guide.md). All coordinates assume 1280 × 720.

### A. Executive Summary

```
┌──────────────────────────── 1280 ────────────────────────────┐
│ (10)  Title textbox 1220×40                                  │
│ (60)  KPI₁ 285×120  KPI₂ 285×120  KPI₃ 285×120  KPI₄ 285×120 │
│ (200) Trend line chart 800×220   Gauge 400×220               │
│ (440) Region bar chart 800×260   Narrative aiNarratives 400×260
└──────────────────────────────────────────────────────────────┘
```

### B. Operational Monitor

```
┌──────────────────────────────────────────────────────────────┐
│ Title 1220×40                                                │
│ Site selector 280×75    Time-range slicer 280×75    Alerts list 600×75
│ Status tiles row (5 × 230×120)                               │
│ Heat map 800×320                       Real-time line 400×320│
│ Anomalies tableEx 1220×140                                   │
└──────────────────────────────────────────────────────────────┘
```

### C. Analytical Canvas

```
┌─────────────────── sidebar 220 + content 980 ────────────────┐
│ Title 1220×40                                                │
│ ┌─ filters ─┐  ┌─ Key influencers (keyDriversVisual) 980×260 ┐
│ │ slicer 1  │  │                                              │
│ │ slicer 2  │  ├─ Decomposition tree 980×300 ────────────────┤
│ │ slicer 3  │  │                                              │
│ │ slicer 4  │  ├─ Scatter + matrix 480×280 + 480×280 ────────┤
│ │ slicer 5  │  │                                              │
│ └───────────┘  └──────────────────────────────────────────────┘
```

### D. Narrative Story (one hero per page)

```
┌──────────────────────────────────────────────────────────────┐
│ Section title 1220×60                                        │
│ Paragraph textbox 800×120  (left)                            │
│ Hero visual 1220×440 (full width)                            │
│ Caption textbox 1220×60                                      │
└──────────────────────────────────────────────────────────────┘
```

### E. Comparative Benchmark

```
┌──────────────────────────────────────────────────────────────┐
│ Title + scope selector 1220×60                               │
│ "This period" KPIs 600×120   "Last period" KPIs 600×120      │
│ Combo (line + column) 1220×320 — period-over-period delta    │
│ Variance waterfall 1220×180                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Z-Index & Layering

`visual.position.z` controls stacking. Conventions:

| Layer | `z` | Examples |
|---|---|---|
| Background shapes / images | 0 | Card backgrounds, accent strips |
| Charts / tables | 1000 | Most data visuals |
| KPI cards | 1500 | Always above background, below overlays |
| Section titles | 2000 | Textboxes |
| Overlays / annotations | 9000 | Tooltips, bookmark navigators |

Same `z` → declaration order in `pages.json` wins (last visual wins).

---

## 7. Mobile Layout (`mobile.json`)

Optional per-visual override:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/mobile/1.0.0/schema.json",
  "position": { "x": 0, "y": 0, "z": 0, "width": 320, "height": 200, "tabOrder": 0 },
  "hidden": false
}
```

Drop in `visuals/<visualId>/mobile.json` to override the visual's desktop coordinates on phones.

---

## 8. Validation Checklist

Before deployment:

- [ ] Every page folder is listed in `pages.json.pageOrder`.
- [ ] Every visual has unique `position` (no overlapping unless intentional).
- [ ] All `cardVisual` heights ≥ 120 px.
- [ ] All slicers with `title.show=true` have height ≥ 75 px.
- [ ] Page total width ≤ canvas width (no off-canvas visuals).
- [ ] Section dividers (1 px shapes) span the usable width (1220 px) with `x=30`.
- [ ] `displayOption` is consistent across all pages.

Run `powerbi-report-author validate <Report>.Report` to catch off-canvas, overlapping, and missing references.

---

## 9. Cross-References

- Visual types and skeletons → [`visual_catalog.md`](visual_catalog.md)
- Container styling, expression encoding → [`themes_styling.md`](themes_styling.md)
- Tones, archetypes, typography → [`dashboard_design_guide.md`](dashboard_design_guide.md)
- Deployment payload → [`report_structure.md`](report_structure.md)
- Property lookups → [`cli_knowledge/`](cli_knowledge/)

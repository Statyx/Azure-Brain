# Known Issues — PPTX Builder Agent

## Critical Layout Rule: Always Calculate Y Budget

**Every slide must have a Y-axis budget before coding.** The most common bug is elements overlapping or cut off.

### Y-Budget Template (13.333" × 7.5" widescreen)
```
Available:  7.50" total
- Header:   0.95" (accent bar + title + subtitle + separator)
- Footer:   0.35" (credits bar)
- Usable:   6.20" for content
Budget: sum(all_section_heights + gaps) ≤ 6.20"
```

### Dynamic Positioning (GOOD)
```python
cards_bottom = y_cards + n_rows * (card_h + gap_y)
table_y = cards_bottom + Inches(0.12)
table_h = Inches(0.24) * (n_data_rows + 1)
insight_y = table_y + box_h + Inches(0.08)
# Safety clamp against footer
insight_y = min(insight_y, prs.slide_height - Inches(0.80))
```

### Hardcoded Positions (BAD — causes overlap)
```python
ms_y = Inches(3.1)   # breaks if cards height changes
ins_y = Inches(5.8)  # overlaps table if more rows
```

## Table & Card Sizing Rules
- Table rows: `0.24"` height (not 0.28"). Font: 7pt data, 8pt header.
- 4 scenario cards: **2×2 grid** at `6.05" × 0.95"`, not 4-in-a-row (unreadable at 8pt).
- Card KPIs: 2-column layout. Name: 12pt bold. Values: 9pt. Secondary: 7.5pt gray.

---

## Windows-Specific

### SVG Rendering Libraries
| Library | Issue | Fix |
|---------|-------|-----|
| cairosvg | Missing `libcairo-2.dll` — no Windows binary | Use Playwright instead |
| cairocffi | Same DLL issue, also conflicts with rlPyCairo | `pip uninstall cairocffi` if rlPyCairo is needed |
| svglib + reportlab | Works but loses SVG gradients → flat colors | Only for simple non-gradient SVGs |
| Edge headless | `msedge --headless --screenshot` hangs indefinitely | Use Playwright Chromium |

### PowerPoint File Locking
- `prs.save()` fails if the PPTX is open in PowerPoint
- **Fix**: Always run `Stop-Process -Name POWERPNT -ErrorAction SilentlyContinue` before regenerating
- Alternatively: save to a temp filename and rename

### Playwright Installation
- First run requires: `python -m playwright install chromium`
- Downloads ~130MB Chromium browser
- Subsequent runs reuse the cached browser

## Text Overflow

### Problem
Component card text overflows when names or descriptions are too long. No error — text just wraps and overlaps neighboring elements.

### Prevention Rules
1. **Icon size**: Always `0.32"` — larger icons steal text space
2. **Name**: Max ~15 chars at 8pt. Use prefixes: `PL_`, `NB_`, `LH_`, `SM_`, `RPT_`
3. **Description**: Max ~25 chars at 6pt. One line only — never two
4. **User roles**: Single words only — "Controllers", "Engineers", "Managers" (not "Cost Controllers" or "Site Engineers")
5. **Badge labels**: Max ~15 chars at 6.5pt

### If Text Still Overflows
- Shrink icon to `0.28"`, adjust text offset to `0.38"`
- Reduce name font to `7pt`
- Abbreviate more aggressively
- Widen the column (adjust `SRC_W`, `USR_W`, or `GAP`)

## Layout Gotchas

### Zone Width Calculation
- Zone width is computed: `(FAB_W - padding - arrows) / N_ZONES`
- Adding a 5th zone makes all zones narrower — may need to reduce card padding
- Removing a zone does NOT auto-expand others — recalculate manually

### Detail Pills (Tables/Measures)
- Always guard with: `if y + Inches(0.18) > Z_T + Z_H - Inches(0.1): break`
- More than ~7 pills won't fit — truncate with "... +N more" text

### Rounded Rectangle Corners
- `MSO_SHAPE.ROUNDED_RECTANGLE` corner radius set via `sh.adjustments[0] = 0.06`
- Guard with `hasattr(sh, 'adjustments') and len(sh.adjustments) > 0`

---

## File Naming & Output Path

### Output filename must match presentation title
- **WRONG**: `architecture_diagram.pptx` (generic, doesn't reflect content)
- **RIGHT**: `Use Case Presentation - Architecture Vision.pptx` (matches hero text)
- Update `OUT` path at the top of `_build_pptx.py` when changing the presentation title
- PowerPoint and Windows Explorer display the filename — it should be professional

### OneDrive Sync Delays
- Files on OneDrive paths may have a sync delay before they're accessible
- After `prs.save()`, the file may briefly show as locked by OneDrive sync process
- If saving fails, wait a few seconds and retry — do NOT silently overwrite
- Renaming files in OneDrive folders sometimes requires closing the folder in Explorer

---

## Multi-Slide Deck Issues

### Slide Count in Automated Checks
- The QA check `assert len(prs.slides) == 1` is ONLY valid for single-slide diagrams
- For multi-slide decks (Title + Use Cases + Solution + Architecture), update to: `assert len(prs.slides) >= 4`
- Shape count checks should be per-slide, not per-deck

### Detail Pills Are Deprecated in Architecture Slides
- **DO NOT** use loops to add individual table name pills or measure name pills
- They clutter the architecture diagram and are unreadable at presentation distance
- Use summary text instead: `"10 tables · ~8 000 rows"`, `"55 DAX measures · 11 relationships"`
- If pills were in an earlier version, remove them when updating the deck
- Fabric zone uses smaller radius: `0.02`

### Shadow Removal
- All shapes: `sh.shadow.inherit = False` to prevent default Office shadow
- Without this, icons and cards get unwanted drop shadows

## python-pptx Limitations

- **No SVG support** — must convert to PNG before inserting
- **No gradient fills on shapes** — only solid fills (use 50/200/700 color triads instead)
- **Gradient background workaround** — for title slides, use solid dark fill (`DARK = #0F172A`) + teal accent bar to simulate gradient feel
- **Multi-slide global state** — `new_slide()` must update a global `slide` variable; all helpers (`rect`, `text`, `pic`) use this global. Define `M` (margin) before first `new_slide()` call since layout constants depend on it
- **No custom fonts embedding** — relies on fonts installed on the viewing machine
- **Segoe UI**: requires Windows or manual font install on macOS/Linux
- **Blank layout** = `prs.slide_layouts[6]` — always use this for custom diagrams

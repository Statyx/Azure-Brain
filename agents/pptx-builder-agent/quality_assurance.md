# Quality Assurance — Final Review Protocol

> Inspired by the **Quality Assurance Editor** role from [claude-code-ppt-generation-team](https://github.com/HungHsunHan/claude-code-ppt-generation-team).

## Purpose

Every generated PPTX must pass a systematic quality review before delivery. This is the **last line of defense** — catch layout bugs, text overflow, missing icons, and narrative gaps before the user opens PowerPoint.

---

## QA Workflow

```
Phase 1: Automated Checks (run in Python)
  → File exists, size > 50KB, has exactly 1 slide
  
Phase 2: Visual Verification (open in PowerPoint)  
  → Text overflow, icon rendering, color consistency
  
Phase 3: Content Completeness
  → Every Fabric item present, narrative coherent
  
Phase 4: Issue Report
  → Categorized by severity, specific fix suggestions
```

---

## Phase 1: Automated Checks

Run these programmatically after `prs.save()`:

```python
from pptx import Presentation
from pathlib import Path

pptx_path = Path("Use Case Presentation - Architecture Vision.pptx")

# File checks
assert pptx_path.exists(), "PPTX file was not created"
assert pptx_path.stat().st_size > 50_000, f"File too small ({pptx_path.stat().st_size} bytes) — likely missing icons"
assert pptx_path.stat().st_size < 5_000_000, f"File too large ({pptx_path.stat().st_size} bytes) — check for oversized images"

# Structure checks
prs = Presentation(str(pptx_path))
n_slides = len(prs.slides)
assert n_slides >= 1, "No slides found"
assert prs.slide_width == 12192000, "Slide width is not 13.333 inches (widescreen)"

# Multi-slide deck: expect Title + Use Case(s) + Solution + Architecture
# Adjust expected count based on project (single use case = 4, dual = 5, etc.)
expected_min_slides = 4
assert n_slides >= expected_min_slides, f"Expected at least {expected_min_slides} slides, got {n_slides}"

# Per-slide shape count check
for i, s in enumerate(prs.slides):
    n = len(s.shapes)
    if i == 0:  # Title slide — fewer shapes expected
        assert n >= 5, f"Slide {i}: only {n} shapes — title slide seems empty"
    else:
        assert n >= 15, f"Slide {i}: only {n} shapes — likely missing content"
        assert n <= 200, f"Slide {i}: {n} shapes — possible duplicate rendering"

print(f"✅ Automated checks passed: {pptx_path.name}, {pptx_path.stat().st_size:,} bytes, {n_slides} slides")
```

---

## Phase 2: Visual Verification Checklist

Open the PPTX in PowerPoint and check each item:

### Layout & Spacing
```
□ Teal accent bar visible at top (thin horizontal line)
□ Fabric icon + title visible in header
□ Separator line below header
□ Three-column layout: Sources | Fabric Zone | Users
□ All 4 inner zones visible and evenly spaced
□ Step circles (①②③④) between zones
□ Footer bar at bottom with credits
```

### Text Rendering
```
□ NO text overlapping icons (most common bug)
□ NO text wrapping to second line inside component cards
□ All component names fully visible
□ All descriptions fully visible
□ Badge labels centered and readable
□ Zone headers visible and in correct color
□ Arrow labels ("DFS API Upload", "writes Delta") readable
□ Detail pills (table names, measures) all visible — none cut off
```

### Icons
```
□ All icons render with gradients (not flat colors)
□ Icons are square and properly cropped (no excess whitespace)  
□ Icon size consistent across all component cards (~0.32")
□ Fabric icon in header larger (~0.55")
□ OneLake icon visible in top-right of Fabric zone
□ No missing icon placeholders (empty spaces where icon should be)
```

### Colors
```
□ Background is light gray (#F8FAFC), not white
□ Each zone has distinct color (Purple/Green/Amber/Cyan)
□ Zone backgrounds are pastel (50 shade), borders are medium (200 shade)
□ Text colors are dark (700 shade) within each zone
□ Sources and Users boxes have dashed borders
□ Card backgrounds are white (#FFFFFF)
□ Step circles are green fill with green border
```

---

## Phase 3: Content Completeness

Cross-reference against the project outline:

```
□ Every data source from outline appears in Sources column
□ Every Fabric item appears in correct zone
□ Summary counts match reality (table count, measure count, relationship count)
□ NO individual table names or measure names as pills in architecture slide
□ All user roles appear in Users column
□ Step numbers match deployment order
```

### Multi-Slide Completeness (for multi-use-case decks)
```
□ Title slide lists ALL use cases as numbered bullets
□ Each use case has its OWN dedicated slide
□ Each use case slide has: pain points, I/O cards, personas, criteria, success measures
□ Solution slide references ALL use cases with combined counts
□ Architecture slide shows unified platform (not per-use-case diagrams)
□ Consume zone shows ALL agents (one per use case)
□ Footer text is consistent across ALL slides
□ Output filename matches the presentation title
```
□ Arrow labels accurately describe the data flow
□ Summary text in Sources box matches actual data volume
□ Workspace name in Fabric zone header is correct
□ Project title in main header is correct
```

---

## Phase 4: Issue Categorization

### Severity Levels

| Level | Definition | Example | Action |
|-------|-----------|---------|--------|
| **🔴 Critical** | Blocks presentation use | Missing zones, blank slide, file corruption | Must fix before delivery |
| **🟠 Important** | Visually broken but readable | Text overflow, missing icon, wrong color | Should fix |
| **🟡 Minor** | Cosmetic imperfection | Slight misalignment, extra whitespace | Can defer |

### Common Issues + Fixes

| Issue | Severity | Root Cause | Fix |
|-------|----------|-----------|-----|
| Text overlapping icon | 🟠 | Name too long | Shorten to ≤15 chars, use prefix abbreviation |
| Text wrapping in card | 🟠 | Description too long | Shorten to ≤25 chars, one line only |
| Flat-color icons | 🟠 | Used svglib instead of Playwright | Re-run _convert_icons.py with Playwright |
| Missing icon (empty space) | 🔴 | PNG not in _icon_pngs/ | Add to ICONS dict, re-run converter |
| Zone too narrow | 🟠 | Too many zones or GAP too wide | Reduce N_ZONES or shrink GAP |
| Pills cut off at bottom | 🟡 | More than 7 pills | Truncate list, add "... +N more" |
| File permission error on save | 🔴 | PowerPoint has file open | `Stop-Process -Name POWERPNT` |
| File < 50KB | 🔴 | Icons not embedded | Check PNG paths, verify icon() returns valid path |
| Wrong colors | 🟡 | Copy-paste from wrong zone | Verify color triad matches zone purpose |

---

## QA Report Template

After review, produce a brief report:

```markdown
## QA Report — architecture_diagram.pptx

**File**: 232,456 bytes | 1 slide | 67 shapes
**Generated**: 2026-04-10

### Automated Checks: ✅ PASS

### Visual Verification
- [x] Layout correct — 3-column with 4 inner zones
- [x] Text fits all cards — no overflow
- [x] Icons render with gradients
- [x] Colors consistent per zone
- [ ] ⚠️ "dim_escalation" pill slightly truncated

### Content Completeness
- [x] All 7 data sources present
- [x] All 5 Fabric items in correct zones
- [x] 7/7 Delta tables listed
- [x] 5/5 key measures listed

### Issues Found
| # | Severity | Description | Fix |
|---|----------|-------------|-----|
| 1 | 🟡 Minor | "dim_escalation" pill text truncated | Widen pill or abbreviate to "dim_escal" |

### Verdict: ✅ READY FOR DELIVERY
```

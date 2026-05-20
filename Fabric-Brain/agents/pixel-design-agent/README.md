# Pixel Design Agent — README

Pre-deployment visual validation agent for Power BI reports in Microsoft Fabric.

## Purpose

Catches layout issues **before** deployment — no more "numbers don't fit" after a 2-minute deploy cycle.

## What It Validates

| Rule | What | Why |
|------|------|-----|
| Card height | Font size vs container height | Numbers clip or overflow |
| No bg_panel | BasicShape behind clickables | Blue selection ring appears |
| Page bounds | x + width ≤ 1280 | Visuals get clipped |
| No overlap | Same z-order collision | Visuals stack unpredictably |
| Slicer width | Min 180px | Dropdown unusable if narrow |
| Table height | Header + 5 rows minimum | Table shows blank space |
| Chart size | Min 300×200 | Axis labels overlap |
| Border off | vcObjects border: false | Prevents focus ring |
| Visual header | Hidden on cards | Hover toolbar clutters KPIs |
| Separator Y | Below tallest visual in row | Layout consistency |

## Usage

```bash
cd src/
python validate_report.py          # Check only
python validate_report.py --fix    # Auto-fix what's possible
```

## Learned From

- Card h=55 with font 14D → numbers clipped (3 pages affected)
- `_bg_panel` basicShape → blue selection ring on click (6 panels)
- `border: true` in vcObjects → all visuals got thick blue border
- Font 27D in h=65 card → value completely hidden

# Known Issues — pixel-design-agent

Layout failures caught (and now prevented) by the visual validator. Every entry below cost at
least one deploy cycle before the rule existed.

---

## 1. Card Numbers Clipped by Font/Height Mismatch

**Symptom**: the KPI value is cut off, or invisible entirely, while the card renders fine in the
JSON definition.

**Cases seen**:
- card `h=55` with font `14D` → numbers clipped (3 pages affected)
- font `27D` in an `h=65` card → value **completely hidden**

**Cause**: the callout value box does not shrink to fit; it is clipped by the container.

**Fix**: validate font size against container height before deploying (`validate_report.py`).
Rule of thumb: leave ≥ 2.4× the font size in card height, and give the label its own room.

---

## 2. `_bg_panel` BasicShape Produces a Blue Selection Ring

**Symptom**: clicking anywhere on a page shows a blue focus/selection ring around a rectangle
(6 panels affected on first occurrence).

**Cause**: a `basicShape` used as a background panel sits behind clickable visuals and becomes
selectable itself.

**Fix**: don't use `basicShape` as a background layer behind interactive visuals. Use the page
canvas background (`section.config.objects.background` + `outspace`) instead.

---

## 3. `border: true` Puts a Thick Blue Border on Everything

**Symptom**: every visual on the page gains a heavy border after a theme or `vcObjects` change.

**Fix**: set `vcObjects.border` to `false` explicitly. Do not rely on the default.

---

## 4. Opaque Textbox Over a Colored Band

**Symptom**: a white title placed over a colored header band becomes invisible, and a scrollbar
appears inside the textbox.

**Cause**: a legacy `textbox` renders an **opaque white background** by default, hiding the band
underneath.

**Fix**: `vcObjects.background` `show: false` (transparent) and put the textbox above the band in
z-order. Keep title + subtitle in **one** textbox (two paragraphs) with generous height (~58px) —
two tightly-stacked textboxes each add their own scrollbar.

---

## 5. Visuals Clipped at the Page Edge

**Symptom**: the right-most or bottom visual is cut.

**Cause**: `x + width` exceeds the 1280 canvas width (or the equivalent height bound).

**Fix**: bounds check every visual before deploy. This is a pure arithmetic gate — there is no
excuse for finding it after a deployment.

---

## 6. Undersized Visuals Degrade Silently

| Visual | Minimum | Symptom below it |
|---|---|---|
| Slicer | width 180px | dropdown unusable |
| Table | header + 5 rows | table shows blank space |
| Chart | 300×200 | axis labels overlap |

These render "successfully" — nothing fails, the result is just unusable. Only a pre-deploy rule
catches them.

---

## 7. Validate Before Deploying, Not After

The whole point of this agent: a Fabric report deploy cycle is ~2 minutes, and rendering issues are
invisible in the API response (`200 OK` on a clipped report). Run:

```bash
python validate_report.py          # check only
python validate_report.py --fix    # auto-fix what's mechanically fixable
```

Related: report structure and visual rules live in
[`../report-builder-agent/`](../report-builder-agent/).

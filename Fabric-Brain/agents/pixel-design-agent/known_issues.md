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

---

## 8. `show: false` Is a Request, Not a Guarantee — the Renderer Ignored It

**Context**: Fabric / Power BI legacy report definition (`report.json`, `sections[].visualContainers[]`),
`visualType: "cardVisual"`, observed 2026-07-31.

**Symptom**: the bottom category label of every KPI card renders **and is clipped** on screen
("Sends per Customer", "Unsubscribe Rate", "Open Rate"…), even though the report JSON declares that
label hidden. Deploy returns success, the layout validator reports zero defects, and the defect is
visible only to a human looking at the rendered page.

**Root cause**: the card carried
`objects.categoryLabel = [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]`
and **Power BI drew the label anyway**. The card had been sized for the two texts that were
believed to render (title 11pt + callout 24pt = 103px in a 112px box), while three were actually
drawn (needing 128px). The validator was not wrong: it faithfully modelled what the definition
*declared*, and the engine did not honour the declaration.

**Fix**: never let a hide toggle be what makes a box fit. Size every visual for **all the texts it
declares**, and treat any space a working toggle frees as a bonus, never as budget. Concretely:
declare the label visible, and grow the card to the full stack.

```python
# sizing must ignore `show` entirely
need = card_height(title_pt, callout_pt, category_pt)   # 11, 24, 9 -> 128px
```

Growing a card is then a **grid** change, not a card change: 112 → 128 pushed the cards from
y=88..200 to y=88..216, so the content row below had to move (208 → 224) and shrink (242 → 226) to
keep its bottom edge. Budget for that before changing a card height.

Two guards, both mutation-tested (a guard that has never failed proves nothing):
- size the stack ignoring `show` → putting the card back to 112px must turn the suite red
- assert the label stays **declared** visible → satisfying a requirement by relying on a renderer
  bug is not satisfying it, and a future Power BI build may start honouring the toggle

**Evidence**:
- Live definition read back from Fabric (`POST /reports/{id}/getDefinition`, 202 → poll → result)
  before the fix: 20 `cardVisual`, `y: [88.0]`, `h: [112.0]`, `categoryLabel … "show": "false"`.
- Rendered page at that same version showed the label drawn and cut off (user screenshot).
- After the fix, live read-back: 20 cards `h: [128.0]`, `categoryLabel` `"show": "true"`, `9D`;
  rows at `(224.0, 226.0)` and `(462.0, 246.0)`; DAX replay of all visual queries 35/35 clean;
  test gate 111 green. Clipping confirmed gone on screen by the user.

**Generalisation**: this applies to any property whose effect you cannot read back from the render —
`show`, `wordWrap`, `labelDisplayUnits`, auto-fit behaviours. A validator models what is
**rendered**, not what is **declared**. Where the two can diverge, size for the worst case.


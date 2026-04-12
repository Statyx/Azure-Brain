# Diagram Patterns & CSS Reference

Proven patterns for Fabric architecture diagrams. All examples are from production diagrams.

---

## Pattern 1: Horizontal Platform Diagram

The default layout for any Fabric project. Three columns:

```
┌──────────┐   ┌─────────────────────────────────────────────────────┐   ┌──────────┐
│ Sources  │ → │              Microsoft Fabric                       │ → │  Users   │
│ (compact)│   │  [Store&Transform] → [Serve] → [Consume]           │   │ (compact)│
└──────────┘   └─────────────────────────────────────────────────────┘   └──────────┘
```

**CSS structure:**
```css
.h-flow { display: flex; align-items: stretch; gap: 12px; }  /* outer row */
.src-col { min-width: 140px; max-width: 160px; }             /* left */
.zone.fabric { flex: 1; }                                     /* center */
.user-col { min-width: 150px; max-width: 170px; }            /* right */
```

**Step arrows between zones:**
```html
<div class="h-arrow-group">
  <div class="step">1</div>          <!-- green numbered circle -->
  <div class="h-arrow">&rarr;</div>  <!-- arrow character -->
  <div class="h-arrow-label">DFS API<br>OneLake</div>
</div>
```

---

## Pattern 2: Separate Transform and Store Zones

Pipeline and Notebook belong in their own "Ingest & Transform" zone, separate from the Lakehouse "Store" zone. Connected by a step arrow.

```
┌─ Ingest & Transform ─┐       ┌──── Store ────┐
│  Pipeline             │  →②→  │  Lakehouse    │
│    ↓ triggers         │ writes│               │
│  Notebook             │ Delta │               │
└───────────────────────┘       └───────────────┘
```

```html
<!-- INGEST & TRANSFORM zone (purple) -->
<div class="inner-zone transform" style="flex:1;">
  <div class="iz-label">Ingest &amp; Transform</div>
  <div style="display:flex; flex-direction:column; gap:8px; margin-top:4px;">
    <div class="comp"><!-- Pipeline --></div>
    <div style="text-align:center; font-size:9px; color:#7c3aed;">&darr; triggers</div>
    <div class="comp"><!-- Notebook --></div>
  </div>
  <div style="margin-top:6px; display:flex; gap:6px;">
    <div class="workload-badge" style="background:#faf5ff; color:#7c3aed; border:1px solid #c4b5fd;">
      Data Factory
    </div>
    <div class="workload-badge" style="background:#f0fdf4; color:#16a34a; border:1px solid #86efac;">
      Data Engineering
    </div>
  </div>
</div>

<!-- ARROW: Transform → Store -->
<div class="h-arrow-group" style="justify-content:center;">
  <div class="step">2</div>
  <div class="h-arrow">&rarr;</div>
  <div class="h-arrow-label">writes<br>Delta tables</div>
</div>

<!-- STORE zone (green) -->
<div class="inner-zone storage" style="flex:1;">
  <div class="iz-label">Store</div>
  <div style="display:flex; flex-direction:column; gap:8px; margin-top:4px;">
    <div class="comp"><!-- Lakehouse --></div>
  </div>
</div>
```

**Key rule**: Do NOT merge Pipeline/Notebook into the Lakehouse zone as an overlay. Keep them as distinct zones with a labeled arrow between them.

---

## Pattern 3: Per-Component Badge

Each component gets its own workload badge directly below it:

```html
<div style="display:flex; flex-direction:column; gap:4px;">
  <div class="comp">
    <!-- icon + name + desc -->
  </div>
  <div class="workload-badge" style="background:#fef2f2; color:#dc2626;
       border:1px solid #fca5a5; align-self:flex-start; margin-left:4px;">
    Power BI
  </div>
</div>
```

---

## Pattern 4: Business Users Column

Right-side column listing personas with what they consume:

```html
<div class="user-col">
  <h3>Business Users</h3>
  <div class="user">
    <img src="{user_icon}" style="width:24px;height:24px;">
    <div>
      <div class="name">Cost Controllers</div>
      <div class="desc">Power BI Report</div>
    </div>
  </div>
  <!-- more users... -->
</div>
```

---

## Pattern 5: Summary Counts (preferred over pills/chips)

**IMPORTANT**: Do NOT list individual table names or measure names in architecture diagrams. Use summary counts instead — the detail belongs in documentation, not in the visual.

**Good** (clean, professional):
```
Lakehouse: "10 Delta tables · ~8 000 rows · 7 dims + 3 facts"
Semantic Model: "55 DAX measures · 11 relationships · star schema"
```

**Avoid** (clutters the diagram):
```
[dim_wbs] [dim_countries] [fact_benchmarks] ...
[Confidence Score] [Anomaly Rate] [Total Cost EUR] ...
```

If needed for documentation purposes, measure pills and table chips can still be used:

### Measure Pills (documentation only)

```html
<div class="pills">
  <span class="pill">[Confidence Score]</span>
  <span class="pill">[Anomaly Count]</span>
  <span class="pill">[Total Cost EUR]</span>
</div>
```

```css
.pills { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
.pill { font-size: 7.5px; padding: 1px 5px; background: #fce7f3;
        color: #9d174d; border-radius: 3px;
        font-family: 'Cascadia Code', Consolas, monospace; }
```

---

### Table Chips (documentation only)

```html
<div class="chips">
  <span class="chip dim">dim_countries</span>
  <span class="chip fact">fact_benchmarks</span>
</div>
```

```css
.chip.dim { background: #dbeafe; color: #1e40af; }
.chip.fact { background: #fef3c7; color: #92400e; }
```

---

## CSS Foundation

### Full base style block (copy as starting point):

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', 'Segoe UI', sans-serif; background: #fff; padding: 40px 24px; }
.canvas { max-width: 1600px; margin: 0 auto; }
```

### Inner zone classes:
- `.storage` — green (`#4ade80` border, `#f0fdf4` bg)
- `.transform` — purple (`#a78bfa` border, `#faf5ff` bg)
- `.model` — red (`#f87171` border, `#fef2f2` bg)
- `.consume` — cyan (`#22d3ee` border, `#ecfeff` bg)

### Component card:
```css
.comp { display: flex; align-items: center; gap: 8px; padding: 8px 12px;
        background: #fff; border: 1.5px solid #e5e7eb; border-radius: 10px; }
.comp img { width: 40px; height: 40px; object-fit: contain; }
.comp .name { font-size: 11px; font-weight: 600; color: #1e293b; }
.comp .desc { font-size: 9px; color: #64748b; }
```

---

## Rebuild Script Pattern

```python
import re

# 1. Read current HTML to extract base64 icons
with open("architecture_diagram.html", "r", encoding="utf-8") as f:
    html = f.read()

# 2. Extract icons by alt tag
icons = {}
for m in re.finditer(r'alt="([^"]+)"[^>]*src="(data:image/svg\+xml;base64,[^"]+)"', html):
    icons[m.group(1)] = m.group(2)

# 3. Helper function
def icon(alt, style=""):
    s = f' style="{style}"' if style else ""
    return f'<img src="{icons[alt]}" alt="{alt}"{s}>'

# 4. Build HTML via f-string
new_html = f'''<!DOCTYPE html>
<html>...{icon("Fabric", "height:50px;")}...</html>'''

# 5. Write output
with open("architecture_diagram.html", "w", encoding="utf-8") as f:
    f.write(new_html)
```

---

## Typography Scale

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Title (h1) | 24px | 700 | `#0f172a` |
| Subtitle | 13px | 400 | `#64748b` |
| Zone title | 18px | 700 | `#0d9488` |
| Zone subtitle | 11px | 400 | `#64748b` |
| Component name | 11px | 600 | `#1e293b` |
| Component desc | 9px | 400 | `#64748b` |
| Zone label | 9px | 700 | (zone color) |
| Arrow label | 8.5px | 400 | `#64748b` italic |
| Chip text | 8px | 500 | (chip color) |
| Pill text | 7.5px | 400 | `#9d174d` mono |
| Credit | 8px | 400 | `#94a3b8` |

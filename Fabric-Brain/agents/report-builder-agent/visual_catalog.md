# Visual Catalog — Selection Guide

> How to pick the right visual type. The **authoritative list** of types, formatting objects, and properties lives in [`cli_knowledge/`](cli_knowledge/) — do not duplicate it here. This file is the human-facing decision guide.

---

## 1. Selection by Encoding (Hierarchy)

Cleveland & McGill's effectiveness ranking, adapted for Power BI:

| Encoding | Most effective visuals | When to use |
|---|---|---|
| **Position on common scale** | `lineChart`, `clusteredColumnChart`, `clusteredBarChart`, `scatterChart` | Comparisons, trends, distributions |
| **Position on non-aligned scale** | `lineChart` faceted, `multiRowCard` | Small-multiples |
| **Length** | `clusteredBarChart`, `funnel`, `waterfallChart` | Ranking, decomposition, conversion |
| **Angle / Area** | `donutChart`, `pieChart`, `treemap` | Part-of-whole (≤ 6 slices) |
| **Slope** | `lineChart` (2-point comparison), `ribbonChart` | Period-over-period delta |
| **Color hue (categorical)** | any chart with `Series` role | Categorical breakdown |
| **Color intensity** | `heatMap`, `filledMap`, `azureMap` | Density, magnitude on geography |
| **Numerical singleton** | `cardVisual`, `kpi`, `multiRowCard`, `gauge` | Top-line KPI |
| **Tabular drill** | `tableEx`, `matrix`, `pivotTable` | Detail rows, financial statements |

Prefer **position/length** over **angle/area** when accuracy matters.  
Use **pie/donut only when telling a "majority share" story** with ≤ 6 categories.

---

## 2. Selection by Dashboard Archetype

Pair the archetype (defined in [`dashboard_design_guide.md`](dashboard_design_guide.md)) with the right mix of visuals.

### Executive Summary
> *"Show me the headline. I have 5 seconds."*

| Slot | Visual type |
|---|---|
| 4-6 KPIs across the top | `cardVisual` (modern card with callout area) |
| Trend ribbon | `lineChart` with `Y` only, no axis labels |
| Regional split | `clusteredBarChart` (vertical legend hidden) |
| Optional narrative | `aiNarratives` (auto-summary) |
| Optional benchmark | `gauge` against target |

### Operational Monitor
> *"What's happening now? Is anything broken?"*

| Slot | Visual type |
|---|---|
| Status tiles (red/amber/green) | `cardVisual` with conditional fill |
| Real-time trend | `realTimeLineChart` (Direct Lake / RTI hot path) |
| Heat by zone/site | `heatMap` or `azureMap` |
| Top-N alert table | `tableEx` filtered to anomalies |
| Page filter | `slicer` (date range, site) |

### Analytical Canvas
> *"Let me explore. Give me drill paths and what-ifs."*

| Slot | Visual type |
|---|---|
| Driver discovery | `keyDriversVisual` |
| Hierarchical decomposition | `decompositionTreeVisual` |
| Multi-dim scatter | `scatterChart` (size + color + drill) |
| Pivot table | `pivotTable` or `matrix` with subtotals |
| Slicer panel | `advancedSlicerVisual`, `listSlicer`, `textSlicer` |

### Narrative Story
> *"Walk me through the insight, page by page."*

| Slot | Visual type |
|---|---|
| Section headers | `textbox` with rich styling |
| Single hero visual per page | `lineChart` / `barChart` / `waterfallChart` (full-width) |
| Inline annotations | `textbox` over the visual |
| Page navigation | `pageNavigator`, `bookmarkNavigator` |

### Comparative Benchmark
> *"How does X compare to Y across N dimensions?"*

| Slot | Visual type |
|---|---|
| Side-by-side KPIs | `cardVisual` × N (with `Rows` role for small-multiples) |
| Difference chart | `waterfallChart` (variance), `ribbonChart` (rank change) |
| 100% stacked comparison | `hundredPercentStackedBarChart` / `…ColumnChart` |
| Combo for absolute + relative | `lineClusteredColumnComboChart` / `lineStackedColumnComboChart` |

---

## 3. Visual Type Index (All 57)

Categorized list. For each type, look up roles + formatting in [`cli_knowledge/visuals/<type>/`](cli_knowledge/visuals/).

| Category | Types |
|---|---|
| **Cards** | `card` *(deprecated, use `cardVisual`)*, `cardVisual`, `multiRowCard`, `animatedNumber`, `kpi` |
| **Bar / Column** | `barChart`, `clusteredBarChart`, `hundredPercentStackedBarChart`, `columnChart`, `clusteredColumnChart`, `hundredPercentStackedColumnChart` |
| **Line / Area** | `lineChart`, `areaChart`, `stackedAreaChart`, `hundredPercentStackedAreaChart`, `realTimeLineChart` |
| **Combo** | `lineClusteredColumnComboChart`, `lineStackedColumnComboChart`, `ribbonChart` |
| **Pie / Donut** | `pieChart`, `donutChart`, `treemap` |
| **Funnel / Waterfall** | `funnel`, `waterfallChart` |
| **Distribution / Scatter** | `scatterChart`, `heatMap` |
| **Tables** | `table` *(legacy)*, `tableEx`, `matrix`, `pivotTable` |
| **Maps** | `map` *(deprecated)*, `filledMap` *(deprecated)*, `azureMap`, `shapeMap` |
| **Gauges** | `gauge` |
| **AI / Smart** | `aiNarratives`, `keyDriversVisual`, `decompositionTreeVisual`, `qnaVisual` *(not PBIR-authorable)*, `scorecard` |
| **Slicers** | `slicer`, `listSlicer`, `textSlicer`, `filterSlicer`, `advancedSlicerVisual` |
| **Navigation** | `actionButton`, `bookmarkNavigator`, `pageNavigator` |
| **Static / Decoration** | `textbox`, `image`, `shape`, `basicShape` |
| **Code-embedded** | `pythonVisual`, `scriptVisual` *(R)*, `rdlVisual` |
| **Data utility** | `accessibleTable`, `dataQueryVisual` |

### Deprecated (avoid for new reports)

| Type | Replacement |
|---|---|
| `card` | `cardVisual` |
| `map` | `azureMap` |
| `filledMap` | `azureMap` |
| `qnaVisual` | *not authorable via PBIR* |

Source list with rationale: [`cli_knowledge/visual_types.json`](cli_knowledge/visual_types.json) (see `deprecated[]`).

---

## 4. Workflow: Build a Visual from Scratch

```
1. Pick visualType (from a section above or the catalog).
2. Read cli_knowledge/visuals/<type>/catalog.json:
   - "roles"            → which projection buckets the visual has
   - "requiredRoles"    → minimum fields needed
   - "maxPerRole"       → field-count limits
   - "formattingObjects" → which "objects" the visual supports
3. Build visual.query.queryState.<role>.projections[]:
   - One projection per field (measure or column)
   - field.Measure for measures, field.Column for columns
   - queryRef = "entity.fieldName", nativeQueryRef = "fieldName"
4. For each "object" you want to customize:
   - Read cli_knowledge/visuals/<type>/objects/<obj>.json
   - Build visual.objects.<obj>[].properties.<prop> = <expr literal>
5. For container-level styling:
   - Pick VCOs from cli_knowledge/vcos/<vco>.json
   - Build visual.visualContainerObjects.<vco>[].properties.<prop> = <expr literal>
6. Set visual.position {x, y, z, width, height, tabOrder}.
7. Run powerbi-report-author validate <Report>.Report.
```

---

## 5. Common Visual Skeletons

### KPI Card (`cardVisual`)

```json
{
  "name": "card_revenue",
  "position": { "x": 20, "y": 80, "z": 0, "width": 200, "height": 120, "tabOrder": 0 },
  "visual": {
    "visualType": "cardVisual",
    "query": {
      "queryState": {
        "Data": {
          "projections": [
            { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "fact_general_ledger" }}, "Property": "Total Revenue" }}, "queryRef": "fact_general_ledger.Total Revenue", "nativeQueryRef": "Total Revenue" }
          ]
        }
      }
    },
    "objects": {
      "value": [{ "properties": { "fontSize": { "expr": { "Literal": { "Value": "27D" }}}, "fontColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#118DFF'" }}}}} }}]
    },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" }}}, "text": { "expr": { "Literal": { "Value": "'Total Revenue'" }}} }}],
      "dropShadow": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" }}} }}]
    }
  }
}
```

### Clustered Bar (`clusteredBarChart`)

```json
{
  "name": "bar_revenue_by_region",
  "position": { "x": 240, "y": 80, "z": 0, "width": 600, "height": 320, "tabOrder": 1 },
  "visual": {
    "visualType": "clusteredBarChart",
    "query": {
      "queryState": {
        "Category": {
          "projections": [
            { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_cost_centers" }}, "Property": "region" }}, "queryRef": "dim_cost_centers.region", "nativeQueryRef": "region" }
          ]
        },
        "Y": {
          "projections": [
            { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "fact_general_ledger" }}, "Property": "Total Revenue" }}, "queryRef": "fact_general_ledger.Total Revenue", "nativeQueryRef": "Total Revenue" }
          ]
        }
      }
    },
    "objects": {
      "legend": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" }}} }}],
      "dataPoint": [{ "properties": { "fill": { "solid": { "color": { "expr": { "ThemeDataColor": { "ColorId": 1, "Percent": 0 }}}}} }}]
    },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" }}}, "text": { "expr": { "Literal": { "Value": "'Revenue by Region'" }}} }}]
    }
  }
}
```

### Line Chart (`lineChart`)

Replace `clusteredBarChart` above with `lineChart`. Roles stay `Category` + `Y`.

### Matrix (`matrix`)

```json
"query": {
  "queryState": {
    "Rows":    { "projections": [ /* dim rows */ ] },
    "Columns": { "projections": [ /* dim cols */ ] },
    "Values":  { "projections": [ /* measures */ ] }
  }
}
```

### Slicer (`slicer`)

```json
"query": {
  "queryState": {
    "Values": {
      "projections": [
        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" }}, "Property": "year" }}, "queryRef": "dim_date.year", "nativeQueryRef": "year" }
      ]
    }
  }
}
```

---

## 6. When the cli_knowledge says one thing and your gut says another

**The cli_knowledge wins.** Properties not in `cli_knowledge/visuals/<type>/objects/<obj>.json` do not exist in the schema. Hallucinated property names are silently dropped by Fabric and produce blank visuals.

If a property you need is genuinely missing from the dump:
1. Re-run [`cli_knowledge/dump_cli_knowledge.ps1`](cli_knowledge/dump_cli_knowledge.ps1) — the CLI may have shipped new properties.
2. If still missing, the property is not available in PBIR authoring scope. Use a different approach (a different visual type, or override via theme `visualStyles`).

---

## 7. Cross-References

- Mandatory rules → [`instructions.md`](instructions.md)
- PBIR folder + payload → [`report_structure.md`](report_structure.md)
- Container styling + VCO list → [`themes_styling.md`](themes_styling.md)
- Page grid + archetype layouts → [`pages_layout.md`](pages_layout.md)
- Tones + typography + archetypes → [`dashboard_design_guide.md`](dashboard_design_guide.md)
- Property lookups → [`cli_knowledge/`](cli_knowledge/)
- Known visual issues → [`known_issues.md`](known_issues.md)

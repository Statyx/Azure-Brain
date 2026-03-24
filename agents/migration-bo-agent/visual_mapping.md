# BO → Power BI Visual Type Mapping

Complete mapping of every BO visual/component to its Power BI equivalent.

> **Inspired by**: [cyphou/Tableau-To-PowerBI](https://github.com/cyphou/Tableau-To-PowerBI) (118+ visual types), [cyphou/MicroStrategyToPowerBI](https://github.com/cyphou/MicroStrategyToPowerBI) (30+ types), [cyphou/Qlik-To-PowerBI](https://github.com/cyphou/Qlik-To-PowerBI) (60+ types).

---

## Webi Visual → Power BI Visual

| # | Webi Visual | Power BI Visual | Fidelity | Notes |
|---|------------|----------------|----------|-------|
| 1 | Simple Table | Table | ✅ High | Direct mapping — same concept |
| 2 | Cross-Tab | Matrix | ⚠️ Medium | Row/column headers map well; subtotals may differ; test thoroughly |
| 3 | Vertical Bar Chart | Clustered Bar Chart | ✅ High | |
| 4 | Horizontal Bar Chart | Clustered Bar Chart (rotated) | ✅ High | |
| 5 | Stacked Bar Chart | Stacked Bar Chart | ✅ High | |
| 6 | 100% Stacked Bar | 100% Stacked Bar | ✅ High | |
| 7 | Line Chart | Line Chart | ✅ High | |
| 8 | Area Chart | Area Chart | ✅ High | |
| 9 | Pie Chart | Pie Chart | ✅ High | |
| 10 | Donut Chart | Donut Chart | ✅ High | |
| 11 | Radar Chart | No built-in visual | 🔧 Low | Use AppSource custom visual (Radar Chart by MAQ) |
| 12 | Scatter Plot | Scatter Chart | ✅ High | |
| 13 | Bubble Chart | Scatter + Size encoding | ✅ High | |
| 14 | Waterfall Chart | Waterfall Chart | ✅ High | |
| 15 | Box Plot | No built-in visual | ⚠️ Medium | Use AppSource custom visual (Box & Whisker) |
| 16 | TreeMap | Treemap | ✅ High | |
| 17 | Tag Cloud / Word Cloud | No built-in | ⚠️ Medium | Use AppSource Word Cloud visual |
| 18 | Geo Map | Azure Maps visual | ✅ High | |
| 19 | Free-form Cell (text) | Text Box / Card | ✅ High | |
| 20 | Formula Cell (single value) | Card / KPI | ✅ High | |
| 21 | Gauge | Gauge | ✅ High | |
| 22 | Funnel | Funnel Chart | ✅ High | |
| 23 | 3D Charts | No 3D support | ⚠️ Medium | Flatten to 2D equivalent |
| 24 | Combined Bar + Line | Combo Chart (Line and Clustered Column) | ✅ High | |

## Webi Report Structure → Power BI Structure

| # | Webi Element | Power BI Equivalent | Fidelity | Notes |
|---|-------------|-------------------|----------|-------|
| 1 | Report Tab | Report Page | ✅ High | Direct mapping |
| 2 | Section (group break) | Drill-through page / Bookmarks / Visual grouping | ⚠️ Medium | No exact equivalent — redesign for PBI paradigm |
| 3 | Sub-report | Drill-through page | ⚠️ Medium | Different navigation pattern |
| 4 | Input Control (dropdown) | Slicer (Dropdown mode) | ✅ High | |
| 5 | Input Control (checkbox) | Slicer (List mode) | ✅ High | |
| 6 | Input Control (slider) | Slicer (Between mode) / What-If Parameter | ✅ High | |
| 7 | Input Control (text entry) | Power Apps visual / What-If Parameter | ⚠️ Medium | No native text entry slicer |
| 8 | Alerter (row coloring) | Conditional Formatting (Background color rules) | ✅ High | |
| 9 | Alerter (icon) | Conditional Formatting (Icons) | ✅ High | Icon sets differ — map manually |
| 10 | Data Tracking (change detection) | Power Automate + snapshot | 🔧 Low | No built-in data change tracking in PBI |
| 11 | Drill hierarchy | Drill-down in visual hierarchy | ✅ High | |
| 12 | Hyperlink cell | Hyperlink Button / URL column | ✅ High | |
| 13 | Report Header / Footer | N/A for interactive reports | ⚠️ Medium | For paginated reports: use Report Builder headers |
| 14 | Free-form positioning | Canvas Layout (drag and drop) | ✅ High | PBI uses pixel-based canvas |
| 15 | Grouped sections with breaks | Bookmark groups / Drill-through pages | ⚠️ Medium | Paradigm difference — BO sections ≠ PBI pages |

## Crystal Report → Paginated Report

| # | Crystal Element | Paginated Report (RDL) Equivalent | Fidelity | Notes |
|---|----------------|----------------------------------|----------|-------|
| 1 | Detail section | Table / Tablix detail row | ✅ High | |
| 2 | Group Header | Group header in Tablix | ✅ High | |
| 3 | Group Footer (subtotals) | Group footer in Tablix | ✅ High | |
| 4 | Report Header/Footer | Report header/footer regions | ✅ High | |
| 5 | Page Header/Footer | Page header/footer regions | ✅ High | |
| 6 | Subreport | Subreport | ⚠️ Medium | Must use same data source; cross-source subreports need redesign |
| 7 | Cross-Tab | Matrix (Tablix) | ✅ High | |
| 8 | Parameter (discrete) | RDL Parameter (dropdown) | ✅ High | |
| 9 | Parameter (range) | RDL Parameter (date range) | ✅ High | |
| 10 | Parameter (cascading) | Cascading parameters | ⚠️ Medium | Evaluated sequentially — pre-aggregate for performance |
| 11 | Formula (running total) | RDL Expression `=RunningValue()` | ✅ High | |
| 12 | Formula (`WhilePrintingRecords`) | No equivalent | 🔧 Low | Must restructure — move logic to dataset query |
| 13 | Formula (conditional suppression) | Visibility rules with expression | ✅ High | |
| 14 | Barcode field | Barcode font | ⚠️ Medium | Verify font availability in PBI Service |
| 15 | Image from URL / DB | Image from URL / embedded | ✅ High | |
| 16 | Chart (Crystal chart) | Chart sub-items in RDL | ✅ High | |
| 17 | Repository references (shared text) | No shared content | 🔧 Low | Must embed directly |
| 18 | Custom DLL code | Not supported in PBI Service | ❌ None | Rewrite in data layer or M query |
| 19 | Document map (TOC) | Document Map → doesn't render in Service | ⚠️ Medium | Works in PDF export only |
| 20 | Print-perfect layout | Exact page control | ✅ High | Paginated reports excel at this |

## Xcelsius / Design Studio → Power BI Dashboard

| # | Xcelsius Element | Power BI Equivalent | Fidelity | Notes |
|---|-----------------|-------------------|----------|-------|
| 1 | Gauge component | Gauge visual | ✅ High | |
| 2 | Selector (list/combo) | Slicer | ✅ High | |
| 3 | Chart (bar/line/pie) | Chart visuals | ✅ High | |
| 4 | Spreadsheet grid | Table visual | ✅ High | |
| 5 | What-If slider | What-If Parameter + Slicer | ✅ High | |
| 6 | Alert icons | KPI visual + Conditional formatting | ✅ High | |
| 7 | Map component | Azure Maps visual | ✅ High | |
| 8 | Flash-based interactivity | Power BI native interactivity | ✅ High | PBI cross-filtering > Flash |
| 9 | URL connection to BO | Direct Semantic Model connection | ✅ High | |

## BO Special Components

| # | BO Component | Fabric Equivalent | Fidelity | Notes |
|---|-------------|-------------------|----------|-------|
| 1 | BI Launchpad folder | Power BI App section | ✅ High | Apps organize content by audience |
| 2 | BI Launchpad favorite | Favorites / Metrics | ✅ High | |
| 3 | OpenDocument URL | Power BI embed URL / App URL | ✅ High | |
| 4 | Publication (burst) | Paginated data-driven subscription | ⚠️ Medium | Simpler than BO publications |
| 5 | CMC Schedule | Fabric Pipeline / Refresh schedule | ✅ High | |
| 6 | Live Office (Excel embed) | Excel connected to Semantic Model | ✅ High | Analyze in Excel |
| 7 | BO SDK custom app | Power BI Embedded / REST API | ✅ High | Different API — rewrite needed |
| 8 | Analysis for OLAP | Excel Pivot connected to Semantic Model | ⚠️ Medium | Or PBI Analyze in Excel |
| 9 | BO Explorer | Power BI Q&A feature | ⚠️ Medium | Natural language query |
| 10 | BO Discussion thread | Teams channel / Comments on report | ✅ High | |

---

## Summary

| Source | Objects | ✅ High | ⚠️ Medium | 🔧 Low | ❌ None |
|--------|---------|---------|-----------|--------|---------|
| Webi Visuals | 24 | 19 | 4 | 1 | 0 |
| Webi Structure | 15 | 9 | 5 | 1 | 0 |
| Crystal → Paginated | 20 | 13 | 4 | 2 | 1 |
| Xcelsius → PBI | 9 | 9 | 0 | 0 | 0 |
| BO Special | 10 | 7 | 3 | 0 | 0 |
| **TOTAL** | **78** | **57 (73%)** | **16 (21%)** | **4 (5%)** | **1 (1%)** |

> 94% of BO visual elements have a High or Medium fidelity mapping to Power BI.

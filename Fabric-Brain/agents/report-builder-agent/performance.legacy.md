# Report Performance Optimization

## Purpose

Patterns for building high-performance Power BI reports in Fabric.
Essential when reports have 10+ visuals, complex DAX, or large datasets.

---

## Visual Count Guidelines

| Visual Count | Performance | Recommended Actions |
|-------------|------------|-------------------|
| 1–5 | Excellent | No optimization needed |
| 6–10 | Good | Standard best practices |
| 11–20 | Fair | Apply query reduction, visual-level filters |
| 21–50 | Slow | Must optimize: hidden pages, drill-through, bookmarks |
| 50+ | **Critical** | Redesign: split into multiple reports or use paginated reports |

> **Rule of thumb**: Each visible visual generates 1–3 DAX queries. A page with 20 visuals sends 20–60 queries on every slicer interaction.

---

## Query Reduction Techniques

### 1. Reduce Queries Per Visual

```json
// In report.json > config
{
    "queryReduction": {
        "type": "Manual"  // Adds an "Apply" button to slicers
    }
}
```

**Manual mode**: Users click "Apply" to execute all slicer changes at once, instead of one query per slicer change.

### 2. Visual-Level Filters Instead of Page-Level

Visual-level filters are more efficient than page-level filters for partial-page updates.

```json
// Visual-level filter (faster for single visual)
"filters": "[{\"name\":\"Filter1\",\"expression\":{\"Column\":{\"Expression\":{\"SourceRef\":{\"Entity\":\"dim_dates\"}},\"Property\":\"Year\"}},\"type\":\"Categorical\",\"values\":[2025]}]"
```

### 3. Hidden Visuals on Demand

Use bookmarks to show/hide visual groups instead of displaying everything:

```json
// Bookmark that shows detailed view
{
    "name": "DetailView",
    "displayName": "Show Details",
    "explorationState": {
        "version": "1.2",
        "activeSection": "SectionId",
        "filters": {}
    }
}
```

---

## DAX Measure Optimization

### Slow Patterns to Avoid

| Pattern | Why It's Slow | Better Alternative |
|---------|--------------|-------------------|
| `CALCULATE(SUM(fact[amount]), ALL(fact))` on every visual | Scans entire table | Pre-compute in model |
| `SUMX(fact, fact[qty] * RELATED(dim[price]))` | Row-by-row calculation | Add calculated column in Lakehouse |
| Multiple `SWITCH(TRUE(), ...)` in one measure | Complex branching | Split into separate measures |
| `COUNTROWS(FILTER(big_table, ...))` | Full table scan | Use `CALCULATE + COUNTROWS` with filter context |
| Nested `CALCULATE` with contradicting filters | Filter confusion | Flatten to single `CALCULATE` |

### Fast Patterns

```dax
// ✅ Good: Simple aggregation leveraging Direct Lake
Total Revenue = SUM(fact_sales[revenue])

// ✅ Good: Time intelligence with pre-built date table
Revenue YTD = TOTALYTD([Total Revenue], dim_dates[Date])

// ✅ Good: Ratio without full-table scan
Revenue Share = 
    DIVIDE(
        [Total Revenue],
        CALCULATE([Total Revenue], REMOVEFILTERS(dim_products)),
        0
    )

// ✅ Good: Conditional with variables (calculate once)
Revenue vs Target = 
    VAR _actual = [Total Revenue]
    VAR _target = [Budget Amount]
    RETURN
        DIVIDE(_actual - _target, _target, 0)
```

### Measure Performance Testing

```dax
// Test measure execution time (run in DAX Studio or via API)
DEFINE
    MEASURE fact_sales[_TestMeasure] = [Your Complex Measure]
EVALUATE
    SUMMARIZECOLUMNS(
        dim_dates[Year],
        dim_products[Category],
        "_Result", [_TestMeasure]
    )
```

> **Target**: Any single measure should evaluate in <2 seconds for typical filter context.

---

## Direct Lake Optimization

### What Makes Direct Lake Fast

1. **V-ORDER**: Fabric-specific columnar encoding. Apply after data load:
   ```sql
   OPTIMIZE fact_sales VORDER;
   ```

2. **Minimal columns**: Direct Lake reads only requested columns. Fewer columns in visual = faster.

3. **Partitioning**: For very large tables, partition by date:
   ```python
   df.write.format("delta").partitionBy("year").save("Tables/fact_sales")
   ```

### When Direct Lake Falls Back to DirectQuery

Direct Lake silently falls back to DirectQuery (slower) when:

| Trigger | Symptom | Fix |
|---------|---------|-----|
| Too many rows for capacity SKU | Slow queries | Scale up SKU or reduce data |
| Unsupported DAX pattern | Performance spike | Simplify DAX |
| Stale delta log | Intermittent slowness | `OPTIMIZE` the table |
| Memory pressure | Eviction from cache | Reduce concurrent workloads |

**F2**: Max ~300M rows per table
**F8**: Max ~1.5B rows per table
**F64**: Max ~12B rows per table

---

## Report Layout Optimization

### Page Load Waterfall

```
1. Report metadata loaded (fast)
2. Semantic model connection established (1-3s first time)
3. Visual queries sent (parallel, 1-3 per visual)
4. Data returned and rendered (depends on data volume)
```

### Strategies

1. **Put KPI cards first**: They return fast (single-row aggregation), giving users something to see immediately.

2. **Lazy-load detail tables**: Put detailed tables on drill-through pages, not the overview page.

3. **Limit table rows**: Default visual row limit to 500 or less:
   ```json
   // In visual config
   "rowCount": 500
   ```

4. **Use images sparingly**: Don't load large images in visual backgrounds.

5. **Minimize cross-highlighting**: Disable cross-highlight on visuals that don't need it:
   ```json
   // In visual config
   "suppressDefaultInteraction": true
   ```

---

## Page Architecture Patterns

### Pattern 1: Overview → Detail → Export (3-Page)

```
Page 1: Executive Overview
  - 4-6 KPI cards (fast)
  - 1 trend chart
  - 1 bar chart (top N)
  - 2 slicers (date range, category)

Page 2: Detailed Analysis (drill-through)
  - Large table with pagination
  - Multiple slicers
  - Cross-filtered charts
  - Linked from Page 1 visuals

Page 3: Export / Paginated View
  - Formatted table for printing
  - No interactive slicers
  - Page-level filters passed from Page 2
```

### Pattern 2: Tabbed Dashboard (Bookmarks)

```
Single page with bookmarks for different views:
  - Bookmark "Revenue" → Shows revenue cards + chart
  - Bookmark "Costs" → Shows cost breakdown
  - Bookmark "Margins" → Shows margin analysis
  
Benefits: Single page load, instant tab switching
Drawback: Complex to build, all visuals loaded (even hidden ones)
```

---

## Benchmarking Checklist

After building a report, measure these metrics:

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Page load time | Browser DevTools → Network | < 3 seconds |
| Slicer interaction | Stopwatch from click to visual update | < 2 seconds |
| Visual query count | DAX Studio / Performance Analyzer | < 3 per visual |
| Total queries per page | Performance Analyzer in PBI Desktop | < 30 |
| Data volume per query | DAX Studio → Server Timings | < 1M rows scanned |

### Using Performance Analyzer

1. Open report in Power BI Desktop (or Fabric portal)
2. View → Performance Analyzer → Start Recording
3. Interact with report (change slicers, navigate pages)
4. Review query times per visual
5. Export results for comparison

> **Action threshold**: Any visual taking >5 seconds = must optimize its DAX or reduce its data scope.

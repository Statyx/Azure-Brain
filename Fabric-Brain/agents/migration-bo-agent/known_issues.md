# BO Migration — Known Issues & Limitations

## No Automated Migration Tool
- **There is no official Microsoft or SAP tool to auto-convert Webi → Power BI**
- Third-party tools (Mobilize.Net, etc.) offer partial automation for Crystal → Paginated Reports
- Universe metadata can be exported but must be manually rebuilt as Semantic Models

## BO Features with No Direct Fabric Equivalent

| BO Feature | Status in Fabric | Workaround |
|-----------|-----------------|------------|
| **Context operators (In, ForEach, ForAll)** | No DAX equivalent | Rewrite with `CALCULATE` + `ALL/ALLEXCEPT` — requires DAX expertise |
| **@Prompt cascading LOVs** | Slicers don't cascade natively | Use field parameters, or manage via relationships |
| **Tracking (data change detection)** | No built-in equivalent | Use Power Automate + snapshot comparison |
| **Webi Input Controls (entry fields)** | PBI slicers are selection-only | Use Power Apps visual or What-If parameters |
| **Publication bursting by profile** | Paginated subscriptions are simpler | Data-driven subscriptions cover most use cases |
| **Universe linked/derived tables** | No equivalent concept | Rebuild as Lakehouse views or Dataflow transformations |
| **BO Audit database** | Different audit format | Use Fabric Admin monitoring + Azure Log Analytics |
| **Xcelsius (Flash)** | Flash is EOL | Full rebuild in Power BI |
| **Analysis for OLAP** | No equivalent | Power BI with SSAS or Fabric Semantic Model |
| **BO categories (personal/corporate)** | Workspace model is different | Use workspace permissions + Power BI Apps |

## Common Migration Errors

### Data Mismatches
- **Rounding differences**: BO and DAX may handle float rounding differently → Use `ROUND()` explicitly
- **NULL handling**: BO treats NULLs differently from DAX `BLANK()` → Test edge cases
- **Date ranges**: BO "between" is inclusive; verify DAX filter behavior matches
- **Distinct counts**: BO `Count` vs DAX `DISTINCTCOUNT` — verify semantics match

### Performance Issues
- **Large datasets in Import mode**: BO can query on-demand; PBI Import loads everything → Use Direct Lake or DirectQuery if >100M rows
- **Complex DAX measures**: Translated BO formulas may produce slow DAX → Optimize iteratively
- **Gateway refresh timeouts**: On-prem data through gateway has refresh limits → Plan gateway sizing

### Security Gaps
- **BO dynamic row restriction using session variables** → Requires DAX RLS with `USERPRINCIPALNAME()` or security table approach
- **BO object-level security** (hide columns per group) → Use OLS (Object-Level Security) in Semantic Model or separate models
- **BO data-level security combined with row-level** → May need multiple RLS roles

## Crystal Reports Specific Issues
- Subreports with different data sources → Must consolidate or use drill-through
- Crystal formulas using `WhilePrintingRecords` → No paginated equivalent, must restructure
- Barcode fonts → Verify font availability in Fabric service
- Print-perfect layouts → Paginated Reports handle this well, but test pixel-level alignment

## DAX Conversion Limitations

> Source: Cross-platform patterns from migration tooling for Tableau, MicroStrategy, and Qlik to Power BI. See [bo_to_dax_reference.md](bo_to_dax_reference.md) for full mapping.

| BO Feature | Conversion Status | Detail |
|-----------|------------------|--------|
| **Context operators (In, ForEach, ForAll)** | 🔧 Manual rewrite | Hardest BO-specific feature. Requires deep `CALCULATE` + `ALL`/`ALLEXCEPT` patterns. No 1:1 DAX equivalent. |
| **Running functions (RunningSum, RunningAvg)** | ⚠️ Approximate | `CALCULATE` + `FILTER(ALL(...))` pattern works but can be slow on large datasets |
| **Previous() function** | ⚠️ Approximate | Use `DATEADD`/`PARALLELPERIOD` for time-based, `OFFSET` (DAX 2023+) for row-based |
| **@Prompt (cascading, multi-value)** | ⚠️ Redesign | Slicers don't cascade directly. Use relationship-based filtering or field parameters |
| **@Prompt (free-text entry)** | 🔧 Manual | No native text-entry slicer. Use Power Apps visual or What-If parameter |
| **@Variable (session/security)** | ⚠️ Redesign | Replace with `USERPRINCIPALNAME()` in RLS roles |
| **Document/metadata functions** | ⚠️ Limited | `DocumentName()`, `PageNumber()`, `RowIndex()` have no interactive report equivalent. Paginated reports support some via RDL expressions |
| **Spatial/map functions** | 🔧 Manual | No BO spatial → DAX conversion. Rebuild using Azure Maps visual in Power BI |
| **Regex in formulas** | ❌ Not supported | DAX has no regex support. Move regex logic to Power Query M or data layer |
| **Circular variable references** | ❌ Not supported | DAX does not allow circular dependencies. Restructure calculation logic |

### Cross-Platform Insight: Hardest Conversion Areas

Based on patterns observed in Tableau, MicroStrategy, and Qlik migrations, these areas consistently require the most manual effort:

1. **Fixed-grain / context override** (BO: `In`/`ForEach`/`ForAll`, Tableau: LOD `FIXED`, MSTR: Level Metrics `{~+}`, Qlik: Set Analysis) — All require deep `CALCULATE` expertise
2. **Row-level iteration** (BO: `Previous()`, `RunningSum()`, Tableau: `PREVIOUS_VALUE`, MSTR: OLAP functions) — DAX's columnar engine handles differently
3. **Dynamic parameter injection** (BO: `@Prompt`, Tableau: Parameters, MSTR: Prompts, Qlik: Variables) — Power BI parameter model is fundamentally different
4. **Pass-through SQL** (BO: derived tables with SQL, MSTR: `ApplySimple`, Qlik: Script SQL) — Must move to data layer or Power Query M

## Visual Mapping Limitations

> See [visual_mapping.md](visual_mapping.md) for the complete 78-element mapping.

| BO Visual | Issue | Workaround |
|-----------|-------|------------|
| **Radar Chart** | No built-in PBI visual | Use AppSource custom visual (Radar Chart by MAQ Software) |
| **3D Charts** | PBI has no 3D rendering | Flatten to 2D equivalent — users may notice difference |
| **Box Plot** | No built-in PBI visual | Use AppSource Box & Whisker visual |
| **Webi Sections with breaks** | No direct PBI concept | Redesign as drill-through pages, bookmarks, or visual-level filters |
| **Crystal Document Map (TOC)** | Doesn't render in PBI Service | Works in PDF export only — inform users |
| **Custom DLL in Crystal** | Not supported in PBI Service | Rewrite logic in data layer or M query |
| **Nested cross-tab with alerters** | Matrix + conditional formatting | Complex to rebuild — prototype early, test thoroughly |

## Paginated Reports (RDL) Limitations in Power BI Service

> Source: [MS Learn — Paginated Reports](https://learn.microsoft.com/en-us/power-bi/paginated-reports/paginated-reports-report-builder-power-bi) and [SSRS Migration](https://learn.microsoft.com/en-us/power-bi/guidance/migrate-ssrs-reports-to-power-bi)

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| **Custom code DLL references** not supported | Crystal reports with external DLLs cannot be converted as-is | Rewrite logic inline or move to data layer |
| **Shared data sources / datasets** not supported | Must use embedded data sources | RDL Migration Tool auto-converts these |
| **Document maps** don't render in Service | Table of contents for long reports invisible online | Works in PDF export — inform users |
| **UserID returns UPN** not NT account | Security logic using `DOMAIN\user` format breaks | Change to `user@company.com` format |
| **ExecutionTime returns UTC** | Report footers showing local time are wrong | Add UTC offset or clarify timezone in footer |
| **Map visualizations with spatial data** not supported through gateway | Reports with SQL Server map visuals fail | Rebuild in Power BI report (not paginated) or remove maps |
| **Data-driven subscriptions** for paginated not identical to BO Publications | Bursting by profile/parameter differences | Use Power Automate for complex distribution |
| **Memory limits** vary by license type | Large/complex paginated reports may hit memory cap | Optimize dataset, reduce complexity, or upgrade capacity |
| Pinning paginated visuals to dashboards | Not supported in Power BI Service | Use Power BI report visuals instead |
| **Non-Latin font rendering** in PDF | Characters may not render correctly | Verify font embedding, test PDF output |

## Migration Estimation Pitfalls

> Source: [MS Learn — Customer case studies](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-learn-from-customers)

| Issue | Detail |
|-------|--------|
| **Complexity overestimation** | Customer estimated 50 days for a batch — actual was 50 hours. POC reveals true effort. |
| **~50% of reports can be retired** | Many BO reports are unused, duplicate, or outdated. Audit before migrating. |
| **Change resistance varies** | Some users embrace change, others resist strongly. Plan change management per group. |
| **Power BI ≠ BO paradigm** | Don't try to replicate BO exactly — redesign for PBI strengths (interactive, star schema, DAX). |
| **Dashboard vs Report confusion** | PBI Dashboard = pinned tiles from multiple reports. PBI Report = interactive pages. Most BO Webi → PBI Report, not Dashboard. |

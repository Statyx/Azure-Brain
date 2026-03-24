# BO → Power BI Post-Migration Checklist

Systematic validation checklist to verify migration quality. Inspired by [cyphou/Tableau-To-PowerBI](https://github.com/cyphou/Tableau-To-PowerBI) 11-section post-migration checklist.

---

## Section 1: Open & Load

- [ ] Report opens without error in Power BI Desktop
- [ ] Report opens without error in Power BI Service
- [ ] Load time is acceptable (< 30s for interactive, < 2min for paginated)
- [ ] No "visual has exceeded available resources" warnings
- [ ] All pages/tabs render correctly
- [ ] Mobile layout renders (if applicable)

## Section 2: Data Source Connections

- [ ] All data sources connect successfully
- [ ] Credentials/gateway configured for PBI Service
- [ ] On-premises data gateway installed and registered (if needed)
- [ ] Connection mode matches recommendation (Import / DirectQuery / Direct Lake)
- [ ] Refresh succeeds without timeout or errors
- [ ] Incremental refresh configured for large tables (if applicable)
- [ ] Sensitive connection strings stored in gateway, not embedded

## Section 3: Semantic Model Validation

- [ ] All tables from original universe present in semantic model
- [ ] Row counts match source (within tolerance)
- [ ] Column names and data types are correct
- [ ] Relationships match original universe joins (cardinality, direction)
- [ ] No ambiguous relationships / inactive relationships are intentional
- [ ] Hierarchies recreated (drill paths work)
- [ ] Calculated columns produce correct values (spot-check 10 rows)
- [ ] Date table present and marked as date table

## Section 4: Measures & Formulas

- [ ] All BO formulas have a corresponding DAX measure or calculated column
- [ ] Simple aggregations (SUM, COUNT, AVG) verified against BO output
- [ ] Context operator conversions (`In`, `ForEach`, `ForAll`) verified with test cases
- [ ] Running functions (RunningSum, Rank, Previous) verified against BO output
- [ ] @Prompt parameters converted to slicers/parameters (test each one)
- [ ] Percentage and ratio calculations match original (±0.01 tolerance)
- [ ] NULL handling behavior matches (BO treats NULL differently than DAX)
- [ ] Formatting (decimal places, currency symbols, date formats) matches original

## Section 5: Report Pages & Layout

- [ ] Same number of pages/tabs as original (or documented deviation)
- [ ] Page titles match or are improved
- [ ] Visual positions approximate original layout
- [ ] Section/group breaks recreated as drill-through or bookmarks
- [ ] Sub-reports recreated as drill-through pages
- [ ] OpenDocument links replaced with Power BI navigation URLs
- [ ] Report background/branding applied

## Section 6: Visuals & Charts

- [ ] Each original visual has a corresponding PBI visual
- [ ] Chart types match mapping (see `visual_mapping.md`)
- [ ] Axis labels, titles, and legends are correct
- [ ] Colors match corporate theme / original design
- [ ] Conditional formatting (alerters) recreated
- [ ] Tooltips display correct information
- [ ] Sort orders match original default sort
- [ ] Data labels shown/hidden as in original

## Section 7: Filters & Interactivity

- [ ] All input controls (dropdowns, checkboxes, sliders) recreated as slicers
- [ ] Slicer default values match original
- [ ] Cross-filtering behavior tested (click visual → others update)
- [ ] Drill-down works to correct levels
- [ ] Drill-through pages receive correct context
- [ ] Bookmarks recreate original "section" navigation (if used)
- [ ] Date range filters work correctly
- [ ] "All" / "None" selection behavior matches original

## Section 8: Row-Level Security (RLS)

- [ ] RLS roles defined in semantic model
- [ ] RLS rules match original BO security (@Variable, universe restrictions)
- [ ] Tested with "View as role" in PBI Desktop
- [ ] Tested with actual user accounts in PBI Service
- [ ] Dynamic RLS (UserPrincipalName-based) verified
- [ ] Admin/manager override roles working
- [ ] Object-level security (OLS) applied if needed for column masking
- [ ] No data leakage between roles

## Section 9: Performance

- [ ] DAX Studio Performance Analyzer run — no single query > 3s
- [ ] Best Practice Analyzer (Tabular Editor) — no critical warnings
- [ ] Storage mode appropriate (Import for < 1GB, DirectQuery/Direct Lake for larger)
- [ ] Aggregations configured for large tables (if DirectQuery)
- [ ] No unnecessary bi-directional relationships
- [ ] Date filters use date columns (not text)
- [ ] Large tables have appropriate summarization (avoid "Do not summarize" on all)
- [ ] Composite model partitioning optimized (if applicable)

## Section 10: Publishing & Sharing

- [ ] Published to correct workspace
- [ ] Workspace roles assigned (Admin, Member, Contributor, Viewer)
- [ ] Power BI App created and configured (if replacing BI Launchpad folders)
- [ ] App audience configured correctly
- [ ] Sensitivity labels applied (if required)
- [ ] Report certified (if replacing production BO report)
- [ ] Embed URLs generated (if replacing OpenDocument/SDK)
- [ ] Mobile-optimized view configured (if needed)

## Section 11: Scheduling & Subscriptions

- [ ] Refresh schedule matches original BO schedule
- [ ] Gateway refresh tested end-to-end
- [ ] Email subscriptions configured (replace BO inbox delivery)
- [ ] Paginated report subscriptions configured (replace BO Publications)
- [ ] Data-driven subscriptions tested (if replacing burst publications)
- [ ] Pipeline deployment rules configured (Dev → Test → Prod)
- [ ] Failure alerts configured (refresh failure notification)

## Section 12: Stakeholder Sign-Off

- [ ] Side-by-side comparison performed with business user
- [ ] Data accuracy validated (pick 5 specific values and verify)
- [ ] Navigation and usability reviewed
- [ ] Performance acceptable to end users
- [ ] Training materials prepared (if UX paradigm changed)
- [ ] Deviations documented and accepted (see fidelity classification)
- [ ] Sign-off obtained from report owner
- [ ] 30-day parallel run period initiated (old BO report + new PBI report)

---

## Checklist Summary Tracker

| Section | Items | Passed | Failed | N/A | Status |
|---------|-------|--------|--------|-----|--------|
| 1. Open & Load | 6 | | | | ⬜ |
| 2. Data Sources | 7 | | | | ⬜ |
| 3. Semantic Model | 8 | | | | ⬜ |
| 4. Measures & Formulas | 8 | | | | ⬜ |
| 5. Report Pages | 7 | | | | ⬜ |
| 6. Visuals & Charts | 8 | | | | ⬜ |
| 7. Filters & Interactivity | 8 | | | | ⬜ |
| 8. RLS | 8 | | | | ⬜ |
| 9. Performance | 8 | | | | ⬜ |
| 10. Publishing & Sharing | 8 | | | | ⬜ |
| 11. Scheduling | 7 | | | | ⬜ |
| 12. Stakeholder Sign-Off | 8 | | | | ⬜ |
| **TOTAL** | **91** | | | | |

> **Pass threshold**: All items Passed or N/A. Any Failed item must have a remediation plan before production release.

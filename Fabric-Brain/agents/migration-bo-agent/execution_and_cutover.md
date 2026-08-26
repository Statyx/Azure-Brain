# BO → Fabric — Execution, Validation and Cutover

Companion to [instructions.md](instructions.md), which covers Phases 0 to 2
(scoping, discovery, architecture design). This file carries the second half of
the framework: **Phases 3 to 6**, the customer case studies and the estimation
template.

The split is not cosmetic. The two halves answer different questions — the spine
answers *what should we build*, this file answers *how do we get there without
breaking the business*. Phases 5 and 6 in particular (validation, parallel run,
decommission, adoption) are the ones a migration skips under pressure, and the
ones whose absence is only discovered after the old stack is switched off.

---

## Phase 3 — Migration Execution

### 3.1 Universe → Semantic Model

> **Data source reference**: For complete mapping of BO connection types (JDBC, ODBC, BICS, JNDI) → Power Query M connectors with gateway planning see [connector_mapping.md](connector_mapping.md).

**Step-by-step:**
1. Export universe structure (IDT export or manual documentation)
2. Map business objects to DAX measures:
   - `=Sum(table[column])` for basic aggregations
   - Custom DAX for BO context operators (`In`, `ForEach`, `ForAll`)
3. Map derived tables to Lakehouse views or Dataflow Gen2 transformations
4. Map prompts (@Prompt) to model parameters or report-level slicers
5. Map dimension LOVs to dimension tables
6. Map row restrictions to RLS roles with DAX filters
7. Map aggregate awareness to composite models or aggregation tables

**Common BO formula → DAX translations:**

| BO Formula | DAX Equivalent |
|-----------|----------------|
| `=Sum([Revenue])` | `Revenue = SUM(Sales[Revenue])` |
| `=Sum([Revenue]) In [Region]` | Context transition — `CALCULATE(SUM(Sales[Revenue]), ALLEXCEPT(Sales, Geo[Region]))` |
| `=RunningSum([Revenue])` | `Running Revenue = CALCULATE(SUM(Sales[Revenue]), FILTER(ALL(Calendar), Calendar[Date] <= MAX(Calendar[Date])))` |
| `=Previous([Revenue])` | Use `DATEADD` or `PARALLELPERIOD` in time intelligence |
| `=Percentage([Revenue])` | `Revenue % = DIVIDE(SUM(Sales[Revenue]), CALCULATE(SUM(Sales[Revenue]), ALL(Sales)))` |
| `=Where` conditions | `CALCULATE` with filter arguments |
| `NoFilter()` | `ALL()` / `REMOVEFILTERS()` |

> **Full reference**: For all 119 BO → DAX function mappings across 10 categories (aggregation, context operators, running/window, string, date, logical, math, document/metadata, @Prompt, formatting) with cross-platform comparison table see [bo_to_dax_reference.md](bo_to_dax_reference.md). Coverage: 68% fully automatic, 90% auto+approximate.

### 3.2 Webi → Power BI Reports

> **Visual reference**: For complete mapping of all 78 BO visual types (Webi, Crystal, Xcelsius) → Power BI see [visual_mapping.md](visual_mapping.md). Summary: 73% High fidelity, 21% Medium, 6% Low/None.

**Migration approach per report:**
1. Document the data query (View SQL in Webi)
2. Identify all variables and formulas
3. Map input controls → Slicers
4. Map report tabs → Report pages
5. Map sections → Drill-through or bookmarks
6. Map alerters → Conditional formatting
7. Map cross-tabs → Matrix visuals (⚠️ test thoroughly — behavior differs)
8. Rebuild in Power BI Desktop connecting to new Semantic Model

**⚠️ No automated Webi → PBI conversion tool exists. This is manual work.**

### 3.3 Crystal Reports → Paginated Reports

**Options:**
1. **Manual rebuild** in Power BI Report Builder — recommended for <50 reports
2. **Third-party tools** (e.g., Mobilize.Net, DataGap) — for large volumes, partial automation
3. **Keep Crystal Server** short-term if reports are complex and low priority
4. **Intermediate SSRS path**: Convert Crystal → SSRS (.rdl) → then use Microsoft's RDL Migration Tool to publish to Power BI Service

**What converts well:** Tabular layouts, parameters, groups, totals, subreports (simple), print-perfect layouts
**What doesn't:** Complex subreports with different data sources, custom DLLs, embedded code, `WhilePrintingRecords` formulas, barcode fonts (verify availability), map visualizations with spatial data

**RDL/Paginated Report considerations (from MS Learn):**
- Shared data sources → must become embedded data sources in Paginated Reports
- Shared datasets → must become embedded datasets
- `UserID` built-in field returns UPN (e.g., `user@company.com`) not NT account (e.g., `DOMAIN\user`) — adjust security logic
- `ExecutionTime` built-in returns UTC — update footer/header time labels
- Cascading parameters are evaluated sequentially — pre-aggregate data when possible
- Document maps don't render in Power BI Service (they work in PDF export)
- Custom code DLL references are not supported in Power BI paginated reports
- Use **deployment pipelines** (Dev/Test/Production) for paginated reports lifecycle
- Test in all target browsers — rendering may differ
- PDF output: verify non-Latin character fonts are embedded correctly

### 3.4 Security Migration

```
BO CMC                          Fabric
─────                           ──────
Enterprise Users         →      Entra ID Users (sync via SCIM or manual)
BO Groups                →      Entra ID Security Groups
Folder: View             →      Workspace Viewer role
Folder: Schedule         →      Workspace Contributor role
Folder: Edit             →      Workspace Member role
Folder: Full Control     →      Workspace Admin role
Universe Row Restriction →      RLS Role + DAX filter
                                Example: [Region] = USERPRINCIPALNAME()
                                or lookup table approach:
                                CONTAINS(SecurityTable, SecurityTable[Email], USERPRINCIPALNAME())
```

### 3.5 Scheduling Migration

| BO Schedule | Fabric Equivalent |
|-------------|-------------------|
| Daily report refresh | Semantic Model scheduled refresh |
| File export to folder | Pipeline → Notebook → OneLake/SharePoint |
| Publication (burst) | Paginated Report data-driven subscription |
| Event-triggered | Reflex trigger → Pipeline |
| A→B→C chain | Pipeline with sequential activities |

---

## Phase 4 — Common Pitfalls & Errors

### 🔴 Architecture Pitfalls
| # | Pitfall | Impact | Mitigation |
|---|---------|--------|------------|
| 1 | **1:1 report migration** (rebuild every report as-is) | Wasted effort on unused reports | Use BO Auditing to kill dormant reports first |
| 2 | **Ignoring the semantic layer** (no shared Semantic Model) | Report sprawl, inconsistent metrics | Build shared Semantic Models = new "Universes" |
| 3 | **Gateway bottleneck** | Refresh failures, performance issues | Plan gateway capacity or migrate to Lakehouse |
| 4 | **Underestimating cross-tab complexity** | Matrix visuals ≠ Webi cross-tabs | Prototype complex cross-tabs early |
| 5 | **No parallel run** | Users distrust new reports | Run BO + Fabric side-by-side 2-4 weeks, compare numbers |

### 🔴 Technical Pitfalls
| # | Pitfall | Impact | Mitigation |
|---|---------|--------|------------|
| 6 | **BO context operators (In, ForEach, ForAll)** | No direct DAX equivalent | Requires deep DAX rewrite, test with sample data |
| 7 | **@Prompt cascading** | PBI slicers don't cascade the same way | Use field parameters or report-level measures |
| 8 | **Universe derived tables with complex SQL** | Can't just copy SQL | Rewrite as Lakehouse views or Dataflow M queries |
| 9 | **Crystal embedded formulas** | Some have no RDL equivalent | Manual rewrite or keep in Crystal until deprecated |
| 10 | **Row-level security gaps** | BO dynamic profile ≠ Fabric RLS | Full security audit before go-live |
| 11 | **Date/time handling** | BO date functions ≠ DAX time intelligence | Build proper date dimension table from day 1 |
| 12 | **Large dataset limits** | Webi can query millions inline | PBI Import has 1M visual limit, Direct Lake handles better |

### 🔴 Organizational Pitfalls
| # | Pitfall | Impact | Mitigation |
|---|---------|--------|------------|
| 13 | **No BO admin involvement** | Missing universe logic, security rules | Engage BO admin as SME throughout |
| 14 | **Big bang migration** | Risk of failure, user rejection | Wave-based: department by department |
| 15 | **No user training** | "Where's my report?" support flood | Train power users first, create video walkthroughs |
| 16 | **Losing BO audit trail** | Compliance gap | Export BO audit data before decommission |

---

## Phase 5 — Validation, Deployment & Parallel Run

> **Detailed checklist**: For a 91-item post-migration validation checklist (12 sections: Open & Load, Data Sources, Semantic Model, Measures, Pages, Visuals, Filters, RLS, Performance, Publishing, Scheduling, Stakeholder Sign-Off) see [post_migration_checklist.md](post_migration_checklist.md).

### 5.1 Validation Framework (4 aspects)

> **MS Learn guidance**: Validate every migrated report across four dimensions before deployment.

#### a) Data Accuracy
- [ ] Compare BO report output vs Fabric report (same date, same filters, same user)
- [ ] Row counts match exactly
- [ ] Aggregations match (SUM, AVG, COUNT, DISTINCTCOUNT — verify semantics)
- [ ] NULL/BLANK handling produces same results
- [ ] Date range filters: verify inclusive/exclusive boundary behavior
- [ ] Rounding: use explicit `ROUND()` if BO and DAX differ on float rounding

#### b) Security
- [ ] RLS: Same user sees same data scope as in BO row restrictions
- [ ] OLS: Hidden columns/measures match BO object-level security
- [ ] Test with multiple user profiles across different security groups
- [ ] Gateway data source permissions match BO connection-level access
- [ ] Test data access from Service, Desktop, mobile, and embedded scenarios

#### c) Functionality
- [ ] Filters/slicers produce same results as BO prompts / @Prompt
- [ ] Drill-through/drill-down behaves correctly
- [ ] Export: PDF/Excel/CSV output works and matches BO format
- [ ] Scheduling: Refresh runs at expected times
- [ ] Subscriptions: Email delivery works for paginated reports
- [ ] Mobile: Report renders on mobile (if required)

#### d) Performance
- [ ] Page load P95 < 10 seconds (compare against BO baseline)
- [ ] Refresh duration within scheduled window
- [ ] Concurrent user stress test: verify capacity handles peak load
- [ ] For slow reports: consider email subscriptions with PDF attachment as alternative

### 5.2 Deployment Strategy

**Use deployment pipelines (Dev → Test → Production):**
```
[Dev Workspace] → [Test Workspace] → [Production Workspace]
    ↑                    ↑                    ↑
  Authors           UAT testers         All users
  build here        validate here       consume here
```

**Deployment steps per wave:**
1. **Dev**: Authors build & iterate in Dev workspace
2. **Test**: Promote to Test workspace → Business users perform UAT
3. **Parameterize data sources**: Use deployment rules to switch connection strings between Dev/Test/Prod databases automatically
4. **Production**: After UAT sign-off, promote to Production workspace
5. **Staged rollout**: Start with pilot group (5-10 users) before full deployment

### 5.3 Parallel Run Protocol

> **MS Learn guidance**: "Run the legacy BI platform in parallel with Power BI for 30-90 days. Decommission when: predetermined time has expired AND all users have access to Power BI AND legacy platform shows no significant activity."

**Protocol:**
1. Run BO and Fabric side-by-side for **30-90 days** (duration depends on report criticality)
2. Business users compare 5-10 critical reports daily (same date, same filters)
3. Log discrepancies in a shared tracker (SharePoint list or Teams channel)
4. Fix, re-validate, and re-deploy through pipeline
5. Monitor BO audit DB: confirm declining usage on legacy
6. Monitor Power BI activity log: confirm increasing usage on Fabric
7. Business sign-off per report wave before BO decommission
8. **Decommission trigger** (all three must be true):
   - Predetermined parallel run period has expired
   - All active users have access to Power BI equivalent
   - No significant query activity on legacy BO report for 2+ weeks

---

## Phase 6 — Decommission, Monitoring & Adoption

### 6.1 Decommission Checklist
- [ ] All active reports migrated and validated
- [ ] BO audit data exported and archived (compliance requirement)
- [ ] BO connections documented (for reference)
- [ ] Universe documentation archived (metadata, business rules, formulas)
- [ ] BO server backup taken before shutdown
- [ ] DNS/bookmarks redirected to Fabric (Power BI App URLs)
- [ ] BO license termination communicated to SAP
- [ ] Legacy system shows no significant activity for 2+ weeks
- [ ] All users confirmed to have access to Fabric equivalents

### 6.2 Post-Migration Monitoring

**Use Power BI Activity Log and Admin Portal:**
- Track active users per workspace (weekly trend)
- Monitor report views: which migrated reports are actually used?
- Identify "orphan" reports with zero views after 30 days → candidate for retirement
- Track refresh failures and data source errors
- Monitor Fabric capacity utilization (CU consumption vs capacity)
- Set up alerts for refresh failures via Power Automate

**Migration tracking dashboard** (build in Power BI):
- Wave progress: % reports migrated, validated, in production
- Adoption curve: active users on Fabric vs active users on BO (over time)
- Quality metrics: validation pass rate, open discrepancies
- Performance metrics: P95 page load time per report

### 6.3 Adoption Accelerators
- Power BI App for each department (replaces BI Launchpad folders)
- Quick-reference card: "BO → Fabric: Where to find your reports"
- Side-by-side screenshot guide: "Your BO report in Fabric"
- Power user community (champions network) — weekly office hours
- Office hours first 2 weeks post go-live (daily, then weekly)
- Video walkthroughs for top 10 most-used reports
- Multi-tier support model:
  - **Tier 1**: Intra-team support + FAQs + documentation
  - **Tier 2**: Champions / power user community
  - **Tier 3**: COE experts (complex issues, new requirements)

### 6.4 Documentation Standards

**Document every migrated semantic model:**
- Source: Original BO universe name and version
- Tables, relationships, measures — with business descriptions
- Data refresh schedule and data source
- RLS roles and security rules
- Known limitations vs BO original
- Contact: Migration team member who built it

**Document every migrated report:**
- Source: Original BO report name, CMS path, and universe
- Changes from original (layout, functionality, data scope)
- Target audience and distribution method (App, subscription, embed)
- Validation status and sign-off date

---

## Lessons from Real Migrations (Customer Case Studies)

> Source: [Microsoft Learn — Learn from customers](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-learn-from-customers)

### Case Study 1 — Consumer Goods Company (3-year phased migration)
- Migrated from **multiple legacy BI platforms** including BO, over 3 years (2017-2020)
- Built **COE with 1,600+ community members** — key to adoption success
- Initial estimate of 50 days for a report batch turned out to be **50 hours** — complexity was overestimated
- **~50% of legacy reports were retired** rather than migrated (unused or duplicate)
- Used a **migration scorecard** tracking: reports migrated, active users, legacy usage declining
- Learned: invest in change management early — some users resist leaving familiar tools

### Case Study 2 — Transportation & Logistics Company (gradual adoption)
- Started Power BI organically, then formalized migration from legacy BI
- Used **balanced centralized/distributed team model**: COE for standards, departments for content
- Emphasized **semantic model reusability**: one shared semantic model serves many reports
- Used **DB2 DirectQuery** to avoid data movement for critical on-prem data
- Created **multi-tier support**: intra-team → community → COE experts
- Formed a **governance committee** to manage migration priorities and standards
- Key lesson: don't force migration — demonstrate value and users will adopt organically

### Key Takeaways for BO Migrations
1. **Half your reports may not need migrating** — Use BO Auditing to find dormant/duplicate reports
2. **Complexity is often overestimated** — POC reveals true effort more accurately than paper estimates
3. **Invest in community before migration** — Champions reduce support burden by 60-70%
4. **Phased approach wins** — Never big bang. Department by department, wave by wave
5. **Mandate shared semantic models** — This is the #1 architecture decision. Prevents report sprawl
6. **Change management is 50% of the work** — Technology migration is the easy part
7. **Monitor adoption metrics from day 1** — Activity logs prove migration success to stakeholders

---

## Estimation Template

| Activity | Small (<50 reports) | Medium (50-200) | Large (200+) |
|----------|--------------------:|----------------:|-------------:|
| Discovery & Inventory | 1-2 weeks | 2-3 weeks | 3-4 weeks |
| Architecture Design | 1 week | 2 weeks | 2-3 weeks |
| Semantic Model Build | 2-4 weeks | 4-8 weeks | 8-16 weeks |
| Report Migration | 4-8 weeks | 8-20 weeks | 20-40+ weeks |
| Crystal → Paginated | 2-4 weeks | 4-10 weeks | 10-20 weeks |
| Security Setup | 1 week | 2-3 weeks | 3-4 weeks |
| Testing & Parallel Run | 2-3 weeks | 3-4 weeks | 4-6 weeks |
| Training & Adoption | 1 week | 2 weeks | 3-4 weeks |
| **Total** | **3-5 months** | **6-12 months** | **12-24 months** |

> **Rule of thumb:** ~0.5-2 days per Webi report (depending on complexity), ~1-3 days per Crystal Report, ~1-2 weeks per Universe → Semantic Model.

# Microsoft Official Power BI Migration Framework

> Source: [Power BI migration overview](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-overview)
> This is the official Microsoft guidance for migrating from any legacy BI platform (including SAP BusinessObjects) to Power BI / Microsoft Fabric.

---

## Framework Overview

Microsoft defines a **5-stage migration process** preceded by a Pre-migration phase:

```
Pre-migration  →  Stage 1  →  Stage 2  →  Stage 3  →  Stage 4  →  Stage 5
                Requirements   Planning      POC       Create &    Deploy &
                Gathering                             Validate    Support
```

Each stage is iterative and applies **per migration wave** (not once globally).

---

## Pre-Migration Steps

> Source: [Pre-migration steps](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-pre-migration-steps)

### Actions
1. **Stakeholder identification**: Identify executive sponsor, business leads, BO admin, IT, power users
2. **Cost-benefit analysis**: Compare current BO TCO (licenses, servers, admin) vs projected Fabric cost
3. **Governance model**: Define before migration — naming conventions, workspace structure, content ownership, certification process
4. **Initial architecture**: Select data layer pattern (Gateway / Lakehouse / Warehouse / Hybrid), workspace topology, security approach
5. **Success criteria**: Define measurable KPIs (see instructions.md → Phase 0 → Success Criteria)
6. **Inventory preparation**: Document all BO assets using CMC/Query Builder — use BO Auditing DB for usage analysis
7. **Automation assessment**: Evaluate options for partial automation (Crystal → RDL tools, metadata export scripts, API-based deployment)

### Key Decisions
- Power BI Pro vs Premium Per User vs Fabric capacity (F SKU)?
- Who will author content — centralized (COE) or decentralized (departments)?
- How will content be consumed — Power BI Apps, embedded, Teams, SharePoint?

---

## Stage 1 — Gather Requirements

> Source: [Gather requirements](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-requirements)

### Report Requirements
For each report in scope:
- **Current functionality**: What does it show? Who uses it? How often?
- **Data requirements**: Sources, refresh frequency, volume, latency needs
- **Improvement opportunities**:
  - **Consolidation**: Can multiple BO reports be merged into one Power BI report with bookmarks/pages?
  - **Efficiency**: Can self-service features replace scheduled BO reports?
  - **Centralized data model**: Can a shared Semantic Model serve multiple reports?

### Prioritization
- Use **complexity scoring** (1-5 scale — see instructions.md Phase 1.3) combined with **business impact** (usage frequency, executive visibility)
- **Quick wins**: Low complexity + high usage → migrate first
- **Retire**: Low usage + any complexity → don't migrate, retire from BO
- **Defer**: High complexity + low usage → migrate in later waves

---

## Stage 2 — Deployment Planning

> Source: [Deployment planning](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-planning)

### Product Choice
For each report, decide the Power BI product:
- **Power BI report (.pbix)**: Interactive, exploration, dashboards → for most Webi report replacements
- **Paginated report (.rdl)**: Print-optimized, pixel-perfect, long tables → for Crystal Reports replacements
- **Excel + Semantic Model**: For users who need Excel pivot tables connected to Fabric
- **Power BI Dashboard**: Pin tiles from multiple reports → for executive summary views

> ⚠️ **BO-specific note**: Power BI "Dashboard" is NOT the same as a Power BI "Report". A Dashboard is pinned tiles from various reports. Most Webi migrations target Power BI Reports, not Dashboards.

### Workspace Management
- One workspace per domain/department (mirrors BO CMC folder structure)
- Separate Dev/Test/Prod workspaces with deployment pipelines
- Shared semantic models in dedicated workspaces (access via cross-workspace connection)

### Data Acquisition Method
- **Import mode**: Data copied into Fabric — best for <100M rows, offline access needed
- **DirectQuery/Direct Lake**: Real-time data, no duplication — best for large datasets, real-time needs
- **Composite model**: Mix import + DirectQuery — best for combining hot (real-time) and cold (historical) data
- **On-premises gateway**: Required when data stays on-prem — plan gateway sizing and clustering

### Storage Mode Decision
| Scenario | Recommended Mode |
|----------|-----------------|
| Data can move to cloud (Lakehouse) | Direct Lake |
| Data stays on-prem, <100M rows | Import via Gateway |
| Data stays on-prem, >100M rows | DirectQuery via Gateway |
| Mixed cloud + on-prem | Composite Model |
| Real-time requirements | DirectQuery or Eventhouse |

---

## Stage 3 — Conduct Proof of Concept (POC)

> Source: [POC guidance](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-proof-of-concept)

### POC Goals
- **Verify assumptions** about data connectivity, performance, and architecture
- **Mitigate risk** by testing the hardest parts first (complex DAX, RLS, large datasets)
- **Validate effort estimates** — compare POC actual effort vs. paper estimates
- **Discover unknown gaps** in BO → Fabric feature mapping

### POC Best Practices
1. **Select representative reports** spanning complexity levels (not just easy ones)
2. **Handle BI platform differences**: Power BI is a different paradigm from BO — don't force-fit BO patterns
3. **Redesign the data model**: Use star schema in Lakehouse. Don't replicate BO's denormalized universe query structure
4. **Take the POC end-to-end**: Data layer → Semantic Model → Reports → Security → Distribution → Validation
5. **Focus on the big picture**: Don't spend days on pixel-perfect layout replication. Same business insight > same visual layout
6. **Treat POC as non-disposable**: POC artifacts should be production-quality and reusable

See also: instructions.md → Phase 2.4 for detailed POC methodology.

---

## Stage 4 — Create & Validate Content

> Source: [Create and validate content](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-create-validate-content)

### Semantic Model Development
1. **Decouple data model from reports**: Build the Semantic Model first, independently of any specific report
2. **Prioritize shared models**: One Semantic Model should serve many reports (like a BO Universe served many Webi reports)
3. **Parameterize data sources**: Use parameters to switch between Dev/Test/Prod database connections
4. **Apply incremental refresh**: For large tables, only refresh changed/new data

### Report Development
1. Build reports connecting to the validated Semantic Model
2. Use workspace-level access control (not sharing individual reports)
3. For Crystal → Paginated: use Power BI Report Builder (or RDL Migration Tool if SSRS intermediate)
4. For Webi → PBI: manual rebuild in Power BI Desktop (no automated tool)

### Validation (4-aspect framework)
See instructions.md → Phase 5.1 for the full validation framework:
- **Data accuracy**: Row counts, aggregations, NULL handling, rounding
- **Security**: RLS/OLS verification with multiple user profiles
- **Functionality**: Filters, drill-through, export, scheduling
- **Performance**: Page load < 10 seconds P95

---

## Stage 5 — Deploy, Support & Monitor

> Source: [Deploy, support, and monitor](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-deploy-support-monitor)

### Deployment Stages
1. **Test workspace**: Internal team testing
2. **UAT**: Business users validate in test workspace with production-like data
3. **Pilot**: Deploy to production workspace, release to 5-10 pilot users first
4. **Full production**: After pilot validation, open access to all intended users
5. **App publishing**: Create Power BI App for polished end-user experience

### Additional Components
- **Gateways**: Validate gateway capacity for production refresh loads
- **Dataflows Gen2**: Ensure shared data transformation logic is deployed
- **Custom visuals**: Verify organizational visuals are approved and deployed
- **Paginated reports**: Verify Report Builder version compatibility

### Parallel Running
- Run legacy BO and Fabric in parallel for **30-90 days** per wave
- **Decommission criteria** (all must be true):
  1. Predetermined parallel run period has expired
  2. All active users have access to Power BI equivalent
  3. Legacy BO report shows no significant activity for 2+ weeks
- Export BO audit data before decommission (compliance)

### Monitoring
- **Power BI Activity Log**: Track views, exports, shares per report
- **Admin Portal usage metrics**: Monitor active users, adoption trends
- **Capacity metrics**: Track Fabric CU consumption vs capacity
- **Refresh monitoring**: Track refresh success/failure rates
- Use Power Automate for failure alerts

### Multi-tier Support Plan
| Tier | Scope | Who |
|------|-------|-----|
| Tier 1 | Self-help, FAQ, documentation | End users + champions |
| Tier 2 | Power user community, office hours, peer support | Champions network |
| Tier 3 | Complex issues, architecture, new requirements | COE experts |

---

## Migration Reasons (from MS Learn)

Common reasons customers migrate from legacy BI (including BO) to Fabric:

1. **Cost reduction**: Consolidate multiple BI tools into one platform
2. **Self-service BI**: Empower business users to create their own reports
3. **Cloud-first strategy**: Eliminate on-premises BI server infrastructure
4. **Modern analytics**: AI (Copilot), real-time intelligence, machine learning integration
5. **Improved collaboration**: Teams, SharePoint integration, shared semantic models
6. **Mobile experience**: Native mobile BI that BO/Crystal don't provide well
7. **Vendor consolidation**: Single Microsoft stack (M365 + Fabric + Power Platform)
8. **License savings**: BO Named/Concurrent licenses are expensive vs Power BI Pro/PPU
9. **End of support**: Flash EOL (Xcelsius), aging BO versions losing vendor support
10. **Compliance**: Better audit trail, sensitivity labels, data governance in Fabric

---

## References

- [Power BI migration overview](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-overview)
- [Pre-migration steps](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-pre-migration-steps)
- [Stage 1: Gather requirements](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-requirements)
- [Stage 2: Deployment planning](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-planning)
- [Stage 3: POC](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-proof-of-concept)
- [Stage 4: Create & validate](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-create-validate-content)
- [Stage 5: Deploy, support, monitor](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-deploy-support-monitor)
- [Learn from customers](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-learn-from-customers)
- [Migrate SSRS reports to Power BI](https://learn.microsoft.com/en-us/power-bi/guidance/migrate-ssrs-reports-to-power-bi)
- [Power BI paginated reports](https://learn.microsoft.com/en-us/power-bi/paginated-reports/paginated-reports-report-builder-power-bi)

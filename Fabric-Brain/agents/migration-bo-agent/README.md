# BO Migration Agent

Agent specialized in SAP BusinessObjects (BO) to Microsoft Fabric migration projects.

## Files

| File | Purpose |
|------|---------|
| [instructions.md](instructions.md) | Full migration framework: phases, mapping, architecture patterns, POC, validation, pitfalls, case studies, estimation |
| [microsoft_migration_framework.md](microsoft_migration_framework.md) | Microsoft official 5-stage Power BI migration framework (MS Learn reference) |
| [discovery_questionnaire.md](discovery_questionnaire.md) | Customer-facing questionnaire: environment, complexity, security, governance readiness, data reusability |
| [known_issues.md](known_issues.md) | Known blockers, unsupported features, DAX/visual conversion limits, paginated report limitations, estimation pitfalls |
| [bo_to_dax_reference.md](bo_to_dax_reference.md) | 119 BO formula → DAX mappings across 10 categories with cross-platform comparison (BO/Tableau/MSTR/Qlik/DAX) |
| [visual_mapping.md](visual_mapping.md) | 78 BO visual/component → Power BI visual mappings (Webi, Crystal, Xcelsius, BO special) with fidelity scores |
| [bo_migration_assessment.md](bo_migration_assessment.md) | Pre-migration readiness scoring (8 categories, GREEN/YELLOW/RED), fidelity classification, strategy advisor matrix |
| [post_migration_checklist.md](post_migration_checklist.md) | 91-item post-migration validation checklist (12 sections) with summary tracker |
| [connector_mapping.md](connector_mapping.md) | BO data connector → Power Query M mapping (17 RDBMS + SAP + file + cloud), migration architecture patterns, gateway planning |

## When to use this agent

- Customer asks to migrate from SAP BusinessObjects to Microsoft Fabric / Power BI
- Assessment of BO → Fabric migration scope and complexity
- Architecture design for BO replacement (data layer + semantic + reports)
- Report complexity scoring and wave planning
- Security model translation (CMC → Fabric RLS/OLS)
- Proof of Concept (POC) planning and execution
- Estimation and project planning
- Governance, COE, and change management guidance
- Post-migration monitoring and adoption strategy

## Key principles

1. **Never 1:1 migrate** — Retire dormant reports (~50% unused), consolidate duplicates
2. **Semantic layer first** — Build shared Semantic Models before reports (replaces Universes)
3. **Wave-based delivery** — Department by department, not big bang
4. **Parallel run mandatory** — Always run BO + Fabric side-by-side 30-90 days before decommission
5. **Usage-driven prioritization** — Migrate most-used reports first, not alphabetically
6. **POC before full migration** — Validate architecture, effort estimates, and feature gaps with a real POC
7. **Governance before content** — Establish COE, naming conventions, ownership model before migrating reports
8. **Change management is half the work** — Build champion network, train power users, invest in community
9. **Monitor adoption from day 1** — Activity logs + migration scorecard prove success to stakeholders
10. **Assess before you migrate** — Score every report (GREEN/YELLOW/RED) to accurately plan waves and effort
11. **Validate systematically** — Use the 91-item checklist, don't rely on ad-hoc testing

## Sources
- [Microsoft Power BI Migration Series](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-migration-overview) (8 articles)
- [SSRS/Crystal → Paginated Reports migration](https://learn.microsoft.com/en-us/power-bi/guidance/migrate-ssrs-reports-to-power-bi)
- [Power BI Paginated Reports overview](https://learn.microsoft.com/en-us/power-bi/paginated-reports/paginated-reports-report-builder-power-bi)
- Real customer case studies from Microsoft Learn
- Cross-platform migration patterns from [cyphou/Tableau-To-PowerBI](https://github.com/cyphou/Tableau-To-PowerBI), [cyphou/MicroStrategyToPowerBI](https://github.com/cyphou/MicroStrategyToPowerBI), [cyphou/Qlik-To-PowerBI](https://github.com/cyphou/Qlik-To-PowerBI)

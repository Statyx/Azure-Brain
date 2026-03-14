# report-builder-agent — Power BI Report Builder

## Identity

**Name**: report-builder-agent  
**Scope**: Everything related to Power BI report creation, visuals, pages, themes, and deployment via Fabric REST API  
**Version**: 1.0  

## What This Agent Owns

| Domain | Fabric Items | Key APIs |
|--------|-------------|----------|
| **Report Creation** | Reports (PBIR-Legacy format) | Report REST API (create, update, getDefinition) |
| **Visual Design** | Cards, Charts, Textboxes, Tables | prototypeQuery, projections, objects/vcObjects |
| **Page Layout** | Sections, canvas sizing, grid | sections[], visualContainers[] |
| **Theming & Styling** | Base themes, colors, fonts, shadows | expression language, vcObjects |
| **Connection Binding** | definition.pbir, XMLA connection | V2 schema, byConnection |

## What This Agent Does NOT Own

- Semantic models / DAX measures → defer to `agents/semantic-model-agent/`
- Data pipelines / ingestion → defer to `agents/orchestrator-agent/`
- OneLake file management → defer to brain `onelake.md`
- Capacity / infrastructure → defer to brain `environment.md`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, mandatory rules, decision trees |
| `dashboard_design_guide.md` | **Design bible** — Layout principles, typography scale, color system, setup checklist |
| `report_structure.md` | Legacy PBIX format, report.json anatomy, definition.pbir, required parts |
| `visual_catalog.md` | All visual types, projections, prototypeQuery, objects/vcObjects |
| `pages_layout.md` | Page config, canvas dimensions, grid system, dashboard templates |
| `themes_styling.md` | Expression language, color system, Python helpers, container styling |
| `known_issues.md` | Report-specific gotchas and debugging checklist |
| `templates/` | Ready-to-use report template and deploy script |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context
2. Read the relevant knowledge file for the task at hand
3. Reference `../../resource_ids.md` for workspace/item IDs

## Key Insight

> **NEVER use PBIR folder format.** Always use Legacy PBIX format  
> (`report.json` with `sections[].visualContainers[]`).  
> The API accepts PBIR but it renders **BLANK** — the single biggest gotcha in this project.

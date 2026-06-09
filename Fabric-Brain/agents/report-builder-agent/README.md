# report-builder-agent — Power BI Report Builder (PBIR)

## Identity

**Name**: report-builder-agent  
**Scope**: Authoring, validating, and deploying Power BI reports in **PBIR folder format** for Microsoft Fabric.  
**Version**: 2.0 — PBIR migration.

## What This Agent Owns

| Domain | Items | Tooling |
|---|---|---|
| **Report authoring** | `<Report>.Report/` PBIR folder | Python writer + `powerbi-report-author` CLI |
| **Visual design** | `visuals/<id>/visual.json` | 57 visual types, 16 VCOs (see [`cli_knowledge/`](cli_knowledge/)) |
| **Page layout** | `pages/<pageId>/page.json` + `pages/pages.json` | 1280×720 grid, archetype templates |
| **Theming** | `StaticResources/SharedResources/BaseThemes/*.json` | Tone palettes, dark/light modes |
| **Connection binding** | `definition.pbir` (v4.0) | `byConnection` XMLA string |
| **Deployment** | Fabric REST `updateDefinition` | Async base64 parts upload |

## What This Agent Does NOT Own

- Semantic models / DAX measures → `agents/semantic-model-agent/`
- Data ingestion → `agents/orchestrator-agent/`
- OneLake file management → `../../onelake.md`
- Capacity / workspace provisioning → `../../environment.md`

## Files

| File | Purpose |
|---|---|
| [`instructions.md`](instructions.md) | **LOAD FIRST** — mandatory rules, decision trees, CLI usage |
| [`report_structure.md`](report_structure.md) | PBIR folder anatomy, schema URLs, required parts, deployment payload |
| [`visual_catalog.md`](visual_catalog.md) | Archetypes → visual-type selection; `visual.json` skeleton; how to query `cli_knowledge/` |
| [`pages_layout.md`](pages_layout.md) | `page.json` + `pages.json`, canvas grid, archetype layouts |
| [`themes_styling.md`](themes_styling.md) | Theme JSON, VCO usage, **`expr` literal cheatsheet** |
| [`dashboard_design_guide.md`](dashboard_design_guide.md) | Tones, typography, color, archetypes (Executive / Operational / Analytical / Narrative / Comparative) |
| [`known_issues.md`](known_issues.md) | PBIR gotchas + debugging checklist |
| [`cli_knowledge/`](cli_knowledge/) | **Ground truth** — 57 visuals × all properties, 16 VCOs, dumped from `powerbi-report-author` |
| [`templates/pbir/`](templates/pbir/) | Minimal working `<Report>.Report/` skeleton |
| [`templates/deploy_report.py`](templates/deploy_report.py) | Reference REST deployment script |
| `*.legacy.md` | Pre-PBIR knowledge (read-only reference, kept for traceability) |

## Quick Start

1. Read [`instructions.md`](instructions.md) — agent rules
2. Read [`report_structure.md`](report_structure.md) — folder anatomy
3. For a specific visual property, **always** consult [`cli_knowledge/visuals/<type>/objects/<obj>.json`](cli_knowledge/visuals/) — never guess
4. Build, then `powerbi-report-author validate <Report>.Report` before deployment

## Source of Truth

> **`cli_knowledge/`** is the only authoritative source for visual types, formatting objects, properties, and enum values.  
> If a property is not listed there, it does not exist. Do not hallucinate.

The dump was generated with `@microsoft/powerbi-report-authoring-cli v0.1.1` against `npm:@microsoft/powerbi-core-visual-schema`. Refresh with `cli_knowledge/dump_cli_knowledge.ps1` when the CLI updates.

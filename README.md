# Github Brain — Fabric & Power BI Knowledge Base

This folder contains accumulated knowledge from building Microsoft Fabric solutions.
It is designed to be loaded at the start of every Copilot session to avoid re-learning
lessons, repeating mistakes, and wasting time on already-solved problems.

## How to Use

This brain is auto-loaded via `.github/copilot-instructions.md` in any project that
references it. Every new session starts with this context.

## Files

| File | Purpose |
|------|---------|
| `fabric_api.md` | Fabric REST API patterns, auth, async operations |
| `report_format.md` | **CRITICAL** — Legacy PBIX format for working reports |
| `visual_builders.md` | PBI visual config structure, expression language |
| `semantic_model.md` | Semantic model deployment via model.bim |
| `onelake.md` | OneLake DFS API patterns for file operations |
| `known_issues.md` | All gotchas, workarounds, what works vs what doesn't |
| `environment.md` | Python, Azure CLI, PowerShell setup notes |
| `resource_ids.md` | IDs, endpoints, connection strings (project-specific) |
| `agent_principles.md` | **MANDATORY** — Agent operating principles, task management, quality standards |

## Specialized Agents

| Agent | Scope | Path |
|-------|-------|------|
| **orchestrator-agent** | Data Pipelines, Ingestion, Notebooks, Copy Jobs, Monitoring | `agents/orchestrator-agent/` |
| **semantic-model-agent** | Semantic Models, DAX Measures, Relationships, model.bim, Direct Lake | `agents/semantic-model-agent/` |
| **report-builder-agent** | Power BI Reports, Visuals, Pages, Themes, Legacy PBIX Format | `agents/report-builder-agent/` |
| **creator-data-agent** | Fabric Data Agents, AI Instructions, Data Sources, Few-Shots, Publishing | `agents/creator-data-agent/` |

Each agent has its own `README.md`, `instructions.md` (system prompt), and domain-specific knowledge files.  
Load the agent's `instructions.md` at session start when working in its domain.

## Priority Reading Order

For a new session working on **Fabric reports / Power BI visuals**:
1. `agents/report-builder-agent/instructions.md` — Agent system prompt, 5 mandatory rules, decision trees
2. `agents/report-builder-agent/report_structure.md` — Legacy PBIX format, report.json, definition.pbir
3. `agents/report-builder-agent/visual_catalog.md` — All visual types, projections, prototypeQuery
4. `agents/report-builder-agent/pages_layout.md` — Canvas grid, dashboard templates
5. `agents/report-builder-agent/themes_styling.md` — Expression language, colors, Python helpers
6. `agents/report-builder-agent/known_issues.md` — Report-specific gotchas & debugging checklist

For a new session working on **orchestration / ingestion**:
1. `agents/orchestrator-agent/instructions.md` — Agent system prompt & decision trees
2. `agents/orchestrator-agent/pipelines.md` — Pipeline creation, activities, execution
3. `agents/orchestrator-agent/ingestion.md` — OneLake upload, Copy Jobs, Shortcuts
4. `agents/orchestrator-agent/notebooks.md` — Spark notebooks for transformations
5. `agents/orchestrator-agent/monitoring.md` — Error handling, retry, health checks

For a new session working on **semantic models / DAX**:
1. `agents/semantic-model-agent/instructions.md` — Agent system prompt & decision trees
2. `agents/semantic-model-agent/model_deployment.md` — model.bim structure, deployment API
3. `agents/semantic-model-agent/dax_measures.md` — DAX function reference & all 26 finance measures
4. `agents/semantic-model-agent/dax_queries.md` — Validation queries, debugging, performance
5. `agents/semantic-model-agent/relationships.md` — Star schema, relationship rules, role-playing dims
6. `agents/semantic-model-agent/known_issues.md` — Semantic-model-specific gotchas & fixes

For a new session working on **Fabric Data Agents**:
1. `agents/creator-data-agent/instructions.md` — Agent system prompt, 5 mandatory rules, decision trees
2. `agents/creator-data-agent/instruction_writing_guide.md` — 7-section framework for writing AI instructions
3. `agents/creator-data-agent/definition_structure.md` — JSON format, parts layout, encoding
4. `agents/creator-data-agent/datasource_configuration.md` — Binding semantic models, lakehouses, warehouses
5. `agents/creator-data-agent/fewshot_examples.md` — How to write effective Q&A training pairs
6. `agents/creator-data-agent/known_issues.md` — Gotchas, debugging checklist

## Key Insight (TL;DR)

> **The Fabric REST API accepts two report formats. Only one renders visuals.**
> Use the **Legacy PBIX format** (`report.json` with `sections[].visualContainers[]`).
> Never use the PBIR folder format (`definition/pages/*/visuals/*/visual.json`).

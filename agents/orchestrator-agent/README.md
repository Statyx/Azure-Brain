# orchestrator-agent — Fabric Data Orchestration & Ingestion

## Identity

**Name**: orchestrator-agent  
**Scope**: Everything related to data orchestration, ingestion, and ETL/ELT in Microsoft Fabric  
**Version**: 1.0  

## What This Agent Owns

| Domain | Fabric Items | Key APIs |
|--------|-------------|----------|
| **Orchestration** | Data Pipelines, Scheduling | DataPipeline REST API, Job Scheduler |
| **Ingestion** | OneLake uploads, Copy Jobs, Shortcuts | OneLake DFS API, CopyJob REST API |
| **Transformation** | Notebooks (Spark), Dataflows Gen2 | Notebook REST API, Spark jobs |
| **Monitoring** | Pipeline runs, Job history | Operations API, Job instances |

## What This Agent Does NOT Own

- Semantic models → defer to brain `semantic_model.md`
- Reports & visuals → defer to brain `report_format.md` / `visual_builders.md`
- Capacity management → defer to brain `environment.md`
- RBAC / security → out of scope

## When NOT to Use This Agent

| If you need to… | Use instead |
|-----------------|-------------|
| Write M / Power Query transformations | `../dataflow-agent/` |
| Route EventStream data (Kafka, custom endpoints) | `../rti-eventstream-agent/` |
| Design star schemas or dimensional models | `../domain-modeler-agent/` |
| Build KQL queries or real-time dashboards | `../rti-kusto-agent/` |
| Create / manage workspaces or capacity | `../workspace-admin-agent/` |
| Deploy items via CLI (`fab deploy`, `fab job run`) | `../fabric-cli-agent/` |
| Build reports or visuals | `../report-builder-agent/` |
| Configure AI Skill / Data Agent instructions | `../ai-skills-agent/` |

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, behavioral rules, decision trees, CLI cross-ref |
| `pipelines.md` | Pipeline creation, activities, definition format, execution |
| `ingestion.md` | OneLake uploads, Copy Jobs, Shortcuts, external sources |
| `notebooks.md` | Spark notebooks for CSV→Delta, transformations |
| `monitoring.md` | Run tracking, error handling, retry patterns |
| `pipeline_definitions.md` | Pipeline JSON schema, expression cookbook (15 real-world patterns), all activity types |
| `known_issues.md` | 10 documented issues — includes Spark debugging walkthrough |
| `templates/README.md` | **Template index** — what each template does, how to deploy, customization checklist |
| `templates/pipeline_bronze_silver_gold.json` | Production 6-activity pipeline (ForEach → Bronze → Silver → Gold → Refresh + failure webhook) |
| `templates/pipeline_ingest_transform.json` | Minimal 2-activity starter pipeline (Wait → Notebook) |
| `templates/notebook_csv_to_delta.py` | Spark notebook: auto-discover CSV subfolders → write Delta tables |
| `templates/orchestrate_ingestion.py` | End-to-end Python script: auth → upload → run → poll |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context
2. Read the relevant knowledge file for the task at hand
3. Reference `../../resource_ids.md` for workspace/item IDs
4. Reference `../../environment.md` for auth setup

## Key Insight (TL;DR)

> **Fabric orchestration is async-first.** Every creation and execution call returns HTTP 202.  
> Always poll `x-ms-operation-id`. Never assume synchronous success.  
> Pipeline cold-start on F16 = ~2 min `NotStarted` before `InProgress`.

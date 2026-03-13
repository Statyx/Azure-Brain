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

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, behavioral rules, decision trees |
| `pipelines.md` | Pipeline creation, activities, definition format, execution |
| `ingestion.md` | OneLake uploads, Copy Jobs, Shortcuts, external sources |
| `notebooks.md` | Spark notebooks for CSV→Delta, transformations |
| `monitoring.md` | Run tracking, error handling, retry patterns |
| `templates/` | Ready-to-use code templates |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context
2. Read the relevant knowledge file for the task at hand
3. Reference `../../resource_ids.md` for workspace/item IDs
4. Reference `../../environment.md` for auth setup

## Key Insight (TL;DR)

> **Fabric orchestration is async-first.** Every creation and execution call returns HTTP 202.  
> Always poll `x-ms-operation-id`. Never assume synchronous success.  
> Pipeline cold-start on F16 = ~2 min `NotStarted` before `InProgress`.

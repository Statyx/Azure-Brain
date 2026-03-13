# semantic-model-agent — Fabric Semantic Model Creation & Management

## Identity

**Name**: semantic-model-agent  
**Scope**: Everything related to building, deploying, and maintaining Semantic Models in Microsoft Fabric  
**Version**: 1.0  

## What This Agent Owns

| Domain | Artifacts | Key Knowledge |
|--------|-----------|---------------|
| **Model Structure** | model.bim (TMSL JSON), definition.pbism | Compatibility levels, Direct Lake mode |
| **Tables & Columns** | Dimension tables, Fact tables | Star-schema design, data types, formatting |
| **Relationships** | Many-to-One, cross-filtering | Cardinality, filter direction, ambiguity |
| **DAX Measures** | KPIs, time-intelligence, ratios | Full DAX language, best practices |
| **DAX Queries** | EVALUATE, DEFINE, SUMMARIZE | Testing queries, validation |
| **Deployment** | Fabric REST API, async operations | Create, update, get definition |
| **Refresh** | Direct Lake, import mode | Refresh triggers, partition management |

## What This Agent Does NOT Own

- Reports & visuals → defer to brain `report_format.md` / `visual_builders.md`
- Data pipelines / ingestion → defer to `agents/orchestrator-agent/`
- OneLake file management → defer to brain `onelake.md`
- Capacity / infrastructure → defer to brain `environment.md`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, rules, decision trees |
| `model_deployment.md` | model.bim structure, API deployment, definition.pbism |
| `dax_measures.md` | DAX reference, measure patterns, time intelligence |
| `dax_queries.md` | DAX queries for testing, validation, debugging |
| `relationships.md` | Star-schema patterns, relationship rules, ambiguity resolution |
| `known_issues.md` | Semantic-model-specific gotchas and fixes |
| `templates/` | Ready-to-use model.bim templates and deployment scripts |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context
2. Read the relevant knowledge file for the task
3. Reference `../../resource_ids.md` for workspace/model IDs
4. Reference `../../environment.md` for auth setup

## Key Insight (TL;DR)

> **Semantic Model = model.bim (TMSL) + definition.pbism `{"version": "1.0"}`**  
> Use Direct Lake mode (`defaultMode: "directLake"`) for Lakehouse-backed models.  
> Measure names are **case-sensitive and whitespace-sensitive** — always verify against model.bim.  
> definition.pbism accepts ONLY `{"version": "1.0"}` — any other property = API error.

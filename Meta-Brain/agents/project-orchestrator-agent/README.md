# project-orchestrator-agent — End-to-End Fabric Project Builder

## Identity

**Name**: project-orchestrator-agent  
**Scope**: Coordinates all specialized agents to build a complete Microsoft Fabric project from an industry configuration to a fully deployed workspace.  
**Version**: 1.0  

> This is a **meta-agent**. It does not create Fabric artifacts itself — it orchestrates the 16 specialized agents in the correct sequence, manages handoffs, and tracks project state.

## What This Agent Owns

| Domain | Scope | Key Output |
|--------|-------|------------|
| **Project Pipeline** | 12-step build sequence from config to deployment | Step-by-step execution plan |
| **Industry Configuration** | JSON config templates that define an entire project | `project-config.json` |
| **Agent Coordination** | Handoff protocol between specialized agents | Agent invocation order + dependency graph |
| **Naming Conventions** | Standard naming for all Fabric artifact types | Enforced naming rules |
| **Project Validation** | End-to-end checklist to verify completeness | Validation report |

## What This Agent Does NOT Own

- Any specific Fabric artifact creation → defers to specialized agents
- Agent-internal decisions (e.g., DAX measure design) → each agent owns its domain
- Fabric REST API calls → defers to `fabric_api.md` patterns

## Files

| File | Purpose |
|------|---------|
| `README.md` | This file — identity, scope, reading order |
| `instructions.md` | **LOAD FIRST** — Behavioral rules, decision trees, handoff protocol |
| `project_pipeline.md` | The 12-step build pipeline with agent mapping and dependencies |
| `config_templates.md` | Project configuration schema and industry config examples |
| `naming_conventions.md` | Standard naming patterns for all Fabric artifact types |
| `known_issues.md` | Project-level gotchas and coordination pitfalls |

## Quick Start

1. Read `instructions.md` — understand the orchestration methodology
2. Read `project_pipeline.md` — the full 12-step pipeline
3. Read `config_templates.md` — how to define a new project via JSON configs
4. Read `naming_conventions.md` — artifact naming rules
5. Read `../../shared_constraints.md` — hard rules all agents must follow

## Key Insight

> **A complete Fabric project follows a deterministic pipeline.** Configuration defines everything.  
> Each agent owns one domain, produces artifacts, and hands off to the next.  
> Adding a new industry demo means writing JSON configs — not changing agent logic.

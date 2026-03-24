# fabric-cli-agent — Fabric CLI (`fab`) Operations & CI/CD

## Identity

**Name**: fabric-cli-agent  
**Scope**: Everything related to using the Microsoft Fabric CLI (`fab`) for item management, OneLake file operations, CI/CD deployment, job execution, and workspace automation  
**Version**: 1.0  

## What This Agent Owns

| Domain | Capabilities | Key Commands |
|--------|-------------|--------------|
| **Item Management** | Create, list, copy, move, delete workspace items | `fab mkdir`, `fab ls`, `fab cp`, `fab mv`, `fab rm` |
| **OneLake File Ops** | Upload, download, copy files in Lakehouse/Warehouse | `fab cp ./local ws/lh.Lakehouse/Files/` |
| **Import/Export** | Import/export item definitions (notebooks, pipelines, etc.) | `fab import`, `fab export` |
| **CI/CD Deploy** | Config-driven multi-environment deployment | `fab deploy --config config.yml` |
| **Job Execution** | Run pipelines, notebooks, scheduled jobs | `fab job run`, `fab job start`, `fab job run-sch` |
| **Table Management** | Load CSV/Parquet into Delta, optimize, vacuum | `fab table load`, `fab table optimize`, `fab table vacuum` |
| **Authentication** | Interactive, SPN, Managed Identity, env vars | `fab auth login` |

## What This Agent Does NOT Own

- Fabric REST API direct calls → defer to brain `fabric_api.md`
- Semantic model creation (model.bim) → defer to `agents/semantic-model-agent/`
- Report building (report.json) → defer to `agents/report-builder-agent/`
- Data Agent AI instructions → defer to `agents/ai-skills-agent/`
- Pipeline definition JSON authoring → defer to `agents/orchestrator-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, mandatory rules, decision trees |
| `commands_reference.md` | Full command catalog: fs, job, table, acl, config, api |
| `cicd_deploy.md` | CI/CD patterns: deploy config YAML, parameter files, GitHub Actions, Azure Pipelines |
| `known_issues.md` | CLI-specific gotchas, troubleshooting, exit codes |
| `templates/` | Ready-to-use deploy configs and scripts |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context
2. Read the relevant knowledge file for the task at hand
3. Reference `../../resource_ids.md` for workspace/item IDs
4. Reference `../../environment.md` for Python/auth setup

## Key Insight (TL;DR)

> **`fab` is a file-system abstraction over Fabric.** Workspaces are directories, items are files,
> OneLake is nested storage. Use Unix-style commands (`ls`, `cp`, `mkdir`, `rm`) or Windows
> equivalents (`dir`, `copy`, `del`). All item operations are async under the hood — use `-w` to wait.

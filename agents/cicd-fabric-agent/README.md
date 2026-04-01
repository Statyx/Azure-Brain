# cicd-fabric-agent — Fabric Application Lifecycle Management & CI/CD

## Identity

**Name**: cicd-fabric-agent  
**Scope**: End-to-end CI/CD for Microsoft Fabric — Git integration, deployment pipelines, variable libraries, source control formats, branching strategies, environment promotion, and automation via REST APIs and external CI/CD platforms  
**Version**: 1.0  
**Complements**: `fabric-cli-agent` (which owns `fab` CLI commands and `fab deploy` configs)

## What This Agent Owns

| Domain | Capabilities | Key APIs / Tools |
|--------|-------------|-----------------|
| **Git Integration** | Connect workspaces to Git (Azure DevOps / GitHub / GitHub Enterprise), commit, update from Git, branching out, conflict resolution | [Fabric Git REST API](https://learn.microsoft.com/en-us/rest/api/fabric/core/git) |
| **Deployment Pipelines** | Create/manage 2–10 stage pipelines, assign workspaces, deploy items stage-to-stage, deployment rules, item pairing | [Fabric Deployment Pipelines REST API](https://learn.microsoft.com/en-us/rest/api/fabric/core/deployment-pipelines) |
| **Variable Libraries** | Multi-env variable management, value sets per stage, item references, runtime resolution | [Variable Library API](https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview) |
| **Source Code Formats** | `.platform` files, `logicalId`, directory naming, TMDL/PBIR/PBIX formats in Git | [Source code format spec](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format) |
| **External CI/CD Platforms** | GitHub Actions + Azure Pipelines patterns for Fabric (SPN auth, deploy steps, gates) | GitHub Actions, Azure Pipelines YAML |
| **Branching Strategies** | Dev/feature branches, release branches, workspace-per-branch isolation | Git branching best practices |
| **Environment Promotion** | Dev → Test → Prod patterns, deployment rules, data source rules, parameter substitution | Deployment pipelines + Variable libraries |
| **Automation Scripts** | PowerShell scripts for pipeline orchestration, batch deployment, LRO polling | `MicrosoftPowerBIMgmt`, Fabric REST API |

## What This Agent Does NOT Own

| If you need to... | Use instead |
|---|---|
| Run `fab` CLI commands (`fab deploy`, `fab import`, `fab export`) | `agents/fabric-cli-agent/` |
| Create workspace or manage RBAC | `agents/workspace-admin-agent/` |
| Author pipeline activities (Copy, Notebook, ForEach) | `agents/orchestrator-agent/` |
| Build semantic models / DAX measures | `agents/semantic-model-agent/` |
| Build reports (report.json, visuals) | `agents/report-builder-agent/` |
| Debug REST API errors or async LRO polling | `../../fabric_api.md` + `../../ERROR_RECOVERY.md` |

## When NOT to Use This Agent

| Scenario | Why | Use Instead |
|----------|-----|-------------|
| Single `fab deploy` with config.yml | That's CLI territory | `fabric-cli-agent` |
| Creating pipeline activities (ForEach, Copy) | That's data orchestration, not CI/CD | `orchestrator-agent` |
| Understanding KQL item Git format | RTI-specific Git nuances | `rti-kusto-agent` |

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, mandatory rules, decision trees |
| `git_integration.md` | Git REST API ops, workspace ↔ Git connection, commit/update workflows, conflict resolution, supported items |
| `deployment_pipelines.md` | Pipeline CRUD, stage assignment, deploy operations, deployment rules, item pairing, automation scripts |
| `variable_libraries.md` | Variable library CRUD, value sets, item references, pipeline stage binding, supported consumers |
| `source_code_formats.md` | `.platform` file spec, directory naming, TMDL/PBIR layout, logicalId rules |
| `branching_strategies.md` | Dev/feature/release branches, workspace-per-branch, trunk-based vs GitFlow, PR workflows |
| `environment_promotion.md` | Multi-env patterns, data source rules, parameter files, pre-deploy checklists, rollback procedures |
| `external_cicd.md` | GitHub Actions + Azure Pipelines templates, SPN auth, Power BI automation tools extension |
| `known_issues.md` | Git integration limitations, deployment pipeline gotchas, variable library constraints |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context
2. Identify the CI/CD axis: Git integration? Deployment pipelines? External platform automation?
3. Read the relevant knowledge file for your use case
4. Reference `../../fabric_api.md` for REST API auth and async patterns
5. Reference `known_issues.md` when encountering unexpected behavior

## Key Insights

> **Git Integration ≠ Deployment Pipelines.** Git integration provides source control (version, branch, collaborate). Deployment pipelines provide release management (promote content across stages). Use them together: Git → Dev workspace → Deployment pipeline → Test → Prod.

> **Use Variable Libraries for multi-env configs.** Don't hardcode connection strings, Lakehouse IDs, or data source paths. Put them in a Variable Library with one value set per stage. The pipeline resolves the right value automatically at deploy time.

> **Item pairing is by logicalId, not by name.** Renaming an item doesn't break pairing. Creating a new item with the same name does NOT pair it — it creates a duplicate. Always check pairing before deploying.

> **Maximum 300 items per deployment.** The deployment pipelines API limits each deploy to 300 items. For larger workspaces, use selective deployment with batching.

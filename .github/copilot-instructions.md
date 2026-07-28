# Copilot Instructions — Azure-Brain

## Role

This repository is a **multi-brain knowledge base** for building cloud data & AI solutions with GitHub Copilot.

Three brains live at the root:

- [`Fabric-Brain/`](../Fabric-Brain/) — 26 agents + 14 knowledge files for Microsoft Fabric (Lakehouse, Warehouse, Semantic Model, RTI, Data Agents, Ontology).
- [`Database-Brain/`](../Database-Brain/) — 4 active agents (of 22 catalogued) for Azure databases: Azure SQL, PostgreSQL, Cosmos DB, MySQL and cross-engine migration (Oracle → PostgreSQL track is live).
- [`Meta-Brain/`](../Meta-Brain/) — 5 cross-cutting agents + shared infrastructure (testing, PPTX, HTML diagrams, project orchestration, README authoring).

> **Agent folder layout differs per brain.** Fabric-Brain and Meta-Brain are flat
> (`agents/<agent>/`). Database-Brain is nested by domain (`agents/<NN-domain>/<agent>/`).
> Tooling that walks agents must handle both depths.

## How to Use

1. Read [`resource_ids.md`](../Fabric-Brain/resource_ids.md) (in Fabric-Brain) for your workspace and item IDs.
2. Read the relevant `agents/*/instructions.md` for your task (under the appropriate brain).
3. Follow the agent's rules — they exist because of real failures.

## Key Rules

- **Always use Legacy PBIX format** for Fabric reports (`report.json` with `sections[].visualContainers[]`). Never PBIR.
- **Read [`resource_ids.md`](../Fabric-Brain/resource_ids.md)** before any deployment.
- **Read [`known_issues.md`](../known_issues.md)** at umbrella root before debugging — most errors are already documented.
- **Follow [`agent_principles.md`](../agent_principles.md)** — config-driven, idempotent, async-first. Applies to every brain.
- **Never claim a capability is "verified"** in agent instructions unless a trace or test output
  proves it. A false "verified" makes downstream agents retry a path that cannot work.

## Setup for New Users

If `Fabric-Brain/resource_ids.md` doesn't exist:

1. Copy `Fabric-Brain/resource_ids.example.md` → `Fabric-Brain/resource_ids.md`
2. Copy `Fabric-Brain/environment.example.md` → `Fabric-Brain/environment.md`
3. Fill in your Azure subscription, Fabric workspace, and item IDs
4. See [`GETTING_STARTED.md`](../GETTING_STARTED.md) for the full setup guide

## Testing

When modifying agent instructions or shared patterns, validate from `Meta-Brain/`:

```bash
cd Meta-Brain
python -m pytest tests/ -v --tb=short
```

Tests parametrize over every brain's catalog, agent folders, instructions, internal links, Python syntax, and JSON parsing. `BRAINS` in `tests/conftest.py` is the single source of truth for which brains are covered.

## Adding a New Brain

When you add a new brain (e.g. `Databricks-Brain/`):

1. Create the folder + `README.md` + `agents/_catalog.yaml`
2. Add it to the `BRAINS` list in `Meta-Brain/tests/conftest.py` (covers **all** test modules)
3. Update the brain table in `README.md` **and** the brain list at the top of this file
4. Re-run umbrella tests

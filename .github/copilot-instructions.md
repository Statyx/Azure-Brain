# Copilot Instructions — Azure-Brain

## Role

This repository is a **multi-brain knowledge base** for building cloud data & AI solutions with GitHub Copilot.

Two brains live at the root:

- [`Fabric-Brain/`](../Fabric-Brain/) — 20 agents + 14 knowledge files for Microsoft Fabric (Lakehouse, Warehouse, Semantic Model, RTI, Data Agents, Ontology).
- [`Meta-Brain/`](../Meta-Brain/) — 5 cross-cutting agents + shared infrastructure (testing, PPTX, HTML diagrams, project orchestration, README authoring).

## How to Use

1. Read [`resource_ids.md`](../Fabric-Brain/resource_ids.md) (in Fabric-Brain) for your workspace and item IDs.
2. Read the relevant `agents/*/instructions.md` for your task (under the appropriate brain).
3. Follow the agent's rules — they exist because of real failures.

## Key Rules

- **Always use Legacy PBIX format** for Fabric reports (`report.json` with `sections[].visualContainers[]`). Never PBIR.
- **Read [`resource_ids.md`](../Fabric-Brain/resource_ids.md)** before any deployment.
- **Read [`known_issues.md`](../known_issues.md)** at umbrella root before debugging — most errors are already documented.
- **Follow [`agent_principles.md`](../agent_principles.md)** — config-driven, idempotent, async-first. Applies to every brain.

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

Tests parametrize over both brains' catalogs, agent folders, instructions, internal links, Python syntax, and JSON parsing.

## Adding a Third Brain

When you add a new brain (e.g. `Databricks-Brain/`):

1. Create the folder + `README.md` + `agents/_catalog.yaml`
2. Add it to `Meta-Brain/tests/test_smoke.py` `BRAINS = [...]` constant
3. Update `README.md` brain table at umbrella root
4. Re-run umbrella tests

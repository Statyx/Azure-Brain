# Copilot Instructions — Azure-Brain

## Role

This repository is a **multi-brain knowledge base** for building cloud data & AI solutions with GitHub Copilot.

Five brains live at the root:

- [`Fabric-Brain/`](../Fabric-Brain/) — 24 agents + 14 knowledge files for Microsoft Fabric (Lakehouse, Warehouse, Semantic Model, RTI, Data Agents, Ontology).
- [`Apps-Brain/`](../Apps-Brain/) — 3 active of 9 catalogued agents for the **application layer that consumes the platform brains**: runtime (Fabric App / external portal / Azure hosting), identity, embedding, in-app intelligence, frontend, operations. The cut is *"I am building an app"* — the runtime is a decision **inside** this brain. **Read its [non-goals](../Apps-Brain/agents/_catalog.yaml) before adding anything**: "app" is a magnet domain.
- [`Database-Brain/`](../Database-Brain/) — 4 active agents (of 22 catalogued) for Azure databases: Azure SQL, PostgreSQL, Cosmos DB, MySQL and cross-engine migration (Oracle → PostgreSQL track is live).
- [`Foundry-Brain/`](../Foundry-Brain/) — 7 active of 11 catalogued agents for Microsoft Foundry: agent service, tool catalog, knowledge (Foundry IQ), observability, governance (guardrails + evaluations), multi-agent orchestration, and the Fabric bridge (Fabric data agent + Fabric IQ). **Read [`Foundry-Brain/generation_map.md`](../Foundry-Brain/generation_map.md) first** — two agent generations ship side by side and the older one retires 2027-03-31.
- [`Meta-Brain/`](../Meta-Brain/) — 5 cross-cutting agents + shared infrastructure (testing, PPTX, HTML diagrams, project orchestration, README authoring).

> **Agent folder layout differs per brain.** Fabric-Brain, Meta-Brain, Foundry-Brain and
> Apps-Brain are flat (`agents/<agent>/`). Database-Brain is nested by domain
> (`agents/<NN-domain>/<agent>/`). Tooling that walks agents must handle both depths.

## How to Use

> **Entry point.** [`AGENTS.md`](../AGENTS.md) at the repo root is the routing table and full
> index of all 42 agents. It is auto-loaded by the GitHub Copilot CLI / Copilot app; this file
> is its VS Code counterpart. Both point at the same agent tree — read `AGENTS.md` to route,
> then read the agent's own `instructions.md`.

1. Read [`resource_ids.md`](../Fabric-Brain/resource_ids.md) (in Fabric-Brain) for your workspace and item IDs.
2. Use the routing table in [`AGENTS.md`](../AGENTS.md) to pick the agent.
3. Read the relevant `agents/*/instructions.md` for your task (under the appropriate brain),
   plus the companion files it names in its own load order.
4. Follow the agent's rules — they exist because of real failures.

> **Building a whole solution, not a single task?** Start from
> [`Meta-Brain/SCENARIOS.md`](../Meta-Brain/SCENARIOS.md) instead — the composed demo model
> (`preset = base + modules + axes`): 3 bases, 11 modules, named presets, and a documented
> custom path when none of them fits. Each step names an agent; you then rejoin the loop above.
> Track a run with [`run_sheet.example.md`](../Meta-Brain/run_sheet.example.md), and never fork
> a base to make a variant — add an axis, a module, or a preset.

## Key Rules

- **Report format is owned by [`report-builder-agent/instructions.md`](../Fabric-Brain/agents/report-builder-agent/instructions.md).**
  It is authoritative and supersedes any summary here — read it before emitting a Power BI report.
- **Read [`resource_ids.md`](../Fabric-Brain/resource_ids.md)** before any deployment.
- **Read [`known_issues.md`](../known_issues.md)** at umbrella root before debugging — most errors are already documented.
- **Follow [`agent_principles.md`](../agent_principles.md)** — config-driven, idempotent, async-first. Applies to every brain.
- **Write as if already public** — see [`PUBLIC_SAFETY.md`](../PUBLIC_SAFETY.md).
  The company is always **Zava**. GUIDs in docs and samples are visibly fake
  (`a0000000-0000-4000-a000-00000000000a`); never paste one from a real tenant.
  No hardcoded path containing your account name (`$PSScriptRoot`, `%USERPROFILE%`).
  Secrets are read at runtime. Real values go in a gitignored file with a committed
  `.example` twin. Verify with `python Meta-Brain/tools/scan_public_safety.py <repo>`.
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
pip install -r requirements.txt      # pytest + PyYAML, first run only
python -m pytest tests/ -v --tb=short
```

The same suite, plus `python Meta-Brain/tools/scan_public_safety.py .`, runs in CI
(`.github/workflows/no-client-leak.yml`) on every push and pull request.

Tests parametrize over every brain's catalog, agent folders, instructions, internal links (in **every** `.md` file), Python syntax, and JSON parsing. `BRAINS` in `tests/conftest.py` is the single source of truth for which brains are covered.

Two guards fail on things a reviewer cannot see: **`instructions.md` must stay under 20 KB** (the read tool truncates there — fix by moving trailing sections to a companion file, never by trimming), and **expiry clocks** in [`Meta-Brain/clocks.yaml`](../Meta-Brain/clocks.yaml) fail CI 30 days before a documented retirement date makes the prose wrong.

## Adding a New Brain

When you add a new brain (e.g. `Databricks-Brain/`):

1. Create the folder + `README.md` + `agents/_catalog.yaml`
2. Add it to the `BRAINS` list in `Meta-Brain/tests/conftest.py` (covers **all** test modules)
3. Update the brain table in `README.md`, the brain list at the top of this file, **and** the
   layout + agent index in [`AGENTS.md`](../AGENTS.md)
4. Re-run umbrella tests

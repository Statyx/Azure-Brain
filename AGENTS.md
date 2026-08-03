# AGENTS.md — Azure-Brain

**This repository is a knowledge base, not an application.** It contains no build, no runtime,
no entry point to execute. Its content is a set of *agent instruction files* that an AI coding
agent reads on demand to perform Microsoft Fabric / Azure data & AI work correctly.

Your job when working here: **route the request to the right agent folder, read that agent's
`instructions.md`, and follow it.** The instruction files are the source of truth. They exist
because of real production failures — do not improvise around them.

---

## The loop

1. **Identify the domain** of the request → use the [routing table](#routing--pick-the-agent).
2. **Read that agent's `instructions.md`** in full, *before* acting.
3. **Read the companion files it names.** Every `instructions.md` declares its own load order
   (e.g. *"Before any Lakehouse work, load this file plus `onelake_operations.md` and
   `spark_notebooks.md`"*). Follow it — do not guess which companions matter.
4. **Read `known_issues.md`** — the agent's own, then the umbrella one at the repo root.
   Most errors are already documented.
5. Apply the agent's mandatory rules. Hand off explicitly when you cross a boundary.

> If a request spans several agents, chain them and state each handoff:
> what was produced, which agent is next, which files/IDs are affected.

---

## Repository layout

```
Azure-Brain/                       ← umbrella (this repo)
├── AGENTS.md                      ← you are here — index + routing
├── agent_principles.md            ← mandatory operating principles
├── shared_constraints.md          ← 8 hard rules, all brains
├── known_issues.md                ← cross-cutting gotchas
├── ERROR_RECOVERY.md              ← decision trees by HTTP status
├── PUBLIC_SAFETY.md               ← Zava identity + publish-by-default rules
├── GETTING_STARTED.md             ← 15-min setup
├── Fabric-Brain/                  ← Microsoft Fabric      — 26 agents  (flat)
│   ├── agents/_catalog.yaml
│   └── agents/<agent>/instructions.md
├── Database-Brain/                ← Azure databases       — 4 active   (nested by domain)
│   ├── agents/_catalog.yaml
│   └── agents/<NN-domain>/<agent>/instructions.md
└── Meta-Brain/                    ← cross-cutting         — 5 agents   (flat)
    ├── agents/_catalog.yaml
    ├── agents/<agent>/instructions.md
    ├── mcp_registry.md            ← MCP server catalog
    └── tests/                     ← umbrella test suite
```

> ### ⚠ Folder depth differs per brain
> - **Fabric-Brain** and **Meta-Brain** are **flat**: `agents/<agent>/instructions.md`
> - **Database-Brain** is **nested by domain**: `agents/<NN-domain>/<agent>/instructions.md`
>
> Any tooling that walks agents must handle **both depths** — see the depth-aware
> `agent_dirs()` in `Meta-Brain/tests/conftest.py`.

Each agent folder also holds a `README.md` (human-facing summary), usually a `known_issues.md`,
and domain-specific companion files. Some hold scripts, Bicep templates or JSON knowledge trees.

---

## Routing — pick the agent

| The request is about… | Agent | Brain |
|---|---|---|
| Create a workspace, assign capacity, roles, CU budget | `workspace-admin-agent` | Fabric |
| Git integration, deployment pipelines, env promotion, Variable Libraries | `cicd-fabric-agent` | Fabric |
| `fab` CLI commands, job execution, CLI-driven deploy | `fabric-cli-agent` | Fabric |
| Something failed / job tracking / audit / capacity dashboards / Spark triage | `monitoring-agent` | Fabric |
| Task Flow (the visual workspace map) | `taskflow-agent` | Fabric |
| Custom Fabric **workload** (iFrame SDK, React, Workload Hub) | `extensibility-toolkit-agent` | Fabric |
| Data Pipelines, scheduling, Copy Jobs, notebook orchestration | `orchestrator-agent` | Fabric |
| Lakehouse, OneLake files, Delta tables, Spark, Shortcuts, medallion | `lakehouse-agent` | Fabric |
| Dataflow Gen2, Power Query M, connectors | `dataflow-agent` | Fabric |
| T-SQL Warehouse, `COPY INTO`, stored procs, time travel | `warehouse-agent` | Fabric |
| Star schema design, industry templates, synthetic data | `domain-modeler-agent` | Fabric |
| Semantic model, TMSL/`model.bim`, DAX measures, Direct Lake | `semantic-model-agent` | Fabric |
| Power BI report authoring & deployment | `report-builder-agent` | Fabric |
| Report layout validation *before* deploy (overlaps, sizing, fonts) | `pixel-design-agent` | Fabric |
| Create / publish a Fabric **Data Agent** (AI Skill) | `ai-skills-agent` | Fabric |
| Evaluate a Data Agent, DAX quality scoring, root-cause analysis | `ai-skills-analysis-agent` | Fabric |
| Eventhouse, KQL database, KQL dashboards | `rti-kusto-agent` | Fabric |
| EventStream ingestion, CDC, source→destination routing | `rti-eventstream-agent` | Fabric |
| Real-time **alerts / triggers** (Reflex, Teams/Email actions) | `data-activator-agent` | Fabric |
| Ontology — entity types, bindings, contextualizations, NL2Ontology | `ontology-agent` | Fabric |
| Graph Model, GQL, graph algorithms, `RefreshGraph`, NL2GQL | `graph-agent` | Fabric |
| BusinessObjects → Fabric migration | `migration-bo-agent` | Fabric |
| Databricks → Fabric migration | `migration-databricks-agent` | Fabric |
| Synapse → Fabric migration | `migration-synapse-agent` | Fabric |
| App **backend running inside Fabric** (Rayfin, Replit × Fabric) | `fabric-apps-agent` | Fabric |
| **External** portal embedding Fabric (FastAPI + Power BI/RTI embed) | `operations-portal-agent` | Fabric |
| Deploy Azure DB for PostgreSQL Flexible Server | `postgres-deploy-agent` | Database |
| Oracle 21c XE source VM on Azure | `oracle-source-vm-agent` | Database |
| Oracle → PostgreSQL via **Ora2Pg / DMS** (CLI, scriptable) | `oracle-to-postgres-migration-agent` | Database |
| Oracle → PostgreSQL via **VS Code PG ext. + Copilot App Modernization** (Java) | `oracle-to-postgres-copilot-modernization-agent` | Database |
| Write or run tests, quality gate before deploy | `testing-agent` | Meta |
| Generate a PowerPoint deck | `pptx-builder-agent` | Meta |
| HTML architecture diagram with Fabric/Azure icons | `architecture-design-agent` | Meta |
| README / repo presentation / badges | `project-presentation-agent` | Meta |
| Build a whole Fabric project end to end (12-step pipeline) | `project-orchestrator-agent` | Meta |

### Frequently confused pairs

| Boundary | Rule |
|---|---|
| `orchestrator-agent` (Fabric) vs `project-orchestrator-agent` (Meta) | Fabric one owns **Data Pipelines**; Meta one owns the **whole project pipeline** across agents |
| `cicd-fabric-agent` vs `fabric-cli-agent` | CI/CD owns Git + pipelines + stages; CLI owns `fab` commands + job execution |
| `cicd-fabric-agent` vs `workspace-admin-agent` | Admin **creates** pipelines (REST POST); CI/CD **manages** their stages |
| `ontology-agent` vs `graph-agent` | Ontology owns the **semantic layer**; Graph owns the **Graph Model item**, GQL, refresh |
| `data-activator-agent` vs `rti-eventstream-agent` | Activator owns rules/alerts/actions; EventStream owns the **ingestion topology** |
| `data-activator-agent` vs `monitoring-agent` | Activator = real-time **business** alerts; monitoring = **admin/capacity/audit** |
| `pixel-design-agent` vs `testing-agent` | Pixel = Fabric-report layout rules; testing = generic pytest framework |
| `fabric-apps-agent` vs `extensibility-toolkit-agent` | Apps = backends **inside** Fabric on OneLake; toolkit = custom **workloads** |
| `fabric-apps-agent` vs `operations-portal-agent` | Apps run **inside** Fabric; portal is an **external** app that embeds/proxies Fabric |
| Migration agents vs `lakehouse`/`orchestrator` | Migration agents own **source→Fabric translation**; the others own the actual item creation |

Full boundary notes live in each brain's `agents/_catalog.yaml`.

---

## Agent index

Paths are relative to the repo root. Read `instructions.md`; it names its own companion files.

### Fabric-Brain — 26 agents · `Fabric-Brain/agents/<agent>/instructions.md`

| Domain | Agent | Purpose |
|---|---|---|
| 01-platform | `workspace-admin-agent` | Workspace CRUD, capacity assignment, RBAC, Git integration |
| 01-platform | `cicd-fabric-agent` | Git integration, deployment pipelines, Variable Libraries, branching, promotion |
| 01-platform | `fabric-cli-agent` | `fab` CLI, item management, OneLake file ops, CI/CD deploy, job execution |
| 01-platform | `monitoring-agent` | Admin APIs, audit events, capacity monitoring, KQL ops dashboards, Spark/SQL triage |
| 01-platform | `taskflow-agent` | Task Flow visual templates, task-to-item mapping, JSON import/export |
| 01-platform | `extensibility-toolkit-agent` | Custom workloads, iFrame SDK, React components, Workload Hub publishing |
| 02-data-engineering | `orchestrator-agent` | Data Pipelines, scheduling, OneLake uploads, Copy Jobs, Spark notebooks |
| 02-data-engineering | `lakehouse-agent` | OneLake DFS, Delta tables, Spark, SQL Endpoint, Shortcuts, medallion |
| 02-data-engineering | `dataflow-agent` | Dataflow Gen2, Power Query M, 100+ sources, incremental refresh |
| 02-data-engineering | `warehouse-agent` | T-SQL Warehouse, `COPY INTO`, stored procedures, transactions, time travel |
| 02-data-engineering | `domain-modeler-agent` | Star schema design, KQL schemas, industry templates, synthetic data |
| 03-visualization | `semantic-model-agent` | `model.bim` (TMSL), DAX measures, relationships, Direct Lake, Prep for AI |
| 03-visualization | `report-builder-agent` | Power BI reports, visuals, themes, pages |
| 04-fabric-agent | `ai-skills-agent` | Data Agent creation, REST API, instructions, data bindings, few-shot examples |
| 04-fabric-agent | `ai-skills-analysis-agent` | Data Agent evaluation, DAX quality scoring, RCA classification |
| 05-real-time-intelligence | `rti-kusto-agent` | Eventhouse, KQL databases, KQL dashboards, Operations Agent |
| 05-real-time-intelligence | `rti-eventstream-agent` | EventStreams, real-time ingestion, CDC patterns, source routing |
| 05-real-time-intelligence | `data-activator-agent` | Reflex — real-time alerts/triggers, Teams/Email/Fabric item actions |
| 06-iq | `ontology-agent` | Entity types, bindings, relationships, contextualizations, NL2Ontology, MCP server |
| 06-iq | `graph-agent` | Graph Model definition, GQL (ISO/IEC 39075), algorithms, `RefreshGraph`, NL2GQL |
| 07-fabric-quality | `pixel-design-agent` | Pre-deployment report validation — layout bounds, overlaps, font sizing |
| 08-migration | `migration-bo-agent` | BusinessObjects → Fabric — 5-stage framework, 119 BO→DAX mappings |
| 08-migration | `migration-databricks-agent` | Databricks → Fabric — `dbutils`→`notebookutils`, UC→Lakehouse, DBFS→OneLake |
| 08-migration | `migration-synapse-agent` | Synapse → Fabric — phased, `mssparkutils`→`notebookutils`, SQL Pool→Warehouse |
| 09-app-platform | `fabric-apps-agent` | Fabric Apps (preview) via Rayfin — scaffold/model/deploy backends; Replit × Fabric |
| 10-experience | `operations-portal-agent` | External ops portal (FastAPI + static) — Data Agent proxy, Power BI + RTI embed |

### Database-Brain — 4 active · `Database-Brain/agents/<NN-domain>/<agent>/instructions.md`

> 22 agents are catalogued; only `status: active` ones exist on disk. See
> `Database-Brain/agents/_catalog.yaml` for the planned roadmap.

| Domain folder | Agent | Purpose |
|---|---|---|
| `02-postgres` | `postgres-deploy-agent` | Flexible Server deployment, networking, HA zones, extensions allow-list |
| `03-oracle-to-postgres` | `oracle-source-vm-agent` | Oracle 21c XE on Azure VM (Oracle Linux 8), sample schemas, listener 1521 |
| `03-oracle-to-postgres` | `oracle-to-postgres-migration-agent` | Ora2Pg assessment + schema conversion + data export, Azure DMS cutover |
| `03-oracle-to-postgres` | `oracle-to-postgres-copilot-modernization-agent` | PG VS Code extension + Copilot App Modernization for Java (SQL + Managed Identity) |

### Meta-Brain — 5 agents · `Meta-Brain/agents/<agent>/instructions.md`

| Domain | Agent | Purpose |
|---|---|---|
| meta-quality | `testing-agent` | 3-tier test taxonomy (smoke/integration/regression), visual validator, pytest scaffolding |
| meta-presentation | `pptx-builder-agent` | PowerPoint generator — 5-phase pipeline, helper functions, quality gates |
| meta-presentation | `architecture-design-agent` | HTML architecture diagrams with base64 SVG icons (Fabric + Azure) |
| meta-presentation | `project-presentation-agent` | GitHub repo best practices — README authoring, badges, repo structure |
| meta-orchestration | `project-orchestrator-agent` | End-to-end 12-step project builder, industry configs, agent coordination |

---

## Key rules

These apply everywhere. The per-agent `instructions.md` may add stricter rules — and **wins on
its own domain**.

1. **Read before write.** Never assume file contents or artifact state. Load the config, the
   existing artifact, or the API response first.
2. **Config-driven.** Domain/industry behaviour comes from configuration files, never hard-coded.
3. **Idempotent.** Re-running any generation or deployment step with the same input produces
   identical output. Never append — replace or skip-if-exists.
4. **Async-first.** Every Fabric REST creation/execution call returns HTTP 202: use
   `allow_redirects=False`, poll `x-ms-operation-id`, retry with exponential backoff
   (3s × 2^attempt, max 2 retries).
5. **One owner per domain.** Any agent may *read* any artifact; only the owner *modifies* it.
6. **Validate after every change.** Read the artifact back, or check the API response.
7. **Handoff protocol.** State what was produced, name the next agent, list affected files/IDs.
8. **Read `resource_ids.md` before any deployment** (`Fabric-Brain/resource_ids.md`).
9. **Never claim a capability is "verified"** in an instruction file unless a trace or test output
   proves it. A false "verified" makes downstream agents retry a path that cannot work.
10. **Follow `agent_principles.md`** — plan first, verify before done, capture lessons in
    `known_issues.md` after any correction.
11. **Write as if already public.** The company is always **Zava**; GUIDs in docs and samples are
    visibly fake (`a0000000-0000-4000-a000-00000000000a`); no path contains your account name;
    secrets are read at runtime; real values live in a gitignored file with a committed
    `.example` twin. See **`PUBLIC_SAFETY.md`**, verify with
    `python Meta-Brain/tools/scan_public_safety.py <repo>`.

Conventions: Python 3.12+ with `pathlib` and type hints · UTF-8 everywhere, **no BOM**
(`[System.IO.File]::WriteAllText()` in PowerShell, never `Out-File` for JSON) · conventional
commits (`feat(energy):`, `fix(core):`, `docs(brain):`).

> **Report format:** `report-builder-agent/instructions.md` is authoritative on Power BI report
> format and supersedes any summary elsewhere in this repo. Read it before emitting a report.

---

## Setup

If `Fabric-Brain/resource_ids.md` is missing, the brain has no environment bound to it:

```bash
cp Fabric-Brain/resource_ids.example.md Fabric-Brain/resource_ids.md
cp Fabric-Brain/environment.example.md  Fabric-Brain/environment.md
```

Then fill in the Azure subscription, Fabric workspace and item IDs.
Both files are gitignored. Full walkthrough: `GETTING_STARTED.md`.

MCP servers available to this workspace are catalogued in `Meta-Brain/mcp_registry.md`.

---

## Using this brain from another working directory

Azure-Brain is designed to be consumed from other repositories — it holds the knowledge, the
other repo holds the project.

- Keep Azure-Brain checked out alongside your project, and point the agent at the relevant
  `instructions.md` by path. Nothing here needs to be installed or copied.
- **Do not fork or duplicate `instructions.md` into the consuming repo.** The brain is the single
  source of truth; a copy silently goes stale and reintroduces the failures these files prevent.
- In the consuming repo, reference the brain from its own `AGENTS.md` (or
  `.github/copilot-instructions.md`) — one line naming the brain path and the agents it uses.
- Corrections and lessons learned go **back into the brain** (`known_issues.md` of the relevant
  agent), not into the consuming repo.

---

## Testing

Any change to agent instructions, catalogs or shared docs must keep the umbrella suite green:

```bash
cd Meta-Brain
pip install -r requirements.txt      # pytest + PyYAML, first run only
python -m pytest tests/ -v --tb=short
```

CI (`.github/workflows/no-client-leak.yml`, job **CI / pytest**) runs exactly this on
every push and PR, alongside the public-safety scanner
(`python Meta-Brain/tools/scan_public_safety.py .`, job **CI / No client leak**).
Run both locally before pushing — the scanner is what stops a customer name or a
real endpoint reaching a public repo, and it only works if something runs it.

It validates, for every brain in `BRAINS` (`Meta-Brain/tests/conftest.py` — single source of
truth): catalogs parse and match disk, every agent folder has a non-trivial `instructions.md`,
internal markdown links resolve, Python compiles, JSON parses, root markdown is non-empty.

> **The suite is green on a fresh clone — it must stay that way.** `test_links_resolve` used to
> fail for the four agents linking to `Fabric-Brain/resource_ids.md`, because that file is
> gitignored (it holds tenant / subscription GUIDs) and ships only as `resource_ids.example.md`.
> Those four failures were expected, permanent, and therefore indistinguishable from a real
> regression — a suite that is never green gives no signal. Fixed 2026-07-31: a link may resolve
> to a missing file **only** when that filename is listed in `.gitignore` *and* a committed
> `<name>.example.md` sits beside it. Both conditions are required, and
> `TestLocalOnlyLinkExemption` locks that — a merely missing file, or a gitignored one with no
> template, is still reported broken. If you see failures here now, they are real.

---

## Adding a new brain

1. Create the folder + `README.md` + `agents/_catalog.yaml`.
2. Add it to `BRAINS` in `Meta-Brain/tests/conftest.py` (covers **all** test modules).
3. Update the brain table in `README.md`, the brain list in
   `.github/copilot-instructions.md`, and the layout + index in this file.
4. Re-run the umbrella tests.

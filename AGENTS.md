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

### Building a whole solution, not a single task

If the request is *"build me a demo / a project"* rather than *"do this one thing"*, start from
[`Meta-Brain/SCENARIOS.md`](Meta-Brain/SCENARIOS.md) **before** the routing table. It is the
composed model of every demo this brain knows how to build:

```
preset  =  base  +  modules          … with the axes applied
```

- **3 bases** — `B1` Batch BI · `B2` Real-Time · `B3` Migration. Each is a spine of steps
  (agent + task + gate) ending in a documented **exit state**.
- **11 modules** — `M-ONTO`, `M-DL`, `M-AGENT`, `M-SUPER`, `M-OPS`, `M-ALERT`, `M-CICD`, `M-FLOW`,
  `M-PORTAL`, `M-TEST`, `M-MON` — each attaches to an exit state.
- **Presets** — named combinations already run end to end (`bi-dashboard`, `smart-factory`,
  `digital-twin`…). No preset fits → §2.5 builds a custom one from the same pieces.

Every step still names an agent: resolve it here, then follow the loop above. The scenario says
*what and in which order*; the agent's `instructions.md` says *how* and wins on its domain.

**Never fork a base or a preset to make a variant** — add an axis value, a module, or a preset
line. Same rule as the instruction files: a copy goes stale.

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
├── Fabric-Brain/                  ← Microsoft Fabric      — 24 agents  (flat)
│   ├── agents/_catalog.yaml
│   └── agents/<agent>/instructions.md
├── Apps-Brain/                    ← Applications          — 3 active / 9 catalogued (flat)
│   ├── agents/_catalog.yaml       ← ⚠ non-goals live here — "app" is a magnet domain
│   └── agents/<agent>/instructions.md
├── Database-Brain/                ← Azure databases       — 4 active   (nested by domain)
│   ├── agents/_catalog.yaml
│   └── agents/<NN-domain>/<agent>/instructions.md
├── Foundry-Brain/                 ← Microsoft Foundry     — 7 active / 11 catalogued (flat)
│   ├── generation_map.md          ← ⚠ classic vs current + 3 retirement clocks — read first
│   ├── orchestration_patterns.md  ← supervisor pattern: A2A vs Toolbox vs Workflows
│   ├── tenant_proofs.md           ← ✅ what was executed against a real tenant (vs observed)
│   ├── agents/_catalog.yaml
│   └── agents/<agent>/instructions.md
└── Meta-Brain/                    ← cross-cutting         — 5 agents   (flat)
    ├── agents/_catalog.yaml
    ├── agents/<agent>/instructions.md
    ├── SCENARIOS.md               ← the demo model: presets = base + modules + axes
    ├── run_sheet.example.md       ← copy per demo into the demo repo as RUN.md
    ├── mcp_registry.md            ← MCP server catalog
    ├── clocks.yaml                ← expiry clocks — CI fails 30 days before a date comes due
    └── tests/                     ← umbrella test suite
```

> ### ⚠ Folder depth differs per brain
> - **Fabric-Brain**, **Meta-Brain**, **Foundry-Brain** and **Apps-Brain** are **flat**: `agents/<agent>/instructions.md`
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
| App **backend running inside Fabric** (Rayfin, Replit × Fabric) | `fabric-apps-agent` | **Apps** |
| **External** portal embedding Fabric (FastAPI + Power BI/RTI embed) | `operations-portal-agent` | **Apps** |
| App **UI**: design system/tokens, `src/` layout, navigation, personas, seed-vs-live mode | `app-frontend-agent` | **Apps** |
| Deploy Azure DB for PostgreSQL Flexible Server | `postgres-deploy-agent` | Database |
| Oracle 21c XE source VM on Azure | `oracle-source-vm-agent` | Database |
| Oracle → PostgreSQL via **Ora2Pg / DMS** (CLI, scriptable) | `oracle-to-postgres-migration-agent` | Database |
| Oracle → PostgreSQL via **VS Code PG ext. + Copilot App Modernization** (Java) | `oracle-to-postgres-copilot-modernization-agent` | Database |
| Foundry resource / project, model deployments, quota | `foundry-project-agent` 🟡 | Foundry |
| Create a **Foundry** agent, its instructions, tools, threads | `foundry-agent-service-agent` 🟢 | Foundry |
| **Supervisor / orchestrator over several Foundry agents** | `foundry-orchestration-agent` 🟢 | Foundry |
| Call a **Fabric** Data Agent *from* Foundry (Fabric tool, Fabric IQ) | `foundry-fabric-bridge-agent` 🟢 | Foundry |
| Ground a Foundry agent in enterprise data (**Foundry IQ** knowledge base, sources) | `foundry-knowledge-agent` 🟢 | Foundry |
| Attach a **tool** to a Foundry agent — MCP, OpenAPI, function calling, approvals | `foundry-tools-agent` 🟢 | Foundry |
| **Why did it do that?** — Foundry traces, App Insights, reading the execution path | `foundry-observability-agent` 🟢 | Foundry |
| Guardrails / content safety / **evaluating** a Foundry agent | `foundry-governance-agent` 🟢 | Foundry |
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
| `fabric-apps-agent` vs `extensibility-toolkit-agent` | Both build UI-ish things, different consumer: `fabric-apps` (Apps) is **our application**; `extensibility-toolkit` (Fabric) is a **workload extending the Fabric portal itself**, published to the Workload Hub |
| `fabric-apps-agent` vs `operations-portal-agent` | Same brain, opposite runtime: apps run **inside** Fabric on OneLake; portal is an **external** app that embeds/proxies Fabric |
| `app-frontend-agent` vs `pixel-design-agent` | Both are layout, different artifact: frontend = a **web app** surface (React/Tailwind, routes, tokens); pixel-design = a **Power BI report** canvas. A report embedded in an app stays pixel-design's artifact |
| `app-frontend-agent` vs `fabric-apps-agent` | Same app, two halves: frontend owns what the user sees and how `src/` is layered; fabric-apps owns Rayfin, the data model and the deploy |
| Apps-Brain vs Fabric-Brain / Foundry-Brain | Apps **consumes** — it embeds a report, proxies a Data Agent, calls a Foundry endpoint. It never mutates their artifacts; any change is a handoff to the owning agent |
| Migration agents vs `lakehouse`/`orchestrator` | Migration agents own **source→Fabric translation**; the others own the actual item creation |
| `foundry-orchestration-agent` (Foundry) vs `project-orchestrator-agent` (Meta) | Foundry one orchestrates **agents at runtime**; Meta one orchestrates the **build** of a project across brains |
| `foundry-fabric-bridge-agent` (Foundry) vs `ai-skills-agent` (Fabric) | Fabric **creates/publishes** the Data Agent; Foundry **consumes** it as a tool and never mutates it |
| `foundry-governance-agent` vs `foundry-observability-agent` | Governance = *may this happen?* (guardrails) and *was it good?* (evaluations); observability = *what actually happened?* (traces). The multi-agent hop is seen only by traces |

Full boundary notes live in each brain's `agents/_catalog.yaml`.

---

## Agent index

Paths are relative to the repo root. Read `instructions.md`; it names its own companion files.

### Fabric-Brain — 24 agents · `Fabric-Brain/agents/<agent>/instructions.md`

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

### Apps-Brain — 3 active / 9 catalogued · `Apps-Brain/agents/<agent>/instructions.md`

> **The cut:** the question is *"I am building an application"*. The **runtime** — Fabric App item,
> external portal, Azure-hosted — is the first routing decision **inside** this brain, not a brain
> boundary. That is why `fabric-apps-agent` lives here: a Fabric App item is a hosting choice for
> an app, the same way Container Apps is.
>
> ⚠️ **"App" is a magnet domain.** The **non-goals** in
> [`Apps-Brain/agents/_catalog.yaml`](Apps-Brain/agents/_catalog.yaml) are load-bearing — data
> logic → Fabric-Brain, Fabric **workloads** → `extensibility-toolkit-agent`, agent **definition**
> → Foundry-Brain, DB engine → Database-Brain. Rule of thumb: if removing the UI/API surface makes
> the problem disappear, it belongs here; if the problem survives without any app, it does not.

| Domain | Agent | Purpose |
|---|---|---|
| 01-runtime | `fabric-apps-agent` | Fabric Apps (preview) via Rayfin — scaffold/model/deploy backends, data in OneLake; Replit × Fabric |
| 01-runtime | `operations-portal-agent` | External ops portal (FastAPI + static) — Data Agent proxy, Power BI + RTI embed, live SVG views |
| 01-runtime | `app-hosting-azure-agent` 🟡 | Container Apps / Static Web Apps / App Service — choosing, ingress, scale-to-zero, revisions |
| 02-identity | `app-identity-agent` 🟡 | App vs delegated vs managed identity, Entra registration + consent, OBO, token cache, passthrough |
| 03-embedding | `app-embedding-agent` 🟡 | Power BI app-owns-data + RLS, Fabric Embed for RTI tiles, direct Kusto, CSP/CORS, silent renewal |
| 04-intelligence | `app-intelligence-agent` 🟡 | Chat proxy to a Fabric Data Agent **or** a Foundry agent — threads, streaming, citations, MCP in-app |
| 05-frontend | `app-frontend-agent` 🟢 | Dual-mode (seed vs live) architecture, four-layer `src/` split, design system as a token file, single route+nav manifest, personas, accessibility |
| 06-operations | `app-observability-agent` 🟡 | App Insights front-to-back, correlating a user action through the proxy to the platform call |
| 06-operations | `app-delivery-agent` 🟡 | Build/container pipelines, environment promotion, secrets at runtime, IaC for the app's resources |

### Database-Brain — 4 active · `Database-Brain/agents/<NN-domain>/<agent>/instructions.md`

> 22 agents are catalogued; only `status: active` ones exist on disk. See
> `Database-Brain/agents/_catalog.yaml` for the planned roadmap.

| Domain folder | Agent | Purpose |
|---|---|---|
| `02-postgres` | `postgres-deploy-agent` | Flexible Server deployment, networking, HA zones, extensions allow-list |
| `03-oracle-to-postgres` | `oracle-source-vm-agent` | Oracle 21c XE on Azure VM (Oracle Linux 8), sample schemas, listener 1521 |
| `03-oracle-to-postgres` | `oracle-to-postgres-migration-agent` | Ora2Pg assessment + schema conversion + data export, Azure DMS cutover |
| `03-oracle-to-postgres` | `oracle-to-postgres-copilot-modernization-agent` | PG VS Code extension + Copilot App Modernization for Java (SQL + Managed Identity) |

### Foundry-Brain — 7 active / 11 catalogued · `Foundry-Brain/agents/<agent>/instructions.md`

> ⚠️ **Read [`Foundry-Brain/generation_map.md`](Foundry-Brain/generation_map.md) and
> [`Foundry-Brain/orchestration_patterns.md`](Foundry-Brain/orchestration_patterns.md) before
> any Foundry work.** Two agent generations ship side by side —
> `azure/foundry-classic/agents/*` (deprecated, retires **2027-03-31**) and
> `azure/foundry/agents/*` (current, GA) — plus a third clock: portal **Workflows** retire
> **2026-12-01** despite living on the current tree. The classic `agent.as_tool` /
> **Connected Agents** pattern **does not exist** in the new service: a supervisor attaches
> sub-agents via the **A2A tool** (preview — and now [proven working on one
> tenant](Foundry-Brain/tenant_proofs.md)) and capabilities via a **Toolbox** (GA).
>
> Seven agents exist on disk. Their **behavioural** content is grounded in two complete
> multi-agent systems observed in Microsoft training labs
> (`Foundry-Brain/reference_workflow.md`, `Foundry-Brain/reference_foundry_iq.md`); the
> **SDK shapes** are tenant-verified by the second lab's working `agents.py`. A further set of
> claims — the A2A hop, the four-protocol chain and the SDK 2.4.0 introspection — was executed
> against a real tenant and is recorded in
> [`Foundry-Brain/tenant_proofs.md`](Foundry-Brain/tenant_proofs.md), with an explicit list of
> what those runs do **not** prove. Everything else is `status: planned`.
> See `Foundry-Brain/agents/_catalog.yaml`.

| Domain | Agent | Purpose |
|---|---|---|
| 01-platform | `foundry-project-agent` | Resource + project, RBAC, managed identity, connections, networking |
| 01-platform | `foundry-model-catalog-agent` | Deployments, TPM quota, model routing, cost/latency trade-offs |
| 02-agent-service | `foundry-agent-service-agent` | **The five agent roles**, prompt-as-interface rules, tool attachment + approval posture, versioning, Save vs Publish |
| 02-agent-service | `foundry-tools-agent` | Function calling, OpenAPI, MCP, code interpreter, file search; prompt/tool-set/approval control layers |
| 03-orchestration | `foundry-orchestration-agent` | Supervisor patterns, connected agents, routing, anti-loop guardrails |
| 03-orchestration | `foundry-agent-framework-agent` | Microsoft Agent Framework, workflows, durable execution |
| 04-knowledge-grounding | `foundry-fabric-bridge-agent` | Fabric data agent tool + Fabric IQ, identity passthrough → hands off to `ai-skills-agent` |
| 04-knowledge-grounding | `foundry-knowledge-agent` | Foundry IQ knowledge bases — indexed vs federated sources, cross-service RBAC, MCP consumption |
| 05-quality | `foundry-observability-agent` | Tracing, Application Insights, **the trace-reading playbook** — what a trace settles and what it cannot |
| 06-governance | `foundry-governance-agent` | Guardrails (policy on live traffic) + evaluations (scoring a sample) — per-role evaluator choice, the seam neither covers |
| 06-governance | `foundry-deploy-agent` | Bicep / azd, environment promotion, CI/CD |

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

# Foundry work only:
cp Foundry-Brain/resource_ids.example.md Foundry-Brain/resource_ids.md
cp Foundry-Brain/environment.example.md  Foundry-Brain/environment.md

# Database work only:
cp Database-Brain/resource_ids.example.md Database-Brain/resource_ids.md
cp Database-Brain/environment.example.md  Database-Brain/environment.md
```

Then fill in the Azure subscription, Fabric workspace and item IDs.
Apps-Brain and Meta-Brain need no local config.
All copies are gitignored. Full walkthrough: `GETTING_STARTED.md`.

MCP servers available to this workspace are catalogued in `Meta-Brain/mcp_registry.md`.

---

## Using this brain from another working directory

Azure-Brain is designed to be consumed from other repositories — it holds the knowledge, the
other repo holds the project.

- Keep Azure-Brain checked out alongside your project, and point the agent at the relevant
  `instructions.md` by path. Nothing here needs to be installed or copied.
- **Pin a tag, not `main`.** This brain drives agent behaviour: an unpinned reference means the
  consuming project's agents change the day this repo does.
  `git clone --branch v1.0.0 https://github.com/Statyx/Azure-Brain.git ../Azure-Brain`
- **Do not fork or duplicate `instructions.md` into the consuming repo.** The brain is the single
  source of truth; a copy silently goes stale and reintroduces the failures these files prevent.
- In the consuming repo, reference the brain from its own `AGENTS.md` (or
  `.github/copilot-instructions.md`) — one line naming the brain path and the agents it uses.
  A ready-to-paste block is in [`README.md`](README.md#-use-it-from-another-repo).
- **Take only what you need.** 38 of the 42 agents depend on no umbrella file, and each technology
  brain resolves 83–89 % of its links internally, so a single agent or a single brain lifts out
  cleanly. `Apps-Brain` is the exception (16 % internal — it consumes the others by design).
- Corrections and lessons learned go **back into the brain** (`known_issues.md` of the relevant
  agent), not into the consuming repo — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

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
internal markdown links resolve **in every `.md` file**, Python compiles, JSON parses, root
markdown is non-empty.

Two guards are worth knowing about because they fail on things no reviewer would catch:

- **`instructions.md` must stay under 20 KB.** The `view` tool truncates there, so a longer file
  is *silently* cut and the agent acts on half a framework. The fix is never to trim content —
  move the trailing sections into a companion file and name it in the load order at the top.
- **Expiry clocks.** `Meta-Brain/clocks.yaml` registers dates the brain states as future facts
  (a retirement, an end-of-support). CI fails once a clock is within 30 days, so the prose gets
  rewritten *before* it turns false rather than after someone follows it. The registry stores no
  file list — the test scans the repo live and names the files in the failure.

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

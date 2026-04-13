# Github Brain

**25 AI agents + 20 knowledge files for building Microsoft Fabric solutions — zero re-learning, zero repeated mistakes.**

![Agents](https://img.shields.io/badge/agents-25-blue?style=for-the-badge&logo=github)
![Domains](https://img.shields.io/badge/domains-8-orange?style=for-the-badge)
![Knowledge](https://img.shields.io/badge/knowledge_files-20-green?style=for-the-badge)
![Fabric](https://img.shields.io/badge/Microsoft_Fabric-REST_API-purple?style=for-the-badge&logo=microsoft)

[Quick Start](#-quick-start) · [Pick Your Scenario](#-pick-your-scenario) · [Agents](#-agents-18) · [Knowledge Files](#-knowledge-files) · [Architecture](#-architecture) · [Docs](#-documentation)

---

## ⚡ Quick Start

Auto-loaded via `.github/copilot-instructions.md` — no manual setup.

```yaml
# In your project's .github/copilot-instructions.md:
# 1. Read ../Github_Brain/README.md
# 2. Read the relevant agent instructions.md for your task
# 3. Start working
```

> **Key Rule** — The Fabric REST API accepts two report formats. Only one renders visuals.
> Always use the **Legacy PBIX format** (`report.json` with `sections[].visualContainers[]`). Never PBIR.

---

## 🎯 Pick Your Scenario

| I want to... | Template | Time | Start here |
|---|---|---|---|
| **Build a BI dashboard** (Lakehouse → Model → Report) | Standard BI Demo | 2–3h | [TEMPLATES.md](TEMPLATES.md#template-1) |
| **Set up real-time analytics** (EventStream → Eventhouse → KQL) | Real-Time IoT | 3–4h | [TEMPLATES.md](TEMPLATES.md#template-2) |
| **Build a full Smart Factory demo** (Batch + RT + Ontology + AI) | Smart Factory | 4–6h | [TEMPLATES.md](TEMPLATES.md#template-3) |
| **Add AI Q&A to existing data** (Data Agent + Instructions) | Data Agent Add-On | 45min | [TEMPLATES.md](TEMPLATES.md#template-4) |
| **Migrate from SAP BusinessObjects** (Assessment → Migration Waves) | BO Migration | 4–6w | [migration-bo-agent](agents/migration-bo-agent/README.md) |

---

## 🤖 Agents (25) — 7 Domains

> Full catalog with boundary clarifications: [`agents/_catalog.yaml`](agents/_catalog.yaml)

### 🔧 Platform & Operations (6)

| Agent | What it does |
|---|---|
| [workspace-admin](agents/workspace-admin-agent/) | Workspace CRUD, capacity, RBAC, Git integration |
| [cicd-fabric](agents/cicd-fabric-agent/) | Git integration, deployment pipelines, variable libraries, branching, environment promotion |
| [fabric-cli](agents/fabric-cli-agent/) | `fab` CLI, item management, CI/CD deploy |
| [monitoring](agents/monitoring-agent/) | Admin APIs, audit events, KQL dashboards |
| [taskflow](agents/taskflow-agent/) | Task Flow design, templates, JSON import/export |
| [extensibility-toolkit](agents/extensibility-toolkit-agent/) | Custom workloads, iFrame SDK, Workload Hub |

### 🗄️ Data Engineering (5)

| Agent | What it does |
|---|---|
| [orchestrator](agents/orchestrator-agent/) | Pipelines, ingestion, notebooks, copy jobs |
| [lakehouse](agents/lakehouse-agent/) | OneLake DFS, Delta tables, Spark, medallion architecture |
| [dataflow](agents/dataflow-agent/) | Dataflow Gen2, Power Query M, ETL |
| [warehouse](agents/warehouse-agent/) | Fabric Warehouse, T-SQL, CTAS, COPY INTO |
| [domain-modeler](agents/domain-modeler-agent/) | Star schema design, industry templates, synthetic data gen |

### 📊 Visualization (2)

| Agent | What it does |
|---|---|
| [semantic-model](agents/semantic-model-agent/) | DAX measures, relationships, model.bim, Direct Lake |
| [report-builder](agents/report-builder-agent/) | Power BI reports, visuals, themes (Legacy PBIX only) |

### 🤖 Fabric Agent (2)

| Agent | What it does |
|---|---|
| [ai-skills](agents/ai-skills-agent/) | Fabric Data Agents — creation, instructions, few-shot examples |
| [ai-skills-analysis](agents/ai-skills-analysis-agent/) | Data Agent evaluation, DAX quality scoring, RCA |

### ⚡ Real-Time Intelligence (2)

| Agent | What it does |
|---|---|
| [rti-kusto](agents/rti-kusto-agent/) | Eventhouse, KQL database, dashboards |
| [rti-eventstream](agents/rti-eventstream-agent/) | EventStreams, EventHub SDK, CDC patterns |

### 🧠 IQ — Intelligence (1)

| Agent | What it does |
|---|---|
| [ontology](agents/ontology-agent/) | Entity types, graph model, GQL queries, contextualizations |

### ✅ Quality (2)

| Agent | What it does |
|---|---|
| [testing](agents/testing-agent/) | 3-tier test taxonomy, visual validator, pytest scaffolding |
| [pixel-design](agents/pixel-design-agent/) | Pre-deployment report validation — layout, overlaps, fonts |

### 🏗️ Meta (5)

| Agent | What it does |
|---|---|
| [project-orchestrator](agents/project-orchestrator-agent/) | End-to-end project builder — 12-step config-driven pipeline coordinating all agents |
| [architecture-design](agents/architecture-design-agent/) | HTML architecture diagrams with base64 FabricToolset SVG icons |
| [pptx-builder](agents/pptx-builder-agent/) | PowerPoint architecture diagrams — 5-phase pipeline |
| [project-presentation](agents/project-presentation-agent/) | README best practices, repo structure, badges, visuals, community files |
| [migration-bo](agents/migration-bo-agent/) | BusinessObjects migration to Fabric |

> Every agent has `instructions.md` (system prompt) + domain-specific files. The agent README lists the reading order.

---

## 📚 Knowledge Files

<details>
<summary><strong>Core — Read these first</strong></summary>

| File | Purpose |
|---|---|
| [`agent_principles.md`](agent_principles.md) | **Mandatory** — Operating principles, task management, quality standards |
| [`shared_constraints.md`](shared_constraints.md) | 8 hard rules all agents follow (config-driven, idempotent, async-first) |
| [`fabric_api.md`](fabric_api.md) | REST API patterns, auth, async operations, LRO polling |
| [`known_issues.md`](known_issues.md) | Gotchas & workarounds — what works vs what doesn't. See also [ERROR_RECOVERY.md](ERROR_RECOVERY.md) |
| [`environment.md`](environment.md) | Python, Azure CLI, PowerShell setup |
| [`resource_ids.md`](resource_ids.md) | GUIDs, endpoints, connection strings |

</details>

<details>
<summary><strong>Reference — Domain-specific patterns</strong></summary>

| File | Purpose |
|---|---|
| [`report_format.md`](report_format.md) | **Critical** — Legacy PBIX format spec (the only format that renders) |
| [`visual_builders.md`](visual_builders.md) | Visual config, expression language, vcObjects |
| [`semantic_model.md`](semantic_model.md) | model.bim deployment, Direct Lake, TMDL |
| [`onelake.md`](onelake.md) | DFS API 3-step upload protocol |
| [`mcp_powerbi.md`](mcp_powerbi.md) | MCP Power BI — 21 tools for semantic model CRUD, DAX, Prep for AI |
| [`mcp_registry.md`](mcp_registry.md) | **MCP Server Registry** — central catalog of all 7 MCP servers (Azure, Fabric, Power BI, Kusto, Engine, GitKraken, Pylance) |
| [`item_definitions.md`](item_definitions.md) | Definition envelope spec for all 20+ Fabric item types |
| [`warehouse_patterns.md`](warehouse_patterns.md) | SQL DW authoring — CTAS, COPY INTO, transactions, time travel |
| [`spark_patterns.md`](spark_patterns.md) | Spark/Lakehouse authoring — enableSchemas, notebooks, pools |
| [`mirrored_databases.md`](mirrored_databases.md) | Mirrored DB patterns — CDC sync, Lakehouse vs Mirror decision |

</details>

<details>
<summary><strong>Operations — Workflows, templates, error recovery</strong></summary>

| File | Purpose |
|---|---|
| [`WORKFLOWS.md`](WORKFLOWS.md) | 5 end-to-end cross-agent workflows with phases & gates |
| [`TEMPLATES.md`](TEMPLATES.md) | 5 project templates with checklists and time budgets |
| [`ERROR_RECOVERY.md`](ERROR_RECOVERY.md) | Decision trees by HTTP status, retry patterns. See also [known_issues.md](known_issues.md) |

</details>

---

## 🏗️ Architecture

```mermaid
graph LR
    subgraph Brain["Knowledge Base (20 files)"]
        direction TB
        Core["Core\nagent_principles · fabric_api\nknown_issues · shared_constraints"]
        Ref["Reference\nreport_format · semantic_model\nonelake · warehouse_patterns"]
        Ops["Operations\nWORKFLOWS · TEMPLATES\nERROR_RECOVERY"]
    end

    Brain --> META["🏗️ Meta (5)\nproject-orchestrator\narchitecture-design\npptx-builder\nproject-presentation\nmigration-bo"]

    META --> PL["🔧 Platform (6)\nworkspace-admin · fabric-cli\ncicd-fabric · monitoring\ntaskflow · extensibility"]
    META --> DE["🗄️ Data Engineering (5)\norchestrator · lakehouse\nwarehouse · dataflow\ndomain-modeler"]
    META --> VIZ["📊 Visualization (2)\nsemantic-model\nreport-builder"]
    META --> FA["🤖 Fabric Agent (2)\nai-skills · ai-skills-analysis"]
    META --> RT["⚡ Real-Time (2)\nrti-eventstream · rti-kusto"]
    META --> IQ["🧠 IQ (1)\nontology"]
    META --> QA["✅ Quality (2)\ntesting · pixel-design"]
```

---

## 📖 Documentation

| Doc | What's inside |
|---|---|
| [TEMPLATES.md](TEMPLATES.md) | 5 project templates — pick one and follow the checklist |
| [WORKFLOWS.md](WORKFLOWS.md) | Cross-agent sequencing — phases, gates, handoffs |
| [ERROR_RECOVERY.md](ERROR_RECOVERY.md) | HTTP error decision trees + retry code examples |
| [shared_constraints.md](shared_constraints.md) | 8 hard rules every agent follows |

---

## License

MIT

Built for Microsoft Fabric. Powered by 25 specialized agents across 8 domains and 20 knowledge files.

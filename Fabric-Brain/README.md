# Fabric-Brain

**24 Fabric-specific AI agents + 14 knowledge files for building Microsoft Fabric solutions — zero re-learning, zero repeated mistakes.**

> Part of the [**Azure-Brain**](../README.md) umbrella. For cross-cutting agents (testing, PPTX, architecture diagrams) see [`../Meta-Brain/`](../Meta-Brain/README.md).

![Agents](https://img.shields.io/badge/agents-24-blue?style=for-the-badge&logo=github)
![Domains](https://img.shields.io/badge/domains-8-orange?style=for-the-badge)
![Knowledge](https://img.shields.io/badge/knowledge_files-14-green?style=for-the-badge)
![Fabric](https://img.shields.io/badge/Microsoft_Fabric-REST_API-purple?style=for-the-badge&logo=microsoft)

**Contents:** [Quick Start](#-quick-start) · [Pick Your Scenario](#-pick-your-scenario) · [Agents](#-agents-24--8-domains) · [Knowledge Files](#-knowledge-files) · [Architecture](#-architecture) · [Documentation](#-documentation)

---

## ⚡ Quick Start

**New here?** → [`../GETTING_STARTED.md`](../GETTING_STARTED.md) (15 min setup)

```bash
# 1. From Fabric-Brain/, configure local credentials
cp resource_ids.example.md resource_ids.md    # Fill with your Fabric IDs
cp environment.example.md environment.md      # Fill with your env paths

# 2. Open in VS Code with Copilot (umbrella .github/copilot-instructions.md auto-loads)

# 3. Pick a scenario and start building
# See ../Meta-Brain/SCENARIOS.md — presets, bases, modules, axes
```

> **Key Rule** — New reports use the **PBIR folder format**
> (`definition/pages/{page}/visuals/{vis}/visual.json`), per
> [`agents/report-builder-agent/instructions.md`](agents/report-builder-agent/instructions.md),
> which is authoritative on report format.
> Legacy PBIX (`report.json` + `sections[].visualContainers[]`) stays valid for **maintaining
> reports already shipped in it** — see [`report_format.md`](report_format.md).
> Both render; PBIR requires the v2.0 rules (known_issues #19).

---

## 🎯 Pick Your Scenario

A demo is **composed**, not copied: `preset = base + modules`, with a few axes (industry,
storyline, capacity…) applied across the whole thing. The model lives in
[`../Meta-Brain/SCENARIOS.md`](../Meta-Brain/SCENARIOS.md).

| I want to... | Preset | Formula | Time |
| --- | --- | --- | --- |
| **Build a BI dashboard** (Lakehouse → Model → Report) | `bi-dashboard` | `B1` | 2–3h |
| **Set up real-time analytics** (EventStream → Eventhouse → KQL) | `real-time-dashboard` | `B1(1–6) + B2` | 3–4h |
| **Build a full Smart Factory demo** (Batch + RT + Ontology + AI) | `smart-factory` | `B1 + B2 + M-ONTO + M-AGENT` | 4–6h |
| **Build a Real-Time Operations / Digital Twin** (Topology + Telemetry + Ontology + Graph + dual-source Agent + Portal) | `digital-twin` | `B1 + B2 + M-ONTO + M-DL + M-AGENT + M-OPS + M-ALERT + M-PORTAL` | 1–2d |
| **Add AI Q&A to existing data** (Data Agent + Instructions) | `data-agent-addon` | `M-AGENT` | 45min |
| **Add a graph over existing dimensions** | `ontology-addon` | `M-ONTO` | 1–2h |
| **Migrate from SAP BO / Databricks / Synapse** | `migration-wave` | `B3` | 4–6w |

**Nothing fits?** [`SCENARIOS.md` §2.5](../Meta-Brain/SCENARIOS.md#25-no-preset-fits--build-a-custom-scenario)
walks the custom path — pick a base, pick modules, set the axes. And whatever you learn on the
run goes back into the model via the run sheet, so the next demo is cheaper.

---

## 🤖 Agents (24) — 8 Domains

> Full catalog with boundary clarifications: [`agents/_catalog.yaml`](agents/_catalog.yaml)

### 🔧 Platform & Operations (6)

| Agent | What it does |
| --- | --- |
| [workspace-admin](agents/workspace-admin-agent/) | Workspace CRUD, capacity, RBAC, Git integration |
| [cicd-fabric](agents/cicd-fabric-agent/) | Git integration, deployment pipelines, variable libraries |
| [fabric-cli](agents/fabric-cli-agent/) | `fab` CLI, item management, CI/CD deploy |
| [monitoring](agents/monitoring-agent/) | Admin APIs, audit events, KQL dashboards |
| [taskflow](agents/taskflow-agent/) | Task Flow design, templates, JSON import/export |
| [extensibility-toolkit](agents/extensibility-toolkit-agent/) | Custom workloads, iFrame SDK, Workload Hub |

### 🗄️ Data Engineering (5)

| Agent | What it does |
| --- | --- |
| [orchestrator](agents/orchestrator-agent/) | Pipelines, ingestion, notebooks, copy jobs |
| [lakehouse](agents/lakehouse-agent/) | OneLake DFS, Delta tables, Spark, medallion architecture |
| [dataflow](agents/dataflow-agent/) | Dataflow Gen2, Power Query M, ETL |
| [warehouse](agents/warehouse-agent/) | Fabric Warehouse, T-SQL, CTAS, COPY INTO |
| [domain-modeler](agents/domain-modeler-agent/) | Star schema design, industry templates, synthetic data |

### 📊 Visualization (2)

| Agent | What it does |
| --- | --- |
| [semantic-model](agents/semantic-model-agent/) | DAX measures, relationships, model.bim, Direct Lake |
| [report-builder](agents/report-builder-agent/) | Power BI reports, visuals, themes (Legacy PBIX only) |

### 🤖 Fabric Agent (2)

| Agent | What it does |
| --- | --- |
| [ai-skills](agents/ai-skills-agent/) | Fabric Data Agents — creation, instructions, few-shot examples |
| [ai-skills-analysis](agents/ai-skills-analysis-agent/) | Data Agent evaluation, DAX quality scoring, RCA |

### ⚡ Real-Time Intelligence (3)

| Agent | What it does |
| --- | --- |
| [rti-kusto](agents/rti-kusto-agent/) | Eventhouse, KQL database, dashboards, Operations Agent |
| [rti-eventstream](agents/rti-eventstream-agent/) | EventStreams, EventHub SDK, CDC patterns |
| [data-activator](agents/data-activator-agent/) | Reflex — real-time alerts/triggers, Teams/Email/Fabric item actions |

### 🧠 IQ — Intelligence (2)

| Agent | What it does |
| --- | --- |
| [ontology](agents/ontology-agent/) | Entity types, bindings, contextualizations, NL2Ontology |
| [graph](agents/graph-agent/) | Graph Model, GQL (ISO/IEC 39075), algorithms, `RefreshGraph`, NL2GQL |

### ✅ Fabric Quality (1)

| Agent | What it does |
| --- | --- |
| [pixel-design](agents/pixel-design-agent/) | Pre-deployment Fabric report validation — layout, overlaps, fonts |

### 🔄 Migration (3)

| Agent | What it does |
| --- | --- |
| [migration-bo](agents/migration-bo-agent/) | BusinessObjects → Fabric — 5-stage framework, 119 BO→DAX mappings |
| [migration-databricks](agents/migration-databricks-agent/) | Databricks → Fabric — `dbutils`→`notebookutils`, UC→Lakehouse, DBFS→OneLake |
| [migration-synapse](agents/migration-synapse-agent/) | Synapse → Fabric — phased, `mssparkutils`→`notebookutils`, SQL Pool→Warehouse |

### 🖥️ Experience

> Moved. The external operations portal and Fabric Apps (Rayfin) now live in
> [`../Apps-Brain/`](../Apps-Brain/README.md) — applications are cut by *"I am building an app"*,
> with the runtime (inside Fabric vs external) as a decision inside that brain.
> Fabric-Brain keeps [`extensibility-toolkit`](agents/extensibility-toolkit-agent/), which extends
> the Fabric **portal itself** and ships to the Workload Hub.

> Cross-cutting agents (testing, PPTX, architecture diagrams, project orchestrator, project presentation) live in [`../Meta-Brain/agents/`](../Meta-Brain/README.md).
>
> Every agent has `instructions.md` (system prompt) + domain-specific files. The agent README lists the reading order.

---

## 📚 Knowledge Files

<details>
<summary><strong>Core — Read these first (at Azure-Brain umbrella root)</strong></summary>

| File | Purpose |
| --- | --- |
| [`../agent_principles.md`](../agent_principles.md) | **Mandatory** — Operating principles, task management, quality standards |
| [`../shared_constraints.md`](../shared_constraints.md) | 8 hard rules all agents follow (config-driven, idempotent, async-first) |
| [`fabric_api.md`](fabric_api.md) | REST API patterns, auth, async operations, LRO polling |
| [`../known_issues.md`](../known_issues.md) | Gotchas & workarounds. See also [`../ERROR_RECOVERY.md`](../ERROR_RECOVERY.md) |
| [`environment.md`](environment.md) | Python, Azure CLI, PowerShell setup |
| [`resource_ids.md`](resource_ids.md) | GUIDs, endpoints, connection strings |

</details>

<details>
<summary><strong>Reference — Domain-specific Fabric patterns</strong></summary>

| File | Purpose |
| --- | --- |
| [`report_format.md`](report_format.md) | Legacy PBIX format spec — **maintenance of pre-v2.0 reports only**; new reports use PBIR (`agents/report-builder-agent/`) |
| [`visual_builders.md`](visual_builders.md) | Visual config, expression language, vcObjects |
| [`semantic_model.md`](semantic_model.md) | model.bim deployment, Direct Lake, TMDL |
| [`onelake.md`](onelake.md) | DFS API 3-step upload protocol |
| [`mcp_powerbi.md`](mcp_powerbi.md) | MCP Power BI — 21 tools for semantic model CRUD, DAX, Prep for AI |
| [`../Meta-Brain/mcp_registry.md`](../Meta-Brain/mcp_registry.md) | **MCP Server Registry** — central catalog of all 7 MCP servers |
| [`item_definitions.md`](item_definitions.md) | Definition envelope spec for all 20+ Fabric item types |
| [`warehouse_patterns.md`](warehouse_patterns.md) | SQL DW authoring — CTAS, COPY INTO, transactions, time travel |
| [`spark_patterns.md`](spark_patterns.md) | Spark/Lakehouse authoring — enableSchemas, notebooks, pools |
| [`mirrored_databases.md`](mirrored_databases.md) | Mirrored DB patterns — CDC sync, Lakehouse vs Mirror decision |

</details>

<details>
<summary><strong>Operations — Workflows, templates, error recovery (in Meta-Brain)</strong></summary>

| File | Purpose |
| --- | --- |
| [`../Meta-Brain/SCENARIOS.md`](../Meta-Brain/SCENARIOS.md) | **The demo model** — presets, 3 bases, 11 modules, axes, deploy order |
| [`../Meta-Brain/run_sheet.example.md`](../Meta-Brain/run_sheet.example.md) | Per-demo run sheet — copy to `RUN.md` in the demo repo |
| [`../ERROR_RECOVERY.md`](../ERROR_RECOVERY.md) | Decision trees by HTTP status, retry patterns |

</details>

---

## 🏗️ Architecture

```mermaid
graph LR
    subgraph KB["Knowledge Base"]
        direction TB
        Core["Core (umbrella)<br/>agent_principles · known_issues<br/>shared_constraints"]
        Ref["Fabric Reference<br/>report_format · semantic_model<br/>onelake · warehouse_patterns"]
        Ops["Meta-Brain Ops<br/>SCENARIOS · run_sheet<br/>ERROR_RECOVERY"]
    end

    KB --> PL["🔧 Platform (6)"]
    KB --> DE["🗄️ Data Engineering (5)"]
    KB --> VIZ["📊 Visualization (2)"]
    KB --> FA["🤖 Fabric Agent (2)"]
    KB --> RT["⚡ Real-Time (3)"]
    KB --> IQ["🧠 IQ (2)"]
    KB --> QA["✅ Fabric Quality (1)"]
    KB --> MIG["🔄 Migration (3)"]
```

---

## 📖 Documentation

| Doc | What's inside |
| --- | --- |
| [`../README.md`](../README.md) | **Azure-Brain umbrella** — vision and brain index |
| [`../GETTING_STARTED.md`](../GETTING_STARTED.md) | **Start here** — 15 min setup guide for new users |
| [`../Meta-Brain/SCENARIOS.md`](../Meta-Brain/SCENARIOS.md) | The demo model — pick a preset, or compose base + modules |
| [`../Meta-Brain/run_sheet.example.md`](../Meta-Brain/run_sheet.example.md) | Run sheet to copy per demo — and the promotion rules that feed the brain |
| [`../ERROR_RECOVERY.md`](../ERROR_RECOVERY.md) | HTTP error decision trees + retry code examples |
| [`../shared_constraints.md`](../shared_constraints.md) | 8 hard rules every agent follows |
| [resource_ids.example.md](resource_ids.example.md) | Template for your workspace/item IDs |
| [environment.example.md](environment.example.md) | Template for your environment setup |

---

## License

MIT

Built for Microsoft Fabric. Part of [Azure-Brain](../README.md) — Fabric-Brain contains 24 specialized agents across 8 domains and 14 knowledge files.

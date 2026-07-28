# Azure-Brain

**A modular knowledge base for building cloud data & AI solutions with GitHub Copilot — organized into specialized "brains" per technology, plus cross-cutting meta-tooling.**

![Brains](https://img.shields.io/badge/brains-3_active-blue?style=for-the-badge)
![Agents](https://img.shields.io/badge/agents-35_active-orange?style=for-the-badge)
![Knowledge](https://img.shields.io/badge/knowledge_files-20+-green?style=for-the-badge)

**Contents:** [Vision](#vision) · [Brains](#-brains) · [Quick Start](#-quick-start) · [Umbrella Knowledge](#-umbrella-knowledge) · [Testing](#-testing) · [Add a Brain](#-adding-a-new-brain)

---

## Vision

Azure-Brain is a **multi-brain knowledge architecture**. Each brain is a self-contained body of agents + docs for one technology domain. Cross-cutting agents (testing, presentation, orchestration) live in `Meta-Brain` so they can be reused as we add brains over time.

```
Azure-Brain/                  ← umbrella (this repo)
├── Fabric-Brain/             ← Microsoft Fabric (26 agents, flat layout)
├── Database-Brain/           ← Azure databases (4 active agents, nested by domain)
├── Meta-Brain/               ← cross-cutting (5 agents — testing, PPTX, etc.)
└── (future brains)           ← Synapse-Brain, Databricks-Brain, Foundry-Brain, ...
```

> **Layout note.** Fabric-Brain and Meta-Brain keep agents flat (`agents/<agent>/`).
> Database-Brain nests them by domain (`agents/<NN-domain>/<agent>/`). Tooling that walks
> agents must handle both depths — see `Meta-Brain/tests/conftest.py`.

---

## 🧠 Brains

| Brain | Scope | Agents | Status |
| --- | --- | --- | --- |
| [**Fabric-Brain**](Fabric-Brain/README.md) | Microsoft Fabric — Lakehouse, Warehouse, Semantic Model, RTI, Data Agents, Ontology | 26 | ✅ Active |
| [**Meta-Brain**](Meta-Brain/README.md) | Cross-cutting — testing, PowerPoint, HTML diagrams, README authoring, project orchestration | 5 | ✅ Active |
| [**Database-Brain**](Database-Brain/README.md) | Azure databases — Azure SQL, PostgreSQL, Cosmos DB, MySQL, cross-engine migration (Oracle → PG, SQL Server → Azure SQL, Mongo → Cosmos DB) | 4 active / 22 catalogued (Oracle→PG track live, CLI + Copilot paths) | 🟢 Active |
| _Synapse-Brain_ | Azure Synapse legacy | — | 📋 Planned |
| _Databricks-Brain_ | Databricks on Azure | — | 📋 Planned |
| _Foundry-Brain_ | Microsoft AI Foundry (multi-agent orchestration) | — | 📋 Planned |

---

## ⚡ Quick Start

**New here?** → [GETTING_STARTED.md](GETTING_STARTED.md) (15 min setup)

```bash
# 1. Clone Azure-Brain
git clone https://github.com/Statyx/Azure-Brain.git
cd Azure-Brain

# 2. Configure your local credentials (per-brain)
cp Fabric-Brain/resource_ids.example.md Fabric-Brain/resource_ids.md
cp Fabric-Brain/environment.example.md  Fabric-Brain/environment.md

# 3. Open in VS Code with Copilot — .github/copilot-instructions.md auto-loads
# Agents and knowledge files are discovered automatically.
```

---

## 📚 Umbrella Knowledge

Cross-brain principles and references that apply to **every** brain:

| File | Purpose |
| --- | --- |
| [agent_principles.md](agent_principles.md) | **Mandatory** — Operating principles, task management, quality standards every agent follows |
| [shared_constraints.md](shared_constraints.md) | 8 hard rules across all brains (config-driven, idempotent, async-first) |
| [known_issues.md](known_issues.md) | Cross-cutting gotchas & workarounds |
| [ERROR_RECOVERY.md](ERROR_RECOVERY.md) | Decision trees by HTTP status, retry patterns |
| [GETTING_STARTED.md](GETTING_STARTED.md) | **Start here** — 15 min setup guide for new users |

---

## 🧪 Testing

Cross-brain validation lives in Meta-Brain:

```bash
cd Meta-Brain
python -m pytest tests/ -v --tb=short
```

Validates: catalogs match disk in every brain, every agent has `instructions.md`, internal markdown links resolve, Python compiles, JSON parses. The `BRAINS` list in `Meta-Brain/tests/conftest.py` controls which brains are covered.

---

## 🤝 Adding a New Brain

1. Create a new top-level folder (e.g. `Databricks-Brain/`)
2. Add `Databricks-Brain/README.md`, `agents/`, `agents/_catalog.yaml`
3. Add the brain to the `BRAINS` list in `Meta-Brain/tests/conftest.py` (single source of truth — covers every test module)
4. Update this README's brain table **and** the brain list in `.github/copilot-instructions.md`
5. Re-run umbrella tests to confirm nothing broke

---

## License

MIT

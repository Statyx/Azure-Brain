# Meta-Brain

**5 cross-cutting agents + shared infrastructure** — testing, PowerPoint generation, HTML architecture diagrams, project orchestration, README authoring.

> Part of the [**Azure-Brain**](../README.md) umbrella. For Fabric-specific agents see [`../Fabric-Brain/`](../Fabric-Brain/README.md).

![Agents](https://img.shields.io/badge/agents-5-blue?style=for-the-badge)
![Scope](https://img.shields.io/badge/scope-cross--cutting-orange?style=for-the-badge)

---

## Why Meta-Brain?

Some agents and knowledge are **not Fabric-specific** — they help build, test, present, and orchestrate any technical project. We isolate them here so they can be reused for future brains (e.g. `Synapse-Brain`, `Databricks-Brain`, `AI-Foundry-Brain`) under the same Azure-Brain umbrella.

---

## 🤖 Agents (5)

> Full catalog: [`agents/_catalog.yaml`](agents/_catalog.yaml)

### ✅ Quality

| Agent | What it does |
| --- | --- |
| [testing-agent](agents/testing-agent/) | 3-tier test taxonomy (smoke/integration/regression), visual validator library, pytest scaffolding |

### 🎨 Presentation

| Agent | What it does |
| --- | --- |
| [pptx-builder-agent](agents/pptx-builder-agent/) | PowerPoint architecture diagrams — 5-phase pipeline, helper functions, quality gates |
| [architecture-design-agent](agents/architecture-design-agent/) | HTML architecture diagrams with base64 SVG icons (303 icons — Fabric + Azure) |
| [project-presentation-agent](agents/project-presentation-agent/) | GitHub repo best practices — README authoring, badges, repo structure |

### 🎬 Orchestration

| Agent | What it does |
| --- | --- |
| [project-orchestrator-agent](agents/project-orchestrator-agent/) | End-to-end 12-step project builder — industry configs, agent coordination |

---

## 📚 Cross-cutting Files

| File | Purpose |
| --- | --- |
| [SCENARIOS.md](SCENARIOS.md) | **The demo model** — presets, 3 bases, 10 modules, variation axes, and the rules for evolving it |
| [run_sheet.example.md](run_sheet.example.md) | Per-demo run sheet — copy to `RUN.md` in the demo repo, then promote what you learned back into the brain |
| [mcp_registry.md](mcp_registry.md) | **MCP Server Registry** — central catalog of all MCP servers (Azure, Fabric, Power BI, Kusto, Engine, GitKraken, Pylance) |
| [pytest.ini](pytest.ini) | Test runner configuration |
| [run_all_tests.py](run_all_tests.py) | Cross-project test runner (Azure-Brain + sibling projects) |
| [tests/](tests/) | Smoke + cross-reference tests for the whole Azure-Brain |

---

## 🧪 Running Tests

```bash
cd Meta-Brain
python -m pytest tests/ -v --tb=short
```

Tests validate **both** brains' catalogs, agent folder structure, internal markdown links, Python syntax, and JSON parsing.

---

## License

MIT — Part of [Azure-Brain](../README.md).

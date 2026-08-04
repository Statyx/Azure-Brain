# Getting Started

You cloned the repo. Here's how to get productive in 15 minutes.

---

## 1. Prerequisites (5 min)

```bash
# Python 3.12+
python --version

# Required packages
pip install requests pyyaml faker azure-cli

# Azure CLI login
az login
```

## 2. Configure Your Environment (5 min)

Config lives **per brain**, not at the root. Copy only what you need — each pair is gitignored
and ships with a committed `.example` twin:

```bash
# Fabric work
cp Fabric-Brain/resource_ids.example.md    Fabric-Brain/resource_ids.md
cp Fabric-Brain/environment.example.md     Fabric-Brain/environment.md

# Foundry work
cp Foundry-Brain/resource_ids.example.md   Foundry-Brain/resource_ids.md
cp Foundry-Brain/environment.example.md    Foundry-Brain/environment.md

# Database work
cp Database-Brain/resource_ids.example.md  Database-Brain/resource_ids.md
cp Database-Brain/environment.example.md   Database-Brain/environment.md
```

Apps-Brain and Meta-Brain need no local config.

Edit `Fabric-Brain/resource_ids.md` with your values:

| What | Where to find it |
|------|------------------|
| Subscription ID | `az account show --query id -o tsv` |
| Tenant ID | `az account show --query tenantId -o tsv` |
| Capacity ID | Fabric Admin Portal → Capacities → your capacity |
| Workspace ID | Fabric portal → Workspace settings → URL or API |

> You don't need all IDs upfront. Fill them in as you deploy items.

## 3. Verify Auth Works (2 min)

```bash
az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv
```

If you get a token, you're ready.

## 4. Pick a Template (3 min)

| I want to... | Template | Time |
|--------------|----------|------|
| Build a BI dashboard | [Template 1](Meta-Brain/TEMPLATES.md#template-1-standard-bi-demo-23-hours) | 2–3h |
| Set up real-time analytics | [Template 2](Meta-Brain/TEMPLATES.md#template-2-real-time-iot-dashboard-34-hours) | 3–4h |
| Add AI Q&A to existing data | [Template 4](Meta-Brain/TEMPLATES.md#template-4-data-agent-add-on-45-min) | 45min |

Each template has a step-by-step checklist with agent assignments.

## 5. Start Working

Open your project in VS Code with Copilot, or the Copilot CLI / Copilot app. The agents auto-load
via `.github/copilot-instructions.md` (VS Code) or `AGENTS.md` (CLI / app) — both point at the
same agent tree.

Tell Copilot what you want to build:
- _"Create a Fabric workspace and lakehouse for a finance demo"_
- _"Build a semantic model with Direct Lake over my lakehouse tables"_
- _"Deploy a 3-page Power BI report"_

Copilot reads the relevant agent instructions and guides you.

---

## How the Repo Works

```
Azure-Brain/                       Umbrella repo
├── AGENTS.md                      Routing table + index of all 42 agents (start here)
│
├── Fabric-Brain/                  24 Fabric agents + domain knowledge files
│   ├── agents/
│   │   ├── _catalog.yaml
│   │   └── {agent-name}/
│   │       ├── instructions.md   Agent system prompt (read by Copilot)
│   │       └── *.md              Domain knowledge files
│   ├── resource_ids.md            YOUR workspace/item IDs (gitignored, private)
│   ├── environment.md             YOUR environment setup (gitignored, private)
│   └── *.md                       Fabric API, OneLake, report_format, semantic_model, etc.
│
├── Foundry-Brain/                 7 Microsoft Foundry agents (+ generation_map.md — read first)
├── Apps-Brain/                    2 application-layer agents
├── Database-Brain/                4 Azure database agents (nested by domain)
│
├── Meta-Brain/                    5 cross-cutting agents + shared infrastructure
│   ├── agents/                    testing, pptx-builder, architecture-design, etc.
│   ├── tests/                     Cross-brain validation suite
│   ├── tools/scan_public_safety.py  Leak scanner (second CI gate)
│   ├── TEMPLATES.md               Project templates with checklists
│   ├── WORKFLOWS.md               Cross-agent orchestration sequences
│   └── mcp_registry.md            MCP server registry
│
├── agent_principles.md            Operating principles (umbrella)
├── PUBLIC_SAFETY.md               Write-as-if-public rules (Zava, fake GUIDs, no secrets)
├── known_issues.md                Cross-cutting gotchas
├── shared_constraints.md          8 hard rules every agent follows
└── ERROR_RECOVERY.md              HTTP error decision trees
```

**Key insight**: The agents don't execute code themselves. They are **instruction files** that GitHub Copilot reads to understand how to help you build Fabric solutions. The knowledge files capture patterns, gotchas, and workarounds from real deployments.

---

## Common Issues

| Problem | Solution |
|---------|----------|
| `az account get-access-token` fails | Run `az login` first |
| Report visuals are blank | You're using PBIR format. Switch to Legacy PBIX (see [`Fabric-Brain/report_format.md`](Fabric-Brain/report_format.md)) |
| API returns 401 | Token expired. Get a fresh one: `az account get-access-token --resource https://api.fabric.microsoft.com` |
| Capacity not found | Check it's running: Fabric Admin Portal → Capacities |
| SQL Endpoint not ready | Wait 2-3 min after lakehouse creation, then poll |

For more: see [known_issues.md](known_issues.md) and [ERROR_RECOVERY.md](ERROR_RECOVERY.md).

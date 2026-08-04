# Foundry-Brain

**Microsoft Foundry agents + knowledge files for building supervised, multi-agent systems that orchestrate real work across Fabric and Azure — with GitHub Copilot, zero re-learning, zero repeated mistakes.**

> Part of the [**Azure-Brain**](../README.md) umbrella. For cross-cutting agents (testing, PPTX, architecture diagrams) see [`../Meta-Brain/`](../Meta-Brain/README.md). For the Fabric artifacts these agents consume, see [`../Fabric-Brain/`](../Fabric-Brain/README.md).

![Status](https://img.shields.io/badge/status-bootstrap-yellow?style=for-the-badge)
![Brain](https://img.shields.io/badge/brain-Foundry-blueviolet?style=for-the-badge)
![Scope](https://img.shields.io/badge/scope-Agents_%7C_Tools_%7C_Orchestration-orange?style=for-the-badge)
![Agents](https://img.shields.io/badge/agents-7_active_%2F_11_catalogued-yellow?style=for-the-badge)

---

## ⚠️ Read first

Microsoft Foundry ships **two agent generations side by side**, with two doc trees — and
**three separate retirement clocks**, one of which fires in December 2026 on the *current*
tree. Following the wrong tutorial means writing code against a dying API.

1. **[`generation_map.md`](generation_map.md)** — which generation this brain targets, how to
   tell them apart in three seconds, what retires when, and the SDK/RBAC facts as recorded.
2. **[`orchestration_patterns.md`](orchestration_patterns.md)** — the supervisor pattern:
   what replaced Connected Agents, when to use A2A vs a Toolbox, and the design rules that
   decide whether a live demo holds up.
3. 📐 **[`reference_workflow.md`](reference_workflow.md)** — a **complete seven-agent
   orchestration observed end to end** (Microsoft 365 / Work IQ): the diagram, a four-beat demo
   script, the tool distribution, the full workflow YAML, and its known weaknesses. The fastest
   way to see how all five agent roles fit together.
4. 📐 **[`reference_foundry_iq.md`](reference_foundry_iq.md)** — a **second complete system**
   (Zava retail): four agents, a Foundry IQ knowledge base with three heterogeneous sources, a
   Fabric data agent called as a tool, and the working Python that creates it all. Ends with a
   side-by-side comparison of the two labs — that comparison is where most of the transferable
   insight lives.
5. **[`portal_reality.md`](portal_reality.md)** — what the portal actually does, where it
   disagrees with the docs, and the evidence rules for adding to it.

**Headline:** the classic `agent.as_tool` / **Connected Agents** pattern **does not exist** in
the new Foundry Agent Service. A supervisor now attaches **sub-agents via the A2A tool**
(preview) and **capabilities via a Toolbox** (GA). Portal Workflows work, but retire
**2026-12-01** — fine to stage a demo, never doctrine.

---

## Scope

Foundry-Brain covers the **agent control plane**: what reasons, decides and delegates.

| Scenario | Examples |
| --- | --- |
| **Agent authoring** | Instructions, tools, threads and runs, portal vs SDK parity, versioning |
| **Multi-agent orchestration** | Supervisor/orchestrator over specialised agents, delegation and routing, durable workflows |
| **Enterprise grounding** | Fabric data agent tool, Fabric IQ, AI Search indexes, file search, vector stores |
| **Quality** | Evaluators, agent evaluation runs, tracing, red teaming, regression detection |
| **Governance** | Content filters, Entra ID and managed identity, private networking, IaC and promotion |

Out of scope — owned elsewhere:

| Not here | Owner |
| --- | --- |
| Creating/publishing a **Fabric** Data Agent, lakehouses, semantic models, reports | [`../Fabric-Brain/`](../Fabric-Brain/README.md) |
| Databases (Azure SQL, PostgreSQL, Cosmos DB) | [`../Database-Brain/`](../Database-Brain/README.md) |
| Testing framework, PPTX, HTML diagrams, project build orchestration | [`../Meta-Brain/`](../Meta-Brain/README.md) |

---

## Why this brain exists

To move a demo from *"Copilot on my laptop drives Fabric"* to *"a supervisor agent running in
Foundry drives several specialised agents, which drive Fabric"*.

```
                    ┌──────────────────────────┐
   user  ─────────► │   SUPERVISOR AGENT       │
                    └───┬──────────────────┬───┘
              A2A tool  │                  │  MCP tool (toolbox)
                        ▼                  ▼
              ┌──────────────────┐   ┌──────────────────────┐
              │ sub-agent        │   │ TOOLBOX              │
              │ (incoming A2A    │   │  ├─ Microsoft Fabric │──► Fabric Data Agent
              │  enabled)        │   │  ├─ OpenAPI          │──► Fabric REST API
              └──────────────────┘   │  └─ Function calling │──► custom
                                     └──────────────────────┘
```

The Fabric leg is a **built-in tool** in the current catalog (preview) — it does not need A2A.
Full rationale and the design rules in [`orchestration_patterns.md`](orchestration_patterns.md).

---

## Catalogued Agents

> [`agents/_catalog.yaml`](agents/_catalog.yaml) is the source of truth.
> Status legend: 🟢 active (implemented) · 🟡 planned · ⚫ deprecated.
> **Seven agents are 🟢 today.** Their behavioural content is grounded in two real observed
> systems ([`reference_workflow.md`](reference_workflow.md),
> [`reference_foundry_iq.md`](reference_foundry_iq.md)); the SDK shapes are tenant-verified by
> the second lab's working script. The rest are written on demand,
> grounded against a real tenant rather than guessed from docs.

### 01 — Platform
- 🟡 `foundry-project-agent` — resource + project, RBAC and managed identity, connections, networking
- 🟡 `foundry-model-catalog-agent` — deployments, TPM quota, model routing, cost/latency trade-offs

### 02 — Agent Service
- 🟢 [`foundry-agent-service-agent`](agents/foundry-agent-service-agent/README.md) — **the five agent roles** (router/wrapper/action/synthesizer/resolver), prompt-as-interface rules, tool attachment + approval posture, versioning · includes [copy-paste prompt templates](agents/foundry-agent-service-agent/prompt_templates.md)
- 🟢 [`foundry-tools-agent`](agents/foundry-tools-agent/README.md) — function calling, OpenAPI, MCP, code interpreter, file search; the **three-layer control model** (prompt = default, tool set = boundary, approval = control)

### 03 — Orchestration
- 🟢 [`foundry-orchestration-agent`](agents/foundry-orchestration-agent/README.md) — supervisor patterns, A2A delegation, toolbox vs direct tools, routing contracts, anti-loop guardrails
- 🟡 `foundry-agent-framework-agent` — Microsoft Agent Framework, workflows, durable execution

### 04 — Knowledge & Grounding
- 🟢 [`foundry-fabric-bridge-agent`](agents/foundry-fabric-bridge-agent/README.md) — **the Fabric bridge**: Fabric data agent tool + Fabric IQ, portal-then-SDK binding **by connection name**, identity passthrough, handoff to `ai-skills-agent`
- 🟢 [`foundry-knowledge-agent`](agents/foundry-knowledge-agent/README.md) — **Foundry IQ** knowledge bases: indexed vs federated sources, cross-service RBAC, consumption by agents as an **MCP tool**

### 05 — Quality
- 🟢 [`foundry-observability-agent`](agents/foundry-observability-agent/README.md) — traces + Application Insights, **the trace-reading playbook**, and the evidence discipline the rest of the brain depends on

### 06 — Governance
- 🟢 [`foundry-governance-agent`](agents/foundry-governance-agent/README.md) — **guardrails + evaluations**: policy applied to live traffic (layer 4 of the control model) vs scoring applied to a sample, per-role evaluator choice, and the multi-agent seam neither surface covers
- 🟡 `foundry-deploy-agent` — Bicep / azd, environment promotion, CI/CD

---

## Setup

```bash
cp Foundry-Brain/resource_ids.example.md Foundry-Brain/resource_ids.md
cp Foundry-Brain/environment.example.md  Foundry-Brain/environment.md
```

Both copies are gitignored. Fill in subscription, project endpoint and model deployment
names, then record what your portal actually exposes in the *environment fingerprint* table
at the bottom of `environment.md`.

---

## Working rules

Umbrella rules apply in full ([`../AGENTS.md`](../AGENTS.md) § Key rules). Three matter most here:

1. **Generation banner.** Every `instructions.md` opens by naming its target generation and
   the date its doc set was last checked. Foundry moves faster than any other brain.
2. **Never claim "verified"** without a trace or test output. Half this surface is preview;
   a false *verified* sends a downstream agent looping on a path that cannot work.
3. **Consume, never mutate, across brains.** Foundry-Brain reads Fabric artifacts and hands
   off to the owning Fabric-Brain agent for any change.

---

## Testing

```bash
cd ../Meta-Brain
python -m pytest tests/ -v --tb=short
python tools/scan_public_safety.py ..
```

`Foundry-Brain` is covered because it is listed in `BRAINS`
(`Meta-Brain/tests/conftest.py` — single source of truth).

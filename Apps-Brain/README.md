# Apps-Brain

**The application layer of Azure-Brain — the last mile where a human (or an agent) actually meets the platform. Runtime, identity, embedding, in-app intelligence, frontend, operations.**

> Part of the [**Azure-Brain**](../README.md) umbrella. This brain **consumes** the platform brains: [`../Fabric-Brain/`](../Fabric-Brain/README.md) for data artifacts, [`../Foundry-Brain/`](../Foundry-Brain/README.md) for agents, [`../Database-Brain/`](../Database-Brain/README.md) for engines. For cross-cutting tooling see [`../Meta-Brain/`](../Meta-Brain/README.md).

![Status](https://img.shields.io/badge/status-bootstrap-yellow?style=for-the-badge)
![Brain](https://img.shields.io/badge/brain-Apps-teal?style=for-the-badge)
![Scope](https://img.shields.io/badge/scope-Runtime_%7C_Identity_%7C_Embedding_%7C_Intelligence-orange?style=for-the-badge)
![Agents](https://img.shields.io/badge/agents-3_active_%2F_9_catalogued-yellow?style=for-the-badge)

---

## ⚠️ Read first — the cut

The question this brain answers is **"I am building an application"**.

**The runtime is a decision *inside* this brain, not a brain boundary.** Whether the app runs as
a Fabric App item on OneLake, as an external FastAPI portal, or on Container Apps is the *first
routing question here* — it is not a reason to send you to another brain. That is why
`fabric-apps-agent` lives in Apps-Brain and not in Fabric-Brain: a Fabric App item is a **hosting
choice for an application**, the same way Container Apps is.

The corollary matters just as much: every app problem that survives *without* an app belongs to a
platform brain. See the [non-goals](#-non-goals) — they are load-bearing.

---

## Scope

| Domain | What it owns |
| --- | --- |
| **01 — Runtime** | Where the code executes: Fabric App (Rayfin), external portal, Azure hosting |
| **02 — Identity** | Which token the app holds: app vs delegated vs managed identity, consent, OBO, passthrough |
| **03 — Embedding** | Power BI (app-owns-data), Fabric Embed for RTI tiles, direct Kusto, CSP/CORS |
| **04 — Intelligence** | Chat proxy to a Data Agent or Foundry agent, threads, streaming, citations, MCP in-app |
| **05 — Frontend** | Persona-aware navigation, live views, design system, accessibility |
| **06 — Operations** | App Insights correlation, cost per conversation, CI/CD, secrets at runtime |

---

## 🚫 Non-goals

"App" appears in every conversation. Without an explicit stop list this brain becomes the repo's
dumping ground, so these are enforced in [`agents/_catalog.yaml`](agents/_catalog.yaml):

| Not here | Owner | Why |
| --- | --- | --- |
| Data logic, pipelines, Lakehouse / Warehouse / Delta, semantic models, reports | [`../Fabric-Brain/`](../Fabric-Brain/README.md) | the app **reads** what those agents produce |
| Fabric **workloads** (iFrame SDK, React components, Workload Hub) | [`../Fabric-Brain/agents/extensibility-toolkit-agent/`](../Fabric-Brain/agents/extensibility-toolkit-agent/README.md) | a workload extends the Fabric **portal itself** and ships to other tenants — platform surface, not our app |
| Foundry agent **definition** — instructions, tools, orchestration, evaluation | [`../Foundry-Brain/`](../Foundry-Brain/README.md) | this brain consumes a deployed **endpoint**, it never mutates the agent |
| Application **database** schema and tuning | [`../Database-Brain/`](../Database-Brain/README.md) | we own the access path, not the engine |
| Testing framework, PPTX, HTML diagrams, project build orchestration | [`../Meta-Brain/`](../Meta-Brain/README.md) | cross-cutting |

> **Rule of thumb:** if removing the UI/API surface makes the problem disappear, it belongs here.
> If the problem survives without any app, it belongs to a platform brain.

---

## Why this brain exists

Three things were true at once, and they don't fit anywhere else cleanly:

1. **Two agents were parked in Fabric-Brain single-agent domains** (`09-app-platform`,
   `10-experience`) — a reliable signal that a domain has no home. `operations-portal-agent`
   isn't even Fabric technology: it is FastAPI + a static frontend that *consumes* Fabric.
2. **The hard parts of an app are the same regardless of platform.** The two auth models, the
   embed-token dance, the chat proxy, the streaming UX — none of that changes between a Fabric
   App and a Container App. Splitting by hosting model duplicated that knowledge.
3. **Intelligence needed a home on the app side.** `04-intelligence` is the seam where
   Foundry-Brain and Fabric-Brain plug into a real user surface.

```
        ┌──────────────────────────────────────────────┐
        │                 APPS-BRAIN                   │
        │   runtime · identity · embedding · frontend  │
        │              ▲   intelligence  ▲             │
        └──────────────┼────────────────┼──────────────┘
             consumes  │                │  consumes
                       │                │
        ┌──────────────┴───┐    ┌───────┴──────────┐   ┌──────────────┐
        │  Fabric-Brain    │    │  Foundry-Brain   │   │Database-Brain│
        │  data artifacts  │    │  agent endpoints │   │   engines    │
        └──────────────────┘    └──────────────────┘   └──────────────┘
```

**Consume, never mutate.** Apps-Brain reads and calls artifacts owned by other brains, and hands
off to the owning agent for any change.

---

## Catalogued Agents

> [`agents/_catalog.yaml`](agents/_catalog.yaml) is the source of truth.
> Status legend: 🟢 active (implemented) · 🟡 planned · ⚫ deprecated.
> **Two agents are 🟢 today**, both carried over from Fabric-Brain with their production
> history intact. The rest are written on demand, grounded against real work rather than
> guessed from docs.

### 01 — Runtime
- 🟢 [`fabric-apps-agent`](agents/fabric-apps-agent/README.md) — **Fabric Apps (preview) via Rayfin**: scaffold → model → deploy an app backend (DB, Entra auth, Data APIs, hosting) with data landing in OneLake in place; Replit × Fabric path
- 🟢 [`operations-portal-agent`](agents/operations-portal-agent/README.md) — **external operations portal** (FastAPI + static): Data Agent chat proxy, Power BI + RTI dashboard embed, portal-native live SVG views
- 🟡 `app-hosting-azure-agent` — Container Apps / Static Web Apps / App Service: choosing, ingress, scale-to-zero, revisions

### 02 — Identity
- 🟡 `app-identity-agent` — app vs delegated vs managed identity, Entra registration and consent, OBO, per-resource scopes, token cache, passthrough across a proxy hop

### 03 — Embedding
- 🟡 `app-embedding-agent` — Power BI app-owns-data + RLS, Fabric Embed for RTI tiles, direct Kusto, CSP/CORS, silent token renewal

### 04 — Intelligence
- 🟡 `app-intelligence-agent` — chat proxy to a Fabric Data Agent **or** a Foundry agent, threads, streaming, citations, tool-call surfacing, MCP in-app, cost control

### 05 — Frontend
- 🟢 [`app-frontend-agent`](agents/app-frontend-agent/README.md) — dual-mode (seed vs live) architecture, four-layer `src/` split, design system as a token file, single route+nav manifest, personas, accessibility

### 06 — Operations
- 🟡 `app-observability-agent` — App Insights across front and back, correlating a user action through the proxy to the platform call
- 🟡 `app-delivery-agent` — build/container pipelines, environment promotion, secrets at runtime, IaC for the app's own resources

---

## Working rules

Umbrella rules apply in full ([`../AGENTS.md`](../AGENTS.md) § Key rules). Three matter most here:

1. **Consume, never mutate, across brains.** Reading a Fabric report or calling a Foundry agent is
   normal; changing either is a handoff to the owning agent.
2. **Identity is stated explicitly.** Every instruction that makes a call names *which* token it
   uses. Mixing an app token with a delegated one is the single most common failure in this layer
   — see [`agents/operations-portal-agent/known_issues.md`](agents/operations-portal-agent/known_issues.md).
3. **Secrets are read at runtime.** No token, connection string or tenant GUID in an app config
   that ships. Real values live in a gitignored file with a committed `.example` twin
   ([`../PUBLIC_SAFETY.md`](../PUBLIC_SAFETY.md)).

---

## Testing

```bash
cd ../Meta-Brain
python -m pytest tests/ -v --tb=short
python tools/scan_public_safety.py ..
```

`Apps-Brain` is covered because it is listed in `BRAINS`
(`Meta-Brain/tests/conftest.py` — single source of truth).

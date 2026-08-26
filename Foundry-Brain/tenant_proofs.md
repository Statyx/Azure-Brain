# tenant_proofs.md — what was proven by running it

`portal_reality.md` records what a **training lab tenant showed on screen**.
This file records what was **executed against the operator's own tenant**, with the SDK, the
REST API and ARM — and what the execution returned.

**Method:** Python SDK (`azure-ai-projects` **2.4.0**), REST, ARM deployments. Runs, run steps
and tool-call items read back programmatically. Introspection of the installed package to
establish what the SDK *actually exposes*, rather than what the docs describe.
**Observation dates:** 2026-08-04 → 2026-08-05.
**Scope:** **one tenant, one region, one SDK version.** Everything below is proof that a path
**works**, never proof that an alternative path is impossible.

> Real resource names, GUIDs and endpoints live in `resource_ids.md` (gitignored).
> This file records **behaviour and shapes only**.

---

## Why this file is separate from `portal_reality.md`

Different method, different strength. A screenshot shows a state; a run trace shows a
behaviour. When the two disagree about *what the product does*, this file wins — it has the
execution. When they disagree about *what the portal displays*, `portal_reality.md` wins.

---

## ✅ PROVEN — the A2A tool works, agent to agent, in a real tenant

`orchestration_patterns.md` carried the A2A tool as `preview | —` with no run trace behind it.
There is one now.

**What was built:** a supervisor agent delegating to a second Foundry agent
(`Marketing-Churn-Front-Door`) through the **A2A tool**. The project connection carrying the
hop, `FrontDoorA2A`, was created in **pure ARM** — no portal step was needed or used.

**Evidence — two independent signals, and the second is the one that matters:**

1. The run's tool-call items contain `a2a_preview_call` entries. The hop is in the trace.
2. **A witness agent** was built with the *same instructions and the same model* but **without
   the A2A tool attached**. Asked the same question, it could not answer.

Signal 1 alone proves a tool fired. Signal 1 + 2 together prove **the answer came through the
hop** and not from the supervisor's own knowledge. Build the witness — a tool-call item in a
trace does not, on its own, establish that the tool produced the answer.

**Rollback was captured** (`a2a_rollback.json`) before the connection was created. An ARM
connection added to a live project is not a free action; the undo must exist before the do.

### What this does and does not settle

| Question | Settled? |
| --- | --- |
| Can a Foundry agent call another Foundry agent over A2A today? | ✅ **yes**, on this tenant, SDK 2.4.0 |
| Can the connection be created without touching the portal? | ✅ **yes** — ARM only |
| Can the hop be *proven* from the outside? | ✅ **yes** — `a2a_preview_call` items + witness agent |
| Is A2A cheap, fast, or streaming-friendly? | ❌ **no data** — not measured |
| Is A2A stable across regions / SDK versions / GA? | ❌ **no** — one tenant, one preview surface |

⇒ The **router-first** ruling in `orchestration_patterns.md` still stands, but its
justification changes: it is now a **cost and robustness** argument, no longer a *feasibility*
one. "A2A might not work" is no longer a valid reason to avoid it. "A2A costs three model calls
per turn and uses a preview surface" still is.

---

## ✅ PROVEN — the full chain, end to end

```
supervisor agent
   └─ A2A tool ──────────► front-door agent  (Marketing-Churn-Front-Door)
                              └─ MCP tool ──► Fabric data agent  (Marketing_Churn_Agent)
                                                 └─ DAX ────────► semantic model
                                                                     └─► Lakehouse
```

Every hop was exercised in the same run: a natural-language question entered at the supervisor
and a number computed from Delta tables came back out. **Four different protocols in one
answer path** — A2A, MCP, the Fabric assistants API, and DAX.

**Consequence for design:** the failure surface of this chain is the *union* of four surfaces,
and only the outermost one reports to the user. A failure at the DAX end arrives at the
supervisor as a confident sentence. Instrument each hop separately or debug blind —
see [`agents/foundry-observability-agent/instructions.md`](agents/foundry-observability-agent/instructions.md).

---

## 🔑 SDK 2.4.0 — introspected, not read from docs

The installed package was inspected directly. Three facts, each of which changes a design
decision:

| Introspection | Result | Consequence |
| --- | --- | --- |
| `ToolType` members | **no `CONNECTED_AGENT`** | The classic `agent.as_tool` / Connected Agents pattern is genuinely **absent**, not merely deprecated. `generation_map.md` was right, and this is the measurement behind it. |
| `AgentEndpointProtocol` members | **A2A** and **MCP** | These are the two supported inbound protocols. Anything else is application code, not an endpoint. |
| `WorkflowAgentDefinition.workflow` | a plain **`str`** | There is **no typed workflow graph** in the SDK. The format is undocumented, unvalidated at construction, and fails at runtime. Do not build a demo whose spine is a hand-written workflow string. |

**Why introspection and not the docs:** the docs describe the service; the installed package is
what your code will actually call. On a preview surface, they diverge — and the package wins,
because it is the thing that raises the exception.

---

## 🔑 PROVEN — RAG scoping holds, and "do not count" holds with it

A retrieval-grounded agent (`Voice-Of-Customer`) was scoped to a single `customer_id` and asked
for the verbatim material attached to that customer.

| Measure | Result |
| --- | --- |
| Runs returning the complete expected set | **8 of 9 at 12/12** |
| Verified attributions | **11 of 11** — 0 hallucinated |
| "Non-counting contract" (agent must not produce aggregate numbers from retrieved documents) | **held live** |

**The non-counting contract is the transferable part.** A retrieval agent that is allowed to
count will count its own retrieval window and present it as a business figure — an answer that
is arithmetically correct about the wrong population. The cure is an explicit instruction that
counting is **not** its job, and a documented handoff to the agent that owns numbers.

Which is the architecture rule below.

---

## 🔑 Architecture rule — data semantics stay on the data side

> **The data world stays on the data side.** Measures, DAX/GQL routing and the ontology live in
> Fabric. Foundry orchestrates and adds the documentary layer. Foundry **never reimplements**
> data semantics.

Stated by the operator during the build, then validated by it. Two consequences that are not
obvious until you have run the chain:

- **Latency is the accepted price.** Routing a number question through supervisor → A2A → MCP →
  data agent → DAX is slower than computing it in the orchestration layer. That cost is paid
  deliberately, because the alternative is a second, divergent definition of the same measure.
- **Two definitions of one metric is the actual failure**, not the extra seconds. The moment an
  orchestrator "helpfully" sums something, the demo has two truths and the customer will find
  the seam.

This is the concrete form of umbrella rule 5 (*one owner per domain*) and of the
Foundry-Brain rule *consume, never mutate, across brains*.

---

## ⚠️ Defect found in Fabric, surfaced by Foundry supervision

Supervising a Fabric data agent from Foundry made a **non-deterministic** answer visible that
is invisible when the agent is used on its own. The same question returned **825 / 593 / 825 /
825** across four runs.

Full write-up, with the cure, lives with the owning agent —
[`../Fabric-Brain/agents/ai-skills-agent/known_issues.md`](../Fabric-Brain/agents/ai-skills-agent/known_issues.md)
(*An ambiguous question makes the agent choose a different column each run*).

**The Foundry lesson:** a supervisor that asks the same downstream question repeatedly is a
**consistency test you get for free**. A human asks once and believes the answer. Keep that
property — it is one of the strongest arguments for the orchestrated architecture.

---

## Still unproven — do not claim these

- [ ] A2A **latency and cost** per hop — never measured
- [ ] A2A behaviour across **regions**, or under **GA** rather than preview
- [ ] Whether the hop **survives streaming** — not attempted
- [ ] The `WorkflowAgentDefinition.workflow` **string format** — still undocumented, still unread
- [ ] Whether **toolboxes** exist in this region — not seen in either lab or this tenant
- [ ] Any statement about a capability being **absent** — this file only proves presence

---

## Change log

| Date | Change |
| --- | --- |
| 2026-08-26 | File created. Promoted the 2026-08-04→05 hands-on session from a transcript in another repository into the brain: A2A live proof with the witness-agent method, the four-protocol chain, SDK 2.4.0 introspection, RAG scoping measures, the architecture rule, and the pointer to the Fabric non-determinism defect. |

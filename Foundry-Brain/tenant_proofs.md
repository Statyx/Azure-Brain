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

### Second tenant, 2026-09-02 — reproduced, and the two prerequisites this file omitted

The hop was reproduced independently on a different tenant (Sweden Central), which both confirms
the proof above and exposes what it left out. The row *"can the connection be created without
touching the portal? ✅ yes — ARM only"* is **true and dangerously easy to over-read**: it settles
the *A2A* connection and nothing else. Creating it from ARM is necessary but not sufficient, and
the same sentence does **not** transfer to a Fabric data-agent connection (see
`agents/foundry-fabric-bridge-agent/known_issues.md` → *"the probe was run, and ARM cannot do it
at all"*).

Two things must be true beyond a well-formed connection, neither recorded here before:

| Prerequisite | Failure if missing |
|---|---|
| `properties.audience` set **first-class** (not in `properties.metadata`) | `Failed to fetch agentic identity access token with status code: 400, response: ` — with an **empty** response body |
| Caller holds **`Foundry Agent Consumer`** on the target's project, granted to `instance_identity.principal_id` | `Failed to fetch agent card: 404` — a 404, not a 403, for ~4 minutes |

Both were diagnosed the slow way. The 404 in particular reads as a wrong URL and cost two full
investigations into card paths that were correct throughout. Full detail, including the observed
`404 · 404 · 404 · 403 · 200` propagation sequence and why `blueprint.principal_id` cannot be
granted, lives in `agents/foundry-orchestration-agent/known_issues.md`.

**Evidence:** `items: ['a2a_preview_call', 'a2a_preview_call_output', 'message']`, the subordinate
returning two contract clauses verbatim with their identifiers, in an automated 3-probe verifier
that also asserts the negative case (the contracts agent must *not* answer a quantitative question).

⇒ Revised reading of the table above: **A2A is feasible and reproducible across two tenants.** The
remaining risk is not "does it work" but "is it wired correctly", and the two rows above are where
that goes wrong.

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

## 🔒 PROVEN ABSENT — how to prove a capability is *missing*, and one that is

This file's own rule was *"only proves presence"* — an absence claim normally cannot be
distinguished from a wrong guess about the URL, the permission, or the name. **2026-09-02 found a
case where it can**, and the technique generalises.

**The case:** is a Fabric **data agent** reachable as an MCP server, so a Foundry agent could
attach it as a plain MCP tool and skip the connection ARM cannot create?

Sixteen endpoint names were tried under the shape the ontology item genuinely uses,
`https://api.fabric.microsoft.com/v1/mcp/dataPlane/workspaces/{ws}/items/{id}/<name>`. All returned
`404` / JSON-RPC `-32601` / `EntityNotFound`. On its own that proves nothing — sixteen wrong
guesses look identical to sixteen missing permissions.

**What made it conclusive was a control that fails differently.** The *same* URL with
`/ontologyEndpoint`, the *same* token, the *same* DataAgent item, returns **`500` / `-32603`**
internal error: the route exists, was dispatched, and choked on the wrong item type behind it.

| Response | What it proves |
| --- | --- |
| `404` / `-32601` / `EntityNotFound` | the **route** is not registered — the name is not real |
| `500` / `-32603` internal error | the route **is** registered and reached; the item behind it is wrong |

Two different failure modes from one endpoint means the server distinguishes *unknown route* from
*bad payload*, so a 404 is a statement about the route and not about us. **Conclusion: a Fabric
data agent exposes no MCP endpoint on the Fabric MCP data plane.** Combined with ARM having no
`AzureFabric` category and `client.connections` being read-only, the portal step is the only
remaining path — see
[`foundry-fabric-bridge-agent/known_issues.md`](agents/foundry-fabric-bridge-agent/known_issues.md).

**Reusable rule:** before concluding a capability is absent, find an input that makes the same
surface fail *a different way*. Without that control, an absence claim is a guess wearing a
status code.

---

### 🔴 RETRACTED 2026-09-03 — the claim above is FALSE. A Fabric data agent *does* expose MCP.

The conclusion in bold above ("a Fabric data agent exposes no MCP endpoint") is **withdrawn**.
It is kept on the page because *how* it went wrong is worth more than the claim was.

**The endpoint, verified live** (Sweden Central, user token, 2026-09-03):

```
POST {fabric_api_base}/mcp/workspaces/{workspace_id}/dataagents/{agent_id}/agent
     Accept: application/json, text/event-stream

initialize  -> 200  serverInfo.name = "DataAgent MCP Server"
tools/list  -> 200  [{ "name": "DataAgent_<agent name>",
                       "inputSchema": {"properties": {"userQuestion": {"type": "string"}}} }]
```

Three MCP route families exist, and they do not share a shape:

| Target | Route |
| --- | --- |
| Data agent | `/mcp/workspaces/{ws}/dataagents/{id}/agent` |
| Ontology | `/mcp/dataPlane/workspaces/{ws}/items/{id}/ontologyEndpoint` |
| Semantic model | `/mcp/fabricaihub/integrations/m365` |

**Two independent mistakes produced the false negative, and either alone was enough.**

1. **Only one axis was varied.** All sixteen probes held
   `/mcp/dataPlane/workspaces/{ws}/items/{id}/` fixed and changed the trailing segment. The data
   agent route drops `dataPlane` *and* replaces `items` with `dataagents`. Sixteen results say
   nothing about a shape that was never sent. **A negative is only as wide as the space actually
   searched — and "sixteen tries" measures effort, not coverage.**

2. **The control was itself broken.** `/ontologyEndpoint` returned `500` / `-32603` because the
   probe omitted `Accept: text/event-stream`, which MCP streamable-HTTP requires. With the correct
   header the *same* URL returns **`200`**. So the row below claiming "500 proves the route is
   registered and reached" was an artefact of a malformed request. The control did fail
   differently — for a reason that had nothing to do with the question being asked.

The second one is the sharper lesson: **a control only controls if it is correct.** A
discriminating result from a broken client discriminates between two of *your* bugs, not between
two states of the service. Before trusting a control, prove the client is right by making it
succeed at least once against something known to work.

**What survives from the original section.** Re-probed 2026-09-03 with five different body shapes
(`AzureFabric` × {CustomKeys+credentials, AAD, UserEntraToken} × {API target, portal target}):
every one returns `Error when parsing request; unable to deserialize request body`, while
`category: "CustomKeys"` is accepted. So `AzureFabric` genuinely is not an ARM category — the
deserializer rejects the enum value regardless of the rest of the body. **That sub-claim was
correct.** What did not follow from it is the conclusion drawn next to it: *"the portal step is
the only remaining path"*. `AzureFabric` is the name of **one binding**, not of the goal. The goal
— Foundry querying the Fabric data agent — has a second binding that ARM creates without a portal:

| Tool | Connection it resolves | Creatable from ARM? |
| --- | --- | --- |
| `MicrosoftFabricPreviewTool` | `CustomKeys` / `AzureFabric` | **No** — portal only |
| `FabricIQPreviewTool` | `RemoteTool` / `GenericProtocol` over MCP | **Yes** |

The error message that misled the search — `No CustomKeys connection found for AzureFabric` —
names a category **you never create**. Searching ARM for the string in an error message is not the
same as searching for the capability the error is about.

**Corrected reusable rule.** Before concluding a capability is absent, state the *axes* the search
covered (name, path shape, category, tool, protocol) and name the ones it did not. Then verify the
control succeeds somewhere before trusting it to fail informatively. An absence claim without both
is a guess wearing a status code — and, written into a brain, it stops the next agent from looking
where the answer actually is.

**Still open, and honestly unresolved.** With the ARM connection created and the endpoint proven
reachable by a user token, the *service-side* call still answers
`returned HTTP 404 (Not Found) while enumerating tools`, in both endpoint modes (`server_url` sent
and omitted), after granting both Foundry system-assigned identities **Admin** on the Fabric
workspace, with all `ServicePrincipal*` Fabric tenant settings enabled. So the cross-service
identity hop is **not** settled here. Do not claim this binding works end to end from an
unattended script on the strength of this entry — the transport and the control plane are proven,
the runtime hop is not.

---

## Still unproven — do not claim these

- [ ] A2A **latency and cost** per hop — never measured
- [ ] A2A behaviour across **regions**, or under **GA** rather than preview
- [ ] Whether the hop **survives streaming** — not attempted
- [ ] The `WorkflowAgentDefinition.workflow` **string format** — still undocumented, still unread
- [ ] Whether **toolboxes** exist in this region — not seen in either lab or this tenant
- [ ] Any statement about a capability being **absent** — this file only proves presence.
      *Amended 2026-09-02:* absence **can** be proven when a control makes the same surface fail a
      different way — see "PROVEN ABSENT" above. Without such a control the bullet stands.
      *Re-amended 2026-09-03:* that amendment was applied to a case where it produced a **false**
      negative, twice over — the search varied one axis, and the control was malformed. The
      technique is not wrong, but it is far weaker than it read: a control must be shown to
      **succeed** somewhere before its failure is allowed to mean anything, and the axes searched
      must be stated. Treat every absence claim in this brain as provisional.
- [ ] Whether `FabricIQPreviewTool` can reach a Fabric data agent **from an unattended script**.
      Transport proven (MCP `200`, `tools/list` returns the tool) and the ARM connection proven
      creatable, but the service-side call still returns `404` while enumerating tools. Unresolved.
      **✅ Resolved 2026-09-03 — it can, and does.** The `404` was a **paused Fabric capacity**,
      which this surface reports as `404` with `CapacityNotActive` in the body while Foundry relays
      only the status. Resumed the capacity → the chain verifies **3/3 unattended, no portal step**.
      See the proof below.

## ✅ PROVEN 2026-09-03 — Foundry → Fabric data agent, unattended, deployed entirely from code

A supervisor calling a **Fabric data agent over MCP** and an **A2A subordinate**, both bound from
ARM, both firing correctly, verified by an oracle that asserts routing **by name and as a pair**
(the right tool fired **and** the other did not):

| Probe | Expected | Result |
|---|---|---|
| quantitative | Fabric fires, contracts stays out | ✅ `DataAgent_Zava_Media_Analyst` alone |
| contractual | contracts fires | ✅ A2A alone |
| the demo | both, one answer | ✅ both, single `### SOURCE` block |

- Connection: `RemoteTool` / `GenericProtocol`, `metadata.type = fabric_iq_preview`,
  `audience = https://api.fabric.microsoft.com`, created by `PUT` at api-version `2025-06-01`.
- **`authType`: both `UserEntraToken` and `ProjectManagedIdentity` work.** `AAD` and
  `AccountManagedIdentity` are rejected by ARM validation for this category. Prefer
  `ProjectManagedIdentity` unattended — it does not depend on a user token being exchangeable.
- The tool fires as **`DataAgent_<data agent name>`**, the MCP server's own tool name — *not* the
  connection name, which is what `MicrosoftFabricPreviewTool` would have used.
- `require_approval="never"` is required, or an unattended run hangs on consent.

**What this does not settle:** nothing about latency, cost or streaming; nothing about GA
behaviour (both tools are preview); and nothing about whether the data agent's own instructions
travel over MCP — **they do not**, so the guard rails must be restated in the calling prompt.

---

## Change log

| Date | Change |
| --- | --- |
| 2026-08-26 | File created. Promoted the 2026-08-04→05 hands-on session from a transcript in another repository into the brain: A2A live proof with the witness-agent method, the four-protocol chain, SDK 2.4.0 introspection, RAG scoping measures, the architecture rule, and the pointer to the Fabric non-determinism defect. |
| 2026-09-02 | A2A **reproduced on a second tenant** (Sweden Central), and the two prerequisites this file had omitted recorded: first-class `properties.audience`, and a `Foundry Agent Consumer` grant whose absence reports as **404**. Also flagged that "ARM only" settles the A2A connection and does **not** generalise to a Fabric data-agent connection, which ARM provably cannot create. |
| 2026-09-02 | Added **PROVEN ABSENT**: a Fabric data agent exposes no MCP endpoint (16 names → `404`/`-32601`, control `/ontologyEndpoint` → `500`/`-32603` on the same item). Amended the "only proves presence" bullet with the control-that-fails-differently technique. |
| 2026-09-03 | **Retracted the 2026-09-02 PROVEN ABSENT claim.** A Fabric data agent *does* expose MCP, at `/mcp/workspaces/{ws}/dataagents/{id}/agent` (`initialize` → `200`, `tools/list` returns the tool). Two independent errors: the search varied only the trailing name and never the path shape, and the `500` control was an artefact of omitting `Accept: text/event-stream` (the same URL returns `200` with it). Recorded the three MCP route families, the `RemoteTool`/`GenericProtocol` ARM connection that `FabricIQPreviewTool` resolves, and the fact that `AzureFabric` not being an ARM category — re-verified across five body shapes — never implied the goal was unreachable. Logged the still-unresolved service-side `404` so the entry does not overclaim. |
| 2026-09-03 | **Resolved that `404`, and promoted the chain to proven.** It was a **paused Fabric capacity**, which the data-agent MCP surface reports as `404` with `CapacityNotActive` in the body while Foundry relays only the status — so the umbrella rule *"capacity paused → 404"* was never reached, because the symptom arrived second-hand and reframed as a routing error. Added the full unattended proof (3/3, no portal step), the working `authType` set for `RemoteTool`, the `DataAgent_<name>` tool-naming rule, and the post-resume 100 s cold-start timeout. Two general habits recorded in [`ERROR_RECOVERY.md`](../ERROR_RECOVERY.md) § 2: re-send a relayed error yourself before believing its interpretation, and treat **identical failures across independent hypotheses** as acquitting all of them rather than as bad luck. |

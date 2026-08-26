# Known Issues — Foundry Knowledge Agent (Foundry IQ)

Two classes, never mixed. **Observed** means it happened in a tenant and there is a screenshot,
a lab step, or working code behind it. **Doc-sourced** means Microsoft says so and we have not
seen it. A false "verified" makes a downstream agent retry a path that cannot work.

---

## Observed — Microsoft "Building Foundry IQ" lab, 2026-08-04

### 1. The search service needs RBAC on the Fabric workspace — and nothing tells you

Before any Fabric IQ knowledge source will work, the **AI Search service** must be added to the
Fabric workspace via *Manage access* → *Add people or groups*, searched **by the search service
name**, with the **Contributor** role.

**Why it bites:** the failure surfaces as a knowledge source that never leaves `Creating`, or an
agent that answers from training data. Neither symptom names a permission.

**Rule:** the search service is a principal. Enumerate every system it must read and grant it
explicitly, before creating sources.

### 2. Knowledge source creation is asynchronous with no completion signal

The lab says it outright: *"If return policy displays Creating, refresh the browser and it should
change to Active."*

**Consequence:** there is no event to await. Anything automating this must poll, and a human must
verify. A source left at `Creating` is neither success nor failure.

### 3. A knowledge base is reached over MCP — with all that implies

`server_label`, `server_url` and `project_connection_id` are read from the project's
*Connected resources* page and passed to `MCPTool(...)`. Retrieval is therefore a tool call:
subject to approval gates, to tool-call ordering, and to whatever limits apply to tools.

**Consequence:** `require_approval="never"` in the lab's code is not a detail. Leave it at a
prompting value and a run will **pause waiting for a human** on every retrieval.

### 4. Source names carry no binding meaning

Observed: a source named `return-policy` is bound to the retail **Lakehouse**, not to any return
policy document. Names are free text set at creation.

**Rule:** never infer a source's content from its name. Open it.

### 5. The portal offers API-key auth first, and the lab takes it

Connecting the Foundry IQ resource offered an *Auth Type* dropdown; the lab selects **API Key**.

**Consequence:** the easy path is key-based. Fine for a lab, wrong as an inherited default.
Record which auth type each environment used, because nothing in the UI will remind you later.

### 6. Grounding does not survive a missing containment clause

Both grounded agents in the lab carry three separate clauses — *only from retrieved knowledge*,
*do not summarize or filter*, *say when the data could not be found*. Each prevents a different
failure. The third is the one people omit, and omitting it converts an empty retrieval into a
confident wrong answer.

### 7. ⚠️ Business data hardcoded into a grounded agent's prompt

`Inventory-Agent` is told *"The response must come only from the Fabric Data Agent tool output"*
and then given a literal list of product IDs "at risk of stockout" in the same prompt.

**This is a lab shortcut, not a pattern.** It makes the demo deterministic and it makes the
agent wrong the day the data changes. If you reuse this lab as a starting point, delete that
block first.

### 8. Two Fabric integrations, one lakehouse, no disambiguation in the UI

The same lakehouse is reachable as a **knowledge source** (Fabric IQ, OneLake catalog) and via a
**Fabric data agent tool**. Both can be attached to the same agent. Nothing warns you, and the
answer gives no clue which path produced it.

**Rule:** attach one. Write down which, and why.

---

## Proven in the operator's own tenant — 2026-08-05

Method and full scope: [`../../tenant_proofs.md`](../../tenant_proofs.md). SDK-driven, run
results read back programmatically. One tenant.

### 9. ✅ Scoping a retrieval agent to one entity holds up

A retrieval-grounded agent scoped to a single `customer_id` was asked for the verbatim material
attached to that customer.

| Measure | Result |
|---|---|
| Runs returning the complete expected set | **8 of 9 at 12/12** |
| Verified attributions | **11 of 11** — 0 hallucinated |

Retrieval scoping is therefore a **usable demo primitive**, not a hope. The one incomplete run
out of nine is the honest number: budget a re-ask, don't promise 100 %.

### 10. 🔑 The "non-counting contract" — and why a RAG agent must never count

The same agent was given an explicit instruction that producing **aggregate numbers** from
retrieved documents is not its job. That contract **held live**.

Write it into every retrieval agent. A RAG agent that is allowed to count will count **its own
retrieval window** and present the result as a business figure — arithmetically correct about
the wrong population, and impossible to spot in the answer text. There is no retrieval setting
that fixes this; the retrieval window *is* the bias.

**Rule:** a knowledge agent answers *what was said, by whom, where*. It **hands off** *how
many* to the agent that owns the measure — in a Fabric context, the data agent
(`Fabric-Brain/agents/ai-skills-agent`) via
[`../foundry-fabric-bridge-agent/instructions.md`](../foundry-fabric-bridge-agent/instructions.md).
Say so in the instructions, in one sentence, and test it with a counting question.

---

## Doc-sourced — not verified in a tenant

| Trap | Source | Note |
|---|---|---|
| Foundry IQ and the Fabric tools are **preview** | `azure/foundry/agents/how-to/tools/fabric-iq` | preview surfaces change without notice; re-check before every engagement |
| Indexed vs federated retrieval have different residency implications | product concept | stated here as an architectural consequence, not a compliance opinion |
| Embedding model choice affects retrieval quality and cost | general Azure AI Search guidance | the lab uses `text-embedding-ada-002` because it is the lab's model, not because it is the right one |

---

## Evidence discipline

A screenshot, or a lab step, is a **point in time** — not a state of the world. Twice already in
this brain a confident conclusion drawn from a single capture turned out to be wrong because a
later step changed the artifact.

So: if you cannot establish that an artifact was complete when it was captured, the mismatch is
an **open question**, not a finding. Open questions live below. They do not live in tables that
read as fact.

---

## Open questions

- Can the Foundry IQ resource be connected with **managed identity** instead of an API key? The
  dropdown had other entries; only `API Key` was exercised.
- What exactly does *content extraction mode* `Minimal` do, and what are the alternatives?
- Does a knowledge base enforce **permission trimming** per end user, or does it read uniformly
  as the search service? The lab's phrase "permission-aware" was never demonstrated.
- Can one knowledge base be shared across projects, or is it project-scoped?
- Is there a supported way to test retrieval **without** an agent in front of it?

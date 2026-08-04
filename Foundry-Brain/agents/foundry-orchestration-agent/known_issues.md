# known_issues — foundry-orchestration-agent

Every real failure goes here. This file is what turns documentation into a brain.

**Convention:** one entry per issue. State the *symptom first* — that's what a future reader
searches for. Mark whether the cause is confirmed against a tenant or inferred from docs.

---

## Doc-sourced traps (not yet observed in a tenant)

### Connected Agents samples do not port

**Symptom:** a tutorial uses `agent.as_tool(...)` or a "Connected Agents" panel; nothing
equivalent exists in the SDK or portal.
**Cause:** that sample targets the **classic** Agents API. Microsoft states plainly that the
Connected Agents tool "isn't available in the new Foundry Agent Service".
**Fix:** use the A2A tool. Mapping table at
`azure/foundry/agents/how-to/migrate#agent-tool-availability`.
**Status:** doc-confirmed, 2026-08-04.

### A sub-agent exists but is never reachable

**Symptom:** the target agent is created and works in the playground, but the supervisor's A2A
tool returns nothing usable.
**Cause:** incoming A2A was never enabled. Creating an agent does not publish an agent card.
**Fix:** PATCH `{BASE_URL}/agents/{agent}?api-version=v1` with both `agent_card` and
`agent_endpoint.protocol_configuration{responses, a2a}`.
**Trap within the trap:** this is **not available in the portal**, and the `agent_card` half
**cannot be set from the Python SDK** — REST only.
**Status:** doc-confirmed, 2026-08-04.

### The protocol silently falls back to v0.3

**Symptom:** behaviour differs from the v1.0 documentation for no obvious reason.
**Cause:** both versions are served on the same base path; with no version signal Foundry
serves **v0.3** by design.
**Fix:** fetch `…/agentCard/v1.0` (SDKs negotiate from `protocolVersion`), or set header
`A2A-Version: 1.0`, or append `?a2a-version=1.0`.
**Status:** doc-confirmed, 2026-08-04.

### Fabric data agent cannot go in a toolbox

**Symptom:** the toolbox refuses the Fabric data agent, or it never appears to the agent.
**Cause:** the toolbox support matrix lists **Fabric data agent = direct integration only**.
`Fabric IQ`, by contrast, *is* toolbox-supported.
**Fix:** attach the Fabric data agent directly to the agent. A supervisor legitimately ends up
with a toolbox *plus* a few direct tools.
**Status:** doc-confirmed, 2026-08-04. An earlier draft of `orchestration_patterns.md` claimed
the opposite — corrected the same day.

### Two hostnames, and the docs disagree

**Symptom:** an endpoint copied from one sample 404s in another context.
**Cause:** A2A paths are documented on `{account}.services.ai.azure.com`, while several
current-generation samples write the project endpoint as `{resource}.ai.azure.com`. Within a
single Microsoft page both forms appear.
**Fix:** read both from the portal, record both in `resource_ids.md`, never infer one from the
other.
**Status:** ⚠️ **unresolved contradiction in the source documentation**. Needs tenant
confirmation.

### Two different minimum SDK versions

**Symptom:** `A2APreviewTool` imports fine but the call that enables incoming A2A fails.
**Cause:** the A2A *tool* page pins `azure-ai-projects>=2.0.0`; the *enable incoming A2A* page
pins `>=2.3.0`.
**Fix:** install the higher floor when doing both sides.
**Status:** doc-confirmed, 2026-08-04.

### Streaming does not cross the A2A hop

**Symptom:** a sub-agent's answer arrives as one block despite streaming being enabled.
**Cause:** streaming responses (SSE) are **not supported on the incoming A2A endpoint**. Only
the text modality is supported at all.
**Fix:** stream from the supervisor to the client; treat the delegation itself as atomic.
Don't design a demo around token-by-token output from a sub-agent.
**Status:** doc-confirmed, 2026-08-04 (listed under Limitations).

### RBAC role names are mid-rename

**Symptom:** the portal shows `Azure AI User` where the docs say `Foundry User`.
**Cause:** rename in flight. Role IDs and permissions unchanged.
**Fix:** treat the pairs as synonyms. The *calling* identity needs **Foundry Agent Consumer**
on the target's project — a distinct, more granular role.
**Status:** doc-confirmed, 2026-08-04.

---

## Tenant-observed issues

Observed across two complete multi-agent systems in Microsoft training labs (2026-08-04).
Full write-ups: [`../../reference_workflow.md`](../../reference_workflow.md),
[`../../reference_foundry_iq.md`](../../reference_foundry_iq.md).

### The router contract is exact string equality — a newline breaks the system

Both dispatchers route with Power Fx string equality on the router's text:

```
=Last(Local.Var5755).Text = "Sales-Associate-Agent"
```

That is why both router prompts, written by different authors for different domains, carry the
same clause: *"Return only the agent name no extra space or new line simple string."*

**This is a type contract, not a style preference.** A trailing newline, a quote, or a polite
preamble makes every condition false and the request falls into the else branch. If you write a
router, state the contract in the prompt **and** verify it with one live run.

### The else branch is where every routing failure lands, and it was wrong in both systems

| System | `elseActions` | Failure mode |
|---|---|---|
| Microsoft-IQ | `SendActivity Local.Var4471` | emits the router's **raw output** — a bare agent name — as the product's answer |
| FoundryIQ | `SendActivity " "` | a single space: the user gets **nothing**, and no error is raised |

Neither raises an error. Neither is distinguishable from a valid decision. Design the else
branch deliberately, and make it say something.

### One system's level-1 condition tests a single value, so the error path is a valid branch

The supervisor is documented as choosing between two agents; the YAML tests
`= "Inventory-Agent"` and sends **everything else** to the level-2 router. A malformed, empty, or
hallucinated response therefore routes plausibly and silently. Prefer an explicit condition per
agent plus a real else.

### Captured variables are written and never read

`Local.Var7934`, `Local.Var8202`, `Local.Var9934` in one workflow; `Local.Var2679` in the other.
All inert. Every agent reads `=System.LastMessage`; **no observed step ever feeds a previous
step's variable forward.** If you rely on structured hand-off between agents, verify it in
**Traces** before believing it — see the open question in
[`../../orchestration_patterns.md`](../../orchestration_patterns.md).

### 🔒 Tool approval cannot be granted inside a workflow preview

Microsoft's own lab note:

> *"Before validating the workflow, test the individual agents and approve the tools. Tool
> approval cannot be completed within the workflow preview and may result in errors."*

The preview has no surface for the consent prompt, so the run **errors** instead of pausing —
with a message that never mentions approval. **Order matters:** run each tool-bearing agent
alone, force the tool call, approve, *then* run the workflow. This is the single most likely
reason a freshly published workflow fails on its first demo.

### `autoSend` is a strategy choice and the two observed systems chose opposites

`true` on one synthesizer (one voice, product-shaped) vs `true` everywhere (narrate every hop,
demo-shaped). Same flag, opposite outcomes, invisible in review. Decide before writing the YAML.

### Routers hold no tools — in both systems

Every router and every synthesizer observed had an **empty** tool set. The agent that decides has
no power to act. Free property, removes a whole class of failure. Keep it.

### Agent names are string literals duplicated across prompts and YAML

A rename must be applied in the router prompt, in every `condition`, and in every
`InvokeAzureAgent.agent.name`. Nothing reconciles them. There is no rename operation.

### Versions accumulate and Save ≠ Publish

Agent version counts in the high double and triple digits were observed on a lab tenant, with no
pruning. Every re-run of a creation script is a release. Before demoing, verify which version is
**published**.

---

After your own first live attempt, add the real error text here. That delta is the whole point of
this file.

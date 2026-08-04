# Known Issues — Foundry Fabric Bridge Agent

Two classes, never mixed. **Observed** means it happened in a tenant, with a screenshot, a lab
step, or working code behind it. **Doc-sourced** means Microsoft says so and we have not seen it.

---

## Observed — Microsoft labs, 2026-08-04

### 1. Tool approval cannot happen inside a workflow preview

Microsoft states it in the lab, unprompted:

> *"Before validating the workflow, test the individual agents and approve the tools. Tool
> approval cannot be completed within the workflow preview and may result in errors."*

**Why it bites:** the failure appears as a workflow error, not as a pending approval. There is
nothing in the message pointing at consent.

**Fix / order of operations:** open each Fabric-bound agent alone → ask something that forces the
tool call → approve (*Always approve this tool*) → then run the workflow.

**This confirms and sharpens an earlier finding.** Tool invocation pauses the run and shows the
operator the concrete call with its arguments. That gate is real; the workflow preview simply has
no surface to render it on.

### 2. The two binding styles are sequential, not alternative — an earlier reading was wrong

A previous pass through the docs recorded "portal binding by GUID" and "SDK binding by
connection" as two competing options. Working code shows they are one flow:

- the **portal** takes `Workspace ID` + `Artifact ID` and produces a **named project connection**;
- the **SDK** calls `project_client.connections.get(<name>)` and passes `connection.id` into
  `ToolProjectConnection`.

**Consequence:** code never contains a Fabric GUID. Environment promotion is a connection swap.
Any instruction that tells you to paste GUIDs into a script is wrong.

### 3. `allow_preview=True` is mandatory and easy to miss

`AIProjectClient(endpoint=..., credential=..., allow_preview=True)` — without it the Fabric
preview tool is not available. The type names themselves flag the maturity:
`MicrosoftFabricPreviewTool`, `FabricDataAgentToolParameters(...)`, field
`fabric_dataagent_preview`.

### 4. The two GUIDs must be scraped out of a browser URL by hand

The lab's own instruction: workspace ID is *"the string that appears between `groups/` and
`/aiskills`"*; artifact ID is *"between `aiskills/` and `?` (do not include the `?`)"*.

**Consequence:** the portal path is brittle and unautomatable. The trailing-`?` warning exists
because people include it.

### 5. ⚠️ The lab's own Fabric-bound agent contradicts itself

`Inventory-Agent` is instructed *"The response must come only from the Fabric Data Agent tool
output"* — and its prompt then hardcodes ten product IDs as "at risk of stockout".

**This is a demo shortcut, not a pattern.** It guarantees the demo lands and guarantees the agent
is wrong the day inventory changes. Delete that block before reusing the agent.

### 6. You inherit the Fabric agent's business definitions, sight unseen

The observed Fabric data agent defines, in its own instructions:
`Revenue = Sum(order_lines.LineTotalAmount)`, `Return Rate = Returns / Orders`, and a full
table-to-domain mapping.

**Consequence:** your Foundry agent quotes those definitions whether or not anyone on the Foundry
side read them. A mismatch produces answers that are internally consistent and externally wrong.
Read that block before shipping; change it only in Fabric.

### 7. The AI Search service — not the user — needs Contributor on the Fabric workspace

Relevant when the lakehouse is reached as a **knowledge source** rather than as a tool. Added in
Fabric via *Manage access* → *Add people or groups*, searching for the **search service name**.
Detail owned by `foundry-knowledge-agent`; recorded here because the two Fabric paths get
confused with each other.

### 8. Both Fabric integrations can be attached to the same agent, silently

Nothing warns you, and the response carries no marker of which path produced it.

---

## Doc-sourced — not verified in a tenant

| Trap | Source | Note |
|---|---|---|
| Fabric tool and Fabric IQ are both **preview** | `azure/foundry/agents/how-to/tools/fabric`, `…/fabric-iq` | re-check before every engagement |
| Fabric IQ supports **background mode** for long-running data agent work | `…/tools/fabric-iq` | never exercised here |
| Identity passthrough semantics across the Foundry → Fabric hop | product docs | the lab used a single lab identity throughout, so nothing was proven about delegation |
| Fabric data agents are a Fabric-side artifact with their own lifecycle | `fabric/data-science/data-agent-foundry` | consistent with what was observed |

---

## Evidence discipline

A screenshot, or a lab step, is a **point in time** — not a state of the world. Item 2 above is
an entry in this brain's correction log: a confident conclusion drawn from docs alone that
working code later overturned.

If you cannot establish that an artifact was complete when it was captured, the mismatch is an
**open question**, not a finding.

---

## Open questions

- Does the Foundry → Fabric hop carry the **end user's** identity, or the project's? Nothing in
  the lab distinguished them — one identity was used throughout.
- Can the project connection be created **without** the portal (CLI, Bicep, SDK)? Only the portal
  path was observed.
- `project_connections` is a list — what happens when a tool fronts several Fabric data agents?
  How does the model choose between them?
- Is there a background/async mode reachable from `MicrosoftFabricPreviewTool`, matching what the
  Fabric IQ docs describe?
- What does the Fabric side see in its own audit log when a Foundry agent calls it?

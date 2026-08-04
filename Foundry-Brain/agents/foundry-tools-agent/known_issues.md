# Known Issues — Foundry Tools Agent

Two classes, never mixed. **Observed** means it happened in a tenant, with a screenshot, a lab
step, or working code behind it. **Doc-sourced** means Microsoft says so and we have not seen it.

---

## Observed — Microsoft labs, 2026-08-04

### 1. The model silently gates the tool list

`Code interpreter` appeared greyed out in the tool picker with the tooltip *"This tool doesn't
work with the model you selected."* This constraint appears in no documentation we found.

**Consequence:** designing the tool set before choosing the model can produce an agent that
cannot be built. Choose the model first.

### 2. Tool approval cannot be granted inside a workflow preview

Microsoft's own lab note:

> *"Before validating the workflow, test the individual agents and approve the tools. Tool
> approval cannot be completed within the workflow preview and may result in errors."*

**Why it bites:** the preview has no surface for the consent prompt, so instead of pausing, the
run **errors** — with a message that never mentions approval.

**Fix:** run each tool-bearing agent alone in the playground, force the tool call, approve
(*Always approve this tool*), then run the workflow.

### 3. A hanging run is often a pending approval

Invocation pauses execution and renders the concrete call:

```
GetDirectReportsDetails({ "userId": "…", "select": "displayName,mail,job…" })
        [ ✓ Approve ▾ ]  [ ✗ Deny ]
           ├ Approve once
           ├ Always approve this tool
           └ Always approve all tools
```

**Rule:** before debugging a stalled agent, check for a pending consent prompt.

### 4. `require_approval="never"` is the lab's default, and it should not be yours

The working script sets it on its MCP tool. That is correct for unattended read-only retrieval
and wrong for anything with a side effect. Nothing in the platform distinguishes the two for you.

### 5. Preview tools are invisible without `allow_preview=True`

`AIProjectClient(endpoint=…, credential=…, allow_preview=True)`. Omit it and the preview tool is
simply absent — the failure does not name preview as the cause.

### 6. Tool families are per-capability, and that is a feature

`Work IQ Mail`, `Calendar`, `Teams`, `OneDrive`, `Word`, `User` attach individually. A six-agent
system was observed with **zero capability overlap** between agents.

**Consequence:** over-attaching is a choice, not a default. Take the granularity.

### 7. Two of five agent roles hold no tools at all

Routers and synthesizers were observed with an empty tool set. *The agent that decides has no
power.* This separation costs nothing and removes a whole class of failure.

### 8. Tool changes are a new agent version, and versions accumulate

Tools are part of the definition passed to `create_version`. Version counts in the high double
and triple digits were observed on a lab tenant, with no visible pruning.

**Consequence:** every re-run of a creation script is a release. Verify which version is
**published**, not just which was saved.

### 9. 🔎 Programmatic approval is hinted at but was never exercised

The lab's `agents.py` imports `McpApprovalResponse` and `ResponseInputParam` from
`openai.types.responses.response_input_param` — **and never uses them.**

That strongly suggests approvals can be answered through the responses API rather than only by a
human in the portal. **Recorded as a lead, not as a capability.** No code path was observed. See
open questions.

---

## Doc-sourced — not verified in a tenant

| Trap | Source | Note |
|---|---|---|
| The current generation has its own **tool catalog** and **toolboxes** (GA) | `azure/foundry/agents/concepts/tool-catalog` | no toolbox was observed in either lab; unknown whether the region had them |
| Classic tool docs live under `…/agents/how-to/tools-classic/…` | classic tree | do not follow them — retires 2027-03-31 |
| Function calling, OpenAPI tools, file search exist in the catalog | tool catalog | none exercised here |
| Toolbox = curated bundle behind one managed MCP endpoint | `…/concepts/tool-catalog` | consistent with knowledge bases being reached over MCP, but that is inference, not evidence |

---

## Evidence discipline

A screenshot, or a lab step, is a **point in time** — not a state of the world. This brain has a
correction log because confident conclusions drawn from single captures have been wrong twice.

If you cannot establish that an artifact was complete when captured, the mismatch is an **open
question**, not a finding.

---

## Open questions

- What are the legal values of `require_approval` besides `"never"`? Only one was seen.
- Can approvals be answered programmatically via `McpApprovalResponse`? The import exists; the
  usage does not.
- Can an approval posture be set as **tenant or project policy**, rather than per tool and per
  operator?
- Do **toolboxes** exist in the observed region? Neither lab used or displayed one.
- Does *Always approve all tools* persist per user, per agent, or per project?
- What do the `Catalog` and `Custom` tabs in the tool picker contain?

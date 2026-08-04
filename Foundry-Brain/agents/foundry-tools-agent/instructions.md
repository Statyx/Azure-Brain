# Foundry Tools Agent

> **Generation:** targets the **current** Foundry Agent Service (`azure/foundry/agents/*`).
> Read [`../../generation_map.md`](../../generation_map.md) first — the classic tree
> (`azure/foundry-classic/agents/*`) retires **2027-03-31** and its tool docs
> (`…/agents/how-to/tools-classic/…`) do not apply.
>
> **Evidence status:** the mechanics below were observed across two Microsoft training labs
> (2026-08-04) — portal flows, a live run with tool approvals, and a working `agents.py`.
> Source: [`../../labs/foundry-iq/raw_capture.md`](../../labs/foundry-iq/raw_capture.md) and
> [`../../portal_reality.md`](../../portal_reality.md). Doc-derived material is labelled inline.

---

## Core Identity

You own **what an agent can do** — the tool layer between a prompt and the outside world:
choosing tools, connecting them, and setting their approval posture.

You do not own the prompt (→ `foundry-agent-service-agent`), the Fabric specifics
(→ `foundry-fabric-bridge-agent`), the knowledge bases (→ `foundry-knowledge-agent`), or the
routing graph (→ `foundry-orchestration-agent`).

The one thing to get right:

> **A tool is the only thing in the system that can actually cause an effect.**
> Prompts express intent. Tools carry it out. Design the tool set as a permission boundary and
> the prompt becomes much less dangerous to get wrong.

---

## Mandatory Rules

1. **Choose the model first.** Model availability **gates** tool availability. Observed:
   `Code interpreter` greyed out with *"This tool doesn't work with the model you selected."*
   Designing tools before the model can produce an unbuildable agent.
2. **Attach the minimum.** Tool families are **per-capability**, not per-product. An agent that
   needs the org chart gets the org-chart tool and nothing else. Then no prompt injection can
   make it send mail.
3. **`allow_preview=True` for any preview tool.** Without it, the tool is simply not there, and
   the error does not say "preview".
4. **Set `require_approval` deliberately, per tool, and write down why.** It is the difference
   between a run that pauses for a human and one that does not.
5. **Pre-approve interactively before running any workflow.** Approval cannot be granted inside a
   workflow preview — see the gate section. This is an operational rule, not a preference.
6. **Prefer a named project connection over inline credentials or GUIDs.** Connections are what
   makes an agent script portable across environments.
7. **Changing tools means a new agent version.** Tools are part of the definition passed to
   `create_version`. Treat a tool change as a release, not an edit.
8. **Never claim verified without a trace.** Doc-derived shapes are *expected*, not proven.

---

## The tool taxonomy, as observed

| Kind | How it is attached | Observed instances |
|---|---|---|
| **Built-in catalog tool** | `Tools` → *Connect a tool* → pick from the catalog | `Fabric Data Agent`, `Code interpreter`, the Work IQ family (`User`, `Mail`, `Calendar`, `Teams`, `OneDrive`, `Word`) |
| **MCP tool** | `MCPTool(server_label, server_url, project_connection_id, require_approval)` | a **Foundry IQ knowledge base** — retrieval is an MCP server |
| **Typed preview tool** | a dedicated SDK type wrapping a project connection | `MicrosoftFabricPreviewTool(fabric_dataagent_preview=…)` |
| **No tools at all** | — | routers and synthesizers; see below |

> **Two of the five agent roles hold no tools.** A router decides and a synthesizer speaks; only
> wrappers, action agents and resolvers touch anything. *The agent that decides has no power* —
> that separation is the strongest structural property in the observed designs, and it is free.

### Work IQ is a family, not a connector

`Work IQ Mail`, `Work IQ Calendar`, `Work IQ Teams`, `Work IQ OneDrive`, `Work IQ Word`,
`Work IQ User` are attached **individually**. Observed distribution across a six-agent system had
**zero overlap** — each agent held exactly the capabilities its job required. Copy that.

---

## 🔒 The three layers of control

This is the model to carry into any security conversation about agents. All three were observed;
they are not equivalent and they are not substitutes.

| Layer | What it is | What it actually does |
|---|---|---|
| Prompt guardrails (*"only if authorized"*) | a **default**, expressed in text | biases behaviour; enforces nothing |
| The attached tool set | a **boundary** | the agent cannot act outside it, whatever the prompt says |
| **Tool-call approval** | a **control** | a human sees the concrete call and its arguments, and can refuse |

Observed approval prompt, from a live run:

```
Context:
  GetDirectReportsDetails({ "userId": "…", "select": "displayName,mail,job…" })
                                                     [ ✓ Approve ▾ ]   [ ✗ Deny ]
                                                        ├ Approve once
                                                        ├ Always approve this tool
                                                        └ Always approve all tools
```

Two operational consequences worth internalising:

- **A run that seems to hang may simply be waiting for consent.** Check for a pending approval
  before debugging anything else.
- **In a demo, approve the first call on screen** to show the gate exists, then switch to
  *Always approve all tools*. That is the right reflex in a demo and the wrong default to inherit
  anywhere else.

### The workflow trap

Microsoft states it plainly in the lab:

> *"Before validating the workflow, test the individual agents and approve the tools. Tool
> approval cannot be completed within the workflow preview and may result in errors."*

The workflow preview has no surface on which to render the consent prompt, so instead of pausing
it **errors** — and the error does not mention approval.

**Required order:** run each tool-bearing agent alone → force the tool call → approve → then run
the workflow.

### `require_approval` in code

```python
mcp_tool = MCPTool(
    server_label=server_label,
    server_url=server_url,
    project_connection_id=project_connection_id,
    require_approval="never",     # observed value
)
```

`"never"` is what the lab uses, and it is why its script-created agents run unattended. It is the
correct setting for a read-only retrieval tool in a pipeline, and the wrong one for anything with
a side effect.

> **Decide per tool.** A knowledge base lookup and a "send mail" action do not deserve the same
> posture, and nothing in the platform will make that distinction for you.

> 🔎 **Observed but unexercised.** The lab's `agents.py` imports
> `McpApprovalResponse` and `ResponseInputParam` from `openai.types.responses.response_input_param`
> — and never uses them. That is a strong hint that approvals can be answered
> **programmatically** through the responses API, rather than only by a human in the portal.
> Recorded as a lead, **not** as a capability: no code path was seen. See *open questions*.

---

## Connecting a tool — the portal step that code depends on

Most external tools resolve through a **project connection**. The pattern is consistent:

1. `Tools` → `Tools` → **Connect a tool**
2. Pick the tool type from the catalog → *Add tool*
3. Fill the connection form — always including a **Name** you choose
4. **Connect**

That name is the contract. In code you never reference the underlying identifiers:

```python
connection = project_client.connections.get(connection_name)   # by NAME
# … then pass connection.id into the tool's parameters
```

**Put the connection name in configuration.** The lab does exactly this — `parameters.env` holds
`fabric_connection_name`, and the script reads it. That single habit is what lets the same script
run against dev, test and prod unchanged.

---

## Attaching tools to an agent

Tools are part of the **definition**, supplied when a version is created:

```python
project_client.agents.create_version(
    agent_name="Rewards-Campaign-Agent",
    definition=PromptAgentDefinition(
        model=model,
        instructions=...,
        tools=[mcp_tool],          # ← a list; one tool object can be reused across agents
    ),
)
```

Two properties worth exploiting:

| Property | Use it for |
|---|---|
| `tools` is a **list** | an agent can hold several tools — but see Rule 2 before you do |
| A tool object is **reusable** | observed: one `mcp_tool` shared by two agents, so the knowledge binding is defined once |

And one to respect: **changing the tool list is a new version.** Agent versions accumulate
(counts in the high double and triple digits were observed on a lab tenant). Every re-run of a
creation script is a release.

---

## Choosing an approval posture

| Tool does | Suggested posture | Reason |
|---|---|---|
| Read-only retrieval in an unattended pipeline | `never` | consent adds nothing; the boundary is the tool set |
| Read-only, but over sensitive data | prompt at least once | the operator should see the arguments |
| Anything with a side effect (send, write, delete, share) | always prompt | this is the only place a human can still intervene |
| Demo of the platform's governance story | prompt once on camera, then relax | the gate is worth showing; the friction is not |

---

## Hard limitations (recorded 2026-08-04)

| Limitation | Consequence |
|---|---|
| The model gates the tool list, silently until you try | pick the model first; a greyed tool is not a bug |
| Preview tools need `allow_preview=True` | and their SDK type names say `Preview` — treat that as a stability warning |
| Approval cannot be granted in a workflow preview | pre-approve, always |
| Tool changes require a new agent version | versions accumulate; there is no visible pruning |
| Portal connection creation is manual | script it where a path exists; otherwise it is a documented runbook step |

---

## Error recovery

| Symptom | Likely cause | Action |
|---|---|---|
| A tool is greyed out in the picker | the selected model does not support it | change the model, or drop the tool |
| A preview tool is absent entirely | `allow_preview=True` missing on the client | add it |
| The run hangs with no output | pending tool approval | look for the consent prompt before debugging |
| A workflow errors on a tool-bearing agent | approval cannot be granted inside the preview | run the agent alone, approve, retry |
| `connections.get(name)` fails | connection missing or misnamed | recreate it; names are exact |
| The agent ignores its tool | the prompt does not name the tool or its argument | name both explicitly — *"send the product name to the X tool"* |
| Behaviour did not change after editing tools | a new version exists but is not the served one | check which version is published |
| An agent does something it should not | the tool set is too broad | fix the boundary, not the prompt |

---

## Handoff protocol

| When | Hand off to | With |
|---|---|---|
| The prompt or output contract needs work | `foundry-agent-service-agent` | the role and the consumer |
| The tool is a Fabric data agent | `foundry-fabric-bridge-agent` | connection name, workspace ID, artifact ID |
| The tool is a Foundry IQ knowledge base | `foundry-knowledge-agent` | knowledge base name and its sources |
| Tools must be sequenced across several agents | `foundry-orchestration-agent` | agent names and output contracts |
| Connections, RBAC or networking must be provisioned | `foundry-project-agent` *(planned)* | resource names and identities |
| Content filters / responsible-AI controls | `foundry-governance-agent` | risk types and scope — **layer 4**, the one you don't own |

---

## Verification checklist

- [ ] Model chosen **before** the tool set
- [ ] Every attached tool is required by the agent's job — no spares
- [ ] `allow_preview=True` where any preview tool is used
- [ ] `require_approval` set per tool, deliberately, and the reason written down
- [ ] Every tool-bearing agent run **alone** and approved before any workflow run
- [ ] Connection names live in configuration, not in code
- [ ] The prompt names the tool and the argument to send it
- [ ] Tool changes treated as a version bump, and the served version verified

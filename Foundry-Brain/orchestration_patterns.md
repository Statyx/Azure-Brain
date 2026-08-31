# Orchestration Patterns — supervisor + connected agents/tools

> **Prerequisite:** read [`generation_map.md`](generation_map.md) first. It records why the
> classic pattern is gone and which clocks are running.
> **Status:** documented from Microsoft Learn on 2026-08-04. Treat every code shape below as
> *expected*, not *proven* — **with one exception**: the **A2A tool** was executed end to end
> against a real tenant on 2026-08-05, with a run trace and a control agent behind it. See
> [`tenant_proofs.md`](tenant_proofs.md).
>
> 📐 **For a complete worked example**, see
> [`reference_workflow.md`](reference_workflow.md) — a seven-agent orchestration observed
> end to end, with the diagram, the demo script, and the full YAML.

## The target pattern

One **supervisor** agent, with specialised capabilities attached directly to it:

```
                    ┌──────────────────────────┐
   user  ─────────► │   SUPERVISOR AGENT       │
                    │   (Prompt Agent)         │
                    └───┬──────────────────┬───┘
                        │                  │
              A2A tool  │                  │  MCP tool (toolbox)
                        ▼                  ▼
              ┌──────────────────┐   ┌──────────────────────┐
              │ sub-agent        │   │ TOOLBOX              │
              │ (Foundry agent   │   │  ├─ Microsoft Fabric │──► Fabric Data Agent
              │  with incoming   │   │  ├─ OpenAPI          │──► Fabric REST
              │  A2A enabled)    │   │  └─ Function calling │──► custom
              └──────────────────┘   └──────────────────────┘
```

Two attachment mechanisms, and the choice between them is the whole design decision.

## Decision: which mechanism for which need

| You want the supervisor to… | Use | Status | Retires |
| --- | --- | --- | --- |
| **classify** a request and let external code dispatch it | **Router agent** — returns a name, calls nothing | GA (it's just a prompt) | — |
| call a **capability** (query Fabric, hit an API, run code) | **Toolbox** → attached as one MCP tool | **GA** | — |
| call **another agent** that reasons and holds its own instructions | **A2A tool** | preview · ✅ [proven in one tenant](tenant_proofs.md) | — |
| follow a **fixed, declarative process** with branching and approvals | Portal **Workflows** | preview | ⚠️ **2026-12-01** |
| orchestrate **in code**, durably | **Microsoft Agent Framework** | — | — (recommended) |
| replicate classic `agent.as_tool` / Connected Agents | ❌ **nothing** — removed | — | — |

### Ruling for demos built on this brain

**Start with the router.** Promote to A2A only when a supervisor genuinely needs to *hold the
conversation* across sub-agent calls. See the pattern below — it was observed in a Microsoft
training lab, and it costs one model call per turn where A2A costs three.

⚠️ **Read this ruling as a cost argument, not a feasibility one.** A2A **works** — proven on a
real tenant with SDK 2.4.0, ARM-created connection, `a2a_preview_call` items in the trace and a
control agent that could not answer without the tool ([`tenant_proofs.md`](tenant_proofs.md)).
*"A2A might not work"* is no longer a reason to avoid it. *"A2A spends three model calls per
turn on a preview surface"* still is. Choose on price and blast radius, not on doubt.

When the supervisor must call: **Supervisor = Prompt Agent. Sub-agents = A2A. Capabilities =
Toolbox.**

Portal Workflows are legitimate to *stage* a visual demo before 2026-12-01, but they are
never written into an instruction file as the recommended path. A brain that teaches a
feature with a four-month runway is a brain that will be wrong by design.

---

## Pattern A — the Router agent (observed in a Microsoft training lab, 2026-08-04)

The simplest supervisor **calls nothing**. It reads the query, decides, and returns *the name of
the agent that should handle it* as a bare string. Something outside — application code, a
workflow, an Agent Framework loop — performs the dispatch.

```
   user ──► ROUTER AGENT (Prompt Agent) ──► "Inventory-Agent"
                                                  │
                                    external dispatcher reads the string
                                                  │
                        ┌─────────────────────────┴──────────────────────┐
                        ▼                                                ▼
                 Inventory-Agent                          Work-IQ-Orchestrator-Agent
                 (Fabric data)                            (M365: Mail, Teams, Calendar,
                                                           SharePoint, OneDrive, Word)
```

### Why this is the right default

| | Router | A2A supervisor |
| --- | --- | --- |
| Preview surface used | none | A2A (preview) |
| Incoming-A2A PATCH per sub-agent | not needed | required, REST-only |
| `Foundry Agent Consumer` grants | not needed | required |
| Protocol version traps | none | v0.3 fallback, JSONRPC-only v1.0 |
| Streaming | unaffected | not supported across the hop |
| Testable | trivially — one string in, one string out | needs a live hop |
| Cost per turn | one classification call | classification + delegation + synthesis |
| Supervisor can combine several sub-agents in one answer | ❌ no | ✅ yes |
| Dispatch logic lives | outside Foundry | inside Foundry |
| Executed end to end in a real tenant | ✅ (two labs) | ✅ ([one tenant, SDK 2.4.0](tenant_proofs.md)) |

The router trades *capability* for *cost and blast radius* — **not** for reliability, which is
the trade this table originally implied. Both columns have now run for real. For a demo, a
training, or any first iteration, the router's trade is still almost always correct. Reach for
A2A when the supervisor must genuinely reason **over the results** of several sub-agents — and
budget the extra model calls when you do.

### Instruction-design rules extracted from the observed router

The lab's router prompt is a good specimen. Six things it does deliberately:

1. **One agent per query, stated as a hard constraint** — *"route it to exactly one specialized
   agent"*. Ambiguity in the output format is the main failure mode of a router.
2. **A capability paragraph per agent, then a separate rules list.** Description and decision
   logic are not mixed. The description teaches the model the domain; the rules resolve edges.
3. **The boundary is drawn on the verb, not the noun.** Inventory *data or recommendations* goes
   to the data agent; inventory *action execution* goes to the M365 agent. The same business
   word splits two ways — and that split is the entire routing contract.
4. **Explicit trigger lexicons for the ambiguous class** — the policy/approval branch lists its
   own keywords (`authorized`, `approve`, `sign-off`, `permitted`, `policy`, `SOP`, `procedure`,
   `governance`, `who can`). Cheaper and far more stable than hoping the model infers it.
5. **A stated tie-breaker.** *"Combined data + action → the action agent."* Every router needs
   one rule for requests that legitimately match two branches.
6. **The output format is over-specified on purpose** — *"plain string, no quotes, no extra
   whitespace, no newline"* — because a parser, not a human, consumes it.

> Rule 6 of `foundry-orchestration-agent` says "name the routing contract". This lab prompt is
> what that looks like when done properly. Reuse its shape.

### Where it breaks

- No sub-agent result ever reaches the router, so it cannot **synthesize** across agents.
- The dispatcher is now **your** code, and it is a real component: it must handle an unknown
  name, an empty string, or a model that answers in a sentence despite the instruction.
- Validate the returned string against an allow-list. Never `eval` it into a call.

---

## Pattern B — the Thin Wrapper agent (observed in the same lab)

The sub-agent that fronts Fabric **adds no reasoning of its own**. Its entire job is to forward
the question to the Fabric data agent and shape the answer. Observed instruction set, in full:

```text
## Role
You answer questions about products, orders, inventory, shipments, stores,
warehouses, customers, and the workforce that handles them, including the
operational impact of events (e.g. a person on leave).

## Tool
You have the Fabric Data Agent as a tool. Forward the user's question to it
and return its response. Do not invent numbers.

## Response shape
Short, factual, label : value lines. Currency includes the symbol; counts are
integers. No prose padding, no tool names, no reasoning steps.
```

Roughly 90 words — against ~6,000 characters of instructions in the Fabric data agent behind it.

### The rule this encodes: one source of semantic truth

The Fabric data agent already owns the business vocabulary, the metric definitions, the table
relationships and the source routing. **The Foundry agent must not restate any of it.**

Duplicating that layer is the single most likely way to break this architecture: the two copies
drift, and the model then holds two contradictory definitions of "revenue". The Foundry agent
gets exactly three responsibilities — **scope, delegation, and output shape** — and nothing else.

| Layer | Owns | Must not own |
| --- | --- | --- |
| Fabric data agent | vocabulary, metrics, joins, table routing, NL2SQL | presentation |
| Foundry wrapper agent | scope statement, delegation, response shape | anything semantic |

### Four techniques worth copying

1. **Explicit delegation verb** — *"Forward the user's question to it and return its response."*
   Leaves no room for the model to answer from its own weights.
2. **`Do not invent numbers`** — a targeted anti-hallucination guard on the one thing that
   *looks* right when it is wrong. Any agent fronting numeric data needs this line.
3. **Output shape specified to the character** — `label : value`, currency carries its symbol,
   counts are integers. Deterministic output is what makes an agent composable.
4. **`No tool names, no reasoning steps`** — stops the agent narrating its own plumbing into the
   answer. Essential when a router or another agent consumes the text downstream.

### Observed architecture, complete

```
   user
     │
     ▼
  Supervisor-Agent ──── returns a name, calls nothing ────► external dispatcher
   (Pattern A: router, Prompt agent, gpt-5.5, no tools)              │
                                                                    │
                    ┌───────────────────────────────────────────────┴──────────┐
                    ▼                                                          ▼
           Inventory-Agent                                    Work-IQ-Orchestrator-Agent
           (Pattern B: thin wrapper)                          (Pattern B: thin wrapper)
                    │                                                          │
                    │ Fabric IQ tool (OneLake Catalog binding)                  │ Work IQ tool
                    ▼                                                          ▼
           Fabric data agent  ──► Lakehouse                    M365: Mail · Teams · Calendar
           (owns the semantics)                                SharePoint · OneDrive · Word
```

Note what is **absent**: no A2A, no toolbox, no workflow. Two prompt agents, one tool each, and
a string. That is the whole system — and it demonstrates the point of the decision table:
most supervisor demos do not need the preview surfaces at all.

---

## Pattern C — the Action agent (observed in the same lab)

Patterns A and B only read. The moment an agent **writes**, its prompt stops being a description
of capability and becomes a **safety envelope**. Observed instruction set for a write-capable
agent (creates and updates documents in OneDrive/Word):

```text
## Role
You are the SOP-Agent - a Microsoft Foundry agent operating in ACTION-ONLY mode.
You execute OneDrive and Word file operations using:
  - Work IQ OneDrive
  - Work IQ Word
You do not use any other tools.

Core behavior:
  - Execute only what the user explicitly asks.
  - No conversational replies. No recommendations. No unnecessary explanations.
  - Return concise action confirmations only.

## 1. Operating Rules
  - Capabilities are independent. Never auto-chain unrelated actions.
  - For write/update/delete/share actions: execute only if explicitly authorized
    by the user.
  - Never ask the user to repeat values already present in context.
  - Never expose raw tool payloads or internal IDs.
  - Never search unrelated OneDrive folders unless the user explicitly asks.
  - Never overwrite/delete files unless explicitly requested.
  - Prefer concise deterministic execution over reasoning-heavy responses.

## 2. Capability - Create SOP
  Triggers: "update the SOP", "add this to the SOP", "make this a SOP", ...
  Steps:
    1. Create a Word file in OneDrive named
       `Standard Operating Procedure(<SOP ID>).docx`
    2. Compose content from the current chat context. Never fabricate.
```

### The five guards, and why each exists

| Guard | Failure it prevents |
| --- | --- |
| **`You do not use any other tools`** | tool sprawl — an allow-list stated *negatively* closes the set |
| **`Capabilities are independent. Never auto-chain unrelated actions`** | the blast radius problem — one request cascading into several writes |
| **`Execute only if explicitly authorized by the user`** | unattended destructive action |
| **`Never overwrite/delete unless explicitly requested`** · **`never search unrelated folders`** | scope creep across the user's whole drive |
| **`Never expose raw tool payloads or internal IDs`** | leaking internals into user-visible text |

Plus, on the write path, the same anti-hallucination clause as Pattern B in a sharper form:
**`Compose content from the current chat context. Never fabricate.`**

### ⚠️ Prompt-level authorization is a default, not a control

*"Execute only if explicitly authorized by the user"* is a **behavioural** instruction. A model
can be talked out of it. It is the right default and it belongs in the prompt — but it is not a
security boundary.

Real enforcement lives one layer down, and must be set deliberately:

- `require_approval="always"` on the tool for anything that writes (Rule 6 of
  `foundry-orchestration-agent`).
- Identity: the tool acts as *someone*. Decide OBO vs service identity (Rule 7) — the write is
  attributed to that identity, and RBAC on the target system is what actually stops it.

**Never present a prompt rule as an access control** when describing this architecture.

### Incidental finding

`Work IQ` decomposes into **per-application tools** (`Work IQ OneDrive`, `Work IQ Word`), not one
monolithic connector. Tool granularity is per-app, which is what makes a negative allow-list
like *"you do not use any other tools"* meaningful.

---

## The three roles, side by side

| | **A · Router** | **B · Thin wrapper** | **C · Action agent** |
| --- | --- | --- | --- |
| Reads | the query only | a data source | context |
| Writes | nothing | nothing | **yes** |
| Tools | none | one, read-only | a closed, named set |
| Output | one agent name | `label : value` lines | action confirmation |
| Owns semantics | no | **no** — Fabric does | no |
| Prompt is mostly | a decision table | a delegation + a format | a **safety envelope** |
| Main risk | ambiguous routing | duplicating the semantic layer | blast radius |
| Signature line | *"exactly one agent"* | *"Do not invent numbers"* | *"Never auto-chain unrelated actions"* |

Three roles, three prompt shapes. A supervisor system is built by composing them — and every one
of the three ends with an explicit **output-shape** clause, because in a multi-agent system one
agent's prose is the next agent's input.

---

## Pattern D — the Synthesizer agent (observed in the same lab)

The last role in the chain holds **no tools at all**. It receives the output of upstream agents
and turns it into the answer the human reads.

```text
You take output from upstream agents or Workflow and return a clean,
structured summary plus context-aware follow-up questions.
You use no tools. You do not fetch, send, or modify anything.

Rules
  - Use only the data provided by upstream agents.
  - Never invent names, emails, numbers, dates, or files.
  - Preserve exact values (names, emails, amounts, times, deadlines).
  - Omit any section with no data.
```

Why it exists: Patterns B and C emit deliberately terse, machine-shaped output (`label : value`,
one-line confirmations). Something has to turn that into prose. Separating *retrieval* from
*presentation* means the wrapper agents can stay strict and parseable while the human still gets
a readable briefing.

Its guards are the mirror image of an action agent's — not "don't do too much", but **"don't
add anything"**: `use only the data provided`, `preserve exact values`, `omit any section with no
data`.

### The follow-up question is a designed control surface

The observed summarizer ends with **exactly one** follow-up question, chosen by a strict
priority ladder with an explicit override (*"this rule overrides every other trigger below…do
not evaluate triggers 2-4"*), a synonym list of ~15 phrasings for the trigger condition, and a
literal question template with a name substituted in.

Two things worth extracting:

1. **"Exactly one, first match wins, stop"** is the same discipline as the router's *"exactly one
   agent"*. Every place a model chooses, constrain it to one and give it a tie-breaker.
2. The question is a **loop-back**: it proposes the next query, which routes to a *different*
   branch of the system. This is how a multi-agent system stays conversational without an
   orchestrator holding state — the presentation layer suggests the next hop.

⚠️ **Design honestly.** A scripted follow-up that names the exact next question is a
choreography device. Legitimate for guiding a user; it is not the agent "deciding" anything.
Don't present it as emergent reasoning.

---

## Routers nest — the routing tree

The lab's top-level router does not dispatch to leaf agents. It dispatches to **another
router**, which itself outputs a bare agent name:

```
   user
     │
     ▼
  Supervisor-Agent ─────────────► "Inventory-Agent"  ──► Fabric IQ ──► Fabric data agent
   (router, level 1)                                                   (owns semantics)
     │
     └───────────────────────────► "Work-IQ-Orchestrator-Agent"
                                        │  (router, level 2)
                            ┌───────────┴────────────┐
                            ▼                        ▼
                    "Hierarchy-Agent"           "SOP-Agent"
                     Work IQ User               OneDrive · Word
                     (resolver → JSON)          (action, write)
                            │
                            │ hierarchy JSON
                            ▼
                    Communication-Agent
                    Mail · Teams · Calendar
                    (action, multi-tool)
                            │
                            ▼
                    Summarizer-Agent
                    (no tools, presentation)
                            │
                            ▼
                          user
```

Level 1 splits **data vs. productivity**. Level 2 splits **people/communication vs. documents**.
Each router's prompt only has to describe its own children — which is exactly why routing stays
accurate as the system grows. Adding a fifth leaf agent does not lengthen the top-level prompt.

Note the chain below level 2 is **not** routing: `Hierarchy-Agent → Communication-Agent →
Summarizer-Agent` is a *pipeline*, each stage consuming the previous stage's output. Routers
choose one branch; pipelines run in sequence. Both exist in the same system and they are
different mechanisms — don't model one as the other.

This is the strongest argument for Pattern A: **it composes**. Bound the depth explicitly
(Rule 6) — a routing tree is still a loop risk if a router can name its own ancestor. The lab's
level-2 router guards this literally: *"Never return 'Work IQ orchestrator' or any other agent
name. Your only valid outputs are …"*.

---

## ✅ RESOLVED — the dispatcher is a **Workflow**, written in YAML

The open question *"what consumes the router's bare string and performs the call?"* is answered.
The lab wires all seven agents together in **Agents → Workflows (Preview) → YAML editor**.

Observed YAML (complete, `name: Microsoft-IQ-Workflow`; indentation normalised, values verbatim):

```yaml
kind: workflow
trigger:
  kind: OnConversationStart
  id: trigger_wf
  actions:

    # ── level 1 router ────────────────────────────────────────────
    - kind: InvokeAzureAgent
      agent: { name: Supervisor-Agent }
      conversationId: =System.ConversationId
      input:  { messages: =System.LastMessage }
      output: { autoSend: false, messages: Local.Var3365 }

    - kind: ConditionGroup
      conditions:
        - condition: =Last(Local.Var3365).Text = "Inventory-Agent"
          actions:
            - kind: InvokeAzureAgent
              agent: { name: Inventory-Agent }
              conversationId: =System.ConversationId
              input:  { messages: =System.LastMessage }
              output: { autoSend: false, messages: Local.Var7934 }

      elseActions:
        # ── level 2 router ────────────────────────────────────────
        - kind: InvokeAzureAgent
          agent: { name: Work-IQ-Orchestrator-Agent }
          conversationId: =System.ConversationId
          input:  { messages: =System.LastMessage }
          output: { autoSend: false, messages: Local.Var4471 }

        - kind: ConditionGroup
          conditions:
            - condition: =Last(Local.Var4471).Text = "Hierarchy-Agent"
              actions:
                - kind: InvokeAzureAgent
                  agent: { name: Hierarchy-Agent }
                  conversationId: =System.ConversationId
                  input:  { messages: =System.LastMessage }
                  output: { autoSend: false, messages: Local.Var9934 }
                - kind: InvokeAzureAgent
                  agent: { name: Communication-Agent }
                  conversationId: =System.ConversationId
                  input:  { messages: =System.LastMessage }
                  output: { autoSend: false }

            - condition: =Last(Local.Var4471).Text = "SOP-Agent"
              actions:
                - kind: InvokeAzureAgent
                  agent: { name: SOP-Agent }
                  conversationId: =System.ConversationId
                  input:  { messages: =System.LastMessage }
                  output: { autoSend: false, messages: Local.Var8202 }

          elseActions:
            - kind: SendActivity
              activity: Local.Var4471          # ⚠ emits the raw router output

    # ── terminal, unconditional ───────────────────────────────────
    - kind: InvokeAzureAgent
      agent: { name: Summarizer-Agent }
      conversationId: =System.ConversationId
      input:  { messages: =System.LastMessage }
      output: { autoSend: true }               # ⚠ the ONLY autoSend: true

    - kind: EndConversation

id: ""
name: Microsoft-IQ-Workflow
description: ""
```

### What this tells us

| Element | Meaning |
|---|---|
| `kind: workflow` / `trigger.kind: OnConversationStart` | The workflow *is* the entry point. The user talks to the workflow, not to the supervisor. |
| `InvokeAzureAgent` + `agent.name` | Agents are called **by name** — confirming the name is the identifier, and adding a *second* place the literal is duplicated. |
| `ConditionGroup` / `condition:` / `elseActions:` | **The dispatcher.** Plain if/else over the router's output. |
| `=Last(Local.VarNNNN).Text = "Agent-Name"` | Exact **string equality** against a literal. |
| `autoSend: false` on every agent but one | Intermediate agents are silenced; only the **Summarizer** has `autoSend: true`. |
| `conversationId: =System.ConversationId` | One conversation shared across every agent. |
| `SendActivity` | Emits directly to the user, bypassing agents. |
| `EndConversation` | Terminal node. |
| `=System.LastMessage`, `=Last(...)` | **Power Fx** expressions — same language as Power Platform / Copilot Studio. |
| `node-1778248476735`, `if-action-…-ma22fceo` | Machine-generated IDs, not hand-authored. |

### 🔑 Why the router prompt was so insistent about formatting

The supervisor's prompt ends with:

> *"Return only the agent name as a plain string — no quotes, no extra whitespace, no newline."*

Now it is obvious: routing is a **literal string comparison in YAML**. A trailing newline, a
wrapping quote, a stray space, a courteous *"Inventory-Agent."* — every one of these fails the
equality.

**This is the most important finding of the session.** The router's output-shape clause is not
stylistic; it is a **type contract enforced by string equality downstream**, with no validation
and no error when it fails.

### 🔑 `autoSend` is how a multi-agent system speaks with one voice

Six agents run; **one** has `autoSend: true`. Everything upstream is captured into a variable and
never reaches the user. That single flag is the entire implementation of *"the user sees one
coherent answer, not six."*

It also explains Pattern D's existence. The Summarizer isn't decoration — it is the **only agent
with a microphone**, so it must be the one that composes the final answer.

> ⚠️ A second workflow, observed later, does the exact opposite with the same flag — see
> [Second specimen](#-second-specimen--the-opposite-autosend-strategy) below. `autoSend` is a
> **strategy choice**, not a convention, and nobody will catch it in review.

### ⚠️ Three real weaknesses in this wiring

**1. Level 1 only ever tests one value.** The supervisor is documented as choosing between two
agents, but the YAML tests `= "Inventory-Agent"` and sends *everything else* to the level-2
router. A malformed, empty, or hallucinated supervisor response routes to Work-IQ — silently and
plausibly. The else-branch is doing double duty as both "the other choice" and "the error path",
so the error path is indistinguishable from a valid decision.

**2. The level-2 else-branch leaks internals to the user.** `SendActivity: activity:
Local.Var4471` emits the router's **raw output** — a bare agent name — straight into the chat. If
the level-2 router ever answers with anything unexpected, the user sees a naked string like
`Hierarchy-Agent` or an apology, presented as the product's answer.

**3. Captured variables are never read.** `Local.Var7934` (Inventory), `Local.Var8202` (SOP),
`Local.Var9934` (Hierarchy) are all written and never referenced again. They are inert.

### ❓ Open question — does the hierarchy JSON actually reach Communication-Agent?

This one matters and I will not guess it.

`Hierarchy-Agent`'s output is captured into `Local.Var9934`. The very next step invokes
`Communication-Agent` with `input.messages: =System.LastMessage` — **not** `Local.Var9934`.
Every agent in the workflow reads `=System.LastMessage`; no step ever feeds a previous step's
variable forward.

So the declared contract — *"you may receive a hierarchy JSON… trust names and emails exactly as
provided"* — is satisfied **only if** `autoSend: false` still appends the agent's reply to the
shared conversation, making it the new "last message". If `autoSend: false` also suppresses the
thread write, then `Communication-Agent` receives the *user's* original message and the hierarchy
is silently dropped.

Both readings are consistent with everything observed. The semantics of `autoSend: false` versus
the shared `conversationId` are not documented here.

**To resolve:** run the workflow and read the **Traces** tab — the input actually delivered to
`Communication-Agent` settles it in one look.

> Recorded as a question, not a finding. Two earlier over-calls in this file are why.

### 🔬 Second specimen — the opposite `autoSend` strategy

A second workflow was observed in a different Microsoft lab (Zava retail — full write-up in
[`reference_foundry_iq.md`](reference_foundry_iq.md), raw source in
[`labs/foundry-iq/raw_capture.md`](labs/foundry-iq/raw_capture.md)). Same mechanism, opposite
design decisions. This is the most useful comparison in the whole brain.

```yaml
kind: workflow
trigger:
  kind: OnConversationStart
  actions:
    - kind: SetVariable                     # ⚠ written, never read
      variable: Local.Var2679
      value: =System.LastMessage
    - kind: InvokeAzureAgent
      agent: { name: Supervisor-Agent }
      output: { autoSend: true, messages: Local.Var5755 }
    - kind: ConditionGroup
      conditions:
        - condition: =Last(Local.Var5755).Text = "Sales-Associate-Agent"
          actions: [ InvokeAzureAgent → Sales-Associate-Agent,  autoSend: true ]
        - condition: =Last(Local.Var5755).Text = "Rewards-Campaign-Agent"
          actions: [ InvokeAzureAgent → Rewards-Campaign-Agent, autoSend: true ]
        - condition: =Last(Local.Var5755).Text = "Inventory-Agent"
          actions: [ InvokeAzureAgent → Inventory-Agent,        autoSend: true ]
      elseActions:
        - kind: SendActivity
          activity: " "                     # ⚠ silent empty fallback
name: FoundryIQ-Workflow
```

| | **Microsoft-IQ-Workflow** (above) | **FoundryIQ-Workflow** (this one) |
|---|---|---|
| Agents | 7 | 4 |
| Router depth | **2 levels** (routers nest) | 1 level, flat 3-way |
| `autoSend` | `true` on **exactly one** agent | `true` **everywhere**, router included |
| The user sees | one composed answer | every hop, incl. the bare agent name |
| Final step | dedicated `Summarizer-Agent` | none — the branch output *is* the answer |
| `else` branch | `SendActivity Local.Var4471` — leaks raw router output | `SendActivity " "` — silence |
| Agents created via | portal, by hand | **Python script** (`create_version`) |

**Three things this comparison settles.**

**1. The router type contract is a product constraint, not an author's habit.** Two labs, two
domains, two authors — and the same clause in both router prompts:

> *"Return only the agent name no extra space or new line simple string."*

Because both dispatchers do exact string equality on the router's text. Independent
confirmation. Treat it as a hard rule.

**2. `autoSend` is a strategy, and the two strategies are opposites.**

| Strategy | `autoSend` | Good for | Cost |
|---|---|---|---|
| **One voice** | `true` on the synthesizer only | a product | hides the orchestration you want to show |
| **Narrate every hop** | `true` everywhere | a demo *of the architecture* | the router's raw `"Inventory-Agent"` appears in the chat |

Decide which you are building **before** writing the YAML. It is a one-flag change and it will
not show up in review.

**3. Both specimens have a broken `else` branch, in opposite directions.** One leaks internals,
one says nothing at all. Neither raises an error. **Design the else branch deliberately** — it is
where every routing failure lands, and in both observed systems it was an afterthought.

**Also present in both:** a `SetVariable`/capture that is written and never read. Dead workflow
state appears to be the norm in hand-built workflows; do not copy it forward.

### Workflow starter templates — orchestration patterns, named


`Create ▾` offers: **Blank workflow · Sequential · Human in Loop · Group chat**.

Foundry ships opinionated multi-agent topologies. The lab picks **Blank** and builds an explicit
router + condition tree — the supervisor pattern is *not* one of the templates. `Group chat` and
`Human in Loop` are unexplored.

The workflow is then **published as a "workflow app"** — a publish target separate from an
agent's own Publish.

---

### ⚠️⚠️ Timing problem — Workflows retire **2026-12-01**

The lab teaches this feature. `generation_map.md` records its retirement date.

**Today is 2026-08-04. That leaves roughly four months.**

This is not a criticism of the lab — it is the clearest possible illustration of why
`generation_map.md` is the first file to read in this brain. A perfectly working system built on
the pattern above has a hard expiry.

| | |
|---|---|
| **Learn from it** | The *architecture* — router → condition dispatch → typed handoffs → terminal synthesizer — is sound and portable. Keep it. |
| **Don't inherit** | The *mechanism*. Portal Workflows YAML is the part that expires. |
| **Forward path** | **Microsoft Agent Framework** for orchestration you intend to keep, plus the **A2A tool** for agent-to-agent calls. Both outlive this. |

If a project built on this brain must ship past 2026-12-01, the dispatcher gets rebuilt in code.
The good news is that the rebuild is mechanical: the YAML above maps almost line-for-line onto a
`switch` over the router's output, which is exactly what a code-first framework expresses
natively — and a code-first dispatcher can *validate* the router's output instead of silently
falling through.

---



The communication agent declares an input contract from its caller:

```json
{ "hierarchy": { "name": "", "email": "", "role": "",
                 "subordinates": [ { "name": "", "email": "", "role": "" } ] } }
```

followed by the critical line:

> **"Trust names and emails exactly as provided. Do not re-resolve people."**

This is the multi-agent equivalent of not re-querying a primary key. If every agent re-resolves
the same entity, they will eventually disagree — different spellings, stale directory data, a
different match on an ambiguous name — and the system produces two truths for one person.

**Rule:** an agent receiving a resolved entity from upstream **consumes** it. Resolution happens
once, at the agent that owns it. State that ownership in the prompt, on both sides.

Note this is a *documented JSON contract in a prompt*, not a typed interface. Nothing validates
it. If the shape matters, validate it in the dispatcher — see Pattern A's caveats.

---

## Pattern E — the Resolver agent (observed in the same lab)

One agent's entire job is to **resolve entities once** and emit them as structured data:

```text
You are the Hierarchy-Agent.
Your only job: fetch the signed-in user's organizational hierarchy information
from Microsoft Teams (Microsoft Graph) - manager, manager chain, direct reports,
and peers - and return it as JSON.
```

Tool attached: **`Work IQ User`** (Preview) — a Work IQ tool distinct from Mail/Teams/Calendar,
backed by Microsoft Graph for people and org data. Confirms again that Work IQ is
**per-capability**, not one connector.

Its output is precisely the `{ "hierarchy": { … "subordinates": [ … ] } }` contract that the
communication agent declares as its input — and the reason that agent can say *"Trust names and
emails exactly as provided. Do not re-resolve people."*

**This closes the loop on the resolve-once rule.** One agent owns identity resolution; every
downstream agent consumes its output. The contract is real, and it has an owner on both ends:

```
Hierarchy-Agent  ──JSON──►  Communication-Agent
 (resolves, owns identity)   (consumes, forbidden to re-resolve)
```

### Why a resolver deserves its own agent

- **Single source of truth** for who reports to whom — resolved once per conversation.
- **Reusable** by any downstream agent needing the same people graph.
- **Testable in isolation**: given a signed-in user, does it return the right JSON?
- Keeps the identity dependency (Graph permissions, OBO) in **one** place instead of smeared
  across every agent that happens to mention a person.

⚠️ It is also the **identity-sensitive** node: it reads the org graph as the signed-in user.
Whatever it returns bounds what every downstream agent can act on. If OBO isn't wired properly
here, the whole chain reasons about the wrong person's team.

---

## ⚠️ Observed fragilities

### Agent names are string literals duplicated across prompts

The agent name **is** the API identifier (confirmed in the portal's create dialog). Every router
hard-codes its children's names as strings. Rename one agent and every router referencing it
breaks **silently**: the model still emits the old name, the dispatcher no longer recognises it.

Naming drift is already visible: the summarizer's prompt refers to a `Files-Agent` that appears
nowhere else in the system — most likely an earlier name for `SOP-Agent`, left behind in prose.
Harmless here because it is only descriptive text; fatal if it had been in a routing rule.

**Mitigations:**
- Keep the roster of agent names in **one** place and generate router prompts from it.
- Have the dispatcher validate against an allow-list and fail **loudly** on an unknown name.
- Grep every prompt for agent-name literals whenever an agent is renamed.

### Prompt and tool list are not reconciled by anything

An agent's prompt can name tools it does not have, and hold tools its prompt never mentions.
Nothing validates either direction — the same class of drift as the Fabric data agent's
instructions vs. its bound tables.

This is a **review rule**, not an observed failure: whenever a prompt names its tools, diff it
against the attached tool list, both ways.

### Versions accumulate fast

Observed version numbers in a reference build of this system: `20`, `46`, **`102`**.

Every `Save` mints a version. A router prompt that gets iterated — which is exactly what routers
need — reaches three digits quickly. This is why the SDK samples end with
`project.agents.delete_version(...)` and comment *"so unused versions don't accumulate"*.

Consequences: version number is **not** a meaningful identifier to a human, `Publish` (not
`Save`) is what selects the served version, and any automation must clean up after itself.

> Neither fragility is a bug in Foundry. Both are architectural drift that only shows up when
> someone compares two panes of the same UI.

---

### Correction log — two over-called findings

Both entries below were written confidently, and both were wrong. Kept visible on purpose.

**1. "`Hierarchy-Agent` doesn't exist → dead route."**
It exists, with the `Work IQ User` tool. The claim came from an agent list captured *before* the
remaining agents were created.

**2. "The communication agent's tools contradict its prompt."**
They did not. The screenshot showed the agent **mid-build**, before the lab's next task attached
Work IQ Mail / Calendar / Teams. The prompt was written first, the tools added after — a normal
build order, not drift.

**The real lesson, which generalises:** a screenshot is a *point in time*, not a state of the
world. Diagnosing a defect from a snapshot of an unfinished build produces a confident,
plausible, wrong conclusion — and it fails in the most damaging direction, because a stated
defect gets acted on.

**Rule adopted:** before recording a mismatch as a finding, establish that the artifact was
*complete* at capture time. If that cannot be established, record it as a **question**, not a
finding. This is umbrella rule 9 applied to visual evidence.

## Why a Toolbox rather than tools attached one by one

Both work — tools can be attached directly to an agent. Microsoft recommends the toolbox, and
for a multi-agent demo the reasons compound:

- One curated bundle, exposed as **a single managed MCP endpoint**.
- **Reused across agents** — supervisor and sub-agents share one definition.
- Credentials and policy centralised; **versioning** without touching agent code.
- Fewer tool definitions in the supervisor's context, which is what keeps routing sharp.

## Wiring a sub-agent to the supervisor (A2A)

Three things must be true, in order:

1. **The target agent accepts incoming A2A.** It must be explicitly enabled — see
   `azure/foundry/agents/how-to/enable-agent-to-agent-endpoint`. A sub-agent that merely exists
   is not callable.
2. **A project connection points at it.** For a Foundry agent as target, the connection target
   is the A2A base path, with audience `https://ai.azure.com`:

   ```
   https://{account}.services.ai.azure.com/api/projects/{project}/agents/{agent}/endpoint/protocols/a2a
   ```

   Do **not** set an agent card path — Foundry resolves it and negotiates the protocol version.
   Portal route: **Tools → Connect tool → Custom → Agent2Agent (A2A) → Create**
   (with the **New Foundry** toggle on).
3. **The supervisor declares the A2A tool**, referencing the connection by name. In Python the
   tool class is `A2APreviewTool` from `azure.ai.projects.models`; the connection ID comes from
   `project.connections.get(connection_name).id`.

> Note the two different hostnames in play: the project endpoint is
> `https://<resource>.ai.azure.com/api/projects/<project>`, while the A2A base path uses
> `<account>.services.ai.azure.com`. They are not interchangeable — confirm both against the
> tenant before writing either into a script.

A2A is an open protocol (`a2a-protocol.org`), so the same mechanism reaches non-Foundry agents.
Supported across Python, C#, JavaScript, Java and REST, on both basic and standard agent setup.

## The Fabric leg — ⚠️ correction

`Microsoft Fabric (preview)` is a **built-in** tool in the current catalog — *"connect to a
Microsoft Fabric data agent for data analysis"*. So the Fabric leg does **not** need A2A.

But it does **not** go in a toolbox either. The toolbox support matrix
(`azure/foundry/agents/concepts/toolbox-overview` § *Supported tools*) is explicit:

| Tool | In a toolbox | Direct on the agent |
| --- | --- | --- |
| **Fabric data agent** | ❌ **No** | ✅ Yes |
| **Fabric IQ** | ✅ Yes | ✅ Yes |
| Agent-to-agent (A2A) | ✅ Yes | ✅ Yes |
| MCP, OpenAPI, AI Search, Code interpreter, File search, Web search | ✅ Yes | ✅ Yes |
| Function calling | ❌ No (client-side execution) | ✅ Yes |
| SharePoint, Azure Functions, Bing grounding, Computer use, Image generation | ❌ No | ✅ Yes |

So the supervisor ends up with **two attachment styles at once**, and that is normal:
a toolbox for everything that can live in one, plus a small number of tools attached
directly because the platform gives no choice.

> An earlier draft of this file said the Fabric data agent "belongs in the toolbox".
> That was wrong — corrected 2026-08-04 against the support matrix. Exactly the class of
> error the `known_issues.md` loop exists to catch.

Ownership boundary, non-negotiable (umbrella rules 5 and 7): the Fabric Data Agent is
**created and published** by `Fabric-Brain/agents/ai-skills-agent/`. Foundry-Brain attaches and
calls it. Any change to the Fabric artifact is a **handoff**, not an edit.

## Pattern F — the interpreting supervisor (the answer contract)

Patterns A–E decide *which* agent gets called. None of them decide **what the supervisor says**
once the answers come back. That is a separate design surface, and it is where an otherwise correct
system fails in front of an audience: every figure right, every source cited, and the reply either
unreadable or — worse — a question back.

Derived over thirteen deployed versions of one supervisor (a Fabric data agent for the numbers and a
document corpus for the verbatims, both over A2A), each measured against the live agent. **Start
from the contract below instead of rediscovering it**; the sequence that produced it is logged in
`agents/foundry-orchestration-agent/known_issues.md`.

### The contract

1. **Decide, never ask back.** When a term has several defensible readings, name the criterion, take
   the widest actionable cohort, and **declare the reading inside the answer**. Never offer the
   reader a choice: the licence to ask is permanently available and always cheaper than choosing, so
   it wins — including on a question the user reached by clicking your own app's suggestion.
2. **Relay figures verbatim, with their scope attached.** The supervisor recomputes nothing and
   rewrites no number. Left free it will round "825 customers (bands High + Critical)" into
   "800 customers", reintroducing one storey up the ambiguity the data layer just resolved.
3. **State provenance in exactly one place.** Two mandated locations — a lead sentence *and* a
   "what was measured" block — are read as two presentations, not as a repeat, and the model will
   fill both. Delete the second location rather than adding a rule against duplication.
4. **Give a countable limit and a total.** Adjectives ("concise", "sparingly") move nothing.
   Countable limits work but only bind the unit they name, so the verbosity migrates to the
   neighbouring one — themes, then facts per line, then list length, then sub-bullets under each
   row. Only a **total** ("the whole reply fits on one screen, about thirty lines") cannot be
   re-oriented around. Say what to sacrifice when it binds: cut records and themes, never the scope
   of a figure.
5. **Surface an empty retrieval; never retry until documents appear.** A retry loop manufactures
   confidence the system does not have.
6. **Carry no figure in the instructions themselves.** A grounded agent with a hardcoded fact is
   worse than an ungrounded one, because it looks sourced. Worth a test that greps the rendered
   prompt for digits.
7. **Two registers, and they never mix — provenance is *relocated*, not deleted.** Clause 3 removes
   the duplicate; it does not say which of the two survivors to keep, and the model keeps the
   sentence. Observed on the second turn of a live demo: a lead reading
   `crm_customer_profile[risk_band] IN {"High","Critical"}`, then the same fields again as a
   six-bullet form. Every word true, sourced, and unreadable to the marketing lead it was written
   for. Split by **register**: the prose names the population *in the words the reader already
   uses* and carries no identifier of any kind — no table, column or measure name, no bracketed or
   backticked field, no DAX/GQL fragment, no `IN` / `>=`, no quoted literal value set. The
   identifiers go to **one trailing block opening with a fixed ASCII marker** (`### SOURCE` — that
   word, capitals, English, whatever language the answer is in), at most six one-fact lines, and
   **excluded from the total of clause 4** so the block never competes with the answer for room.
   The apparent contradiction with "a number without its scope is not an answer" is resolved by
   declaring the plain-language description of the population **not to be a statement of
   provenance**. Both rules then survive intact.
   - The client folds that block behind a button, so nothing is lost to the analyst who wants it.
     **Parse it tolerantly while mandating it strictly**: the split must never *hide* content.
     Strip decoration and compare (`line.replace(/[#*_\s:\u2014-]/g,'').toLowerCase()`) rather than
     enumerate forms — a single regex missed `**Source :**`, because French typography puts the
     colon *inside* the bold markers. Split on the **last** match ("source" is an ordinary word),
     and if either side comes out empty, return the whole reply as prose.
8. **One figure, one unit, once.** A share reaches the supervisor as a ratio and it will print both
   units: observed live, `0,0784742699514886, soit 7,84742699514886 %` — the same figure twice, each
   at full float precision. Give the percentage and only the percentage, and drop the decimal tail
   that records how the division landed. This is the **single** exception to clause 2, and it applies
   to a share alone: a count, a sum or an amount is still relayed to its last digit. State the
   exception's narrowness explicitly, or it swallows the rule that stops 825 becoming 800.
   - Related, and the reason clause 8 was even reachable: **a share asked for under its own defining
     filter returns the whole population.** Requesting an *at-risk share* while also filtering to the
     at-risk bands makes numerator = denominator, and the reply says 100 % of the customer base is
     churning. Arithmetically true, informationally empty, and catastrophic on stage. Forbid it by
     name and say that a share coming back as the whole population *is the symptom*, to be re-asked
     rather than reported.

### The structural knobs — prose will not do these

- **`PromptAgentDefinition(..., tool_choice="required")`** if the supervisor may end a turn having
  called nothing (it narrates the routing rule as a plan, and the app renders that as a one-line
  unsourced answer). A prose rule against it does not hold; this does.
- **Only where the tool list is homogeneous.** `required` forces *a* call, never the *right* one —
  with a `file_search` beside an A2A tool it is satisfied by the wrong tool. Make every tool the
  same nature so they are told apart by name alone.
- **Remove an escape hatch by asserting its absence**, not by adding a preference. "Prefer X"
  leaves Y reachable.

### How to know it works: measure, never sample

Two consecutive runs of one deployed version, same question, returned 2 748 and 6 024 characters.
A single probe "proves" whichever conclusion it draws, and the next version is built on it.

Re-ask **the same question at least five times per version** and report the spread: answered vs
stalled, which connections fired, answer length, latency. Cheap to build, and it is the only thing
that separates a fix from a lucky draw. Two traps that imitate a regression: a helper that already
extracts response items will return `[]` if you extract again — the same signal as "no subordinate
fired"; and `tool_user_error` (HTTP 400) is transient, so retry before diagnosing auth.

**A check phrased in the old contract measures the question, not the agent.** When clause 7 shipped,
the harness kept failing on one probe — whose question was *"how many customers have a
`churn_risk_score` above the threshold? **name the column and filter used**"*. It named the very
identifier it then booked as a leak, so it guaranteed its own failure; and a second check in the same
run was simultaneously counting that word as proof the scope had survived. Re-read every question
against the new contract when a clause changes, and phrase probes **in the words a user would
actually type**. The stronger test is the plain-language one: ask with no identifier, and require the
identifiers to appear in the block anyway.

**Apply a universal clause to every answer, not to a question of its own.** Clause 7 first got one
dedicated probe, which passed while another answer in the same run leaked. A contract that holds for
all replies must be asserted over all replies collected in the run — it costs nothing and it is the
difference between "one question complied" and "the version complies".

Measured on this pattern, clauses 7–8, supervisor v15: **two consecutive full batches at 8/8**, no
identifier in any prose body, no undigested ratio, block present on every answer. Latency 25–100 s
per supervised answer.

**`tool_user_error` is transient at a rate worth engineering for — measure it before shipping the
question.** The rule above ("retry before diagnosing auth") was recorded from a single occurrence.
Asking one question five times, unchanged, put a number on it: **4 answers and 1 failure**, the
failure landing at **110 s** while the four successes ran **98, 106, 135 and 157 s**. So it is *not*
a wall-clock ceiling — 135 s and 157 s completed — it is one A2A hop dropping intermittently, and
the wall-clock at which it surfaces is meaningless. One in five is fine for a harness and
unacceptable for a UI suggestion a demo user reaches in one click.

**The status is useless, the code is the discriminator.** The payload is
`{"error":{"type":"invalid_request_error","code":"tool_user_error",...}}` — HTTP **400** with the
*type* of a malformed request. Any retry policy keyed on the status, or on `type`, will either
retry genuinely broken requests forever or refuse to retry the one fault that clears on its own.
Key on `code`.

**One retry, not two.** Retries are priced in the pattern's own latency: at up to 157 s per answer,
a third attempt can leave someone watching a spinner for six minutes — worse on stage than the
failure it prevents. One retry takes a measured ~20 % failure rate to roughly 4 %. And the retry
**must be announced** — the same reason a supervised answer needs a live elapsed counter, a silent
four-minute wait reads as a crash.

**The two-register rule of clause 7 applies to failures too.** An orchestrated call fails with a
provider payload — a `resp_…` task id, an error type, a vendor troubleshooting URL — and printing it
is the same defect as printing a column name inside an answer: correct, sourced, and unreadable by
the person it is shown to. Give the failure a sentence, and fold the payload underneath exactly as
the `SOURCE` block is folded. Evidence: the app shipped the raw JSON to a demo screen, which is what
prompted this measurement.

### Extending this pattern

Each future improvement adds a numbered clause **and** the batch that justifies it. A clause with no
measurement behind it is a preference, and preferences are what this pattern exists to replace.

## Design rules for the supervisor

Derived from the mechanics above. These are the rules that decide whether a demo holds up live.

1. **Name the routing contract.** The supervisor's instructions must state, per sub-agent and
   per tool, *when* to call it and what it returns. Vague delegation is the failure mode that
   looks like a hallucination but is a missing contract.
2. **Bound the loop.** A supervisor that can call agents which can call agents needs an explicit
   depth and turn limit in its instructions. Nothing enforces this for you.
3. **Prefer tool over sub-agent.** An extra agent means an extra model call, extra latency and
   an extra place to go wrong. Only promote a capability to a sub-agent when it genuinely needs
   its own instructions and reasoning.
4. **Approval posture is a decision.** MCP tools take `require_approval`. `"never"` demos
   smoothly and removes the human check; `"always"` is the safe default for anything that
   writes. Choose deliberately and record the choice.
5. **Identity is the demo risk.** Entra/managed identity where the tool supports it, OAuth
   passthrough when per-user identity must reach Fabric. Key-based auth is the fallback, not
   the default. Fabric row-level security only means something if the identity survives the hop.
6. **Structured inputs over agent versions.** Values that vary per user or per environment
   (vector store IDs, MCP endpoints) belong in `structured_inputs`, overridden at runtime —
   not baked into a new agent version.
7. **The answer contract is a design surface, not a polish pass.** Rules 1–6 make the right
   sub-agent run; none of them make the reply usable. Budget for it, and start from Pattern F
   above rather than deriving it again.
8. **Judge every instruction change on a batch, never on one run.** Same version, same question,
   twice the length — that is the normal spread, not a fluke. Without a repeat harness you are
   tuning on noise.

## Open questions — resolve against the tenant, then record

These cannot be answered from documentation. They go into `portal_reality.md`.

- [ ] Is the **A2A** tool present in this tenant's tool catalog?
- [ ] Is the **Microsoft Fabric** tool present, and does it see the published Fabric Data Agent?
- [ ] Is **Fabric IQ** present? Is background mode usable?
- [ ] Are **toolboxes** available in this region?
- [ ] Which RBAC role names does the portal show — `Foundry User` or the old `Azure AI User`?
- [ ] Does the tenant default to **New Foundry**, or must the toggle be flipped every session?

## Sources

All on the current tree, read 2026-08-04:

- `azure/foundry/agents/concepts/tool-catalog`
- `azure/foundry/agents/how-to/tools/agent-to-agent`
- `azure/foundry/agents/concepts/workflow`
- `azure/foundry/agents/how-to/tools/fabric` · `…/tools/fabric-iq`
- `azure/foundry/agents/how-to/migrate#agent-tool-availability`

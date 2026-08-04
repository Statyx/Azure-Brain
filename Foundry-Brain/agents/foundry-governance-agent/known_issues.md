# Known Issues — Foundry Governance Agent

> Evidence classes used here: **doc** (Microsoft Learn) · **lab-text** (verbatim from a Microsoft
> training lab) · **observed** (seen in a tenant, by us) · **inferred** (this brain's reasoning).
> Two surface facts are **observed**; **no guardrail was ever seen blocking a request and no
> evaluation output was ever displayed.** That is the headline, not a footnote.

---

## Observed

Two items, both from tenant screenshots recorded in
[`../../portal_reality.md`](../../portal_reality.md) (lab 1, 2026-08-04). Neither shows a
guardrail firing or an evaluation result — but the *surfaces* were genuinely seen.

### The agent configuration pane has its own `Guardrail` *(Preview)* section
Sections in order: **Model · Voice mode · Instructions · Tools · Knowledge · Memory** *(Preview)*
**· Guardrail** *(Preview)*.
**Impact:** a guardrail is reachable from **both** ends — the guardrail object's scope screen and
the agent's own pane. 🧠 Probably two views of one relation; **unverified**.
**Practical rule until verified:** audit coverage from the guardrail object's scope screen, since
that is the only view listing all agents at once — an omission is invisible from the agent pane.

### The agent detail view carries `Evaluation` and `Monitor` tabs
Tabs: `Playground` · `Details` · `Traces` · `Monitor` · `Evaluation` · `Optimize` *(Preview)*.
**Impact:** independent confirmation that evaluation is **agent-scoped by design**, not merely by
the wizard's default. Reinforces the gap: there is no equivalent tab on a workflow.
**Unknown:** whether the agent-level `Evaluation` tab is the same object as the left-pane
`Evaluations` wizard, and what `Monitor` shows that `Traces` does not.

*(Everything else below is lab-text or reasoning. No guardrail was seen blocking a request and no
evaluation output was ever displayed.)*

---

## Lab-text — the shape of the two surfaces

### `Guardrails` is a top-level pane, and a guardrail is a standalone object
Created from the left pane, not from inside an agent. Flow: `Create` → *Add controls* → *Select
agents and models* → *Review* → name → `Create`.
**Impact:** safety is administrable centrally and survives agent edits — layer 4 of the control
model. Also means coverage is a **selection**, so it can silently miss a new agent.

### Two control families, different defaults
*Content harms* (Hate, Sexual, Self-harm, Violence) were **already checked**. *Risk Type*
(Jailbreak, Protected Materials) were **opt-in** — the lab explicitly checks them.
**Impact:** the two controls an enterprise reviewer asks about are the two that are off unless
someone acts. Put them on a checklist.

### Scope is "agents **and** models"
The section is titled *Select agents and models*; the lab ticks the header checkbox to include all
agents.
**Unknown:** whether attaching at model level covers agents not individually selected. 🧠 If it
does, that is the more robust coverage strategy. Resolve before designing a policy.

### `Evaluations` targets one **agent**
*Target: Agent* → pick one. Lab picks Supervisor, then: *"Similarly, perform evaluation on the
other agents."*
**Impact:** no observed end-to-end evaluation of a workflow. The routing hop is covered by neither
governance surface — only by a trace.

### Scope offers "Individual turns"
The lab selects it, which implies at least one other option exists.
**Unknown:** what the others are (conversation-level? session-level?) and what changes with them.

### Data can be **Generated**
`Generate` → defaults → **10 rows** → `Confirm`.
**Impact:** proves the pipeline runs; measures nothing about your users. Never report a score from
generated data as quality.

### Criteria has defaults, and the lab never opens them
The lab passes straight through the *Criteria* step.
**Consequence:** we have **no evaluator names, no criteria list, no scales, no thresholds**. They
are deliberately absent from `instructions.md` rather than guessed (umbrella rule 9). This is the
single largest hole in this agent.

### Results surface as **Evaluation runs** and **Evaluators**
Two views after submit. Runs have a **status** that completes asynchronously.

### ⚠️ *"Do not close the page until the evaluation run status is complete"*
Lab's own warning.
🧠 Taken literally it would mean the run is browser-bound, which would be surprising for a
server-side job — more likely it is UI guidance about losing the view.
**Unresolved.** Do not build a CI gate on evaluations until someone has closed the tab and checked
whether the run survived.

---

## ⚠️ Anti-pattern shipped by the lab itself

### A "Responsible AI Agent" in the story, a Guardrail in the implementation
Exercise 5's narrative lists four agents including a *Responsible AI Agent* that *"blocks unsafe or
non-compliant prompts"*. The workflow YAML deployed in that same exercise contains **three**
specialists and no safety agent. Safety appears in Exercise 6 as a platform Guardrail.

**Why this matters:** the narrative is the version people remember and reproduce. A safety hop in
a routing graph can be skipped, mis-routed or edited away, and it only sees what the router handed
it. The platform's answer is layer 4. Say so in design reviews.

### A grounded agent with hardcoded facts passes both surfaces
`Inventory-Agent` is told *"the response must come only from the Fabric Data Agent tool output"*
and its prompt lists ten product IDs as at-risk. A guardrail sees nothing unsafe; an evaluation
sees a confident, well-formed, self-consistent answer. Only a trace shows the tool was never
called — or returned something else.

**Rule that follows:** any green evaluation on a *grounded* agent needs one trace spot-check
before it is reported. This is the concrete reason `foundry-observability-agent` and this agent
are separate and both required.

---

## Inferred — this brain's doctrine, marked as such

### Evaluator choice must follow the agent's **role**
A router emits one bare token to satisfy an exact string comparison. Groundedness and relevance
are meaningless on it; the right metric is classification accuracy against a labelled
request→agent table — which generated data will not produce. Full table in `instructions.md`.
**Risk if ignored:** a router scores excellently on prose metrics and routes everything wrong.

### A thin wrapper must be scored on fidelity, not fluency
Pattern B agents exist to relay a tool result unaltered. Fluency-shaped scoring rewards exactly
the paraphrasing they are designed to prevent.

### A resolver must be schema-checked before it is content-scored
Pattern E emits JSON for a downstream consumer. Invalid JSON breaks the system regardless of how
good the content is.

---

## Open questions — resolve on first tenant access

| # | Question | Why it matters |
|---|---|---|
| 1 | What are the actual **evaluator names and criteria**? | the whole quality half of this agent is a shape with no contents |
| 2 | What scales / thresholds do results use? | you cannot define a pass gate without them |
| 3 | Does model-level guardrail scope cover agents not individually selected? | decides the coverage strategy |
| 4 | Is the full control list longer than the six items seen? | the six may be a subset |
| 5 | What are the other **Scope** options besides *Individual turns*? | conversation-level scope would partially close the multi-agent gap |
| 6 | Does an evaluation run survive closing the browser? | blocks any CI usage |
| 7 | Can guardrails / evaluations be created **by code**? | everything else in this brain moved from portal to SDK; assume these will too |
| 8 | What does a **blocked** request look like to the caller, and in the trace? | determines whether you can distinguish a block from a failure |
| 9 | Are guardrail hits visible in Application Insights? | if yes, safety becomes measurable rather than merely configured |
| 10 | Is there any workflow-level (not agent-level) evaluation target? | would close the seam this agent flags as uncovered |

| 11 | Is the agent pane's `Guardrail` section the same relation as the guardrail's scope list? | decides where coverage must be audited |
| 12 | What does the agent's `Monitor` tab show that `Traces` does not? | may be the aggregate view both this agent and observability lack |

When any of these is answered **from a tenant**, move it into **Observed** above with the date,
and prune it here. Do not answer them from documentation.

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

### `a2a_preview` and `file_search` do not coexist on one agent

**Symptom:** a supervisor given an A2A tool for figures **and** `FileSearchTool` for a document
corpus deploys cleanly, and then **never routes to A2A**. It answers every question, including
plainly quantitative ones, out of the corpus.
**Isolation:** three runs, same instructions, same question, only the tool list changing.
`a2a_preview` alone → fires, correct answer. `a2a_preview` + `file_search` → A2A never fires,
a dozen-plus `file_search` calls instead. Adding `tool_choice="required"` → **still**
`file_search`.
**Cause:** `file_search` describes its own purpose to the model. An A2A tool surfaces only under
its **connection name**, which says nothing about what it fronts. The model picks the tool it
can read.
**Fix:** naming the A2A tool in the prompt did **not** work (two attempts). The fix is
architectural — expose the corpus over A2A **as well**, so both tools are the same nature and
are told apart by name only.
**Status:** tenant-observed, 2026-08.

### `Failed to fetch agent card: 400` — reads as a permission fault, is not one

Confirms the doc-sourced trap above **in a tenant**, with the real error text. An agent declared
with `protocols: [a2a]` but **no `agent_card`** is reachable and unusable: the caller fails at
invoke with `Failed to fetch agent card: 400`. Every instinct says RBAC; nothing is wrong with
RBAC. Write the card, and **never overwrite an existing one** — it may have been hand-tuned.
Also: **never set `agent_card_path`.** Foundry resolves the card and negotiates the protocol
version itself; setting it is actively harmful.
**Status:** tenant-observed, 2026-08.

### Read and write the agent endpoint as raw JSON — the SDK drops `protocols`

`AgentEndpointConfig` has **no `protocols` field**, so `agent.as_dict()` returns `None` for a
block the REST API returns in full. Round-tripping through the SDK model therefore **silently
deletes** `protocols` — disabling `responses` and breaking the front door you just built.
Merge-patch also **replaces arrays**: re-list every protocol, or you turn one off.
`api-version` for the Agents API is the literal string **`"v1"`** — a date-shaped value returns
400 and reads as a broken route. (ARM connections use a dated version; the two are not the same.)
**Status:** tenant-observed, 2026-08.

### A connection is not validated at creation — only at invoke

A connection pointing at a `.invalid` host was accepted with **HTTP 200**. Creation success says
nothing about reachability, so a broken target surfaces much later, inside an agent run, as a
tool failure. Do not treat a created connection as a working one.
**Status:** tenant-observed, 2026-08.

### Verify routing by connection NAME, never by tool type

Every A2A subordinate emits the same item type (`a2a_preview_call`), so **the type no longer
identifies which one ran** — only `name` does. A check written on the type alone passes happily
while the supervisor asks the document corpus for a number. Assert the expected tool fired
**and** that the other did not.
Corollary on observability: A2A hops are visible live — a streamed response emits an output-item
event for the A2A call at roughly a fifth of total latency, then keepalives. But **only the
supervisor's own hops stream**; whatever happens inside a subordinate arrives all at once with
its output. Do not animate inner steps as if they had been observed.
**Status:** tenant-observed, 2026-08.

### A relay contract with no interpretation mandate produces an echo — and the fix is upstream

**Symptom:** a supervisor built to relay subordinate figures faithfully reads as a bare
pass-through. Users say it "just returns what the data agent said".
**Cause, two layers.** The prompt only ever said what *not* to add (never recompute, never
restate, never round) and never once asked for a reading. But the decisive cause was upstream:
**no question in the calling app could reach the second subordinate**, so there was only ever one
source, nothing to juxtapose, and no synthesis was possible. The prompt rewrite alone was
cosmetic.
**Fix:** before blaming a synthesis prompt, prove that two sources actually arrive.
**Status:** tenant-observed, 2026-08.

### Granting interpretation buys the opposite defect, and prose rules will not contain it

**Symptom:** having asked for provenance and a reading, the answer becomes unusable the other
way — the same facts stated twice (as a lead sentence *and* as bullets), seventeen verbatims
across seven themes each followed by a gloss, and a closing paragraph about what to ask next.
Every sentence true and sourced; the whole unreadable. The dominant grievance sat third of seven
at the same visual weight as one voiced once — **a false picture assembled out of true
quotations**.
**Cause and fix — the transferable part:** a prose rule cannot beat a structural mandate. *"State
the provenance in one place and nowhere else"* was already in the prompt and was disobeyed,
because the **shape** section mandated two places: a lead carrying the scope, and a
"what-the-data-measured" section. The model read a sentence and a bullet list as different
presentations, not a repeat. **Deleting the second location** cut the answer by more than half in
a single deploy. Same mechanism on volume: *"a couple of quotations"* was read **per theme**, so
cap the **themes**, not the quotations.
Adjectives ("sparingly", "concise", "operational") moved nothing on their own. Removing a
mandate did. Also: never ask a reading to name "the question worth asking next" — that puts
process talk exactly where the insight was expected.
**Status:** tenant-observed across three deployed versions of the same prompt, measured on one
fixed question, 2026-08.

### The same prompt asked the user a question — one click into a demo

**Symptom:** the supervisor answered a **canned suggestion from the calling app's own UI** with a
clarifying question ("which reading of *at risk* do you mean?"), called no subordinate, and the app
rendered it under its "unsourced answer" banner. On a prepared question, on stage, the agent replied
with an intake form.
**Cause:** the prompt's cure for ambiguity was *"ask the reader which reading they meant"*. That
licence is permanently available and always cheaper than choosing, so the model took it — and a term
with three defensible readings (a risk band, a score threshold, a lifecycle stage; 800 / 825 / 593
customers, all correct) guarantees it fires. The ambiguity was real and correctly diagnosed; the
**remedy** was the defect.
**Fix:** replace the licence with a decision — name the criterion, take the widest actionable
cohort, and **declare the reading inside the answer**. Nothing is lost: the reading is still stated,
only the refusal is gone.
**Transferable:** deleting an escape hatch is not done until a test asserts its **absence**. "Prefer
X" leaves Y reachable, and a model under any pressure takes the cheaper branch. Grep the rendered
instructions for the forbidden move and fail the build on it.
**Status:** tenant-observed, 2026-08.

### Cap the wrong unit and the verbosity moves — only a total cannot be re-oriented around

**Symptom:** four consecutive prompt versions, each fixing the previous overrun, each obeyed to the
letter, each producing an answer as long as the one before — once **more than twice** as long
(8 591 characters, a fifty-row list, from a version whose only new rule was a per-line fact cap).
**Cause:** every cap named a *local* unit and left a neighbouring one free. Cap the **themes** and
quotations-per-theme absorb it. Cap the **layout** ("one line per record") and seven attributes move
onto the line. Cap **facts per line** and the list grows to fifty rows. Cap facts *and* list length
and each record sprouts **sub-bullets** — the same form in a third orientation.
**Fix:** two moves together. Make the unit **countable** ("a line that names more than three things
in total is over the limit", not "be concise" — adjectives moved nothing at any point), and add a
**total**: the whole reply fits on one screen, about thirty lines, headings included. The total is
the only constraint no layout routes around, and it must say what to sacrifice — cut records and cut
themes, never the scope of a figure.
**Evidence:** answer length went from 2 070–8 591 characters to **2 004–3 079** across six runs.
**Corollary — duplication migrates rather than dies.** Suppressed at the provenance level it
returned as identifiers printed in the lead *and* in the list, then a third time in the quotation
section. Each individual removal was obeyed.
**Status:** tenant-observed across five deployed versions of one prompt, 2026-08.

### A prose rule cannot stop a model ending its turn early — `tool_choice` can

**Symptom:** roughly **one turn in four** returned in ~6 s having called **nothing**, replying with
its plan — *"I must first question the two sources separately"*, an echo of the routing rule read as
a procedure to narrate. The calling app renders that as a one-line answer under its "unsourced"
banner: indistinguishable from a broken deployment.
**Cause:** routing instructions describe a sequence, and a sequence can be narrated instead of
executed. An explicit prose rule against it ("announcing a call is not making it; call them now, in
this turn") did **not** hold.
**Fix:** `PromptAgentDefinition(..., tool_choice="required")`. Structural, not persuasive.
**0 stalls in 6 runs**, both subordinates called every time.
**Read this next to the `a2a_preview` / `file_search` entry above — same knob, opposite verdict.**
There, `required` was powerless because a `file_search` was present to satisfy it; the model met the
constraint with the wrong tool. Here every tool on the agent is a subordinate, so there is nothing
to satisfy it *with* except the data. `required` fixes "called nothing"; it can never fix "called
the wrong one".
**SDK note:** `PromptAgentDefinition._attribute_map` is **empty** and `__init__` is
`(*args, **kwargs)`, so introspection tells you nothing about which fields exist. The only way to
know is to construct the object and read `as_dict()`. `tool_choice="required"` serialises.
**Status:** tenant-observed, 2026-08.

### Judge a prompt change on a batch — one run cannot tell you anything

**Symptom:** two consecutive runs of the **identical** deployed version, on the identical question,
returned 2 748 and 6 024 characters — one acceptable, one a regression. A third gave 2 070. A single
probe "proves" whichever conclusion it happens to draw, and the next version is then built on it.
**Fix:** re-ask the same question **at least five times** per version and report the spread, not a
sample. This is what turned the sequence above from opinion into measurement.
**Two harness traps that imitate a real regression:**
- If the helper already returns extracted response items, calling the extractor **again** on its
  result yields `[]` — which reads exactly like *"no subordinate fired"*, the same signal the app's
  unsourced banner uses. A tooling bug and a genuine routing failure are indistinguishable from the
  metric alone. Confirm against the answer text before believing either.
- `tool_user_error` (HTTP 400, body linking the A2A auth troubleshooting guide) is **transient**: it
  arrived once and the identical call succeeded on retry. Retry before diagnosing auth.
**Status:** tenant-observed, 2026-08.

---

After your own first live attempt, add the real error text here. That delta is the whole point of
this file.

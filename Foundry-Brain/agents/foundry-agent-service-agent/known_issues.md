# Known issues — foundry-agent-service-agent

Two sections, deliberately separated: what was **observed running**, and what was **read in
documentation**. Never promote a row from the second to the first without a trace.

---

## Observed — training lab, 2026-08-04

Seen in a Microsoft training lab (~15 screenshots, including a live workflow run). These are
product behaviours, not tenant quirks.

### 1. The model gates which tools you can attach

`Code interpreter` appears in the picker but is **disabled**, with the tooltip *"This tool
doesn't work with the model you selected."*

Found in no documentation. It inverts the natural build order: the model becomes an
architectural decision made *before* tool design, not a tuning knob afterwards.

**Do:** choose the model, open the tool picker under it, confirm every required tool is
selectable — then design.

### 2. `Save` and `Publish` are independent states

`Save` greys out when there are no pending edits; `Publish` stays active. A change can be saved
and not served, indefinitely.

Compounded when a Fabric data agent is involved — that has its own Draft/Publish. **A change can
be saved at both ends and live at neither.**

**Do:** when a prompt edit "has no effect", check the published version before debugging the
prompt.

### 3. Versions accumulate — 102 observed

One system's agent list: `20`, `46`, **`102`**. The **router** had the most, because routing is
tuned by rewording.

**Do:** call `delete_version(...)` in automation. Never identify an agent by version number.

### 4. Nothing reconciles the prompt against the attached tools

A prompt can name tools the agent doesn't have, and an agent can hold tools its prompt never
mentions. No warning either way. An agent told it has Mail, and given Web search, will attempt
the task and produce a confident, sourceless answer.

**Do:** diff prompt-declared tools against attached tools, in both directions, at review.

### 5. Tool invocation pauses for human approval

A live run stopped and displayed the concrete call — `GetMyDetails({"select": "…", "expand": ""})` —
with `Approve once` / `Always approve this tool` / `Always approve all tools` / `Deny`.

Two consequences:
- **A run that "hangs" may simply be waiting for approval.** Check the Preview pane first.
- **Approvals interrupt a live demo.** The lab's own guidance is to select *Always approve all
  tools*. Correct for a demo, wrong as an inherited default. Decide before presenting.

### 6. Agent creation asks for the name only

The create dialog collects a name — *"serves as its identifier in the API"* — and nothing else.
Model and instructions come later.

**Do:** any automation must handle an agent that exists but is unusable. And treat the name as
an identifier: it is duplicated into router prompts **and** workflow YAML, so a rename breaks
two other places silently.

### 7. Work IQ is per-capability, and that is a feature

Separate attachable tools: `User`, `Mail`, `Calendar`, `Teams`, `OneDrive`, `Word` — all
`Preview`. Observed distribution across one system had **zero overlap**, with routers and the
synthesizer holding no tools at all.

**Do:** attach per capability. It makes least privilege expressible: an agent that only needs the
org chart cannot be talked into sending mail.

### 8. The playground ships a connectivity smoke test

Starter prompt, portal-provided: *"Confirm the connectivity for all tools in this agent."*

**Do:** run it after attaching tools and **before** writing instructions. It separates "the
prompt claims a tool" from "the tool actually answers" — which is issue 4's only cheap remedy.

---

## Doc-sourced — expected, not verified

No execution trace exists for any of these.

| # | Trap | Source |
|---|---|---|
| 1 | Two agent generations ship side by side; classic samples don't apply to the current service | `generation_map.md` |
| 2 | `agent_card` **cannot** be set from the Python SDK — exposing an agent over A2A requires a REST PATCH | A2A docs |
| 3 | The portal cannot enable incoming A2A at all | A2A docs |
| 4 | A2A defaults to protocol **v0.3** if unspecified; v1.0 is JSONRPC-only | A2A docs |
| 5 | No streaming across an A2A hop; text modality only | A2A docs |
| 6 | SDK floors differ: `>=2.0.0` to call an agent, `>=2.3.0` to expose one | A2A docs |
| 7 | Fabric **data agent** is not toolbox-supported (Fabric **IQ** is) | toolbox support matrix |
| 8 | Background mode requires a model that supports it | Fabric IQ docs |

---

## Evidence discipline

Two findings were recorded as defects earlier in this brain and **both were wrong**: an agent
declared missing that existed, and a prompt/tool mismatch that was just the build mid-step.

Root cause: **a screenshot is a point in time, not a state of the world.** An unfinished build
looks exactly like a broken one, and a stated defect gets acted on.

**Rule:** before recording a mismatch as a finding, establish that the artifact was *complete* at
capture time. If that can't be established, it is a **question**, not a finding.

---

## Open questions

- Does a resolver's JSON actually reach the next agent? Every agent in the observed workflow read
  `=System.LastMessage`, never the previous step's variable. Depends on undocumented
  `autoSend: false` semantics. → **read the `Traces` tab on a real run**
- Can tool approval be pre-configured as policy rather than clicked per run?
- What does an agent's **`YAML`** tab contain — is the definition round-trippable?
- What does **`Call agent`** expose?
- `Routines` (Preview) — **zero results on Learn**. Assert nothing.
- Do `Memory` / `Guardrail` (Preview) change the prompt contract?

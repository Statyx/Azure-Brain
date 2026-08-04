# Known Issues — Foundry Observability Agent

Two classes, never mixed. **Observed** means it happened in a tenant, with a screenshot, a lab
step, or working code behind it. **Doc-sourced** means Microsoft says so and we have not seen it.

> ⚠️ This file is thinner than the other agents' on purpose. **We have never seen a trace.**
> The portal *flow* is lab-text; the trace *contents* are unknown. Everything about span shapes
> and field names is deliberately absent rather than guessed.

---

## Observed — Microsoft lab, 2026-08-04

### 1. Traces require Application Insights, and the missing button is the signal

From the Workflow page: **Traces → Connect → Create new resource → name → Create**.

The lab's own note:

> *"If you don't see the option to Connect to Application Insights, ignore Steps 1, 2, and 3, as
> Application Insights has already been connected."*

**Consequence:** the absence of a `Connect` button is not an error state. Any runbook that says
"click Connect" will read as broken on an already-configured project.

### 2. The unit of inspection is the Conversation ID

> *"Select Traces, select any of the Conversation IDs, to review the agent and tool call. You can
> also review the input, output, and metadata for that conversation."*

So the portal exposes, per conversation: **agent calls**, **tool calls**, and **input / output /
metadata** for each. That is the full extent of what we know the surface contains.

No cross-conversation or aggregate view was shown. Fleet-level analysis presumably means querying
the Application Insights resource directly — **unverified**.

### 3. Traces are positioned as the debugging surface for orchestration, by Microsoft

The lab places Traces immediately after workflow validation, framed as *"inspect the execution
path"*. It is the intended answer to "which agent actually ran".

### 4. A stalled workflow preview is usually a pending approval, not a failure

Microsoft's note:

> *"Before validating the workflow, test the individual agents and approve the tools. Tool
> approval cannot be completed within the workflow preview and may result in errors."*

**Why it belongs here:** the symptom presents as an observability problem ("nothing happened, no
error") and gets debugged as one. It isn't. Check for a pending consent before opening traces.

### 5. Guardrail and evaluation results live in *different* panes

Guardrails and Evaluations are separate left-nav items with their own result views (*Evaluation
runs*, *Evaluators*). They do **not** appear inside the trace view of a conversation.

**Consequence:** "is this system behaving?" is answered in three unconnected places. Do not expect
one screen.

---

## Doc-sourced — not verified in a tenant

| Item | Note |
|---|---|
| An **OpenTelemetry**-based tracing path exists alongside the portal Traces tab, landing in Application Insights / Azure Monitor | not exercised; no instrumentation call recorded here on purpose |
| Content capture (prompts / completions) may be opt-in rather than default | unverified — and it is the setting that decides whether traces contain customer data |
| Span and attribute naming follows gen-AI semantic conventions | plausible, unconfirmed; **do not write field names into instructions from memory** |
| Sampling behaviour | unknown — matters, because a sampled-out conversation looks identical to one that never ran |

---

## Evidence discipline

This agent enforces umbrella rule 9 for the rest of the brain, so it has to hold itself to it
first.

A screenshot is a point in time, not a state of the world. A trace is better — it is a record of
one execution — but it is still **one** execution. Two rules follow:

1. **Do not generalise from a single conversation.** "The variable wasn't passed" becomes "the
   platform never passes variables" only after several runs, or a doc.
2. **Record the observation, not the conclusion.** Write down the input string you saw. The
   interpretation can be revised; the string cannot.

---

## Open questions

The first real trace should close most of these. Record answers here, then tighten the playbook
in `instructions.md`.

- **What is actually in a trace?** Span names, attributes, whether token counts / latency / cost
  appear, and whether prompt and completion content is captured.
- **Does `autoSend: false` still write the agent's reply to the shared thread?** The single
  highest-value question in this brain — it decides whether a workflow can hand structured data
  between agents at all. Look at the *input delivered* to the downstream agent.
- **Are traces retroactive?** Assumed not. Never demonstrated.
- **Is the agent version visible in a trace?** If yes, "Save ≠ Publish" becomes trivially
  diagnosable.
- **Is there an aggregate / cross-conversation view**, or is it Application Insights queries only?
- **How long are traces retained**, and does it follow the Application Insights resource's policy?
- **Do guardrail interventions appear in a trace**, or only in the Guardrails pane?
- **What happens to tracing when Workflows retire (2026-12-01)?** Is the Traces tab tied to the
  workflow surface, or to the agents themselves?

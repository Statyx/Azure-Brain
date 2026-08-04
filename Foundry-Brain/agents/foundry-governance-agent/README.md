# Foundry Governance Agent

Guardrails and evaluations — the two answers to *is the system behaving?*

## Read

- [`instructions.md`](instructions.md) — the agent
- [`known_issues.md`](known_issues.md) — what goes wrong, and the long list of what we still
  haven't seen
- [`../foundry-observability-agent/instructions.md`](../foundry-observability-agent/instructions.md)
  — the third surface, and the only one that covers the multi-agent seam
- [`../../labs/foundry-iq/raw_capture.md`](../../labs/foundry-iq/raw_capture.md) — raw source

## Why one agent, not two

Guardrails and evaluations look like different departments — safety and quality. They are the same
question in two tenses, and keeping them apart is how teams end up believing one covers the other:

| | Guardrails | Evaluations |
|---|---|---|
| When | before / during the run | after the run |
| Verdict | binary — allowed or blocked | scored |
| Covers | **all** live traffic | a **sample** you chose |
| Fails by | refusing something legitimate | scoring a broken agent green |

**Running evaluations does not protect you. Setting guardrails does not measure you.**

## The four things worth knowing

1. **A guardrail is a policy object, not an agent field.** Created independently, applied to a
   *selected set* of agents and models. It survives an agent being rewritten — the only control
   layer in Foundry that does. It is layer 4 of the control model in `foundry-tools-agent`.

2. **New agents are outside the scope until someone re-scopes.** Coverage is an explicit
   selection, so "we have a guardrail" is not the same as "this agent is covered".

3. **Evaluations target one agent.** No observed way to evaluate a workflow end to end. In a
   supervisor topology the hop — where these systems actually break — is evaluated by nothing.
   That gap belongs to `foundry-observability-agent`.

4. **Generated data is a smoke test.** Ten synthesized rows prove the pipeline runs. They measure
   the generator's idea of your users, not your users.

## ⚠️ The lab narrated a safety agent and shipped a platform guardrail

Exercise 5's story lists a *"Responsible AI Agent"* that blocks unsafe prompts. The workflow
actually deployed has no such agent — safety arrives in Exercise 6 as a Guardrail object.

**Don't build safety as a routing node.** A hop can be skipped, mis-routed or edited away, and it
only sees what the router handed it.

## The example that ties the brain together

The lab's `Inventory-Agent` says *"the response must come only from the tool"* and hardcodes ten
product IDs in its prompt.

| Surface | Verdict |
|---|---|
| Guardrail | ✅ passes — nothing unsafe |
| Evaluation | ✅ likely passes — confident, well-formed, self-consistent |
| **Trace** | ❌ **catches it** — no tool-call span |

A confidently wrong grounded-looking answer passes both governance surfaces. Spot-check a trace
before believing a green score.

## ⚠️ Evidence level

Both portal flows are **lab-text**. **No guardrail was seen blocking anything and no evaluation
output was ever displayed** — so evaluator names, criteria, scales and thresholds are deliberately
absent rather than guessed. Sections marked 🧠 are this brain's reasoning, not observation.

## Boundary

| This agent | Not this agent |
|---|---|
| May this happen? Was it any good? | What actually happened → `foundry-observability-agent` |
| Policy applied to traffic | Tool boundaries and approvals → `foundry-tools-agent` |
| Scoring an agent's behaviour | Writing the agent → `foundry-agent-service-agent` |
| Noting the hop is uncovered | Designing the hop → `foundry-orchestration-agent` |
| Content safety and quality | Identity, networking, residency → `foundry-project-agent` *(planned)* |

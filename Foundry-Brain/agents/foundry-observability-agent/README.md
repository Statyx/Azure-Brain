# Foundry Observability Agent

How anyone knows what actually happened inside a Foundry system.

## Read

- [`instructions.md`](instructions.md) — the agent
- [`known_issues.md`](known_issues.md) — what goes wrong, and what we still haven't seen
- [`../../orchestration_patterns.md`](../../orchestration_patterns.md) — the open questions this
  agent exists to close
- [`../../labs/foundry-iq/raw_capture.md`](../../labs/foundry-iq/raw_capture.md) — raw source

## Why it exists

In a multi-agent system the response tells you almost nothing. A coherent paragraph can come from
the right agent citing the right tool, or from the wrong agent improvising from its prompt —
**indistinguishable at the output.** The trace is the only place the difference is visible.

This brain has a correction log because two findings were called from screenshots and both were
wrong. Umbrella rule 9 — *never claim verified without a trace* — is unenforceable unless someone
knows how to get one. That is this agent.

## The three things people get wrong

1. **Connecting Application Insights after the interesting run.** Telemetry is emitted live. The
   first failed demo — the one you most want to inspect — is usually the one you cannot.

2. **Treating a good answer as evidence of grounding.** No tool-call span means the answer came
   from the prompt. One observed lab agent is told "tool output only" *and* carries ten hardcoded
   product IDs; only a trace shows which one spoke.

3. **Using traces as a quality metric.** A trace answers *what happened*, never *was it good*.
   Aggregate quality is `foundry-governance-agent`'s job.

## ⚠️ Evidence level

The portal flow is lab-text. **No trace was ever shown to us** — field names and span shapes in
`instructions.md` are marked unverified. Treat the trace-reading playbook as *questions to ask*,
not a schema, and tighten it after your first real trace.

## Boundary

| This agent | Not this agent |
|---|---|
| What happened, in one conversation | Whether it was good → `foundry-governance-agent` |
| The evidence trail | What should be blocked → `foundry-governance-agent` |
| Reading the execution path | Designing it → `foundry-orchestration-agent` |
| That a tool was called | Which tools may exist → `foundry-tools-agent` |
| That retrieval returned nothing | Why the source is broken → `foundry-knowledge-agent` |

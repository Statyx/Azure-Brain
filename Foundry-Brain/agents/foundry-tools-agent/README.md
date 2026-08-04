# Foundry Tools Agent

What an agent can actually *do*: tool selection, connections, and approval posture.

## Read

- [`instructions.md`](instructions.md) — the agent
- [`known_issues.md`](known_issues.md) — what goes wrong
- [`../../portal_reality.md`](../../portal_reality.md) — tenant observations behind this
- [`../../labs/foundry-iq/raw_capture.md`](../../labs/foundry-iq/raw_capture.md) — raw source

## The three things people get wrong

1. **The model gates the tool list.** Observed: `Code interpreter` greyed out — *"This tool
   doesn't work with the model you selected."* Pick the model first, or you will design an agent
   that cannot be built.

2. **Approval is a real control, and it breaks workflow demos.** Tool invocation pauses the run
   and shows the operator the concrete call with its arguments. But that consent prompt **cannot
   be rendered inside a workflow preview** — so the run errors instead. Run each tool-bearing
   agent alone, approve, then run the workflow.

3. **The tool set is the permission boundary, not the prompt.** A prompt saying *"only if
   authorized"* is a default. The attached tools are the boundary. Fix over-reach by removing a
   tool, never by adding a sentence.

## The three layers, in one table

| Layer | What it is | What it does |
|---|---|---|
| Prompt guardrails | a **default** | biases behaviour; enforces nothing |
| Attached tool set | a **boundary** | the agent cannot act outside it |
| Tool-call approval | a **control** | a human sees the call and can refuse |

## Boundary

| This agent | Not this agent |
|---|---|
| Generic tool mechanics, MCP, approval posture | The prompt → `foundry-agent-service-agent` |
| Tool wiring in general | Fabric specifics → `foundry-fabric-bridge-agent` |
| A knowledge base *as a tool* | Its sources and retrieval → `foundry-knowledge-agent` |
| One agent's capabilities | Sequencing several agents → `foundry-orchestration-agent` |

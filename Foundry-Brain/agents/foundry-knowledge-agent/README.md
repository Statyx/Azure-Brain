# Foundry Knowledge Agent — Foundry IQ

Grounding a Foundry agent in enterprise knowledge: **Foundry IQ** knowledge bases, their
sources, and how an agent consumes one.

## Read

- [`instructions.md`](instructions.md) — the agent
- [`known_issues.md`](known_issues.md) — what goes wrong
- [`../../labs/foundry-iq/raw_capture.md`](../../labs/foundry-iq/raw_capture.md) — the raw lab
  capture everything here was distilled from
- [`../../reference_foundry_iq.md`](../../reference_foundry_iq.md) — the end-to-end reference
  implementation this agent is one leg of

## The three things people get wrong

1. **Foundry IQ needs an Azure AI Search resource behind it** — and that search service reads on
   **its own identity**. If it can't see the source system, retrieval returns nothing and the
   agent looks like it is hallucinating. The Fabric case needs **Contributor on the Fabric
   workspace**.

2. **A knowledge base is consumed as a tool, over MCP.** The portal's *Connect to Foundry IQ*
   button and a code `MCPTool(server_label=…, server_url=…, project_connection_id=…)` are the
   same thing. Which means approval gates and tool semantics apply to your retrieval.

3. **Fabric appears twice, in two different places.** *Fabric IQ (OneLake Catalog)* is a
   **knowledge source** — federated retrieval, no data movement. *Fabric Data Agent* is a
   **tool** — you delegate the question to a published Fabric artifact. Wiring both and hoping
   is not a design.

## Boundary

| This agent | Not this agent |
|---|---|
| Knowledge bases, knowledge sources, retrieval identity | The agent's prompt → `foundry-agent-service-agent` |
| Foundry IQ **as a source of knowledge** | Fabric data agent **as a tool** → `foundry-fabric-bridge-agent` |
| Reading from a Fabric lakehouse | Creating or changing any Fabric artifact → `Fabric-Brain/agents/ai-skills-agent` |

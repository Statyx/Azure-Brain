# Foundry Fabric Bridge Agent

Making a Foundry agent able to ask Microsoft Fabric a question — and trust the answer.

## Read

- [`instructions.md`](instructions.md) — the agent
- [`known_issues.md`](known_issues.md) — what goes wrong
- [`../../reference_foundry_iq.md`](../../reference_foundry_iq.md) — the end-to-end reference
  implementation this bridge sits inside
- [`../../labs/foundry-iq/raw_capture.md`](../../labs/foundry-iq/raw_capture.md) — raw source

## The three things people get wrong

1. **Two Fabric integrations, not one.** *Fabric IQ (OneLake Catalog)* is a **knowledge source** —
   federated retrieval over a lakehouse. *Fabric Data Agent* is a **tool** — you delegate the
   question to a published Fabric artifact that reasons for itself. Attaching both to one agent
   is legal, silent, and almost always wrong.

2. **The portal and the SDK are not competing binding styles — they are sequential.** The portal
   turns two GUIDs from the Fabric URL into a named **project connection**. Code then resolves
   that connection **by name**. Which is why the same script promotes across environments
   unchanged. Never hardcode the GUIDs.

3. **Approve the tool before running the workflow.** Tool approval cannot be completed inside a
   workflow preview — Microsoft says so explicitly. Run each Fabric-bound agent alone, force the
   tool call, approve, *then* run the workflow. Skipping this produces errors that look like
   anything but a permission prompt.

## Boundary — the hard one

> **This agent never modifies a Fabric artifact.**

| This agent | Not this agent |
|---|---|
| The Foundry side of the hop: connection, tool, wrapper prompt | Creating / publishing a Fabric data agent → `Fabric-Brain/agents/ai-skills-agent` |
| Reading the Fabric agent's metric definitions and agreeing them | Changing them → same handoff |
| Calling a lakehouse's data agent | The lakehouse itself → `Fabric-Brain/agents/lakehouse-agent` |
| Fabric **as a tool** | Fabric **as knowledge** → `foundry-knowledge-agent` |

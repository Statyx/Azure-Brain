# Generation Map — Microsoft Foundry agents

> **Read this before writing or following any Foundry instruction file.**
> Established 2026-08-04 from Microsoft Learn. Re-check the retirement date and the
> `foundry-classic` URL prefix before every demo — this is the fastest-moving surface
> in the whole umbrella.

## The problem this file exists to prevent

Microsoft Foundry's agent platform currently ships **two generations side by side**, with
two separate documentation trees, **and three separate retirement clocks**. A tutorial found
by a generic web search has roughly a coin-flip chance of targeting something with a
published end-of-life date.

| Generation | Docs URL prefix | Status (2026-08-04) |
| --- | --- | --- |
| **Classic** — "Foundry (classic) agents" | `learn.microsoft.com/azure/foundry-classic/agents/…` | Deprecated. Announced retirement **2027-03-31**. |
| **Current** — "Microsoft Foundry Agents Service" | `learn.microsoft.com/azure/foundry/agents/…` | Generally available. Has its own **tool catalog** and **toolboxes** (GA). |

### ⏰ Three retirement clocks, not one

The trap is that a feature can sit on the **current** tree and still be retiring — sooner
than the classic generation itself.

| What | Retires | Source |
| --- | --- | --- |
| Classic agents API, incl. **Connected Agents** | **2027-03-31** | classic docs banner |
| Foundry portal **Workflows** (visual builder) | **2026-12-01** | `azure/foundry/agents/concepts/workflow` |
| Microsoft **Agent Framework** | — (the recommended forward path) | same page |

> Portal Workflows are on the *current* documentation tree and still retire **before** the
> classic generation does. "It's in the new docs" is not evidence that something is durable.
> Check the page banner every time.

### How to tell the generations apart in three seconds

1. Look at the URL. `foundry-classic` in the path ⇒ retiring generation.
2. Classic pages carry a banner: *"This document refers to the Microsoft Foundry (classic)
   agents… Agents (classic) are now deprecated and will be retired on March 31, 2027."*
3. Classic tool docs live under `…/agents/how-to/tools-classic/…`; the current tool catalog
   lives at `…/azure/foundry/agents/concepts/tool-catalog`.
4. In the portal, the **New Foundry** toggle must be **on** for the current experience.
   Current-generation docs say so explicitly at the top of every procedure.

## Ruling for this brain

**Foundry-Brain targets the current generation** (`azure/foundry/agents/*`).

Classic may be documented only:

- as a **migration source** — "if your project was built on classic, here is the move", or
- when a capability exists **only** in classic and has no current equivalent yet. In that
  case the instruction file must say so explicitly, name the missing equivalent, and carry
  the date the gap was checked.

Every Foundry-Brain `instructions.md` opens with a generation banner:

```markdown
> **Generation:** Microsoft Foundry Agents Service (current, `azure/foundry/agents/*`).
> Classic (`azure/foundry-classic/*`, retires 2027-03-31) is out of scope — see
> [`../../generation_map.md`](../../generation_map.md).
> Doc set last checked: YYYY-MM-DD.
```

## Where multi-agent orchestration actually lives — **RESOLVED 2026-08-04**

> The 2026-08-04 bootstrap left this open. It is now closed by a first-party statement, quoted
> below. Full pattern guidance lives in [`orchestration_patterns.md`](orchestration_patterns.md).

Microsoft states it plainly on `azure/foundry/agents/how-to/tools/agent-to-agent`:

> *"Migrating from `agent.as_tool` or Connected Agents? **The Connected Agents tool from the
> classic Agents API isn't available in the new Foundry Agent Service.** To connect one agent
> to another, use one of the following approaches: **A2A tool** … **Workflows** …"*

So the classic supervisor pattern has **no like-for-like replacement**. It splits into three:

| Want | Current-generation mechanism | Status | Durable? |
| --- | --- | --- | --- |
| Supervisor calls a **sub-agent** | **Agent-to-Agent (A2A) tool** | preview | ✅ yes |
| Supervisor calls **tools** | **Toolbox** — curated bundle behind one managed MCP endpoint | **GA** | ✅ yes |
| Declarative multi-agent process | Portal **Workflows** (sequential / group chat / human-in-the-loop) | preview | ❌ retires 2026-12-01 |
| Code-first orchestration | **Microsoft Agent Framework** | — | ✅ recommended path |

Classic → current tool mapping table: `azure/foundry/agents/how-to/migrate#agent-tool-availability`.

### ✅ Confirmed by introspecting the SDK, not just by reading the doc

The paragraph above is Microsoft's statement. It was independently **measured** on
`azure-ai-projects` **2.4.0** (see [`tenant_proofs.md`](tenant_proofs.md), 2026-08-05):

| Introspection | Result |
| --- | --- |
| `ToolType` members | **no `CONNECTED_AGENT`** — the pattern is absent from the package, not merely discouraged |
| `AgentEndpointProtocol` members | **A2A** and **MCP** — the two supported inbound protocols |
| `WorkflowAgentDefinition.workflow` | a plain **`str`** — no typed graph; the format is undocumented and fails at runtime, not at construction |

The last row is the one that costs money: a demo whose spine is a hand-written workflow string
has no compile-time safety net at all.

### Consequence for this brain

`agent.as_tool` and Connected Agents **must not appear** in any Foundry-Brain instruction file
except as a migration source. Portal Workflows may be used to *stage a demo* but must never be
written as doctrine — an instruction file that teaches them is teaching a path that expires
2026-12-01.

## The Fabric bridge

First-party and documented — this is the load-bearing brick for Foundry → Fabric demos.
The Fabric tool is listed in the **current-generation built-in tool catalog**, which settles
that it survived the generation change.

| Path | Reference |
| --- | --- |
| **Microsoft Fabric (preview)** — built-in tool: *"Connect to a Microsoft Fabric data agent for data analysis"* | `azure/foundry/agents/how-to/tools/fabric` |
| **Fabric IQ** (preview) — connect agents to Fabric, incl. running a Fabric data agent in **background mode** | `azure/foundry/agents/how-to/tools/fabric-iq` |
| Fabric-side view of the same integration | `fabric/data-science/data-agent-foundry` |

Both are **preview**. Preview surfaces move without notice; re-check before each demo and
log every discrepancy in the owning agent's `known_issues.md`.

## SDK and platform facts (recorded 2026-08-04)

Sourced from `azure/foundry/agents/how-to/tools/agent-to-agent` and `…/concepts/tool-catalog`.
**✅ The core Python path is now tenant-verified** by a working Microsoft lab script
(`agents.py`, captured in [`labs/foundry-iq/raw_capture.md`](labs/foundry-iq/raw_capture.md)) —
rows marked ✅ below were executed successfully against a live project. The rest remain
doc-only and **unverified**.

| Item | Value | Evidence |
| --- | --- | --- |
| Python SDK | `pip install "azure-ai-projects>=2.0.0"` (GA) | ✅ ran |
| C# SDK | `Azure.AI.Projects` NuGet | doc |
| TypeScript SDK | `@azure/ai-projects` (GA) | doc |
| Java SDK | `com.azure:azure-ai-agents:2.0.0` | doc |
| Project endpoint | `https://<resource>.services.ai.azure.com/api/projects/<project>` | ✅ portal-observed |
| Client construction | `AIProjectClient(endpoint=…, credential=DefaultAzureCredential(), allow_preview=True)` | ✅ ran |
| Agent creation | `project_client.agents.create_version(agent_name=…, definition=PromptAgentDefinition(model=…, instructions=…, tools=[…]))` | ✅ ran |
| Connection lookup | `project_client.connections.get(<name>)` → `.id` | ✅ ran |
| OpenAI client | `project_client.get_openai_client()` | ✅ ran |
| Invocation | `openai.responses.create(..., extra_body={"agent_reference": {"type": "agent_reference", "name": …}})` | ✅ ran |
| Agent kinds | **Prompt Agents** (server-side, Projects SDK) vs **Hosted Agents** (Agent Framework `FoundryChatClient`, ephemeral in-process) | doc |

> ⚠️ **`allow_preview=True` is mandatory** to see preview tools (e.g. the Fabric data agent
> tool). Omit it and the tool type is simply absent — the resulting error never says "preview".

> ⚠️ **`agent_reference` needs its own `type` discriminator** (tenant-verified 2026-09-02). The
> abbreviated form `{"agent_reference": {"name": "My-Agent"}}` that reads naturally from the docs
> is rejected; the object must carry `"type": "agent_reference"` alongside `"name"`. This row was
> marked `doc` until it was run, and the shorthand was the first thing tried.

> ⚠️ **Hostname:** the portal shows `<resource>.services.ai.azure.com`. Some documentation shows
> `<resource>.ai.azure.com`. Copy the endpoint from the portal's *Project details* page; do not
> assemble it from a doc sample.

Minimum working dependency set, as shipped by the lab:

```
python-dotenv
openai
azure-identity
azure-ai-projects>=2.0.0
aiohttp
```

### ⚠️ RBAC roles were renamed

**Foundry User**, **Foundry Owner**, **Foundry Account Owner**, **Foundry Project Manager**
were previously *Azure AI User*, *Azure AI Owner*, *Azure AI Account Owner*, *Azure AI Project
Manager*. Role IDs and permissions are unchanged; both names may appear while the rename rolls
out. Typical need: **Contributor/Owner** on the Foundry resource for management, **Foundry
User** to build an agent.

> ⚠️ Hosted agents are **not supported in the workflow designer**. To orchestrate from inside a
> Hosted agent, use Microsoft Agent Framework workflows.

## Ownership boundary

Foundry-Brain **consumes** Fabric artifacts; it never modifies them. Creating or publishing
a Fabric Data Agent belongs to `Fabric-Brain/agents/ai-skills-agent/`. Crossing that line
is a handoff, stated explicitly (umbrella rules 5 and 7).

## Change log

| Date | Change |
| --- | --- |
| 2026-08-04 | File created. Classic/current split recorded, retirement date 2027-03-31, Fabric + Fabric IQ tool paths recorded, connected-agents generation question left open. |
| 2026-08-04 | **Open question closed.** Connected Agents confirmed absent from the new service; replacements are the A2A tool + Workflows. Portal Workflows found to retire **2026-12-01** — a second, earlier clock on the *current* tree. Toolbox (GA), SDK versions, project endpoint format and the Foundry RBAC rename recorded. Pattern guidance split out into `orchestration_patterns.md`. |

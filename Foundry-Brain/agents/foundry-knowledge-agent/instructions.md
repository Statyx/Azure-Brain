# Foundry Knowledge Agent — Foundry IQ

> **Generation:** targets the **current** Foundry Agent Service (`azure/foundry/agents/*`).
> Read [`../../generation_map.md`](../../generation_map.md) first — the classic tree
> (`azure/foundry-classic/agents/*`) retires **2027-03-31** and its grounding samples do not apply.
>
> **Evidence status:** the flows below were observed end-to-end in a Microsoft training lab
> ("Building Foundry IQ", 2026-08-04) — portal steps, the working `agents.py`, and the shipped
> `parameters.env`. Full source: [`../../labs/foundry-iq/raw_capture.md`](../../labs/foundry-iq/raw_capture.md).
> Anything doc-derived rather than observed is labelled inline.

---

## Core Identity

You own **grounding**: how a Foundry agent gets access to enterprise knowledge it did not
learn during training.

In the current generation that means one product — **Foundry IQ** — and one object: the
**knowledge base**. You build knowledge bases, attach knowledge sources to them, and expose
them to agents.

You do **not** own the agent's prompt (→ `foundry-agent-service-agent`), the routing graph
(→ `foundry-orchestration-agent`), or anything on the Fabric side of a Fabric binding
(→ `foundry-fabric-bridge-agent`, and beyond it `Fabric-Brain/agents/ai-skills-agent`).

The one thing to get right:

> **A knowledge base is not a folder of documents. It is a retrieval service with an identity,
> a model, and its own RBAC — and agents consume it as a tool.**

---

## Mandatory Rules

1. **Provision the search resource before the knowledge base.** Foundry IQ is backed by an
   **Azure AI Search** service. No search resource, no knowledge base — the *Knowledge* page
   asks you to pick one and connect before it will let you create anything.
2. **Grant the search service access to every system it must read.** Foundry IQ reads on
   *its own* identity, not the caller's. Observed: the AI Search service had to be added as
   **Contributor** on the **Fabric workspace** before the Fabric IQ source would work. This is
   the single most likely silent failure in the whole flow — see Rule 8.
3. **One knowledge base, many sources.** Do not create a knowledge base per document set. The
   knowledge base is the unit an agent binds to; the sources are what you add and remove
   underneath it without touching any agent.
4. **Every knowledge base needs a chat completion model.** It is set on the knowledge base
   itself, separately from any agent's model. Retrieval reasons with its own model.
5. **Match the embedding model to the source type.** Only sources that get *indexed* take an
   embedding model. Federated sources (Fabric IQ) do not — they are queried in place.
6. **Know which sources move data and which do not.** Blob and AI Search sources are **indexed**
   (a copy is embedded and stored). Fabric IQ is **federated** (no data movement). This changes
   your answer to *"where does the customer's data live?"* — get it right in front of a CISO.
7. **Verify the source reaches `Active`.** Creation is asynchronous. A source sitting at
   `Creating` is not a failure and not a success. Refresh, then check — the lab says so
   explicitly for the Fabric IQ source.
8. **Test retrieval before blaming the prompt.** An agent that "hallucinates" against a
   knowledge base is usually a knowledge base returning nothing. Query the knowledge base path
   first, prompt second.

---

## The object model

```
Azure AI Search resource                    ← the backing service. Connected once per project.
└── Knowledge base                          ← what an agent binds to. Has a name + a chat model.
    ├── Knowledge source  (Azure Blob Storage)      indexed    · needs an embedding model
    ├── Knowledge source  (Azure AI Search Index)   indexed    · reuses an existing index
    └── Knowledge source  (Fabric IQ / OneLake)     federated  · no data movement
```

Observed instance from the lab, for shape:

| Layer | Value |
|---|---|
| Search resource | `srch-foundry-iq-lab-<id>`, auth type **API Key** |
| Knowledge base | `foundry-lab-knowledgebase`, chat completion model `gpt-5.4-mini` |
| Source 1 | `customer-loyalty-data` — Blob, container `customerloyalty`, extraction **Minimal**, embedding `text-embedding-ada-002` |
| Source 2 | `product-catalog` — existing AI Search index `product-catalog-index` |
| Source 3 | `return-policy` — **Fabric IQ (OneLake Catalog)**, bound to a Lakehouse |

> Note the third source is *named* `return-policy` but bound to the retail **Lakehouse**. Source
> names are free text and carry no binding meaning. Do not infer content from a source name — in
> a customer's tenant it will be wrong at least once.

---

## 🔑 How an agent actually consumes a knowledge base

This is the finding that reframes everything, and it is **verified in working code**.

There are two paths, and they produce the same thing:

### Path A — portal, no code

`Agents` → pick the agent → **Knowledge** section → `Add` → **Connect to Foundry IQ** → pick the
knowledge base → `Connect` → `Save`.

### Path B — code, and what Path A is really doing

The knowledge base is exposed as an **MCP server**. The project's *Connected resources* page
surfaces three values, and they go straight into an `MCPTool`:

```python
from azure.ai.projects.models import MCPTool

mcp_tool = MCPTool(
    server_label=server_label,              # from project Connected resources
    server_url=server_url,                  # the knowledge base's MCP endpoint
    project_connection_id=project_connection_id,
    require_approval="never",               # ← see the tools agent; this is a real control
)
```

…then attached like any other tool:

```python
project_client.agents.create_version(
    agent_name="Rewards-Campaign-Agent",
    definition=PromptAgentDefinition(model=..., instructions=..., tools=[mcp_tool]),
)
```

**Consequences you should act on:**

| Because | Therefore |
|---|---|
| Grounding is a *tool*, not a special agent field | it obeys tool rules — approval gates, tool-call limits, ordering against other tools |
| The binding is an **MCP endpoint + a project connection** | it can be pointed at a different knowledge base without touching the agent's prompt |
| `require_approval` applies to it | a knowledge base call can pause a run waiting for a human, exactly like a Fabric call |
| Two agents can share one `mcp_tool` object | observed: `Rewards-Campaign-Agent` and `Sales-Associate-Agent` were built from the same instance |

> **Corollary, and a good line in front of an architect:** "no custom RAG code" is accurate, but
> it is not magic — retrieval was moved behind a managed MCP endpoint. You still own the source
> configuration, the identity, and the failure modes. You stopped owning the chunking loop.

---

## Choosing a knowledge source type

| You have | Use | Data moves? | Needs embedding model | Notes |
|---|---|---|---|---|
| Loose files (PDF, docx, policies) in a container | **Azure Blob Storage** | ✅ indexed | ✅ | Choose a *content extraction mode* — the lab used `Minimal` |
| An AI Search index someone already built | **Azure AI Search Index** | already indexed | ❌ | Fastest path; you inherit its schema and its staleness |
| Structured enterprise data in a Lakehouse / OneLake | **Fabric IQ (OneLake Catalog)** | ❌ federated | ❌ | Bound by **browsing the catalog**, not by pasting GUIDs |
| A published Fabric **data agent** (NL→SQL over a semantic model) | *not a knowledge source* | — | — | That is a **tool**, not knowledge → `foundry-fabric-bridge-agent` |

**The last row is the one people get wrong.** Fabric appears twice in Foundry, in two different
places, doing two different things:

- **Fabric IQ (OneLake Catalog)** → added under *Knowledge sources*. Retrieval over lakehouse data.
- **Fabric Data Agent** → added under *Tools*. Delegates a natural-language question to a
  published Fabric artifact that answers it with its own reasoning.

Same vendor, same lakehouse, different contract. Decide which one you need **before** you open
the portal, or you will wire both and not know which answered.

---

## Authoring an agent that uses a knowledge base

Grounding does not make an agent truthful on its own. Both grounded agents in the lab carry an
explicit containment clause, and both are worth copying verbatim in spirit:

```
• Generate responses only from the retrieved knowledge and tool outputs.
  Do not assume or invent any values.
• Do not summarize, filter, or remove any important information from the knowledge source.
• If the required information is not available in the knowledge or tool output,
  clearly state that the data could not be found.
```

Three separate instructions, doing three separate jobs:

| Clause | Failure it prevents |
|---|---|
| *only from retrieved knowledge* | the model answering from its training data |
| *do not summarize or filter* | the model silently dropping rows the consumer needed |
| *state that the data could not be found* | an empty retrieval being dressed up as an answer |

The third one is the one people forget, and it is the one that turns a silent wrong answer into
a visible gap.

> ⚠️ **Anti-pattern, observed in the lab.** `Inventory-Agent` is told *"The response must come
> only from the Fabric Data Agent tool output"* — and then its instructions hardcode a list of
> product IDs "at risk of stockout". Those two clauses contradict each other. It works in a demo
> because the hardcoded list happens to match. In production it is a stale answer with a
> confident tone. **Never put business data in a prompt when the whole point of the agent is to
> fetch that data.**

---

## Provisioning order (the order matters)

1. Deploy an **embedding model** in the project (`text-embedding-ada-002` in the lab) — needed
   before you can create an indexed source.
2. Deploy a **chat completion model** — needed by the knowledge base itself.
3. Create / identify the **Azure AI Search** resource.
4. Grant that search service access to every downstream system it must read
   (**Contributor on the Fabric workspace** for Fabric IQ sources).
5. In the project: `Knowledge` → pick the Foundry IQ resource → choose auth type → `Connect`.
6. `Create a knowledge base`.
7. Add sources one at a time; each has its own dialog and its own auth.
8. Name the knowledge base, set its chat completion model, `Save knowledge base`.
9. Refresh until every source reads **Active**.
10. Bind it to an agent — portal *Knowledge* section, or `MCPTool` in code.

Steps 4 and 9 are the two that get skipped, and they are the two that cause the failures that
look like prompt problems.

---

## Hard limitations (recorded 2026-08-04)

| Limitation | Consequence |
|---|---|
| Foundry IQ is **preview** | surfaces move without notice; re-check before every engagement |
| Backed by Azure AI Search — a separate billable resource | it is on the customer's bill and in the customer's region; say so early |
| Source creation is **asynchronous**, with a `Creating` state and no completion event | you must refresh and verify; automation must poll |
| The lab connected the search resource with **API Key** auth | key-based auth is the easy path, not the right one — prefer managed identity where the portal offers it, and record which you used |
| Indexed sources hold a **copy** of the data | deletion and residency questions apply to the index, not just the source |

---

## Error recovery

| Symptom | Likely cause | Action |
|---|---|---|
| Knowledge source stuck on `Creating` | asynchronous creation, or a permission the service cannot report | refresh; if it does not go `Active`, check the search service's RBAC on the source system |
| Fabric IQ source fails or returns nothing | the **AI Search service** lacks Contributor on the Fabric workspace | add it in Fabric → *Manage access*, by the search service name |
| Agent answers from training data despite a knowledge base | binding present, retrieval empty | query the knowledge base directly before touching the prompt |
| Agent returns a partial answer, dropping rows | no *do not summarize or filter* clause | add the containment clause; this is a prompt fix, not a retrieval fix |
| Cannot create an indexed source — no embedding model offered | embedding model not deployed in this project | deploy `text-embedding-ada-002` (or equivalent) first |
| `Knowledge` page will not let you create a knowledge base | no Foundry IQ (AI Search) resource connected | connect the resource first; the dropdown is the gate |
| Two Fabric answers disagree | both a Fabric IQ **source** and a Fabric data agent **tool** are attached | remove one; decide the contract deliberately |

---

## Handoff protocol

| When | Hand off to | With |
|---|---|---|
| The agent's prompt or output contract needs work | `foundry-agent-service-agent` | the role (router/wrapper/action/synthesizer/resolver) and the consumer |
| A Fabric **data agent** must be called as a tool | `foundry-fabric-bridge-agent` | the connection name, workspace ID, artifact ID |
| The Fabric artifact itself must be created or changed | `Fabric-Brain/agents/ai-skills-agent` | ⚠️ **never modify a Fabric artifact from here** |
| Tool approval, MCP mechanics, `allow_preview` | `foundry-tools-agent` | which tools and their approval posture |
| Several agents must be routed between | `foundry-orchestration-agent` | the agent names and their output contracts |
| The search resource / RBAC / networking must be provisioned | `foundry-project-agent` *(planned)* | region, identity, resource names |

---

## Verification checklist

- [ ] Search resource connected; auth type recorded (key vs identity)
- [ ] Every source reads **Active**, not `Creating`
- [ ] Search service has RBAC on every system it reads — Fabric workspace included
- [ ] Knowledge base has a chat completion model set
- [ ] Indexed sources have an embedding model; federated ones do not
- [ ] The agent's prompt carries all three containment clauses
- [ ] No business data hardcoded in a prompt that exists to fetch that data
- [ ] Retrieval tested directly, before any prompt tuning
- [ ] It is written down whether each source is **indexed** (copy) or **federated** (in place)

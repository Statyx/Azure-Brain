# Known Issues — Foundry Fabric Bridge Agent

Two classes, never mixed. **Observed** means it happened in a tenant, with a screenshot, a lab
step, or working code behind it. **Doc-sourced** means Microsoft says so and we have not seen it.

---

## Observed — Microsoft labs, 2026-08-04

### 1. Tool approval cannot happen inside a workflow preview

Microsoft states it in the lab, unprompted:

> *"Before validating the workflow, test the individual agents and approve the tools. Tool
> approval cannot be completed within the workflow preview and may result in errors."*

**Why it bites:** the failure appears as a workflow error, not as a pending approval. There is
nothing in the message pointing at consent.

**Fix / order of operations:** open each Fabric-bound agent alone → ask something that forces the
tool call → approve (*Always approve this tool*) → then run the workflow.

**This confirms and sharpens an earlier finding.** Tool invocation pauses the run and shows the
operator the concrete call with its arguments. That gate is real; the workflow preview simply has
no surface to render it on.

### 2. The two binding styles are sequential, not alternative — an earlier reading was wrong

A previous pass through the docs recorded "portal binding by GUID" and "SDK binding by
connection" as two competing options. Working code shows they are one flow:

- the **portal** takes `Workspace ID` + `Artifact ID` and produces a **named project connection**;
- the **SDK** calls `project_client.connections.get(<name>)` and passes `connection.id` into
  `ToolProjectConnection`.

**Consequence:** code never contains a Fabric GUID. Environment promotion is a connection swap.
Any instruction that tells you to paste GUIDs into a script is wrong.

### 3. `allow_preview=True` is mandatory and easy to miss

`AIProjectClient(endpoint=..., credential=..., allow_preview=True)` — without it the Fabric
preview tool is not available. The type names themselves flag the maturity:
`MicrosoftFabricPreviewTool`, `FabricDataAgentToolParameters(...)`, field
`fabric_dataagent_preview`.

### 4. The two GUIDs must be scraped out of a browser URL by hand

The lab's own instruction: workspace ID is *"the string that appears between `groups/` and
`/aiskills`"*; artifact ID is *"between `aiskills/` and `?` (do not include the `?`)"*.

**Consequence:** the portal path is brittle and unautomatable. The trailing-`?` warning exists
because people include it.

#### Correction, 2026-08 — "unautomatable" is too strong when you deployed the Fabric side yourself

The two GUIDs are only hard to obtain if you arrive holding nothing but a browser URL. They are
not new values: **workspace ID** and **artifact ID** are exactly what the Fabric REST API returns
when it creates the workspace and the data agent, so any scripted Fabric deploy is already holding
both before the Foundry side starts. Scraping them back out of a URL recovers, by hand, values the
deploy wrote to disk minutes earlier.

So the rule splits in two:

- **Arriving at a pre-existing Fabric estate** — the portal path stands. Item 4 is unchanged: scrape
  carefully, mind the `?`.
- **Deploying both halves in one chain** — pass `workspace_id` and `data_agent_id` straight from
  deploy state into an ARM connection PUT. No browser, no copy-paste, and the connection is created
  in the same idempotent step as everything else.

**Status:** *unconfirmed for the ARM half.* The identity of the GUIDs is established — it follows
from the URL format the lab itself documents and from the creation responses. What is **not**
established is the ARM request body: the `category` a *Fabric data agent* connection expects is
undocumented, and no tenant has accepted or rejected one here. An implementation that probes
`FabricDataAgent` → `MicrosoftFabric` → `CustomKeys`, records the winner, and falls back to printed
portal steps exists in a demo repo; it has not been run.

**Do not read this as "the portal step is unnecessary."** Read it as: the *inputs* to that step are
already in your hand, and the remaining unknown is one field.

**Related:** a connection is **not validated at creation** — an unreachable target is accepted with
HTTP 200 and only fails at invoke. So a scripted connection proves less than it appears to, and
still needs a routing probe behind it.

#### Correction — 2026-09-02: the probe was run, and ARM cannot do it at all

The implementation described above as *"it has not been run"* has now been run against a live
tenant (Sweden Central, `Microsoft.CognitiveServices/accounts/*/projects/*`). It **failed**, and the
failure changes the conclusion rather than completing it.

**The remaining unknown was not one field. The category does not exist on the control plane.**

`MicrosoftFabricPreviewTool` fails at *runtime*, after the connection is created and the agent is
built, with:

```
No CustomKeys connection found for AzureFabric
```

So the tool resolves a connection that is `CustomKeys` **and** of category `AzureFabric`. Measured
against ARM:

| Attempt | Result |
|---|---|
| `category: AzureFabric` | rejected — `unable to deserialize request body`, at api-versions `2025-04-01-preview`, `2025-06-01`, `2025-06-01-preview`, `2025-08-01-preview`, `2025-10-01-preview`, `2025-11-15-preview` |
| `category: MicrosoftFabric` + `authType: CustomKeys` | rejected — *"AuthType for MicrosoftFabric Connection can only be AAD, UserEntraToken"* |
| `category: MicrosoftFabric` + `authType: AAD` | **accepted, HTTP 200** — and then refused by the tool at runtime |
| data-plane `client.connections` | read-only: `get`, `get_default`, `list`. No `create`. |

Brute-forcing the category enum (it is *not* a discriminator, so it yields no list — see the
enumeration technique below) gives: **accepted** — `MicrosoftFabric`, `AzureOneLake`,
`AzureSynapseAnalytics`, `CustomKeys`, `RemoteA2A`, `RemoteTool`. **Rejected** — `AzureFabric`,
`azurefabric`, `Fabric`, `FabricDataAgent`, `PowerBI`, `MicrosoftOneLake`.

**Revised rule: the portal step is REQUIRED for a Fabric data-agent connection, not a fallback.**
The paragraph above — *"do not read this as 'the portal step is unnecessary'"* — was right to hedge,
and the hedge should now be read as a hard requirement. Create the connection once in the portal,
under the name the deploy resolves by, and keep everything else scripted.

**The expensive part is that ARM says yes.** `MicrosoftFabric`/`AAD` is stored and returns 200, so a
deploy script that treats "ARM accepted it" as its success oracle reports success and fails six
steps later inside a model run. **ARM acceptance is not tool validation.** The only oracle for a
connection is a real question routed through the tool that consumes it.

**Evidence:** runtime error above, reproduced on every run of a 3-probe verifier; the six api-version
rejections and the enum brute-force were run against a scratch connection name; the same verifier's
A2A probe passes in the same run, so the harness itself is known good.

**Technique worth reusing —** make the validator enumerate itself. Sending a deliberately invalid
*discriminator* returns the full legal set. `authType: "__probe__"` returned all 21 values:
`RegistryIdentity, Basic, None, PAT, SAS, ServicePrincipal, AccessKey, ApiKey, CustomKeys, OAuth2,
AccountKey, AAD, DelegatedSAS, ProjectManagedIdentity, AccountManagedIdentity, UserEntraToken,
AgentUserImpersonation, AgenticIdentityToken, AgenticUser, UserTokenAndProjectManagedIdentity,
DeveloperConnection`. **Limit:** this works only for discriminators. `category` is not one — an
unknown value yields only `unable to deserialize request body`, so it must be brute-forced.

**Method note, recorded because it nearly cost the demo:** the first of these probes was run
*against the production connection*, which was deleted before knowing whether any replacement would
be accepted. It was restored from a rollback captured seconds earlier. `tenant_proofs.md` already
states the rule — *the undo must exist before the do* — and the correct move was a scratch
connection name from probe one, not from probe four.

#### Correction — 2026-09-02 (same day): the MCP route does not exist either

Having proved ARM cannot create the connection, the obvious next hope was to skip the connection
entirely and reach the data agent as an **MCP server**, the way `foundry-tools-agent` attaches any
other MCP tool. Fabric *does* run an MCP data plane, and the ontology agent documents a working
URL shape for it (`mcp_ontology.md`):

```
https://api.fabric.microsoft.com/v1/mcp/dataPlane/workspaces/{ws}/items/{id}/ontologyEndpoint
```

Sixteen endpoint names were tried against that shape with a live `api.fabric.microsoft.com` token
and a JSON-RPC `initialize`, pointed at a **DataAgent** item: `aiSkillEndpoint`,
`dataAgentEndpoint`, `aiAssistantEndpoint`, `mcpEndpoint`, `aiassistant`, `aiAssistant`, `aiskill`,
`aiSkill`, `dataAgent`, `dataagent`, `agentEndpoint`, `queryEndpoint`, `openai`, `endpoint`, bare
`/items/{id}`, `/aiskills/{id}`. Also `/mcp/dataPlane/workspaces/{ws}` and `.../{ws}/items`.

**All returned HTTP 404**, JSON-RPC `-32601`, `errorCode: EntityNotFound`.

**The control is what makes this conclusive.** The same URL with `/ontologyEndpoint`, against the
same DataAgent item, returns **HTTP 500** `-32603` *"unable to complete your request due to an
internal error"* — the route exists and is dispatched, and fails only because the item is the wrong
type. A 404 on every other name therefore means **the route itself does not exist**, not that
permissions or the item are wrong. Endpoint names on this surface are per-item-type, and no
DataAgent name is registered.

| Signal | Meaning |
|---|---|
| `404` / `-32601` / `EntityNotFound` | route not registered — the endpoint name is not a real one |
| `500` / `-32603` internal error | route exists, dispatched, wrong item type behind it |

**Rule: a Fabric data agent is not reachable as an MCP server on the Fabric MCP data plane.**
Do not spend a session guessing endpoint names — use the 404-vs-500 discriminator above to settle
it in one request. (Unrelated and still true: `https://api.fabric.microsoft.com/v1/mcp/powerbi`
exists as a *different* MCP surface — see `Fabric-Brain/fabric_api.md`. It is not a data-agent
route.)

**Consequence — this closes the last alternative.** Three independent negatives now converge:
ARM has no `AzureFabric` category, the data plane's `client.connections` is read-only, and the MCP
data plane exposes no data-agent endpoint. **The portal step is the only path**, which promotes the
"revised rule" above from *strong recommendation* to *the only known method*.

**Evidence:** 16 probe URLs, all `404 / -32601 / EntityNotFound` with Fabric `requestId`s;
control `/ontologyEndpoint` → `500 / -32603` on the same item and token; item confirmed as
`"type":"DataAgent"` by `GET /v1/workspaces/{ws}/items/{id}` returning 200 in the same script run,
so the token, workspace and item id are all known good.

#### 🔴 RETRACTION — 2026-09-03: the MCP route *does* exist, and the portal is *not* the only path

The two blocks above conclude that the portal step is the only known method. **That conclusion is
withdrawn.** Both negatives it rests on were over-stated, and one of them was produced by a broken
probe. Nothing above is deleted — the reasoning is the lesson.

**1. The data agent's MCP endpoint exists.** Verified live, Sweden Central, 2026-09-03:

```
POST https://api.fabric.microsoft.com/v1/mcp/workspaces/{ws}/dataagents/{agent_id}/agent
     Accept: application/json, text/event-stream

initialize -> 200   serverInfo.name = "DataAgent MCP Server", protocolVersion 2025-06-18
tools/list -> 200   [{"name": "DataAgent_<agent name>",
                      "inputSchema": {"properties": {"userQuestion": {"type": "string"}}},
                      "annotations": {"readOnlyHint": true}}]
```

Three route families exist and they do **not** share a shape:

| Target | Route |
|---|---|
| **Data agent** | `/mcp/workspaces/{ws}/dataagents/{id}/agent` |
| Ontology | `/mcp/dataPlane/workspaces/{ws}/items/{id}/ontologyEndpoint` |
| Semantic model | `/mcp/fabricaihub/integrations/m365` |

The sixteen probes all held `/mcp/dataPlane/workspaces/{ws}/items/{id}/` fixed and varied only the
last segment. The data agent route drops `dataPlane` **and** uses `dataagents` instead of `items`.
Sixteen results say nothing about a shape never sent.

**2. The control was malformed.** `/ontologyEndpoint` returned `500` because the probe omitted
`Accept: text/event-stream`, required by MCP streamable-HTTP. With the header, the same URL returns
**200**. The 404-vs-500 table above is therefore an artefact of the client, not a property of the
server — and the "conclusive" reasoning built on it was circular. **A control only controls if it
is correct: make it succeed once against something known to work before letting its failure mean
anything.**

**3. The connection IS creatable from ARM — with a different category.** `AzureFabric` really is
not an ARM category (re-probed 2026-09-03 across five body shapes — `CustomKeys`+credentials, AAD,
UserEntraToken, API target, portal target — all `unable to deserialize request body`). But that is
a fact about **one binding**, not about the goal:

| Tool | Connection it resolves | From ARM? |
|---|---|---|
| `MicrosoftFabricPreviewTool` | `CustomKeys` / `AzureFabric` | **No** — portal only |
| `FabricIQPreviewTool` | `RemoteTool` / `GenericProtocol`, MCP `target` | **Yes** |

The working body, `PUT .../projects/{proj}/connections/{name}?api-version=2025-06-01`:

```json
{"properties": {
  "category": "RemoteTool",
  "group": "GenericProtocol",
  "authType": "UserEntraToken",
  "audience": "https://api.fabric.microsoft.com",
  "target": "https://api.fabric.microsoft.com/v1/mcp/workspaces/{ws}/dataagents/{id}/agent",
  "isSharedToAll": false,
  "useWorkspaceManagedIdentity": false,
  "metadata": {"type": "fabric_iq_preview"}
}}
```

- `metadata.type` is **undocumented and load-bearing**: without it the connection is created and
  resolves by name, and the tool still refuses it.
- `audience` is the **Fabric** one. The azd docs show `https://analysis.windows.net/powerbi/api`;
  prefer what a working portal-made connection produced over what the document says.
- **The connection name must not contain underscores** under `RemoteTool` —
  *"Connection name must be 1-64 characters long and can only contain alphanumeric characters,
  dashes, and dots."* `MicrosoftFabric` accepted underscores, so a name that worked for years
  starts failing the moment the category changes. The rule is **category-dependent**, not global.

**4. What misled the whole search.** The runtime error is
`No CustomKeys connection found for AzureFabric`. I searched ARM for `AzureFabric`, correctly found
nothing, and concluded the goal was unreachable. **The error names a category you never create.**
Searching for the string in an error message is not the same as searching for the capability the
error is about.

**⚠️ Still unresolved — do not read this as "it works end to end."** With the ARM connection
created and the endpoint proven reachable by a user token, `FabricIQPreviewTool` still fails at run
time with:

```
The remote MCP server at https://api.fabric.microsoft.com:443/v1/mcp/workspaces/{ws}/dataagents/{id}/agent
returned HTTP 404 (Not Found) while enumerating tools
```

Ruled out so far: endpoint mode (fails identically whether `server_url` is sent or omitted and the
connection `target` used); Fabric workspace RBAC (both the Foundry **account** and **project**
system-assigned identities granted `Admin` on the workspace — neither had *any* access before, and
granting it changed nothing); Fabric tenant settings (`ServicePrincipalAccessPermissionAPIs`,
`ServicePrincipalAccessGlobalAPIs` and both admin-API settings are **enabled**). The item is
published — the user-token probe lists its tool. So the failure is in the **cross-service identity
hop**, and it is not yet characterised. `PowerBIMCP` is disabled on this tenant; whether an
equivalent gate exists for the data-agent MCP surface was not determined.

**Evidence:** live `initialize`/`tools/list` 200s with the tool name returned; ARM `PUT` accepted
and read back with `category=RemoteTool`; the five-body `AzureFabric` rejection sweep; workspace
`roleAssignments` before (one User) and after (two ServicePrincipal Admins); `GET
/v1/admin/tenantsettings` for the service-principal flags; three verifier runs after each change,
all failing identically.

### 5. ⚠️ The lab's own Fabric-bound agent contradicts itself

`Inventory-Agent` is instructed *"The response must come only from the Fabric Data Agent tool
output"* — and its prompt then hardcodes ten product IDs as "at risk of stockout".

**This is a demo shortcut, not a pattern.** It guarantees the demo lands and guarantees the agent
is wrong the day inventory changes. Delete that block before reusing the agent.

### 6. You inherit the Fabric agent's business definitions, sight unseen

The observed Fabric data agent defines, in its own instructions:
`Revenue = Sum(order_lines.LineTotalAmount)`, `Return Rate = Returns / Orders`, and a full
table-to-domain mapping.

**Consequence:** your Foundry agent quotes those definitions whether or not anyone on the Foundry
side read them. A mismatch produces answers that are internally consistent and externally wrong.
Read that block before shipping; change it only in Fabric.

### 7. The AI Search service — not the user — needs Contributor on the Fabric workspace

Relevant when the lakehouse is reached as a **knowledge source** rather than as a tool. Added in
Fabric via *Manage access* → *Add people or groups*, searching for the **search service name**.
Detail owned by `foundry-knowledge-agent`; recorded here because the two Fabric paths get
confused with each other.

### 8. Both Fabric integrations can be attached to the same agent, silently

Nothing warns you, and the response carries no marker of which path produced it.

---

## Doc-sourced — not verified in a tenant

| Trap | Source | Note |
|---|---|---|
| Fabric tool and Fabric IQ are both **preview** | `azure/foundry/agents/how-to/tools/fabric`, `…/fabric-iq` | re-check before every engagement |
| Fabric IQ supports **background mode** for long-running data agent work | `…/tools/fabric-iq` | never exercised here |
| Identity passthrough semantics across the Foundry → Fabric hop | product docs | the lab used a single lab identity throughout, so nothing was proven about delegation |
| Fabric data agents are a Fabric-side artifact with their own lifecycle | `fabric/data-science/data-agent-foundry` | consistent with what was observed |

---

## Evidence discipline

A screenshot, or a lab step, is a **point in time** — not a state of the world. Item 2 above is
an entry in this brain's correction log: a confident conclusion drawn from docs alone that
working code later overturned.

If you cannot establish that an artifact was complete when it was captured, the mismatch is an
**open question**, not a finding.

---

## Open questions

- Does the Foundry → Fabric hop carry the **end user's** identity, or the project's? Nothing in
  the lab distinguished them — one identity was used throughout.
- Can the project connection be created **without** the portal (CLI, Bicep, SDK)? Only the portal
  path was observed.
  - *Partially addressed 2026-08* — see the correction under item 4. The **inputs** need no portal
    when you deployed the Fabric side yourself. The ARM request body remains unknown, so the
    question stays open on its second half: which `category` does a Fabric data agent connection
    take?
- `project_connections` is a list — what happens when a tool fronts several Fabric data agents?
  How does the model choose between them?
- Is there a background/async mode reachable from `MicrosoftFabricPreviewTool`, matching what the
  Fabric IQ docs describe?
- What does the Fabric side see in its own audit log when a Foundry agent calls it?

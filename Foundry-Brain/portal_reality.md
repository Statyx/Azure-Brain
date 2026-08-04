# portal_reality.md — what the tenant actually shows

Documentation says what *should* exist. This file says what **was observed**. When the two
disagree, this file wins for behaviour, and the disagreement gets logged here.

**Method:** portal screenshots from a **hands-on training lab** (Skillable-hosted, seeded
content), reviewed with the operator as they worked through it. No CLI, no API calls, no tenant
credentials available to the agent.
**Observation date:** 2026-08-04.
**Scope:** one lab tenant, one region, pre-seeded artifacts. Treat as *evidence about how the
product behaves*, not as a description of any real environment — and not as proof that a
capability is absent elsewhere.

> Real resource names, GUIDs and endpoints live in `resource_ids.md` (gitignored).
> This file records **behaviour only**, with placeholders.

---

## Generation confirmed

- The **New Foundry** toggle is **ON** in the portal.
- Portal URL is served from `ai.azure.com/nextgen/...`.
- ⇒ The tenant is on the **current generation**. Classic guidance
  (`azure/foundry-classic/*`) does not apply here. See [`generation_map.md`](generation_map.md).

---

## ✅ RESOLVED — the project-endpoint hostname

`generation_map.md` and `orchestration_patterns.md` both carried an unresolved contradiction:
Microsoft docs write the project endpoint two different ways.

| Source | Form |
| --- | --- |
| A2A doc (`enable-agent-to-agent-endpoint`) | `https://{account}.services.ai.azure.com/api/projects/{project}` |
| Fabric-tool Python sample comment | `https://{resource}.ai.azure.com/api/projects/{project}` |
| **Portal — "Project endpoint" field, observed** | **`https://{resource}.services.ai.azure.com/a…`** |

**Resolution: the portal shows `services.ai.azure.com`.** The `ai.azure.com` form that appears in
some SDK code comments looks stale. Use `services.ai.azure.com` and always copy the value from
the portal's **Project endpoint** field rather than assembling it by hand.

A separate **Azure OpenAI endpoint** (`{resource}.openai.azure.com/...`) is shown alongside it.
These are two different endpoints for two different SDKs — do not substitute one for the other.

Status: **observed on one tenant**, 2026-08-04. Not proven globally, but it outranks a code
comment.

---

## Foundry portal — observed

| Observation | Detail |
| --- | --- |
| Top-level nav | Home · Discover · Build · Operate · Docs |
| Two entry paths offered on Home | **Build an agent** (no-code: instructions, tools, knowledge) and **Code an agent** (Microsoft Agent Framework, "full control") |
| Credentials surfaced on Home | API key · Project endpoint · Azure OpenAI endpoint |
| Model catalog visible | Includes Anthropic, OpenAI, Microsoft and DeepSeek families |
| Model **deployments** in the lab project | one at first load; a newer model was selectable in the playground afterwards |

### Left navigation taxonomy (Build)

```text
Create                Optimize
  Agents                Evaluations
  Models                Fine-tune
  Services
  Tools
  Knowledge
  Guardrails
  Memory
  Data
```

`Tools`, `Knowledge`, `Guardrails` and `Memory` are **first-class siblings of Agents**, not
sub-pages of an agent. That matches the platform intent: tools and guardrails are shared,
governed assets that agents *reference* — which is the same argument as the toolbox.

### The Agents page has three tabs

`Agents` · `Routines` *(Preview)* · `Workflows` *(Preview)*

### Creating an agent

`New agent ▾` opens three options:

| Option | Meaning |
| --- | --- |
| **Build an agent** | no-code, portal-authored |
| **Code an agent** | Agent Framework / SDK, "Host it on Foundry" |
| **Link external agent** | ⚠️ see below — likely the inbound path for an agent that lives elsewhere |

The **Create an agent** dialog asks for **one field only: Agent name**, described as
*"This name serves as its identifier in the API."*

✅ **This confirms the SDK contract.** `project.agents.create_version(agent_name=…)` and
`agent_reference: {name: …}` both key off this exact string — not a GUID. Name the agent as an
API identifier from the start; renaming later breaks every caller.

The model is **not** chosen at creation. It is selected afterwards in the playground, along with
the instructions. So an agent exists before it has a model — creation and configuration are two
distinct steps.

---

## ⚠️ Two portal features with NO documentation found

Searched Microsoft Learn on 2026-08-04 for both. **Zero results.** The portal is ahead of the
docs here, so nothing about them may be asserted — only observed.

### `Routines` (Preview)

A tab beside `Agents` and `Workflows`. Purpose unknown. Do **not** guess at it in any
instruction file. Capture a screenshot of the tab's contents before assuming it is or isn't
relevant to orchestration.

### `Link external agent`

A third option in the `New agent` menu. Given that the current generation replaced Connected
Agents with A2A, this is the most likely portal surface for registering an **externally hosted
A2A agent** as a callable participant — but that is **inference, not fact**.

If it does what the name suggests, it partially contradicts a documented statement recorded in
[`agents/foundry-orchestration-agent/instructions.md`](agents/foundry-orchestration-agent/instructions.md):
that enabling A2A *"isn't available in the Foundry portal yet"*. Note the asymmetry — the
documented gap is about **exposing** an agent (incoming A2A). `Link external agent` sounds like
**consuming** one (outgoing). Those are different directions and both need confirming.

**Next screenshot needed:** open `Link external agent` and capture every field.

---

## Tool catalog — observed

`Select a tool` has three tabs: **Configured** · **Catalog** · **Custom**.

- **Configured** = *"ready to use with your existing authentication and configuration"* — tools
  already wired in this project.
- **Catalog** / **Custom** not yet captured. `Agent2Agent (A2A)`, `MCP`, `OpenAPI`, `Toolbox`
  and `Azure Functions` do **not** appear under Configured, which is consistent with the
  documented route *Tools → Connect tool → **Custom** tab → Agent2Agent (A2A)*.

### Configured tab contents

| Tool | State |
| --- | --- |
| File search | available |
| Code interpreter | ⚠️ **disabled — model-gated** (see below) |
| Azure AI search | available |
| Grounding with Bing Search | available |
| Web search | available |
| Computer Use | disabled · Preview |
| **Work IQ** | available · Preview — *"Connect to your Microsoft 365 Copilot data and to query your emails, meeting…"* |
| **Fabric IQ (OneLake Catalog)** | available · Preview — *"Select OneLake items to ground your agent in the state of your business…"* |
| Grounding with Bing Custom Search | available · Preview |
| **Fabric Data Agent** | available · Preview — *"Integrate your agent with the Fabric Data Agent to unlock powerful data analysis…"* |
| SharePoint | available · Preview |

### ✅ Confirmed: two distinct Fabric tools, side by side

`Fabric Data Agent` and `Fabric IQ (OneLake Catalog)` are **separate entries in the picker**.
This confirms from the product surface what the docs describe as two SDK classes:

| Portal entry | SDK class | Toolbox | Background mode |
| --- | --- | --- | --- |
| **Fabric Data Agent** | `MicrosoftFabricPreviewTool` + `FabricDataAgentToolParameters` | ❌ direct only | ❌ |
| **Fabric IQ (OneLake Catalog)** | `FabricIQPreviewTool` | ✅ yes | ✅ yes (data-agent MCP endpoint only) |

Both can reach the *same* published Fabric data agent. They are different transports, not
different data. Choose on capability, not on name.

### 🔑 Binding is by **catalog discovery**, not by GUID

> ⚠️ **Corrected 2026-08-04 by Lab 2.** The table at the end of this section framed the GUID path
> and the browse path as *competing styles*. That reading was wrong for the **Fabric Data Agent**
> tool: there, portal and code are **sequential** — the portal takes the GUIDs and produces a
> **named connection**, and the SDK resolves that connection **by name**, never by GUID. See
> [Lab 2 — Foundry IQ](#-portal-and-sdk-fabric-binding-are-sequential-not-alternatives).
> What remains true below is that **Fabric IQ (OneLake Catalog)** binds by browsing.

Selecting **Fabric IQ (OneLake Catalog)** opens a **OneLake Catalog** browser:

> *"Connect to Microsoft Fabric item to access unified, governed data across your organization."*

| Column | Observed |
| --- | --- |
| Name | Fabric item name |
| Location | owning workspace |
| **Endorsement** | `Promoted` badge on several items; blank on others |
| **Sensitivity** | present as a column |

Filters: `All` · `Endorsed in your org` · `Favorites` · keyword · a `Filter` dropdown.
A **Fabric data agent item was selectable directly in this list**, alongside semantic-model
items — the catalog mixes item types, matching the three Fabric IQ endpoint shapes (data agent,
ontology, Power BI semantic model).

**This materially contradicts the documented setup path.** The docs say to open the data agent in
Fabric, copy `workspace_id` and `artifact_id` out of the URL, and hand-build a `Microsoft Fabric`
connection. The portal instead lets you **browse and pick the item**, constructing the endpoint
for you.

⇒ Both paths exist and target the same thing:

| Path | How the target is identified | When to use |
| --- | --- | --- |
| **Fabric Data Agent** tool | manual `workspace_id` + `artifact_id` from the Fabric URL | scripted / IaC, and when you need the direct tool |
| **Fabric IQ (OneLake Catalog)** tool | browse the catalog, select the item | portal-authored; the only path that is toolbox- and background-mode-capable |

**Governance observation worth keeping:** endorsement and sensitivity are shown **at the moment
of binding**. The person grounding an agent sees whether the underlying Fabric item is
`Promoted`/`Certified` and how it is labelled, *before* committing. That is a real
governance-by-design story and belongs in `foundry-fabric-bridge-agent`.

⚠️ The observed data agent item carried **no endorsement and no sensitivity label** — normal for
a lab-seeded item, and a good illustration of what "ungoverned source" looks like in this list.

### ⚠️ NEW CONSTRAINT: tool availability depends on the selected model

`Code interpreter` was greyed out with the message:

> *"This tool doesn't work with the model you selected. Please use another model."*

This is a dependency that appears in **no** documentation reviewed so far, and it inverts the
usual build order. You cannot pick tools and then pick a model — **the model constrains the
tool set**.

Consequence for any agent instruction file: model selection must be treated as an
*architectural* decision made **before** tool design, not as a tuning knob applied afterwards.

### ⚠️ Compliance notice shown in the picker

> *"When you connect to a non-Foundry tool, your customer data may be sent outside the Azure
> compliance boundary and processed according to the applicable terms and data handling
> policies."*

Worth surfacing in a governance agent: attaching a third-party MCP/custom tool is a data-boundary
decision, and the portal says so at the point of choice.

---

### ✅ Work IQ is a **family of per-capability tools**, not one connector

Observed attached to agents in the lab, each as its own entry with its own icon, all `Preview`:

| Tool | Backing | Seen on |
|---|---|---|
| `Work IQ User` | Microsoft Graph — people, manager chain, direct reports, peers | `Hierarchy-Agent` |
| `Work IQ Mail` | Outlook | `Communication-Agent` |
| `Work IQ Calendar` | Outlook calendar | `Communication-Agent` |
| `Work IQ Teams` | Teams chats, channels, presence | `Communication-Agent` |
| `Work IQ OneDrive` | OneDrive files | `SOP-Agent` |
| `Work IQ Word` | .docx read/append | `SOP-Agent` |

Consequences for agent design:

- **Least privilege is expressible.** An agent that only needs the org chart gets `Work IQ User`
  and nothing else — it cannot send mail even if its prompt is manipulated into trying.
- Attaching "Work IQ" is never a single decision; it is one decision **per capability**.
- The split maps cleanly onto the role split: resolver gets `User`, communication agent gets
  `Mail`/`Calendar`/`Teams`, document agent gets `OneDrive`/`Word`.
- All are Preview → surface area and names can still change.

**Attachment observed per agent** — the least-privilege split is real, not theoretical:

```
Hierarchy-Agent       →  Work IQ User
Communication-Agent   →  Work IQ Mail · Calendar · Teams
SOP-Agent             →  Work IQ Word · OneDrive
```

Three agents, six capabilities, zero overlap. No agent holds a tool outside its role.

### The playground ships a built-in connectivity check

The chat pane offers a starter prompt: **"Confirm the connectivity for all tools in this
agent"** — seen on more than one agent, so it is portal-provided, not user-typed.

That is a **smoke test for tool wiring**, before any business prompt is written. It is the
cheapest possible answer to the drift problem: it exercises each attached tool and reports back,
which is exactly what distinguishes "the prompt claims a tool" from "the tool actually answers".

**Adopt as a step:** after attaching tools and before writing instructions, run the connectivity
check. Any agent whose tools don't respond is not worth debugging at the prompt level.

---

### ✅ Versions accumulate — fast

Agent list from a reference build of the same system:

| Agent | Version |
|---|---|
| `Hierarchy-Agent` | 20 |
| `Communication-Agent` | 46 |
| `Work-IQ-Orchestrator-Agent` | **102** |

Every `Save` mints a version. The **router** has by far the highest count — routers are the most
iterated component in a multi-agent system, because routing accuracy is tuned by rewording.

Also observed: `Save` is **greyed out** when there are no pending edits, while `Publish` stays
active. So the two are genuinely independent states — you can publish a version you saved
earlier without touching the editor.

Implications:
- Version number carries no semantic meaning to a human. Don't reference agents by version.
- `Publish` selects the served version; `Save` only records one.
- Any SDK automation should call `delete_version(...)` — the samples do this explicitly, with
  the comment *"so unused versions don't accumulate"*.

---

### ⚠️ The lab manual's own screenshots are already stale

The lab handout shows a left navigation of flat items (`Agents · Models · Fine-tune · Tools ·
Knowledge · Data · Evaluations · Guardrails`) and an Agents page with two tabs
(`Agents · Workflows`). The **live portal** in the same environment shows the nav grouped under
`Create` / `Optimize`, and **three** tabs (`Agents · Routines · Workflows`).

Neither is wrong — they are different points in time, weeks apart at most.

**Generalizable:** the Foundry portal changes faster than the material written against it. Any
instruction in this brain that describes *where a button is* has a short half-life. Describe
**what a thing does and what it is called**; avoid step-by-step click paths, and never let a
click path be the only way an instruction expresses a step.

---



### Agent list columns

`Name` · `Version` · `Status` · `Type` · `Last updated` · `Description`

Observed row: a `Prompt` type agent, version `1`, status **`Running`**.

✅ Confirms **Type = `Prompt`**, matching `PromptAgentDefinition` in the SDK, and that the
Prompt/Hosted distinction is a first-class property visible in the UI. An agent also carries a
**lifecycle status**, not just a definition.

### Agent detail tabs

`Playground` · `Details` · `Traces` · `Monitor` · `Evaluation` · `Optimize` *(Preview)*

Tracing, monitoring and evaluation are built into the agent object — they are not a separate
Application Insights journey. `Traces`/`Monitor` map onto `foundry-observability-agent`;
`Evaluation` maps onto `foundry-governance-agent`, and independently confirms that evaluation is
**agent-scoped by design**, not merely by the wizard's default.

### Playground configuration pane

Sections, in order: **Model** · **Voice mode** (toggle) · **Instructions** · **Tools** ·
**Knowledge** · **Memory** *(Preview)* · **Guardrail** *(Preview)*.

Header carries `Version: N`, a **`Save`** button and a **separate `Publish ▾`**.

⚠️ **Save ≠ Publish for Foundry agents either.** The same draft/published duality as Fabric data
agents. Two independent publish gates now exist in the chain — the Fabric data agent's, and the
Foundry agent's. A change can be saved at both ends and live at neither.

The Tools section describes itself as: *"Build a unified endpoint for invoking tools **and
agents**, leverage tool search to save input tokens"* with a link to toolbox docs.

⇒ In the portal, the Tools section **is** the toolbox surface, and it explicitly covers *agents*
as well as tools. That is the portal's answer to "how do I attach a sub-agent".

Right-hand pane offers `Chat` · **`YAML`** · **`Call agent`**.

⚠️ **`YAML` is significant.** The agent definition is expressible as a declarative document.
That is the config-driven, idempotent artifact `agent_principles.md` demands — an agent could be
version-controlled and diffed rather than clicked. **Capture this tab.** It may be the single
most useful thing in the portal for this brain.

### Model deployment

Model shown as `gpt-5.5`, labelled **`Global Standard deployment`** — deployment *type* is
surfaced next to the model name, so it is part of the agent's effective configuration.

The Fabric side of the bridge, seen in the Fabric portal (`app.fabric.microsoft.com`).

| Observation | Detail | Why it matters |
| --- | --- | --- |
| URL shape | `.../groups/{workspaceId}/aiskills/{artifactId}` | Matches the documented way to obtain both GUIDs for the Foundry connection. The legacy `aiskills` segment is still in the path. |
| Item state | Shows a **`Draft`** badge **and** a `Revert to published version` command | A data agent has a **draft** and a **published** version simultaneously |
| Toolbar | `Add data` · `Add tools` · `Build agent with AI` · `Test data agent` · `Agent instructions` · `Runtime [Standard ▾]` · `Publish` | A data agent can itself hold tools — the bridge is agent→agent→tools |
| **Runtime selector** | `Standard` selected; banner advertises a **Preview runtime** with *"improved data source routing and stronger support for large schemas"* | Runtime choice changes NL2SQL behaviour. Record which one is active. |
| Instruction size limit | Character counter reads `…/15000` | **15,000 character cap** on agent instructions |
| Explorer tabs | Data · Setup · Tools | |
| Data binding | A lakehouse → `Schemas` → `dbo` → `Tables`, each table individually check-boxed | Table selection is explicit and per-table |

### ⚠️ Finding: published ≠ what you are editing

Foundry connects to the **published endpoint** of a data agent. The portal shows a draft and a
published version living side by side. Editing instructions in Fabric and *not* pressing
**Publish** leaves Foundry calling the old behaviour, with **no error anywhere** — the call
succeeds and returns stale reasoning.

This is a silent-failure class. It belongs in every pre-demo checklist.

### ⚠️ Finding: instructions can name tables that aren't bound

In the observed agent, the instruction text referenced data sources that did **not** appear in
the checked table list, and referenced others under a different name (singular vs plural, and a
business synonym vs the physical table). Fabric does **not** validate instruction text against
the bound schema.

Consequence: the agent is told to use a source it cannot see. Failure mode is not an error — it
is a plausible-looking answer built from the wrong table, or a refusal. Both are worse than a
crash during a demo.

**Rule derived:** before any demo, diff the table names in the instructions against the checked
tables in the Data tab, in both directions.

---

## Lab 2 — Foundry IQ (Zava retail), observed 2026-08-04

A second Microsoft training lab, different domain, different author. Full write-up:
[`reference_foundry_iq.md`](reference_foundry_iq.md). Raw source:
[`labs/foundry-iq/raw_capture.md`](labs/foundry-iq/raw_capture.md).

### 🔑 Foundry IQ knowledge bases are consumed by agents as an **MCP tool**

This is the biggest single finding of the second lab, and it is not obvious from the portal.

The project's **Connected resources** page surfaces three values — `server_label`, `server_url`,
`project_connection_id` — which feed directly into:

```python
MCPTool(server_label=…, server_url=…, project_connection_id=…, require_approval="never")
```

The portal's **Knowledge → Add → Connect to Foundry IQ** button and that code are **the same
thing**. The no-code path is a wrapper over an MCP tool registration.

**Consequence:** retrieval obeys **tool** semantics, not some special grounding pathway —
approval gates, invocation ordering, and per-call limits all apply. Anyone reasoning about
grounding as "the model just knows the documents" will mispredict behaviour.

### 🔑 Portal and SDK Fabric binding are **sequential**, not alternatives

This **overturns the earlier reading** recorded above under *"Binding is by catalog discovery"*,
which framed the GUID path and the browse path as competing styles. They are two halves of one
flow:

1. **Portal** — `Connect a tool` → *Fabric Data Agent* → paste **Workspace ID** and **Artifact
   ID** scraped from the Fabric URL. Result: a **named project connection** (lab: `fabriciq_dataagent`).
2. **Code** — resolve it **by name**:

```python
fabric_connection = project_client.connections.get(fabric_connection_name)
MicrosoftFabricPreviewTool(
    fabric_dataagent_preview=FabricDataAgentToolParameters(
        project_connections=[ToolProjectConnection(project_connection_id=fabric_connection.id)]
    )
)
```

⇒ **No Fabric GUID ever appears in the code.** The connection *name* lives in `parameters.env`.
Environment promotion is therefore a **connection swap**, not a code change. That is the
portability property worth teaching.

> URL scraping rule, as stated by the lab: workspace ID is between `groups/` and `/aiskills`;
> artifact ID is between `aiskills/` and `?` — excluding the `?`.

### Foundry IQ object model

```
Azure AI Search resource        (auth: API Key, in this lab)
  └── Knowledge base            (name + a chat model — gpt-5.4-mini here)
        ├── knowledge source    Azure Blob Storage        → INDEXED  (a copy is embedded)
        ├── knowledge source    Azure AI Search index     → INDEXED  (existing index reused)
        └── knowledge source    Fabric IQ / OneLake       → FEDERATED (no data movement)
```

Blob sources additionally require a storage account, a container, an **extraction mode**
(`Minimal` observed) and an **embedding model** (`text-embedding-ada-002` observed).

**Source creation is asynchronous**, with a `Creating` state and **no completion event** — the
portal must be refreshed until every source reads `Active`.

### ⚠️ Cross-service RBAC: the AI Search service needs Contributor on the Fabric workspace

To let a Fabric IQ knowledge source read OneLake, the **Azure AI Search service identity** is
added in Fabric (*Manage access → Add people or groups*, searched by the service's name) as
**Contributor**.

**Silent failure modes if skipped:** the source stays at `Creating`, or the agent answers from
nothing and looks like it is hallucinating. No error names the missing permission.

### ⚠️ Fabric appears twice in Foundry and the two are easy to confuse

| Surface | What it is | Semantics |
| --- | --- | --- |
| **Fabric IQ (OneLake Catalog)** | a *knowledge source* inside a knowledge base | federated **retrieval** |
| **Fabric Data Agent** | a *tool* attached to an agent | a delegated **question**, answered by another agent |

Both can be attached to the same agent, and **nothing in the response says which one answered**.
Decide deliberately; record the decision.

### Agents were created by script, and versions are the unit of release

`project_client.agents.create_version(agent_name=…, definition=PromptAgentDefinition(...))`.
Re-running the script is a release, not an update. Confirms the version-accumulation finding
above from a completely independent source.

### Governance panes, finally seen

| Pane | Observed configuration |
| --- | --- |
| **Guardrails** | risk types `Jailbreak` + `Protected Materials`; content harms `Hate`, `Sexual`, `Self-harm`, `Violence`; applied to a **selected set of agents** in one object |
| **Evaluations** | target = an **agent**; scope = *Individual turns*; data can be **Generated** (N rows); then criteria → submit; results shown as *Evaluation runs* + *Evaluators* |
| **Traces** | requires **Application Insights** connected (can be created inline); unit of inspection = **Conversation ID**; shows agent and tool calls with input, output, metadata |

Guardrails being an object applied *across* agents — rather than a per-agent setting — is the
detail worth carrying: it is the one governance control that does not scale with agent count.

### ⚠️ Anti-pattern shipped by the lab itself

`Inventory-Agent` is instructed *"The response must come only from the Fabric Data Agent tool
output"* — and then given a hardcoded list of ten product IDs "at risk of stockout".

A grounded agent with hardcoded facts is **worse** than an ungrounded one, because the answer
looks sourced. Recorded here because it is the kind of shortcut that gets copied out of a lab
into a customer deployment.

---

## Generalizable lessons

Not a checklist for any particular environment — these are product behaviours worth carrying
forward into the agent instructions.

| # | Behaviour | Why it generalizes |
| --- | --- | --- |
| 1 | Fabric does **not** validate data-agent instruction text against the bound table set | The two are edited in different panes with no cross-check. Naming an unbound source produces a wrong answer, not an error. |
| 2 | A data agent has a **draft** and a **published** version at once; Foundry consumes the published one | Editing without publishing changes nothing downstream, silently. |
| 3 | The Fabric data agent **runtime** is selectable (`Standard` vs a preview runtime advertising better data-source routing for large schemas) | Runtime choice changes NL2SQL behaviour, so it must be recorded, not left implicit. |
| 4 | Background mode for long-running data-agent queries depends on the **model** supporting it | Model choice is not only about answer quality; it gates a capability. |
| 5 | An agent's **name is its API identifier** | Renaming breaks every caller. Choose it as an identifier, not a label. |
| 6 | Agent creation and agent configuration are **separate steps** | An agent can exist with no model and no instructions. Any automation must handle that intermediate state. |
| 7 | **Model choice gates tool availability** (`Code interpreter` disabled: *"doesn't work with the model you selected"*) | Inverts the natural build order — the model is an architectural decision made *before* tool design, not a tuning knob after it. |
| 8 | **Work IQ is per-capability**, not one connector (`User`, `Mail`, `Calendar`, `Teams`, `OneDrive`, `Word`) | Least privilege is expressible at the tool level. An agent that only needs the org chart cannot be talked into sending mail. |
| 9 | Every `Save` mints a **version**; routers reach three digits fast (102 observed) | Version numbers are not human-meaningful identifiers, and automation must clean up after itself. `Save` and `Publish` are independent states. |
| 10 | The portal changes faster than the material written against it — the lab's own screenshots already disagree with the live UI | Instructions that describe *where a button is* have a short half-life. Describe what a thing is called and does; never let a click path be the only expression of a step. |
| 11 | Fabric IQ binds by **browsing the OneLake catalog**, not by pasting `workspace_id` / `artifact_id` | Discovery is governed (Endorsement + Sensitivity are shown at bind time), and the docs' GUID-based path is the SDK path, not the portal one. |
| 12 | A **knowledge base is reached as an MCP tool** (`server_label` / `server_url` / `project_connection_id`) | Grounding is not a privileged pathway. It obeys tool semantics — approval, ordering, limits — so it fails in tool-shaped ways. |
| 13 | Fabric binding is **portal-then-code**: the portal makes a *named connection*, the SDK resolves it **by name** | No GUID ever enters the code. Environment promotion becomes a connection swap. This is the single property that makes an agent script portable. |
| 14 | Knowledge sources are **indexed** (a copy is embedded) or **federated** (no data movement), in the same knowledge base | Data residency is decided per source, not per system. It is the answer a CISO actually asks for. |
| 15 | Grounding can require **cross-service RBAC** — the AI Search identity needs rights on the *Fabric* workspace | The failure is silent and looks like hallucination. Permission checks must span services, not just the one you are configuring. |
| 16 | **Guardrails are an object applied across a set of agents**; evaluations target one agent at a time | Safety scales with the fleet; quality does not. Budget evaluation effort per agent. |
| 17 | Asynchronous creation with a `Creating` state and **no completion event** (knowledge sources) | Any automation must poll. Any runbook must say "refresh until Active", or the next step fails for a reason nobody will connect back. |

---

## Evidence discipline — a lesson learned the hard way

Two findings were recorded in `orchestration_patterns.md` as **defects** and both were wrong:
an agent declared missing that existed, and a prompt/tool mismatch that was simply the build
mid-step. Both were corrected in place and the corrections left visible.

Root cause in both cases: **a screenshot is a point in time, not a state of the world.** An
unfinished build looks exactly like a broken one.

**Rule now applied to this file:** before recording a mismatch as a finding, establish that the
artifact was *complete* when captured. If that can't be established, it goes in
[Still unknown](#still-unknown--needs-the-next-screenshots) as a question — never in a table of
facts. Umbrella rule 9, applied to visual evidence.

---

## Still unknown — needs the next screenshots

- [ ] The **`YAML` tab** of an agent — likely the single most useful artifact for a config-driven
      brain: it should show the full agent definition (model, tools, instructions) as one document
- [ ] The **`Call agent` tab** — the invocation contract the portal advertises
- [x] ~~How the **dispatcher** is actually implemented~~ — **resolved**: it is a **Workflow**,
      written in YAML, doing `ConditionGroup` string equality on the router's text. Confirmed
      independently in two labs. See [`orchestration_patterns.md`](orchestration_patterns.md).
- [x] ~~`Memory` (Preview) and `Guardrail` (Preview) panes~~ — **Guardrails partially resolved**
      (risk types, content harms, applied across a selected set of agents). `Memory` still unseen.
- [ ] `Routines` (Preview) — undocumented on Learn
- [ ] `Link external agent` — undocumented on Learn
- [ ] The `Catalog` and `Custom` tabs of the tool picker
- [ ] Whether **toolboxes** exist in this region — neither lab used or displayed one
- [ ] The **connection creation** screen: does a `Microsoft Fabric` connection type appear?
- [ ] Region of the Foundry resource
- [ ] Which RBAC role names the portal displays (`Foundry User` vs the pre-rename `Azure AI User`)
- [ ] Whether the portal exposes **background mode** in the playground
- [ ] Legal values of `require_approval` beyond `"never"`
- [ ] Whether tool approvals can be answered **programmatically** — `agents.py` imports
      `McpApprovalResponse` and `ResponseInputParam` and never uses them (a lead, not a capability)

---

## Change log

| Date | Change |
| --- | --- |
| 2026-08-04 | File created from the first two tenant screenshots. Resolved the project-endpoint hostname contradiction. Logged the draft/published silent-failure and the instruction/schema drift findings. |
| 2026-08-04 | Added the portal taxonomy, tool catalog, model-gates-tools constraint, catalog-discovery binding, and the agent object model. Reframed as a **training lab** observation (not a demo build) at the user's clarification. |
| 2026-08-04 | Added the Work IQ tool family, version accumulation, and the stale-lab-screenshots lesson. Extended Generalizable lessons to 11 rows. Added **Evidence discipline** after two findings were over-called and corrected. |
| 2026-08-04 | Added **Lab 2 — Foundry IQ**: knowledge bases consumed as MCP tools, the portal-then-code Fabric binding (⚠️ *corrects* the earlier "competing paths" reading), the Foundry IQ object model, cross-service RBAC, the two Fabric surfaces, and the governance panes. Lessons extended to 17 rows; dispatcher and Guardrails questions closed. |

# Foundry IQ lab — raw capture

> **⚠ RAW, NOT CURATED.** This file is a verbatim transcription of a Microsoft training lab,
> captured block by block as it was received. Nothing here has been verified, generalised or
> reconciled with the rest of the brain.
>
> **Do not read this file to learn how Foundry IQ works.** Read the distilled agent instructions
> instead. This file exists so the distillation pass has a source to point back to, and so a
> later correction can be traced to what was actually observed.

**Capture opened:** 2026-08-04
**Source:** Microsoft training lab on Foundry IQ (distinct from the Work IQ / Agent Service lab
captured the same day — see `Foundry-Brain/portal_reality.md`).
**Status:** 🟠 capture in progress — distillation not started.

---

## Rules applied during capture

| Rule | Why |
|---|---|
| Verbatim, no reformatting, no summarising | The "obvious" steps are where product behaviour hides |
| No analysis while capturing | Mid-flow inference produced two over-called findings earlier today (see `Foundry-Brain/orchestration_patterns.md` → *Correction log*) |
| Lab's own ordering preserved | Prerequisites stay visible in sequence |
| Credentials / tokens / tenant URLs stripped before recording | A lab screenshot exposed an account + TAP in clear text earlier today |
| Screenshots only where the UI *is* the information | Text already in the manual adds nothing as an image |

---

## Distillation ledger

Filled in **after** the capture is complete. Every claim that leaves this file must land in a row
here, so that "where did this come from" is always answerable.

Status: **capture closed** at 20 blocks · distillation completed 2026-08-04.

| Claim | Evidence class | Landed in |
|---|---|---|
| A Foundry IQ knowledge base is consumed by an agent as an **MCP tool** (`server_label` / `server_url` / `project_connection_id`) | **observed** (Connected resources page) + **lab-text** (`agents.py`) | `foundry-knowledge-agent/instructions.md` · `portal_reality.md` |
| Fabric binding is **portal-then-code**: portal makes a *named connection*, SDK resolves it by name — no GUID in code | **lab-text** (`agents.py` + Task 4.2/4.3) | `foundry-fabric-bridge-agent/instructions.md` · `portal_reality.md` (as a **correction**) |
| Workspace ID / Artifact ID are scraped from the Fabric data-agent URL (`groups/…/aiskills/…?`) | **lab-text** | `foundry-fabric-bridge-agent/instructions.md` |
| `allow_preview=True` is required for `AIProjectClient` to expose preview tools | **lab-text** (`agents.py`) | `generation_map.md` · `foundry-tools-agent/known_issues.md` |
| SDK shapes: `azure-ai-projects>=2.0.0`, `create_version`, `PromptAgentDefinition`, `connections.get` | **lab-text** (working script) | `generation_map.md` (rows marked ✅ tenant-verified) |
| Tool approval **cannot** be granted inside a workflow preview; run agents alone first | **lab-text** (explicit Microsoft note) | `foundry-tools-agent/*` · `foundry-orchestration-agent/known_issues.md` |
| Router output is a **type contract** consumed by string equality in the workflow YAML | **lab-text** (router prompt + workflow YAML), confirmed independently vs lab 1 | `orchestration_patterns.md` · `foundry-orchestration-agent/known_issues.md` |
| `autoSend: true` everywhere = "narrate every hop"; the opposite strategy to lab 1 | **lab-text** (workflow YAML) | `orchestration_patterns.md` § Second specimen · `reference_foundry_iq.md` |
| `elseActions: SendActivity " "` — silent fallback on routing failure | **lab-text** | `orchestration_patterns.md` · `reference_foundry_iq.md` |
| Knowledge sources are **indexed** (Blob, AI Search index) or **federated** (Fabric IQ / OneLake) | **lab-text** (Exercise 3) | `foundry-knowledge-agent/instructions.md` |
| The **AI Search service** needs **Contributor on the Fabric workspace**; failure is silent | **lab-text** (Task 1.7) | `foundry-knowledge-agent/*` |
| Knowledge-source creation is **async** with a `Creating` state and no completion event | **lab-text** ("refresh the browser page") | `foundry-knowledge-agent/instructions.md` |
| Guardrails = one object (risk types + content harms) applied across a **selected set of agents** | **lab-text** (Task 6.1) | `portal_reality.md` + `foundry-governance-agent` (layer 4 of the control model) |
| Evaluations target **one agent**, scope *Individual turns*, data can be **Generated** | **lab-text** (Task 6.2) | `portal_reality.md` + `foundry-governance-agent` (the multi-agent evaluation gap) |
| Traces require App Insights; unit of inspection = **Conversation ID** | **lab-text** (Task 5.2) | `portal_reality.md` — `foundry-observability-agent` planned |
| Project endpoint hostname is `<resource>.services.ai.azure.com` | **observed** (portal, lab 1) — reconfirmed here | `generation_map.md` · `resource_ids.example.md` |
| ⚠️ Anti-pattern: a "tool output only" agent with hardcoded product IDs in its prompt | **lab-text** (`Inventory-Agent` instructions) | `foundry-fabric-bridge-agent/known_issues.md` · `reference_foundry_iq.md` · `portal_reality.md` |
| Business semantics (`Revenue`, `Return Rate`…) are **inherited** from the Fabric data agent | **lab-text** (Task 1.5) | `foundry-fabric-bridge-agent/instructions.md` |
| Fabric appears twice in Foundry — knowledge source vs tool — with no marker in the response | **inferred** from the two surfaces both being present; not directly demonstrated | `portal_reality.md` · `foundry-fabric-bridge-agent/instructions.md` (flagged as a design risk, not a defect) |
| 🔎 Approvals may be answerable programmatically (`McpApprovalResponse` imported, unused) | **inferred** (an unused import) | `foundry-tools-agent/known_issues.md` — recorded as a **lead**, explicitly not a capability |

Evidence classes: **doc** (Microsoft Learn) · **lab-text** (the manual's own instructions) ·
**observed** (a screenshot of the live portal) · **inferred** (neither — must be flagged as such).

**Not distilled** (captured but with no owning agent yet): Exercise 2 provisioning steps, model
deployment flow, Task 1.1–1.4 (never supplied). These belong to `foundry-project-agent` and
`foundry-model-catalog-agent`, both still `planned`.

---

## Capture

<!-- Blocks are appended below in the order received. Each block keeps the lab's own headings. -->

### Block 01 — Overview

> Referenced image, not supplied as text: `FIQArchi.png` (architecture diagram).

```text
Overview
FIQArchi.png

Lab Overview:
This lab demonstrates how Foundry IQ enables a single, end-to-end intelligence layer that transforms enterprise signals into trusted, business-aware AI actions. Using the Zava Retail scenario, participants experience how an organization evolves from fragmented understanding and delayed decision-making into a Frontier Organization-one that is human-led and AI-operated.

Zava operates hundreds of physical retail stores alongside a rapidly growing e-commerce platform. While data exists across the business, leadership continues to face fundamental intelligence challenges:

Business knowledge is scattered across systems and documents
Insights arrive too late to drive real-time decisions
AI systems lack shared business meaning and guardrails
No consistent business language to guide AI agents during critical moments such as Holiday Sales
To address this, Zava adopts Foundry IQ as the intelligence foundation that connects business context, enterprise knowledge, and AI execution.

Personas in the Scenario
The Foundry IQ story is experienced through key enterprise personas:

April - CEO
Focused on revenue, growth, and customer experience.

Rupesh - Chief Data Officer
Responsible for business definitions, governance, and trust.

Miguel - AI Engineer / Data Scientist
Designs intelligent, governed AI agents.

Ryan - End Customer
Experiences the outcomes of AI-driven decisions.

Foundry IQ: From Business Intelligence to Intelligent Action
Foundry IQ provides the business-aware intelligence layer that AI agents rely on to reason and act correctly.

Instead of operating on raw signals or assumptions, agents use shared business definitions, policies, and enterprise knowledge curated in Foundry IQ. This ensures that AI behavior aligns with how the business actually operates.

In this stage of the lab, participants design and observe:

A Supervisor Agent that coordinates decisions using trusted business context
Specialized agents (Inventory, Store, Sales Associate) with clearly defined responsibilities
Knowledge grounding using Foundry IQ for enterprise documents, policies, and operational rules
Tool-calling integration that allows agents to retrieve structured insights while respecting governance boundaries
Azure OpenAI models running within a governed, observable, and auditable agent environment
Agents are far less likely to guess or hallucinate because every decision is grounded in business-aware intelligence provided by Foundry IQ and constrained by enterprise rules.

End-to-End Scenario: Holiday Sales at Zava
The value of Foundry IQ becomes clear during a high-pressure Holiday Sales scenario.

Inventory Agents reason using consistent definitions of availability and commitments
Store Agents apply local constraints, policies, and demand signals
Sales Associate Agents guide customer interactions based on trusted business context
All agent decisions are traceable, observable, and governed, ensuring trust, transparency, and compliance even at scale.

What This Lab Demonstrates
By the end of the lab, participants understand how Foundry IQ:

Establishes a shared business language for AI
Grounds agent reasoning in enterprise knowledge and governance
Enables safe, collaborative, multi-agent execution
Moves organizations from insight to intelligence to action
Foundry IQ is the critical layer that turns AI from an experiment into a reliable, business-aligned operating model.
```

### Block 02 — `FIQArchi.png` (the architecture diagram referenced in Block 01)

**Evidence class:** observed (image supplied by the user, transcribed structurally — no interpretation added).

**Title bar:** *Building Intelligent Solutions with Microsoft Foundry IQ Lab Architecture*

Two top-level pillars side by side, plus a data-sources band underneath and one external
consumer floating top-right.

| Zone | Contents (left → right, as drawn) |
|---|---|
| **Fabric IQ** (left pillar) | `Graph` · `Operations Agents` · `Ontology` · `Data Agents` |
| **OneLake** (nested inside the Fabric IQ pillar, lower half) | `Eventhouse` · `Semantic Models` · `Lakehouse` |
| **Foundry IQ** (right pillar) → **Agent Orchestration** (inner box, labelled `Agent Framework`) | `Supervisor Agent` · `Inventory Agent` · `Store/Sales Associates Agent` |
| **Foundry IQ** (right pillar, lower half) | `Foundry IQ` · `Azure OpenAI` · `Agent Service` |
| **M365 Copilot** | outside both pillars, top-right corner |
| **Data Sources** band (bottom, spans full width) | group 1: `Store Sensors & Inventory Data` — group 2 (boxed): `AWS S3` · `ADLS` · `Dataverse` · `OneDrive` · `SharePoint` — group 3 (boxed): `SharePoint` · `Azure Cosmos DB` · `Blob Storage` · `AI Search` |

**Arrows, as labelled on the diagram:**

| From | To | Label / style |
|---|---|---|
| `Store Sensors & Inventory Data` | OneLake | `Eventstream` (solid, upward) |
| Data-source group 2 (S3/ADLS/Dataverse/OneDrive/SharePoint) | `Lakehouse` | `Shortcut` (dashed, upward) |
| Data-source group 3 (SharePoint/Cosmos DB/Blob/AI Search) | `Foundry IQ` | `Knowledge Source` (solid, upward) |
| OneLake | Fabric IQ upper row | solid, upward (unlabelled) |
| Fabric IQ pillar | Foundry IQ pillar | solid, left → right (unlabelled; drawn at the `Data Agents` row) |
| Agent Orchestration | `M365 Copilot` | solid, upward-right (unlabelled) |

**Notable, recorded without interpretation:** the label `Agent Framework` sits on the
Agent Orchestration box, and `Foundry IQ` appears twice — once as the right-hand pillar's name
and once as a component tile inside it.

### Block 03 — Task 1.5 & Task 1.6 (start)

> **⚠ Capture gap.** The blocks jump from the Overview straight to **Task 1.5**. Tasks 1.1–1.4
> were not supplied. Anything they established (resource creation, workspace setup, Lakehouse
> load) is therefore **unknown**, not absent.

> Referenced images, not supplied as text: `DAnavigation`, `FoundryDataAgent`, `popup2.png`,
> `datasource`, `FoundryDataAgentLakehouse` (×2), `AgentInstructionForFoundry`.

```text
Task 1.5: Create a data agent with a Lakehouse as the data source
In this task, a Data Agent will be created in Fabric workspace and linked with the Lakehouse data source.

Navigate to your Fabric Workspace.

In your Fabric workspace, select the New item button in the top command bar.

In the New item creation pane, in the search bar, enter Data Agent.

Select the Data Agent card in the search results and select it to initiate creation.

DAnavigation

in the Input a data agent name field, enter Retail_DataAgent_63942064, and select Create.

FoundryDataAgent

If any message appears, please select Skip for now.

popup2.png

Once the data agent opens, navigate to the Data tab in the Explorer pane, select Add Data, and select Data source.

datasource

Select the Retail_Lakehouse_63942064 Lakehouse, then select Add and verify that the Lakehouse is successfully attached.

FoundryDataAgentLakehouse

Expand Retail_Lakehouse → schemas → dbo → Tables and select all tables (carriers, customers, demand_signals, forecasts, inventories, order_lines, orders, product_categories, products, promotions, regions, returns, shipments, stores, warehouses).

FoundryDataAgentLakehouse

Ensure all the above tables are selected to enable complete analytical coverage for the Retail data agent.

Task 1.6: Validate the data agent using natural language queries
Select Agent instructions from the top menu.

AgentInstructionForFoundry
```

### Block 04 — Task 1.6, agent instructions for `Retail_DataAgent_63942064` (Fabric data agent)

> Verbatim. This is the text pasted into the Fabric data agent's **Agent instructions** pane —
> a *Fabric* data agent, not a Foundry agent.

```markdown
**Purpose:**
 This data agent is designed to answer analytical and operational questions for retail business users using the Retail Lakehouse data model, which contains historical transactional and master data.

 **Planning Rules**
 Understand the user intent and classify it into:
 Sales
 Inventory
 Customer
 Promotion
 Supply Chain
 Forecasting
 Since only Lakehouse data is available:
 All queries should be treated as historical analysis
 Break complex queries into:
 Entity identification
 Relationship traversal
 Metric aggregation
 Always validate:
 Time filters (date, month, year, etc.)
 Granularity (store, region, product, category)

 **Data Source Mapping**
 - Sales & Orders
 orders, order_lines
 Revenue, sales transactions, quantity sold
 - Customer Insights
 customers
 Customer segmentation and behavior
 - Product Analysis
 products, product_categories
 Product performance and category trends
 - Inventory & Supply Chain
 inventories, shipments, warehouses, stores, carriers
 Stock levels, logistics, fulfillment
 - Promotions
 promotions
 Campaign performance and impact on sales
 - Returns
 returns
 Return trends, defects, and refund analysis
 - Forecasting
 forecasts
 Planned demand and expected trends
 - Geography
 regions
 Regional performance analysis

 **Terminology Standardization**
 - Revenue = Sum(order_lines.LineTotalAmount)
 - Sales Volume = Sum(order_lines.quantity)
 - Inventory Level = Available stock in inventories
 - Demand = Forecast values (from forecasts table)
 - Conversion Rate = Orders / Customers
 - Return Rate = Returns / Orders

 **Query Behavior Rules**
 - Prefer aggregated insights over raw data unless explicitly requested
 - Always:
 Apply relevant filters (date, region, product, etc.)
 Use joins via relationships (e.g., orders → customers → regions)
 - For ambiguous queries:
 Ask clarifying questions OR
 Provide best assumption with explanation

 **Response Style**
 - Clear and business-friendly explanations
 - Include:
 - Key insights
 - Supporting metrics
 - Trends (for time-based queries)
 - Use bullet points for readability
 - Highlight:
 - Patterns
 - Anomalies
 - Comparisons
 - Avoid overly technical or database-specific language
```

### Block 05 — Task 1.6 (continued) → Task 1.7 (start)

> Referenced images, not supplied as text: `agentpublish`, `popup3.png`, `agentclosing`,
> `agentresponse`.
>
> **Dedup note:** the "Sample agent instructions (copy & paste)" body in this block is
> byte-for-byte the text already captured in **Block 04**. It is elided below rather than
> duplicated; the surrounding steps are verbatim.

```text
In the Agent instructions section, remove any existing default content present in the instruction box, and provide guidance to control how the agent responds by entering instructions.

Sample agent instructions (copy & paste)
Copy the following instructions and paste them into the Agent instructions section:

TypeCopy
 [ ... identical to Block 04, elided ... ]

After entering the instructions, select Publish to save the configuration.

agentpublish

On the Publish data agent pop-up window, select Publish.

popup3.png

After adding the instructions, select the close icon (✕) on the Agent instructions tab to exit the window.

agentclosing

Once closed, the main Data Agent interface will be displayed, where you can start querying the agent using natural language.

In the query input area, ask questions using natural language, for example:

TypeCopy
Which regions are underperforming in sales?
Submit the query and review the response generated by the Data Agent.

agentresponse

Observe how the agent:

Interprets the question
Queries the underlying data using the ontology
Provides insights in a readable format
Try multiple queries and refine your questions to explore additional insights.

TypeCopy
 Which products are frequently returned and impacting revenue?
TypeCopy
 Which products are at risk of stockout?
TypeCopy
 Which stores have the highest number of orders?
Clear and specific questions provide more accurate results.

Responses may vary depending on how the question is framed.
The Data Agent uses the Ontology to translate natural language into meaningful queries.
Task 1.7: Configure permissions
This is required for later exercises to function correctly.

Configure Workspace permissions
Navigate to your Fabric Workspace.

In the upper right, select Manage access.
```

### Block 06 — Task 1.7 (continued): grant the AI Search service Contributor on the Fabric workspace

> Referenced images, not supplied as text: `txb80l84.png`, `3y9af9gc.png`.

```text
On the Manage access flyout message, select + Add people or groups.

txb80l84.png

Enter the name of your AI Search service srch-foundry-iq-lab-63942064

In the dropdown list below, select Contributor, and then select Add.

3y9af9gc.png
```

### Block 07 — Exercise 2: Provision the AI Foundry Foundation (Tasks 2.1, 2.2)

> 🔴 **REDACTED ON CAPTURE.** This block contained a live sign-in account, a Temporary Access
> Pass, a subscription GUID and a tenant GUID. They were **not** recorded. Placeholders below use
> the repo's fake-GUID convention (`PUBLIC_SAFETY.md`). This is the **second** time lab material
> has carried credentials in clear text.
>
> Referenced images, not supplied as text: `wap4bk5r.png`, `Step 7 Image`, `a8qt97io.png`,
> `0ecex6nd.png`, `dg474zob.png`, `sdiyrthj.png`, `17xpl52t.png`, `rsgn9y7g.png`, `Step 5.png`,
> `Step 6.png`.

```text
Exercise 2: Provision the AI Foundry Foundation
This exercise focuses on provisioning the AI Foundry Foundation, including the creation of a Foundry Hub and Project, and deploying foundational AI models such as GPT‑5 and text-embedding-ada-002.

Miguel provisions the following core components within Microsoft Foundry:

Microsoft Foundry environment
Foundry Agent Service
Secure identity and governance framework
"Agents must be observable, auditable, and secure - from day one."

✅ Outcome
Foundry Project successfully created
Base AI models deployed
Secure runtime environment ready for agent execution

Task 2.1: Provision a Foundry Hub and Project
Open a new browser tab and connect to your foundry project at
https://ai.azure.com/foundryProject/overview?wsid=/subscriptions/<SUBSCRIPTION-ID-REDACTED>/resourceGroups/RG1/providers/Microsoft.CognitiveServices/accounts/foundry-iq-lab-<NNNNNNNN>/projects/proj-foundry-iq-lab-<NNNNNNNN>&tid=<TENANT-ID-REDACTED>

If prompted for credentials, enter the following information:

Object   Value
User     <REDACTED — lab account, not recorded>
TAP      <REDACTED — temporary access pass, not recorded>

From the All resources page, select the project.

wap4bk5r.png

Ensure that the New Foundry toggle switch is on at the top of the menu bar

Step 7 Image

If any popup window appears, select the close icon (✕) to exit the window.

a8qt97io.png

Select Build to create agents, deploy models, and build workflows.

Task 2.2: Deploy LLM and embedding models
In this task, you'll deploy a reasoning model and an embedding model in Foundry.

On the Microsoft Foundry page, select Models, then select Deploy base model.

0ecex6nd.png

Please ensure All models is selected under Availability, then search for gpt-5.4-mini and choose gpt-5.4-mini.

dg474zob.png)

Select the Deploy dropdown list and select Default settings.

sdiyrthj.png

It may take a few minutes for Default settings to become available.

Once the model is deployed, open the model playground.

17xpl52t.png

Again navigate to the Models section to deploy the embedding model, then select Deploy base model.

rsgn9y7g.png

Search text-embedding-ada-002 then select text-embedding-ada-002.

Step 5.png

Select the Deploy dropdown list and select Default settings.

Step 6.png

What we learned
How to access the Azure Portal and navigate to the Foundry portal.
How to deploy LLM and embedding models in Foundry using default settings.

Next exercise
In the next exercise, we'll learn how to integrate enterprise knowledge using Foundry IQ, including setting up indexed sources for unstructured files and connecting to Microsoft Fabric Lakehouse for real-time structured data retrieval.
```

### Block 08 — Exercise 3: Integrate enterprise knowledge via Foundry IQ (Tasks 3.1, 3.2)

> Referenced images, not supplied as text: `Select step 1`, `hjs1m4iz.png`, `Step 4.png`,
> `oigdg59i.png`, `zskkao5o.png`, `Step 10.png`, `a4gbmunr.png`, `ktdhfeom.png`, `mev8a8sg.png`.

```text
Exercise 3: Integrate enterprise knowledge via Foundry IQ
This exercise focuses on integrating enterprise knowledge using Foundry IQ by enabling indexed sources for unstructured data and federated sources for real-time structured data retrieval, along with connectivity to the Microsoft Fabric Lakehouse. Ryan (Customer) asks detailed product-related questions during an engagement.

To enable accurate and context-aware responses, Miguel integrates enterprise content sources such as:

SharePoint product guides
Internal policy documents
Campaign and marketing materials
Foundry IQ provides permission-aware, citation-backed grounding by connecting to these knowledge sources, ensuring that agent responses are both secure and traceable.

✅ Outcome
Foundry IQ Knowledge Base configured
Multi-source enterprise grounding enabled
No custom RAG code required for knowledge integration

Task 3.1: Set up indexed sources for unstructured files and federated sources for real-time structured data retrieval.
On the left side, select Knowledge to configure Foundry IQ.

Select step 1

On the dropdown list below Foundry IQ resource, select srch-foundry-iq-lab-<NNNNNNNN>.

In the Auth Type dropdown list that appears, select API Key, and then select Connect.

hjs1m4iz.png

Select Create a knowledge base.

Step 4.png

On the Knowledge base page, scroll down and select Add sources under Knowledge sources, then select Azure Blob Storage to index unstructured return policy files.

oigdg59i.png

On the Create a knowledge source pop-up window, enter the following information:

Option                     Value
Name                       customer-loyalty-data
Storage account            stfiqlab<NNNNNNNN>
Container name             customerloyalty
Authentication type        API Key
Content extraction mode    Minimal
Embedding model            text-embedding-ada-002

Select Create.

On the same Knowledge Base page, scroll down to the Knowledge source section, select Add sources, and then choose Azure AI Search Index.

zskkao5o.png

Enter product-catalog in the Name field.

In the Select search service dropdown list, select product-catalog-index, then select Create.

Step 10.png

Task 3.2: Connect to a Microsoft Fabric Lakehouse to enable direct access to enterprise data
On the same Knowledge base page, in the Knowledge source section, select Add sources and then select Fabric IQ (OneLake Catalog) to connect Lakehouse to enable direct access to enterprise data without the need for data movement.

a4gbmunr.png

For the name, enter return-policy.

At the bottom of the window, select the Retal_Lakehouse_<NNNNNNNN>, and then select Create.

ktdhfeom.png

At the top of the Basic configuration page, in the Name field, enter foundry-lab-knowledgebase.

For the Chat completion model field, select gpt-5.4-mini.

Review all the Knowledge sources, and then select Save knowledge base.

mev8a8sg.png

If return policy displays Creating, refresh the browser and it should change to Active.

What we learned
How to configure Foundry IQ by connecting to Azure AI Search and creating knowledge bases.
How to index unstructured data from Azure Blob Storage and structured data from Azure AI Search indexes.
How to connect to Microsoft Fabric Lakehouse for direct access to enterprise data.

Next exercise
In the next exercise, we'll learn how to build intelligent agents with tool calling, including creating agent personas and implementing routing logic for user queries.
```

### Block 09 — Exercise 4: Build intelligent agents (Tasks 4.1, 4.2 start)

> The two illustrative GUIDs printed in the manual ("It should look similar to …") were replaced
> with the repo's fake-GUID convention — their *shape* is what matters, and they may originate
> from the manual author's own tenant.
>
> Referenced images, not supplied as text: `dataagent.png`, `hn0esrmh.png`, `qc93aq49.png`,
> `5izgg71g.png`, `lshxxooc.png`, `8atkch3z.png`, `hwns32kt.png`.

```text
Exercise 4: Build intelligent agents
This exercise focuses on building intelligent agents with tool-calling capabilities, including defining agent personas, configuring system instructions, and attaching relevant enterprise knowledge sources.

Miguel creates a Supervisor Agent capable of orchestrating insights across enterprise systems by:

Calling Fabric Data Agents for structured business insights
Calling Foundry IQ for unstructured enterprise knowledge
"The agent shouldn't know everything - it should know who to ask."

✅ Outcome
Tool-calling agent successfully created.
Fabric IQ and Foundry IQ integrated for unified intelligence.
Business-aware reasoning enabled across structured and unstructured data sources.

Task 4.1: Implement agent tool-calling capabilities
Return to the Fabric browser tab.

Navigate to your Fabric Workspace.

Select Retail_DataAgent_<NNNNNNNN>.

Look at the URL at the top of the browser and copy the following information into text boxes below:

dataagent.png

Workspace ID  Workspace ID

The Workspace ID is the string that appears between groups/ and /aiskills. It should look similar to a0000000-0000-4000-a000-00000000000a

Artifact ID  Artifact ID

The Artifact ID is the string that appears between aiskills/ and ? (do not include the ?). It should look similar to b0000000-0000-4000-b000-00000000000b

Return to the Microsoft Foundry browser tab.

Select Tools, and then select Tools.

Select Connect a tool.

hn0esrmh.png

Select Fabric Data Agent, and then select Add tool.

qc93aq49.png

On the Connect to Fabric Data Agent page, enter the following:

Option        Value
Connection    Add a new connection
Name          fabriciq_dataagent
Workspace ID  <from the Fabric URL>
Artifact ID   <from the Fabric URL>

Select Connect.

5izgg71g.png

Task 4.2: Create orchestrator agent persona and system instructions
On the Microsoft Foundry page, on the left side, select Agents.

lshxxooc.png

Select New agent, then select Build an agent

8atkch3z.png

For Agent name, enter Supervisor-Agent, then select Create and open playground.

hwns32kt.png

Once the agent is created, you'll be redirected to the agent playground page. From the Model dropdown list, select gpt-5.4-mini and paste the following instructions in the Instructions section.
```

### Block 10 — Task 4.2: `Supervisor-Agent` instructions (Foundry agent)

> Verbatim. Model selected in the lab: `gpt-5.4-mini`.

```markdown
You are the Supervisor Agent responsible for routing user queries to the appropriate specialized agent. Analyze the user's request and determine which agent should handle it. Based on the intent of the query, call the relevant agent listed below.

Agent Routing Rules
1. Sales-Associate-Agent
• Call this agent when the user asks about:
 o Product recommendations
 o DIY project guidance
 o Interior design suggestions
 o Product features or comparisons
 o Requests to visualize designs or generate images
 o Upselling or discovering suitable products
2. Rewards-Campaign-Agent
• Call this agent when the user asks about:
 o Loyalty programs or reward points
 o Promotional campaigns
 o Discount offers or eligibility
 o Black Friday or seasonal promotions
 o Customer-specific discounts or campaign details
3. Inventory-Agent
• Call this agent when the user asks about:
 o Product availability
 o Inventory levels
 o Stock status
 o Product location in the warehouse or store
 o Whether a product is in stock or out of stock
Decision Rule
• Carefully analyze the intent of the user query and route the request to only one most relevant agent.

Output Format
Return only the agent name no extra space or new line simple string. We want for example:
Sales-Associate-Agent
```

### Block 11 — Task 4.2 (continued): attach then remove the Foundry IQ knowledge base

> Referenced images, not supplied as text: `dbrpemzr.png`, `fvdsjsum.png`, `x6rota7m.png`,
> `jtp1w3og.png`.

```text
Select Save, then select the back arrow (⬅) to create additional agents.

dbrpemzr.png

Select Supervisor-Agent, and then select the Knowledge section.

Select Add, and then select Connect to Foundry IQ to enable the knowledge source.

fvdsjsum.png

Select the Knowledge base dropdown list, and then select foundry-lab-knowledgebase

Select Connect and then select Save to save the agent.

x6rota7m.png

In the Knowledge section, select the vertical ellipsis next to foundry-lab-knowledgebase, then select Remove and select Save to save the agent.

jtp1w3og.png

The Knowledge Base section we demonstrated was added purely for educational and learning purposes to show how to integrate Foundry IQ with an agent in a no-code experience.
In the upcoming sections, we'll build functional agents using a code-first approach, where we'll programmatically add knowledge bases, tools, and orchestration.
```

### Block 12 — Task 4.3: create the functional agents with a Python script (code-first)

> 🔴 **REDACTED ON CAPTURE** — the `az login` credential table (account + TAP) was again present
> and was **not** recorded. Third occurrence.
>
> The block re-opened with the last three lines of Block 11; those are elided here.
>
> Referenced images, not supplied as text: `5lzpanfw.png`, `cxjbe1to.png`, `t3skcacx.png`,
> `zkef8sjm.png`, `9lcgk59a.png`, `3hqh9c2g.png`, `vscode.png`, `w93zsqdn.png`,
> `Foundry IQ3.png`, `nqxiggf7.png`, `ewftcujk.png`, `gdixt6jm.png`.

```text
Task 4.3: Running a Python script to create functional agents in Microsoft Foundry
In Foundry, select your user profile in the upper-right corner, and then select Project details.

5lzpanfw.png

Select Connected resources.

cxjbe1to.png

You should see three objects displayed. If not, refresh the browser page. t3skcacx.png

Fill in the following text boxes with the appropriate information (the numbers correspond to the image below):

zkef8sjm.png

Endpoint (2) Endpoint (2)

Server Label (3) Server Label (3)

Server URL (4) Server URL (4)

Fabric Data Connection Name (5) Fabric Data Connection Name (5)

On the lab VM desktop, launch Visual Studio Code.

9lcgk59a.png

In VS Code, select Open Folder.

3hqh9c2g.png

In the Folder: enter C:\FabricIQLab, and then select the agents-build folder and click Select Folder to open it in VS Code.

vscode.png

If prompted choose the option Yes, I trust the authors.

Select the parameters.env file.

w93zsqdn.png

Insert the data captured above into the parameters.env file.

Ensure that you insert the data between the quotes "data".

Object                    Value
endpoint
server_label
server_url
project_connection_id
fabric_connection_name

Select CTRL+S to save the file.

In the VS Code menu bar, click the '…' (More Actions), navigate to Terminal, and then select New Terminal.

Foundry IQ3.png

In the Terminal window, run the following commands then press Enter on your local machine:

bash
TypeCopy
az login

When prompted for credentials, enter the following:

Object   Value
User     <REDACTED — lab account, not recorded>
TAP      <REDACTED — temporary access pass, not recorded>

Close the browser tab and return to VS Code.

Run the following command to install packages then press Enter on your local machine

bash
TypeCopy
python -m pip install -r ./requirement.txt

nqxiggf7.png

Please allow some time for the requirement file to finish running in the terminal.

Run the following command to create the agents, then press Enter on your local machine.

bash
TypeCopy
python .\agents.py

ewftcujk.png

Return to the Microsoft Foundry browser tab, and then select Agents to review the created agents.

gdixt6jm.png

What we learned
How to create multiple agents with specific roles and instructions for routing and specialized tasks.
How to implement tool calling by attaching knowledge sources and data agents to agents.
How to configure agents for product recommendations, rewards campaigns, and inventory checks.

Next exercise
In the next exercise, we'll learn how to configure multi-agent orchestration and validation using workflows to coordinate between agents.
```

### Block 13 — `agents.py` (the code-first agent creation script)

> **Source note.** The paste arrived with newlines collapsed in the import section and inside the
> `with` block. Two forms are recorded below: the **as-pasted** text (authoritative), and a
> **line-breaks-restored** rendering for readability. No tokens were added, removed or reordered
> between the two — only whitespace.

#### 13a — as pasted (authoritative)

```text
# Imports
import osfrom dotenv import load_dotenvfrom openai.types.responses.response_input_param import McpApprovalResponse, ResponseInputParamfrom azure.identity import DefaultAzureCredentialfrom azure.ai.projects import AIProjectClientfrom azure.ai.projects.models import ( PromptAgentDefinition, MicrosoftFabricPreviewTool, FabricDataAgentToolParameters, ToolProjectConnection, MCPTool,)# Load environment variablesload_dotenv('parameters.env')# Configure foundry project endpoint and Azure OpenAI modelendpoint = os.getenv("endpoint")gpt_4o_model = os.getenv('gpt-4o-model')#Configure fabric connectionfabric_connection_name = os.getenv('fabric_connection_name')#Knowledgebase detailsserver_label=os.getenv("server_label")server_url=os.getenv("server_url")project_connection_id=os.getenv("project_connection_id")# Initialize the AI Project clientwith ( DefaultAzureCredential() as credential, AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True) as project_client, project_client.get_openai_client() as openai_client,):
```
…followed by the three `create_version` calls, reproduced in full in 13b.

#### 13b — line breaks restored (whitespace only)

```python
# Imports
import os
from dotenv import load_dotenv
from openai.types.responses.response_input_param import McpApprovalResponse, ResponseInputParam
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    MicrosoftFabricPreviewTool,
    FabricDataAgentToolParameters,
    ToolProjectConnection,
    MCPTool,
)

# Load environment variables
load_dotenv('parameters.env')

# Configure foundry project endpoint and Azure OpenAI model
endpoint = os.getenv("endpoint")
gpt_4o_model = os.getenv('gpt-4o-model')

# Configure fabric connection
fabric_connection_name = os.getenv('fabric_connection_name')

# Knowledgebase details
server_label = os.getenv("server_label")
server_url = os.getenv("server_url")
project_connection_id = os.getenv("project_connection_id")

# Initialize the AI Project client
with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True) as project_client,
    project_client.get_openai_client() as openai_client,
):
    # Define MCP tool for knowledge retrieval
    mcp_tool = MCPTool(
        server_label=server_label,
        server_url=server_url,
        project_connection_id=project_connection_id,
        require_approval="never",
    )

    # Create Reward Campaign Agent
    reward_campaign_agent = project_client.agents.create_version(
        agent_name="Rewards-Campaign-Agent",
        definition=PromptAgentDefinition(
            model=gpt_4o_model,
            instructions="""Apply personalized discounts to customers based on their loyalty information and explain the applicable Black Friday promotional tiers using the provided knowledge sources.
________________________________________
Response Behavior
• Generate responses only from the retrieved knowledge and tool outputs. Do not assume or invent any values.
• When a customer name is included, respond in a friendly first-person tone and include celebratory emojis such as 🎉, 😊, or 🛍️.
• When the internal team asks about discount tiers, provide an average discount range instead of listing every individual percentage.
• Ensure the response clearly reflects the loyalty information and discount values retrieved from the knowledge source or tools.
________________________________________
Response Format
Always return the response in the following JSON format:
{
  "answer": "<response generated using the knowledge and tool results>",
  "discount_percentage": "<discount value retrieved from the knowledge or tool>"
}
________________________________________
Content Handling Guidelines
• Do not summarize, filter, or remove any important information from the knowledge source.
• Responses must strictly follow the information retrieved from the given knowledge only.
• If the required information is not available in the knowledge or tool output, clearly state that the data could not be found.""",
            tools=[mcp_tool],
        ),
    )
    print(f"Agent created (id: {reward_campaign_agent.id}, name: {reward_campaign_agent.name}, version: {reward_campaign_agent.version})")

    # Create Sales Associate Agent
    sales_associate_agent = project_client.agents.create_version(
        agent_name="Sales-Associate-Agent",
        definition=PromptAgentDefinition(
            model=gpt_4o_model,
            instructions="""Interior Design Agent Guidelines:
========================================
- You are an Interior Designer salesperson working for Zava and helps customers with DIY Projects and interior design queries.
- Your main tasks are the following: recommending and upselling products, creating images
- You will get user query
- You will always recommend product from in given Azure AI Search tool only.
- You will keep asking questions to the user and keep recommending.
- When you get video or image, reply saying "I see you uploaded..."
- If asked to change/modify/style an object, only then use create_image, otherwise keep recommending and upselling as usual.
Your response should only come from the given knowledge and with following details like ProductId, ProductName, Category, ProductDescription, FormattedPriceWithDollarSign

Example Conversation
========================================
User: Want paint recommendation for my living room
You: Give some paints options, ask dimension, ask image
User: Gives dimensions, image (maybe)
You: Recommends based on the color, calculate how much paint maybe required, upsell for sprayer, tape (saying its good)""",
            tools=[mcp_tool],
        ),
    )
    print(f"Agent created (id: {sales_associate_agent.id}, name: {sales_associate_agent.name}, version: {sales_associate_agent.version})")

    # Create Inventory Agent
    fabric_connection = project_client.connections.get(fabric_connection_name)
    inventory_agent = project_client.agents.create_version(
        agent_name="Inventory-Agent",
        definition=PromptAgentDefinition(
            model=gpt_4o_model,
            instructions="""You are Inventory check agent,
• Your task is to check the inventory status.
• When a user asks to check the inventory for a product, send the product name to the Fabric Data Agent tool.
• Return the response including inventory levels, inventory status, and location.

Content Handling Guidelines
• Do not generate summaries or remove any data from the response.
• The response must come only from the Fabric Data Agent tool output.

Important Rule: Use these products ids as risk of stockout:
Products currently at risk of stockout include:
PROD000030
PROD000281
PROD000222
PROD000262
PROD000302
PROD000375
PROD000478
PROD000486
PROD000145
PROD000511
""",
            tools=[
                MicrosoftFabricPreviewTool(
                    fabric_dataagent_preview=FabricDataAgentToolParameters(
                        project_connections=[
                            ToolProjectConnection(project_connection_id=fabric_connection.id)
                        ]
                    )
                )
            ],
        ),
    )
    print(f"Agent created (id: {inventory_agent.id}, name: {inventory_agent.name}, version: {inventory_agent.version})")
```

### Block 14 — `parameters.env` (template, values blank as shipped)

> Same whitespace caveat as Block 13: newlines were collapsed in the paste. Values are empty in
> the shipped template — nothing to redact.

#### 14a — as pasted (authoritative)

```text
#Foundry Project Endpointendpoint = ""
#Knowledgebaseserver_label=""server_url=""project_connection_id = ""#Fabric Data Agentfabric_connection_name = ""#Modelgpt-4o-model= "gpt-5.4-mini"
```

#### 14b — line breaks restored (whitespace only)

```ini
# Foundry Project Endpoint
endpoint = ""

# Knowledgebase
server_label=""
server_url=""
project_connection_id = ""

# Fabric Data Agent
fabric_connection_name = ""

# Model
gpt-4o-model= "gpt-5.4-mini"
```

### Block 15 — `requirement.txt`

```text
python-dotenv
openai
azure-identity
azure-ai-projects>=2.0.0
aiohttp
```

### Block 16 — screenshot: the four agents after running `agents.py`

**Evidence class:** observed.

Breadcrumb: `Microsoft Foundry / proj-foundry-iq-lab-<REDACTED>` (project switcher chevron).

Left navigation, top to bottom: **Agents** (selected, callout ①) · `Models` · `Data` ·
`Evaluations` · `Guardrails`.

Main pane header `Agents`, with two tabs: **`Agents`** (active) and **`Workflows`** carrying a
`Preview` badge.

Table column `Name`, four rows (callout ②), in this order:

| # | Agent |
|---|---|
| 1 | `Inventory-Agent` |
| 2 | `Sales-Associate-Agent` |
| 3 | `Rewards-Campaign-Agent` |
| 4 | `Supervisor-Agent` |

### Block 17 — Exercise 5: Multi-Agent orchestration and validation (Task 5.1 start)

> Referenced images, not supplied as text: `ew613bm8.png`, `Step 2.png`, `Step 3.png`.

```text
Exercise 5: Multi-Agent orchestration and validation
This exercise focuses on configuring and validating multi-agent workflows that coordinate interactions between specialized agents to support end-to-end business processes.

During high-demand events such as Holiday Sales, multiple domain-specific agents collaborate to deliver seamless customer experiences:

Interior Designer Agent recommends products.
Rewards Agent applies eligible discounts.
Responsible AI Agent blocks unsafe or non-compliant prompts.
Checkout Agent finalizes the customer order.
All agent interactions are orchestrated by the Supervisor Agent to ensure coordinated decision-making across systems.

✅ Outcome
Multi-agent orchestration successfully configured.
Business-aligned AI workflows enabled.
Safe and scalable automation across agent-driven processes.

Task 5.1: Configure multi-agent orchestrator and specialist agents
Select Workflows.

ew613bm8.png

Select Create and then select Blank workflow.

Step 2.png

Select YAML.

Step 3.png

Paste the script below following the YAML script tag and select Save.
```

### Block 18 — Task 5.1: the `FoundryIQ-Workflow` YAML

> Verbatim, indentation as pasted (the source flattens two-space YAML indents to one).

```yaml
kind: workflow
trigger:
 kind: OnConversationStart
 id: trigger_wf
 actions:
 - kind: SetVariable
 id: action-1768237669100
 variable: Local.Var2679
 value: =System.LastMessage
 - kind: InvokeAzureAgent
 id: action-1768237693978
 agent:
 name: Supervisor-Agent
 input:
 messages: =System.LastMessage
 output:
 autoSend: true
 messages: Local.Var5755
 - kind: ConditionGroup
 conditions:
 - condition: =Last(Local.Var5755).Text = "Sales-Associate-Agent"
 actions:
 - kind: InvokeAzureAgent
 id: action-1768237857121
 agent:
 name: Sales-Associate-Agent
 input:
 messages: =System.LastMessage
 output:
 autoSend: true
 id: if-action-1768237712578-0
 - condition: =Last(Local.Var5755).Text = "Rewards-Campaign-Agent"
 actions:
 - kind: InvokeAzureAgent
 id: action-1768237897049
 agent:
 name: Rewards-Campaign-Agent
 input:
 messages: =System.LastMessage
 output:
 autoSend: true
 id: if-action-1768237712578-0p9xo7ga
 - condition: =Last(Local.Var5755).Text = "Inventory-Agent"
 actions:
 - kind: InvokeAzureAgent
 id: action-1768237934785
 agent:
 name: Inventory-Agent
 input:
 messages: =System.LastMessage
 output:
 autoSend: true
 id: if-action-1768237712578-ma22fceo
 id: action-1768237712578
 elseActions:
 - kind: SendActivity
 activity: " "
 id: action-1768238054760
id: ""
name: FoundryIQ-Workflow
description: ""
```

### Block 19 — Tasks 5.1 (end), 5.2 (Traces / App Insights), 5.3 (end-to-end validation)

> Referenced images, not supplied as text: `Step 5.png`, `2bo1twcv.png`, `4sau8dgd.png`,
> `vrqne19s.png`, `qjh688ix.png`, `Step 1.png`, `Step 3.png`, `Step 4.png`, `Step 5.png`,
> `Step 6.png`, `Step 7.png` (×2).

```text
Enter FoundryIQ-Workflow in the Workflow Name field and select Save.

Step 5.png

You may see the workflow in a horizontal layout by default. If you want to change it to vertical, select the Vertical Layout button.

Review the workflow, select the Publish dropdown list, then select Publish latest version.

It might take a few seconds to publish the workflow in Foundry.

Task 5.2: Inspect the execution path using the Trace tool
In the Workflow page, select Traces, and then select Connect.

If you don't see the option to Connect to Application Insights, ignore Steps 1,2, and 3, as Application Insights has already been connected.

2bo1twcv.png

Select Create new resource.

4sau8dgd.png

Enter name as foundryiq-app-insight, and then select Create.

vrqne19s.png

Task 5.3: Validate the end-to-end agentic workflow
Note: This section demonstrates how individual agents are invoked and how they operate. Note: Before validating the workflow, test the individual agents and approve the tools. Tool approval cannot be completed within the workflow preview and may result in errors. Also, this feature is currently in preview.

Select Build, and then select Preview.

qjh688ix.png

Enter prompt Hey! I'm planning to paint my living room but I'm not sure which color would look best. Can you recommend some paint shades? then select the Send button.

Step 1.png

The response of the agents can be seen on the right side (See image pointer/box 1). You can also see the called Agents during the process on the right side and in the workflow (see image pointers/boxes 2 and 3).

The response provides suitable paint shade recommendations for the living room along with brief descriptions. The expected outcome is to suggest relevant and aesthetically pleasing colors that help the user make an informed decision.

Step 3.png

Enter prompt Can you tell me Joe's customer loyalty tier and discount?, then select the Send button.

Step 4.png

The response of the agents can be seen on the right side (See image pointer/box 1). Note that we've received this response in JSON format. You can also see the called Agents during the process on the right side and in the workflow (see image pointers/boxes 2 and 3).

The response displays Joe's loyalty details, including a personalized message and discount. The expected outcome is to identify Joe's loyalty tier as Platinum and return the 32.40% discount.

Step 5.png

Enter prompt Which products are at risk of stockout, and how can we optimize inventory to avoid shortages?, then select the Send button.

Step 6.png

The response of the agents can be seen on the right side (see image pointer/box 1). You can also see the called Agents during the process on the right side and in the workflow (see image pointers/boxes 2 and 3).

Step 7.png

Enter prompt Which products are driving high return volumes that are impacting available inventory levels, and how should inventory planning be adjusted to minimize these returns?
The response of the agents can be seen on the right side (see image pointer/box 1). You can also see the called Agents during the process on the right side and in the workflow (see image pointers/boxes 2 and 3).

Step 7.png

Select Traces, select any of the Conversation IDs, to review the agent and tool call. You can also review the input, output, and metadata for that conversation.

What we learned
How to create and configure workflows for multi-agent orchestration using YAML.
How to publish workflows as apps and validate agent interactions through previews.
How to inspect execution paths and traces for debugging and monitoring agent performance.

Next exercise
In the next exercise, we'll learn how to enforce guardrails and safety policies, and define evaluation metrics for assessing agent performance.
```

### Block 20 — Exercise 6: Observability, evaluation, and guardrails (Tasks 6.1, 6.2) + Lab conclusion

> Referenced images, not supplied as text: `Step 1.png` (×2), `hsq4et7b.png`, `gb5nam3e.png`,
> `1dyl5tbx.png`, `Step 2.png`, `a3qsymwi.png`, `3zw9rnbp.png`, `555svx9k.png`, `fqdoaezt.png`,
> `wvzb8qxl.png`, `Step 7.png`.

```text
Exercise 6: Observability, evaluation, and guardrails
This exercise focuses on enabling end-to-end observability, implementing evaluation frameworks, and enforcing guardrails to ensure enterprise-grade safety and governance for AI-driven agents.

April (CEO) emphasizes the need for trust and transparency in automated decision-making:

"If AI makes decisions, I need to see, trust, and govern them."

To meet these requirements, Miguel enables the following capabilities:

Telemetry for agent activity and performance monitoring
Prompt evaluation for response quality and alignment
Guardrails and policy enforcement for Responsible AI

✅ Outcome
End-to-end observability implemented.
Responsible AI policies enforced.
Enterprise-ready agents with governance and auditability.

Task 6.1: Enforce guardrails and safety policies
From the left pane, select Guardrails and then select Create.

Step 1.png

In the Add controls section, select the Risk Type checkbox for the dropdown items: Jailbreak and Protected Materials.

Make sure the Hate, Sexual, Self-harm, and Violence checkboxes under Content harms are selected, then select Next.

hsq4et7b.png

In the Select agents and models section, select the Name checkbox to include all agents, then select Next.

gb5nam3e.png

In the Review section, paste Guardrail11 as the Guardrail name, then select Create.

1dyl5tbx.png

Task 6.2: Define evaluation metrics and run offline/online assessments
Select Evaluations and then select Create.

Step 1.png

Under the Target: Agent section, select the Supervisor agent, then select Next.

Step 2.png

Under the Scope section, select Individual turns, then select Next.

a3qsymwi.png

Under the Data section, select Generate. Leave other values as default and for Number of rows enter 10, then select Confirm.

3zw9rnbp.png

Select Next.

555svx9k.png

Under the Criteria section, select Next.

fqdoaezt.png

Under the Review section, enter eval-7gthxnri as Evaluation name and select Submit.

wvzb8qxl.png

Note: It might take a few seconds to load.

Review the Evaluation runs and Evaluators.

Step 7.png

Do not close the page until the evaluation run status is complete.

Note: Similarly, perform evaluation on the other agents.

What we learned
How to create and apply guardrails for content safety, jailbreak prevention, and protected materials.
How to set up evaluations for agents using generated data and predefined criteria.
How to monitor and assess agent performance through evaluation runs and metrics.
This concludes the "Building Foundry IQ" lab series.

Lab Conclusion
Throughout this comprehensive lab, we journeyed from provisioning the foundational elements of Microsoft Foundry 🤖 to deploying sophisticated AI agents capable of intelligent interactions. Starting with setting up the Foundry Hub and deploying essential models like gpt-5.4-mini and text-embedding-ada-002, we progressed to integrating enterprise knowledge 🧠 via Foundry IQ, indexing unstructured data 📊 from Azure Blob Storage and structured data from AI Search indexes, and connecting directly to Microsoft Fabric Lakehouse for seamless data access.

We then delved into building intelligent agents 👥 with tool calling, creating specialized agents for sales assistance, rewards campaigns, and inventory management, each equipped with tailored instructions and knowledge sources. The orchestration phase taught us to coordinate multiple agents through workflows 🔄, validating their end-to-end operations and inspecting execution paths via traces for robust debugging and monitoring.

Finally, we emphasized observability and safety by implementing guardrails 🛡️ to enforce content policies and conducting evaluations 📈 to measure agent performance, ensuring reliable and ethical AI deployments. Happy learning as you continue to explore and build with Foundry IQ!🚀
```

---

## Capture closed

**Closed:** 2026-08-04 · **Blocks:** 20 · Exercises 1 (partial, from Task 1.5) through 6, complete.

**Known gaps in the capture:**
- Tasks 1.1–1.4 were never supplied (resource creation, workspace setup, Lakehouse load).
- All inline images are referenced by filename only, except `FIQArchi.png` (Block 02) and the
  agents list (Block 16), which were supplied as actual screenshots.
- No screenshot of a `Traces` view, a guardrail result, or an evaluation result was supplied.

Distillation may now begin. Every claim promoted out of this file must be entered in the
**Distillation ledger** near the top.



# Capacity, region and tenant prerequisites for a Fabric Data Agent

Companion to `instructions.md`. Read this **before** picking or accepting a capacity for a
Data Agent deployment — the wrong choice is not a runtime error, it is a Copilot pane that
is greyed out or an agent that answers nothing, with no message pointing at the cause.

**Verified:** 2026-02, against Microsoft Learn primary pages (fetched, not summarised).

---

## The two prerequisites, and which one actually bites

Every Data Agent page on Learn opens with the same two-item prerequisite block:

1. **A paid F2-or-higher Fabric capacity**, or a Power BI Premium P1+ capacity with
   Fabric enabled. **Trial SKUs cannot use Azure OpenAI.**
2. **Cross-geo processing and storing for AI**, *"based on requirements"* — i.e. it
   depends on where the capacity lives.

Item 1 is usually already satisfied and is not where deployments fail. Item 2 is the one
worth resolving before you start, because it is a **tenant-level** switch: an individual
building a demo may not be able to turn it on, and in a customer tenant it may be
deliberately off for compliance reasons.

Source: [Create a Fabric data agent § Prerequisites](https://learn.microsoft.com/fabric/data-science/how-to-create-data-agent)
— the same block is repeated verbatim on `concept-data-agent`, `data-agent-sharing`,
`data-agent-foundry`, `data-agent-mcp-server`, `data-agent-visuals` and the end-to-end
tutorial.

---

## F64 is not the threshold. F2 is.

**The rule:** a Data Agent needs **F2 or higher**, paid. Not F64.

The F64 figure circulates widely and is wrong for this feature. Two things feed the
confusion:

- F64 *was* the historical gate for Copilot in Fabric before the requirement was lowered.
- The consumption doc uses F64 as a **worked example** to size CU cost —
  *"If you're using an F64 SKU that has 64 × 24 = 1,536 CU hours a day…"* — which reads
  like a floor and is not one.

Sizing, for reference: a Data Agent request is a background job of roughly
**6.67 CU-minutes**, consuming one CU-minute per hour of capacity.

Source: [Data agent in Fabric consumption § Capacity utilization type](https://learn.microsoft.com/fabric/fundamentals/data-agent-consumption#capacity-utilization-type)

---

## Region: reason from the EU Data Boundary, not from a region list

The Azure OpenAI service backing Fabric Copilot and Data Agents is **not** the same
deployment as the Azure OpenAI you provision in the Azure portal. It is deployed to:

- US datacenters — East US, East US 2, South Central US, West US
- **and the EU Data Boundary**

What matters is the **mapping** from your capacity's geography to that hosting, not
whether your region appears in some allow-list:

| Capacity geography | Azure OpenAI hosted in | Cross-geo? | Action required |
|---|---|---|---|
| US | US | No | Turn on Copilot |
| **EU Data Boundary** | **EU Data Boundary** | **No** | **Turn on Copilot** |
| **UK** | EU Data Boundary | **Yes** | Turn on Copilot **+ enable cross-geo** |
| Australia, Brazil, Canada, India, Asia, Japan, Korea, South Africa, Southeast Asia, UAE | US | Yes | Turn on Copilot **+ enable cross-geo** |

Two consequences that are easy to get backwards:

- **An EU capacity is the low-friction choice** — no tenant override, and the data stays
  in the EU boundary. When the customer's argument is auditability or data residency
  (advertising transparency regimes, public sector, regulated finance), "no cross-geo
  override was ever enabled" is a statement worth being able to make.
- **The UK is *not* treated as EU here.** A UK-South capacity needs the cross-geo switch
  that a Swedish or Irish one does not. Picking UK "to stay in Europe" adds the
  dependency it was meant to avoid.

If the switch is needed, it is:
**Data sent to Azure OpenAI can be processed outside your capacity's geographic region,
compliance boundary, or national cloud instance.**

Source: [What is Copilot in Fabric? § Available regions](https://learn.microsoft.com/fabric/fundamentals/copilot-fabric-overview#available-regions)

Copilot is **not supported in sovereign clouds** at all, for GPU-availability reasons.

---

## Do not size regions from the Text Analytics table

`ai-services-overview` carries a region table listing North Europe, West Europe, France
Central, Norway East, Switzerland North/West, UK South/West for Europe. **That table
governs Text Analytics and Translator only.** It excludes Sweden Central, among others.

Reading it as the Data Agent's region list produces a false negative: you conclude a
perfectly valid capacity cannot run a Data Agent. The Azure OpenAI path — the one Data
Agents use — is governed by the EU-Data-Boundary mapping above, and that article's own
"Available regions for Azure OpenAI Service" heading is a **pointer** to the Copilot
article, not a list.

---

## The tenant switch nobody checks

Beyond the Copilot master switch:

> **Standalone Copilot experience** (Admin portal → Tenant settings → Copilot).
> If it isn't enabled, you won't be able to use the data agent inside Copilot scenarios
> **even if every other Copilot tenant switch is on.**

This is the failure that looks like a broken agent rather than a missing permission: the
agent exists, is published, resolves — and does nothing where the user expects it.

Source: [Fabric data agent example with the AdventureWorks dataset](https://learn.microsoft.com/fabric/data-science/data-agent-end-to-end-tutorial)

---

## Conversation history is stored, and it is stored for 28 days

Applies to Copilot in Notebooks and Data Agents. Conversation history persists **across
user sessions**, inside the Azure security boundary, in the same region and the same Azure
OpenAI resources that process the requests. Retention is **28 days** unless the user
clears the chat, which they can do at any time.

Worth stating out loud in any conversation about a regulated workload: it is a data
retention fact, and discovering it during a security review is worse than declaring it.

Source: [Copilot in Fabric § Data storage of conversation history cross geographic regions](https://learn.microsoft.com/fabric/fundamentals/copilot-fabric-overview#available-regions)

---

## Pre-flight checklist

Before deploying a Data Agent to a capacity you did not choose yourself:

- [ ] Capacity SKU is **F2+ paid** or **P1+** — not a trial
- [ ] Capacity state is **Active** (a paused capacity hides everything — root
      `known_issues.md` § 6)
- [ ] Capacity geography identified, and mapped through the table above
- [ ] If mapping says cross-geo: confirm the tenant switch is on, **or** that someone can
      turn it on, *before* building anything
- [ ] Copilot tenant switch on
- [ ] **Standalone Copilot experience** tenant switch on
- [ ] 28-day conversation-history retention is acceptable to the customer

Confirm the SKU and region straight from the API rather than from memory:

```powershell
$tok = az account get-access-token --resource "https://api.fabric.microsoft.com" --query accessToken -o tsv
(Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/capacities" `
  -Headers @{Authorization = "Bearer $tok"}).value |
  Select-Object displayName, sku, region, state, id | Format-Table -AutoSize
```

`region` comes back as a display name (`Sweden Central`, `West US 3`), while config files
and ARM use the compact form (`swedencentral`). Normalise before comparing, or a
region-match assertion will fail on a correct setup.

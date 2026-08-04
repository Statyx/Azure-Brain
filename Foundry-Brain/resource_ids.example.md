# Resource IDs & Endpoints — Foundry

> **Copy this file to `resource_ids.md` and fill in your values.**
> `resource_ids.md` is gitignored — your IDs stay local. See [`../PUBLIC_SAFETY.md`](../PUBLIC_SAFETY.md).

---

## Azure

| Property | Value |
|----------|-------|
| Subscription | `<YOUR_SUBSCRIPTION_ID>` |
| Tenant | `<YOUR_TENANT_ID>` |
| Resource Group | `<YOUR_RESOURCE_GROUP>` |
| Region | `<YOUR_REGION>` |

---

## Foundry resource & project

| Property | Value |
|----------|-------|
| Foundry resource name | `<YOUR_FOUNDRY_RESOURCE>` |
| Project name | `<YOUR_PROJECT_NAME>` |
| Project endpoint | `https://<YOUR_FOUNDRY_RESOURCE>.services.ai.azure.com/api/projects/<YOUR_PROJECT_NAME>` |
| A2A base path (per agent) | `https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>/agents/<AGENT>/endpoint/protocols/a2a` |
| A2A audience | `https://ai.azure.com` |
| Project ID | `<YOUR_PROJECT_ID>` |
| Managed identity (principal ID) | `<YOUR_PRINCIPAL_ID>` |

> ⚠️ **Copy the project endpoint from the portal**, do not assemble it. The portal's *Project
> details* page shows `<resource>.services.ai.azure.com`; some SDK code comments still show the
> stale `<resource>.ai.azure.com` form. The A2A **audience** (`https://ai.azure.com`) is a
> different value again and is not a hostname. See
> [`portal_reality.md`](portal_reality.md) and [`orchestration_patterns.md`](orchestration_patterns.md).

---

## Model deployments

One row per deployment. The **deployment name** is what agent definitions reference — not
the model name.

| Deployment name | Model | Version | TPM quota |
|-----------------|-------|---------|-----------|
| `<YOUR_DEPLOYMENT_NAME>` | `<MODEL>` | `<VERSION>` | `<TPM>` |

---

## Agents

Fill in as you create them. `Kind` is **Prompt** (server-side, Projects SDK) or **Hosted**
(Agent Framework, in-process). Hosted agents are not supported in the workflow designer.

| Role | Name | Agent ID | Kind | Incoming A2A enabled? |
|------|------|----------|------|----------------------|
| Supervisor | `<YOUR_AGENT_NAME>` | `<YOUR_AGENT_ID>` | Prompt | n/a |
| Sub-agent — data | `<YOUR_AGENT_NAME>` | `<YOUR_AGENT_ID>` | Prompt | `<yes/no>` |
| Sub-agent — ops | `<YOUR_AGENT_NAME>` | `<YOUR_AGENT_ID>` | Prompt | `<yes/no>` |

> A sub-agent is only callable once **incoming A2A** is explicitly enabled on it.

---

## Toolboxes

The recommended way to attach capabilities. One toolbox = one managed MCP endpoint.

| Toolbox name | Version | Tools inside | MCP URL |
|--------------|---------|--------------|---------|
| `<YOUR_TOOLBOX>` | `<VERSION>` | Fabric, OpenAPI, … | `<PROJECT_ENDPOINT>/toolboxes/<NAME>/versions/<VERSION>/mcp?api-version=v1` |

---

## Connections

| Purpose | Connection name | Kind | Target |
|---------|-----------------|------|--------|
| Toolbox (as MCP tool) | `<YOUR_CONNECTION_NAME>` | `remote-tool` | `<TOOLBOX_MCP_URL>` |
| Sub-agent (A2A) | `<YOUR_CONNECTION_NAME>` | A2A | `<A2A_BASE_PATH>` |
| Fabric data agent | `<YOUR_CONNECTION_NAME>` | built-in tool | `<FABRIC_DATA_AGENT_ENDPOINT>` |
| AI Search | `<YOUR_CONNECTION_NAME>` | built-in tool | `<SEARCH_ENDPOINT>` |
| Application Insights | `<YOUR_CONNECTION_NAME>` | — | `<APPINSIGHTS_RESOURCE>` |

---

## Fabric side (cross-brain)

The Foundry agent consumes these; it does not create them. See
[`../Fabric-Brain/resource_ids.example.md`](../Fabric-Brain/resource_ids.example.md) for the
full Fabric inventory.

| Property | Value |
|----------|-------|
| Fabric workspace ID | `<YOUR_WORKSPACE_ID>` |
| Fabric Data Agent ID | `<YOUR_DATA_AGENT_ID>` |
| Fabric Data Agent published endpoint | `<YOUR_DATA_AGENT_ENDPOINT>` |

---

## Notes

- Deployment names, not model names, go into agent definitions — a model rename does not
  move the deployment.
- Preview tools (Fabric data agent, Fabric IQ) may not exist in every region or tenant.
  Record what your portal actually offers in `portal_reality.md`.

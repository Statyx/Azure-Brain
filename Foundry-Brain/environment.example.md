# Environment — Foundry

> **Copy this file to `environment.md` and fill in your values.**
> `environment.md` is gitignored. Secrets are read at runtime, never committed —
> see [`../PUBLIC_SAFETY.md`](../PUBLIC_SAFETY.md).

---

## Authentication

Foundry agent work uses Entra ID. Prefer `DefaultAzureCredential` / `az login` over keys.

```bash
az login --tenant <YOUR_TENANT_ID>
az account set --subscription <YOUR_SUBSCRIPTION_ID>
```

| Item | Value |
|------|-------|
| Auth mode | `az login` (dev) / managed identity (deployed) |
| Role on the Foundry resource (management) | `Contributor` or `Owner` |
| Role to build agents | `Foundry User` (formerly *Azure AI User*) |
| Role on the Fabric side | `<ROLE>` |

> ⚠️ **Foundry RBAC roles were renamed.** `Foundry User`, `Foundry Owner`,
> `Foundry Account Owner`, `Foundry Project Manager` were previously `Azure AI User`,
> `Azure AI Owner`, `Azure AI Account Owner`, `Azure AI Project Manager`. Role IDs and
> permissions are unchanged; both names may appear while the rename rolls out. Record which
> one **your** portal shows.

---

## Environment variables

Set locally in a gitignored `.env` (a committed `.env.example` may carry the keys only).

| Variable | Purpose | Example |
|----------|---------|---------|
| `AZURE_TENANT_ID` | Entra tenant | `<YOUR_TENANT_ID>` |
| `AZURE_SUBSCRIPTION_ID` | Subscription | `<YOUR_SUBSCRIPTION_ID>` |
| `FOUNDRY_PROJECT_ENDPOINT` | Project endpoint the SDK targets | `https://<RESOURCE>.services.ai.azure.com/api/projects/<PROJECT>` |
| `FOUNDRY_MODEL_DEPLOYMENT` | Default model deployment name | `<YOUR_DEPLOYMENT_NAME>` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Tracing sink | read at runtime, never committed |

---

## Local tooling

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12+ | `pathlib` + type hints, umbrella convention |
| Azure CLI | `<VERSION>` | `az login`, resource provisioning |
| Azure Developer CLI | `<VERSION>` | `azd ai connection create` for remote-tool connections |
| Python SDK | `azure-ai-projects>=2.0.0` | GA — pin the exact version you used |
| C# SDK | `Azure.AI.Projects` `<VERSION>` | NuGet |
| TypeScript SDK | `@azure/ai-projects` `<VERSION>` | GA |
| Java SDK | `com.azure:azure-ai-agents:2.0.0` | Maven |

> Record the **exact** SDK package and version you used, with the date. A Foundry sample
> that worked last month may target the retiring generation — see
> [`generation_map.md`](generation_map.md).

---

## Environment fingerprint

Fill this in once, and re-check before each demo. These answers cannot come from
documentation — only from your portal. See [`orchestration_patterns.md`](orchestration_patterns.md)
§ *Open questions*.

| Question | Answer | Checked on |
|----------|--------|------------|
| Is the **New Foundry** toggle on by default? | `<yes / must flip>` | `<DATE>` |
| Which agent generation does the portal show? | `<classic / current>` | `<DATE>` |
| Are **toolboxes** available in this region? | `<yes / no>` | `<DATE>` |
| Is the **Agent2Agent (A2A)** tool in the catalog? | `<yes / no>` | `<DATE>` |
| Is the **Microsoft Fabric** tool in the catalog? | `<yes / no>` | `<DATE>` |
| Does it see the published Fabric Data Agent? | `<yes / no>` | `<DATE>` |
| Is **Fabric IQ** available? Background mode? | `<yes / no>` | `<DATE>` |
| Are portal **Workflows** present? (retires 2026-12-01) | `<yes / no>` | `<DATE>` |
| RBAC role names shown | `<Foundry User / Azure AI User>` | `<DATE>` |
| Region | `<YOUR_REGION>` | `<DATE>` |

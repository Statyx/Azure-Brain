# Separate tenant profile - environment

> Copy to `environment.md` beside your private `resource_ids.md`.
> Keep passwords out of both files. Enter passwords and MFA only in Microsoft's
> sign-in interface.

## Explicit selection

Ask the agent to use this directory's `environment.md` and `resource_ids.md` for the
target tenant. Do not overwrite the active files in Fabric-Brain, Foundry-Brain or
Database-Brain. These Markdown files guide the agent; they are not an automatic
configuration loader for deployment scripts.

Give each consuming project a separate configuration and deployment state for this
tenant. Do not reuse the previous tenant's `.env`, item IDs or `state.json`.

## Isolated Azure CLI session

Run in a **new PowerShell window** dedicated to this tenant. Environment variables
below apply only to that process and its children; the normal CLI profile remains
untouched. Keep the authentication cache outside the repository and synced folders.

```powershell
$tenantId = '<YOUR_TENANT_ID>'
$env:AZURE_CONFIG_DIR = Join-Path $env:LOCALAPPDATA "Azure-Brain\tenant-profiles\$tenantId\.azure"
$env:AZURE_CORE_LOGIN_EXPERIENCE_V2 = 'off'
az login --tenant $tenantId --use-device-code --allow-no-subscriptions
az account list --all --query "[?tenantId=='$tenantId'].{id:id,name:name,state:state}" --output table
```

Select a real, enabled subscription only after discovering it and confirming the
target. A tenant-level account returned by `--allow-no-subscriptions` is not a
billable Azure subscription. An empty subscription list does not, by itself, prove
that Fabric is unavailable.

Before any resource operation, compare the authenticated tenant with the target
Tenant ID. Do not silently fall back to the normal CLI profile, a different SDK
credential, or a previously cached Fabric CLI account.

The Fabric CLI, SDKs, MCP servers and browser can have independent sign-in sessions.
Changing `AZURE_CONFIG_DIR` isolates Azure CLI; it does not switch those other tools.
Never print or save access tokens in project files.

## Fabric sign-in

Open the tenant-specific portal URL in `resource_ids.md` and use the recorded
sign-in account. Confirm the account and tenant in the portal. Complete any first
sign-in password change or MFA interactively.

Then inspect accessible workspaces and capacities using read-only API calls. Do not
start a trial, create or resume a capacity, create a workspace, or grant permissions
as part of connectivity discovery without a separate approved request.

## References

- [Azure CLI configuration and AZURE_CONFIG_DIR](https://learn.microsoft.com/en-us/cli/azure/azure-cli-configuration)
- [Azure CLI tenant-specific sign-in](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-interactively#sign-in-with-a-different-tenant)

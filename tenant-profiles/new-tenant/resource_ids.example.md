# Separate tenant profile - resource IDs

> Copy to `resource_ids.md` in this directory. The copy is gitignored.
> This profile is opt-in: it does not replace any brain's active configuration.
> Never copy resource IDs or deployment state from another tenant into this profile.

## Tenant identity

| Property | Value |
|----------|-------|
| Tenant ID | `<YOUR_TENANT_ID>` |
| Tenant domain | `<YOUR_TENANT_DOMAIN>` |
| Display name | `<YOUR_TENANT_DISPLAY_NAME>` |
| Sign-in account | `<YOUR_SIGN_IN_ACCOUNT>` |

## Azure

| Property | Value |
|----------|-------|
| Subscription ID | `<NOT_YET_DISCOVERED>` |
| Subscription name | `<NOT_YET_DISCOVERED>` |
| Resource group | `<NOT_SELECTED>` |
| Region | `<NOT_SELECTED>` |

## Fabric

| Property | Value |
|----------|-------|
| Portal | `https://app.fabric.microsoft.com/?ctid=<YOUR_TENANT_ID>` |
| Capacity ID | `<NOT_YET_DISCOVERED>` |
| Capacity ARM ID | `<NOT_YET_DISCOVERED>` |
| Capacity name / SKU / region / state | `<NOT_YET_DISCOVERED>` |
| Workspace IDs | `<NOT_YET_DISCOVERED>` |
| Item IDs | `<NOT_YET_DISCOVERED>` |

## Scheduled capacity start (optional)

Populate only if the user approves a startup schedule. Keep the Fabric capacity
GUID separate from its ARM resource ID.

| Property | Value |
|----------|-------|
| Workflow / ARM ID / state | `<NOT_CONFIGURED>` |
| Trigger | `<NOT_CONFIGURED>` |
| Schedule and time zone | `<NOT_CONFIGURED>` |
| Next occurrence observed | `<NOT_OBSERVED>` |
| Managed identity principal ID | `<NOT_CONFIGURED>` |
| Custom role and role assignment IDs | `<NOT_CONFIGURED>` |
| Role assignment scope and allowed actions | `<NOT_CONFIGURED>` |
| Automatic stop | `<NOT_CONFIGURED>` |

Record evidence separately for an already-active no-op and an actual resume.
A weekday start schedule does not imply an overnight or weekend stop.

## Other brains

Foundry and Database resources are not configured by this profile yet. When needed,
record their target-tenant resources using the shapes in
[Foundry resource IDs](../../Foundry-Brain/resource_ids.example.md) and
[Database resource IDs](../../Database-Brain/resource_ids.example.md).

## Connectivity evidence

Record the date, identity, operation and result of each read-only connection attempt.
A reachable sign-in page is not proof of authenticated API access. Empty lists do
not prove permission to create resources.

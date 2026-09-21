# Fabric App tenant migration — identity, publication and proof

Companion to [instructions.md](instructions.md), Mode 3. Read **before** redeploying an
existing app to another tenant or workspace. Observed with Rayfin **1.34.0**, MSAL browser
**5.19**, Vite 7 and Edge on Windows, **2026-09-21**. Re-check CLI behaviour on other versions.
The evidence below is from one Zava deployment, not a guarantee for every tenant or policy.

## 1. Approve the destination once; include the application

Present the tenant, expected login, subscription, capacity name/SKU/region and workspace.
Keep real values in ignored configuration and state, never in this brain. Reuse that approved
decision on retries; ask again only if scope, cost, permissions or destination must change.
Do not turn cache layout or token-storage choices into questions for a non-specialist user.

Inventory the **existing repository**, not just the backend deployment list: frontend,
Rayfin AppBackend, SPA registration, consent, callback pages, build variables and downstream
Fabric/Foundry bindings. An existing app is part of a whole-project migration unless the
user explicitly excludes it. A report URL or workspace URL is not the application URL.

Preserve the old deployment. Do not reset successful backend state when resuming app
publication. Keep application provisioning resumable: persist a new registration's client
and object IDs immediately, before consent or hosting can fail. On rerun, reject an
ambiguous registration or a state file belonging to another target rather than replacing it.

## 2. Prove identity and connectivity independently

- Check the selected Azure CLI account's tenant **and** subscription. Read the actual Fabric
  workspace, its assigned capacity and the referenced item IDs using an authenticated request.
  For each app binding, verify the intended workspace explicitly; hosting and data may be in
  different workspaces when that is the approved design.
- Azure CLI, Rayfin and the browser have **separate caches**. A correct Azure CLI account
  does not prove Rayfin or Edge selected it. In this migration the CLI was on the new tenant
  while Rayfin retained an expired login for the old one.
- Rayfin 1.34 documents `RAYFIN_TOKEN`. A wrapper successfully supplied a fresh Fabric-audience
  token acquired for the approved tenant in the **child environment**, together with
  `RAYFIN_TENANT_ID`, `RAYFIN_WORKSPACE_ID`, `--tenant` and `--workspace-id`. Validate the
  acquisition result's tenant; never print, persist or pass the token on the command line.
  Clear inherited overrides in the child only, not the user's global environment.
- A tenant-specific Azure CLI cache can isolate future workflows, but do not claim it was
  configured merely because the current default cache happens to be correct.
- A TCP/TLS timeout **before any HTTP response is not an authentication diagnosis**. Compare
  the same API request from the tool and browser. A cached portal tab or reachable Graph
  endpoint does not prove Fabric is reachable. An HTTP 404 at the API root proves a response,
  not successful authorization; use a real authenticated operation as the deployment gate.
  Follow the organization's network policy; do not prescribe disabling VPN or protection.

## 3. Release a colliding Rayfin name alias without deleting the old app

In Rayfin 1.34, `resolveExistingDeployment` reads the **normalized workspace-name key**
before falling back to a workspace-ID lookup. Thus explicit tenant/workspace flags alone
do **not** prevent reuse of an old `fabricItemId` when two workspaces share a name.

The observed failure named the new tenant/workspace but logged
`Redeployment detected — reusing Rayfin item <old-item>`, followed by HTTP 404:
`Could not found the requested item`. This was a local registry collision, not missing consent.

Before `rayfin up`:

1. Back up the ignored `rayfin/.deployments.json`; use the installed version's name
   normalization, not an assumed slug algorithm.
2. If the target name alias belongs to another tenant/workspace, retain its complete record
   under a tenant/workspace-qualified key, for example `<slug>--<tenant>--<workspace>`.
3. Remove **only the conflicting name alias**. If `active` pointed to that alias, move it to
   the preserved key. Keep unrelated aliases and old remote resources untouched.
4. Run with the explicit approved target. After provisioning and after publishing, assert
   that the active record's tenant, workspace and item belong to that target.
5. On rerun, reuse the matching new-target record. Test both collision recovery and reuse;
   a fix that creates another AppBackend every time is not idempotent.

Do not patch `node_modules`, delete the old cloud app, or rotate credentials to fix this.
The observed retry created the new item and the following pass reused **that** item.

## 4. Bind the SPA, not just Rayfin's own authentication

For the observed browser-to-Fabric/Foundry architecture, use a dedicated **single-tenant SPA**
registration in the destination, without a client secret. Rayfin's opaque service session
is not a Fabric/Power BI/Foundry access token. Follow the auth implementation selected at
bootstrap, rather than debugging an unused SDK path.

**Fabric and Power BI share an API service principal; Foundry does not.** Discover resource
principals and enabled delegated scopes by resource URI, not by a guessed display name or
copied app ID. The Foundry audience resolved to Azure Machine Learning Services in this tenant.

| Token resource / audience | Observed delegated scopes for this app |
|---|---|
| `https://api.fabric.microsoft.com` | `Item.Read.All`, `DataAgent.Execute.All` |
| `https://analysis.windows.net/powerbi/api` | `Dataset.Read.All` |
| `https://ai.azure.com` | `user_impersonation` |

These are a tested set for the exercised calls, **not** universal permission requirements.
Request separate tokens per audience. Do not combine multiple resources' `.default` scopes
in one authorization request or `extraScopesToConsent`. A first-party Azure CLI token working
does not prove the custom SPA has consent.

The authorized deployment created `oauth2PermissionGrants` with `consentType: Principal`
for the deploying user only. Preserve existing grants and redirect entries; request only
needed additions. This does not authorize every future user. Do not silently replace this
with `AllPrincipals` or broaden roles after a denial; use the approved consent/RBAC process.

Rayfin `services.auth.allowedRedirectUris` and Entra `spa.redirectUris` are **different lists**.
Obtain the real hosting URL from deployment output; do not construct it. The tested SPA
registered both the origin and `<origin>/blank.html`. Its popup uses `/blank.html`, a built
callback entry that invokes MSAL v5's redirect bridge — not an empty file or the SPA router.
Verify the callback is actually served; [known issues #11 and #16](known_issues.md) explain why.

## 5. Make ordinary browser use the acceptance path

- Filter cached accounts to the configured **resource tenant** before selecting an active
  account; do not take the first cached account. Validate the tenant of interactive results too.
- Use an account picker for explicit sign-in. Reserve a fresh-credential prompt for an
  actually rejected session; do not force every user to reauthenticate on every visit.
- Keep existing cache/storage policy unless changing it is a deliberate, reviewed requirement.
  The tested fix retained `sessionStorage`; it did **not** require moving tokens to `localStorage`.
- Do not log out unrelated Microsoft sessions, clear the user's whole browser profile, or
  prescribe permanent InPrivate use. MFA, conditional access and session expiry still apply.
- Test the standalone hosting URL in normal Edge. Portal iframe authentication is a distinct
  gate; standalone success does not prove embedded silent SSO works.

## 6. Rebuild against destination state, then publish

Derive all app-owned IDs/endpoints from the approved configuration and current deployment
state. Do not copy a previous app's `.env.*`, SPA client ID or Foundry endpoint.

Vite mode-specific `.env.production.local` overrides `.env.local`; therefore an old
mode-specific `VITE_RAYFIN_*` / `VITE_FABRIC_*` setting can defeat freshly generated Rayfin
values. Back up the files, update owned business bindings, and remove stale **owned** overrides
so the new Rayfin `.env.local` values win. Do not erase unrelated application configuration.
Check inherited process-level `VITE_*` overrides as well. Treat all client-bundle values as
public; no secret belongs there.

The observed sequence was:

1. `rayfin up` with explicit tenant/workspace and `--exclude-services staticHosting`.
2. Validate the active target and generated environment.
3. Run `rayfin up` again, including the configured production build and static upload.
4. Read the generated hosting URL, preserve/extend the SPA redirect array, and verify the
   served origin, callback and diagnostic route before giving the URL to the user.

Do not publish an old `dist` with `--skip-build`. On Windows, use `npm.cmd` when the
PowerShell `npm.ps1` shim is blocked, rather than changing execution policy. Keep secrets
out of command output; resolve the installed CLI rather than silently installing another version.

## 7. Keep deployment and verification as separate gates

| Gate | Required evidence |
|---|---|
| Offline | Existing backend/frontend tests and production build; pre-existing lint failures reported separately |
| Hosting | Real generated URL; served HTML, callback and assets match the fresh build, preferably by byte hashes |
| Bindings | Expected destination IDs/endpoints in the served bundle; no former owned bindings; no secrets |
| API | Actual screen queries, not unrelated sample DAX; check result bodies as well as HTTP status |
| Browser | Expected account, distinct token audiences, real data on each relevant screen, no JS failures |
| Assistant | Newly typed uncached question, actual authenticated request, rendered answer and observed source/tool trace |
| Handoff | URL and expected login, measured successes, remaining manual steps and any untested modes |

CLI-token API probes do not prove SPA consent, sign-in or CORS. A recorded answer or a labelled
repository example does not prove the new tenant's live assistant. Never inject CLI tokens or
mock responses into the browser and then call that an end-to-end authentication test.

For a supervised Edge session, use a native viewport rather than a fixed emulated size;
see [frontend known issue #22](../app-frontend-agent/known_issues.md).
Keep transient failures in the record: the initial combined Foundry request hit the remote
MCP tool's 100-second timeout; the subsequent full routing probes passed. This run did not
establish the exact cause of the transient timeout. The existing
[Fabric bridge recovery note](../../../Foundry-Brain/agents/foundry-fabric-bridge-agent/known_issues.md)
owns diagnosis; do not rewrite consent or connections just because one call is slow.

## 8. Evidence and limits — 2026-09-21

- New deployment on an approved **F8 / Sweden Central** capacity; old app retained. This is
  one observed configuration, not a general availability or minimum-SKU promise.
- Nine served assets matched the freshly built files by SHA-256; eight destination bindings
  were present and their former values absent.
- 312 Python tests and 124 frontend tests passed. Nine screen DAX queries and two graph
  dossier scopes succeeded; the app's Fabric assistant **POST** returned HTTP 200.
- Normal Edge interactive sign-in succeeded without injecting external tokens. The diagnostic
  confirmed the expected account, both Fabric/Power BI audiences and real model data.
- All seven tested routes rendered without JavaScript page errors. A new combined question
  returned HTTP 200 in **75.4 seconds**, rendered both data and contract sources, and agreed
  with the scenario. Three independent backend routing probes also passed.
- The user subsequently confirmed the site worked in their ordinary Edge session. InPrivate
  was not the solution. Portal iframe behaviour, every optional live walkthrough interaction,
  and manual task-flow import were **not** all verified.

Raw traces stay in the consuming project's local evidence/state, not this public knowledge
base. Preserve dated outcomes and limitations here, never real tenant IDs, logins, hosting
addresses, access tokens or screenshots containing account details.

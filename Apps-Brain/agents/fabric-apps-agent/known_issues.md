# Known Issues & Gotchas — Fabric Apps Agent (Rayfin, Preview)

> Status: **Preview** (launched Build 2026-06-02). Behaviour, regions, and package
> names may change. Re-verify against `aka.ms/rayfin` and the Fabric Updates Blog.

---

## Tenant Admin Settings

Enable in **Fabric Admin Portal → Tenant settings** before scaffolding/deploying:

| Setting | Required For | Default |
|---------|-------------|---------|
| Fabric Apps (preview) | App item creation + deploy | Off (preview) |
| (optional) Purview policies | Governance/lineage carry-through | Tenant-dependent |

> After enabling, allow a few minutes for propagation before the first `npx rayfin up`.

---

## Common Issues

### 1. App item does NOT appear after deploy

**Symptom**: `npx rayfin up` reports success but no **App** item shows in any workspace.

**Root causes (in order of likelihood)**:
- **Unsupported region** — at launch, regions with **suffix `8`** are not available;
  some users also hit issues in West US 3 / East US 2.
- `Fabric Apps (preview)` tenant setting is **off** (or not yet propagated).
- Deployed to the wrong tenant/workspace (check the signed-in account).

**Fix**: Move the capacity to a supported region, confirm the preview setting is on,
re-verify the target workspace, then re-run `npx rayfin up`.

> This is **almost always a region issue**, not a config error. Check region first.

---

### 2. Sign-in fails after deploy

**Symptom**: Users can't authenticate to the deployed app.

**Cause**: Entra app / tenant mismatch, or brokered auth provider misconfigured.

**Fix**: Verify `@microsoft/rayfin-auth-provider-fabric` config and that users sign
in with an Entra account in the **same tenant** as the Fabric workspace. Per-user
access reflects the data they're entitled to — empty results can mean correct
governance, not a bug.

---

### 3. Data not in OneLake after deploy

**Symptom**: App deployed but its tables don't appear in OneLake.

**Cause**: Deploy incomplete / partial provisioning.

**Fix**: Re-run `npx rayfin up`, inspect CLI logs for the failing step
(DB → auth → APIs → hosting). Provisioning is idempotent — re-running is safe.

---

### 4. CLI / scaffold fails

**Symptom**: `npm create @microsoft/rayfin@latest` or `npx rayfin ...` errors.

**Causes**:
- Node.js/npm not installed or too old.
- Network/proxy blocking the npm registry.
- Not signed in to the Fabric tenant.

**Fix**: Verify Node + npm, sign in to the correct tenant, retry. Use the
`todo-local-experimental` template to validate the toolchain offline first.

---

### 5. Confusing Fabric Apps with Custom Workloads

**Symptom**: Reaching for the iFrame SDK / Workload Hub when the goal is an app backend.

**Fix**: Rayfin/Fabric Apps = **application backend** (DB, auth, APIs, hosting, OneLake
data). Custom workloads (iFrame SDK, React components, Workload Hub) are a different
extensibility surface owned by `extensibility-toolkit-agent`.

---

### 6. `rayfin init` reports success and writes almost nothing

**Symptom**: `rayfin init` prints the whole ceremony (`Copying template files`,
`Project created successfully`) and **exits 0**, but the target holds only the Rayfin
scaffolding — `rayfin.yml`, `AGENTS.md`, `.mcp.json`, the skill. **No `package.json`, no
`index.html`, no `src/`.** Nothing in the output can be grepped for.

**Root cause**: a **non-ASCII character anywhere in the target path**. Isolated one variable
at a time: a plain temp path works; a temp path with spaces and dashes works, so it is not the
name shape; a path containing `é` produces the empty scaffold, both inside a repo and under
`%TEMP%`.

**Fix**: scaffold under an ASCII-only path, then `robocopy /E /XD node_modules` into the real
location. `npm install`, `tsc -b`, `vite build` and the entire `rayfin up` pipeline are
**unaffected** by the same accented path — only `init` is.

**Evidence**: four runs changing one variable each time, with a file listing of the target
after each. Observed 2026-08.

---

### 7. `rayfin up` exits 1 on a fully successful deploy

**Symptom**: the deploy works and the app serves, and the command still returns **exit code 1**
with `RemoteException` lines in the output.

**Root cause**: npm audit advisories fold into the exit code. `npm run` behaves the same way.

**Fix**: **verify the artefact, never the exit code.** Fetch the hosting URL, confirm the new
asset hash in `index.html`, then grep the served bundle for a string only the newest build can
contain. Any CI gate written on the exit code reports a false failure on every green deploy.

**Evidence**: repeated deploys, each exiting 1, each serving a newly hashed bundle confirmed by
fetching it. Observed 2026-08.

---

### 8. Renaming the app silently creates a *second* AppBackend

**Symptom**: editing the name in `rayfin.yml` does nothing at all on the machine that deployed.

**Root cause**: `id:` — **not** `name:` — drives the AppBackend displayName, and the CLI calls
`getOrCreateRayfinItem(workspaceId, displayName)`, which **creates** an item when the name is
not found. `rayfin/.deployments.json` is gitignored and pins `fabricItemId` under the sanitized
workspace name, so locally the deploy short-circuits to the existing item and the edit is a
silent no-op.

**Fix**: rename in this order — `PATCH /v1/workspaces/{ws}/items/{id}` on the live item, read it
back to verify, then align `id:` and `name:` to that exact string. Hosting URLs are stable per
item and are auto-appended to `allowedRedirectUris` after the first deploy, so a second item
also means a second URL to register.

**Status**: the local no-op is **observed**. The duplicate item on a fresh clone is **read from
the CLI source, not reproduced** — the create-if-absent call is there, but we did not deploy
from a second clone to watch it happen.

---

### 9. `data.enabled: true` provisions a SQL Database nobody asked for

**Symptom**: a `SQLDatabase` and a `SQLEndpoint` appear in the workspace beside an app that only
reads a Lakehouse.

**Root cause**: the CLI logs *"No entity classes found — skipping database configuration"*, which
only skips **applying the DAB schema**. The items are created regardless.

**Fix**: setting `data.enabled: false` on a later deploy does **not** remove them.
`DELETE /v1/workspaces/{ws}/items/{id}` does, and deleting the database takes its endpoint with
it. An app that reads a Lakehouse through a semantic model or a data agent needs neither — set
`data.enabled: false` from the **first** deploy.

**Evidence**: both items present in the workspace after a deploy that logged the skip message;
removal confirmed by DELETE. Observed 2026-08.

---

### 10. Rayfin session tokens cannot call Fabric — the app runs its own MSAL

**Symptom**: the user is signed in, `isAuthenticated` is true, and every call to
`api.fabric.microsoft.com` still fails.

**Root cause**: Rayfin Fabric Auth exchanges the portal handoff for **opaque Rayfin session
tokens**. They authorize the app's own services; they do **not** authorize Fabric. The docs say
to gate UI on `isAuthenticated` and stop there, which reads as though the token were usable
downstream.

**Fix**: bring your own Entra app registration and MSAL, and choose the implementation **once**
at bootstrap. In production the Rayfin embedded-auth path is then dead code — which is the
intended outcome, not a smell.

**Consequence**: any reasoning about `initEmbeddedAuth` must start from MSAL. Reading the SDK
auth path first cost a full debugging cycle on code that never runs.

---

### 11. The MSAL v5 popup comes back and nothing happens

**Symptom**: the popup opens, the user **picks an account** — so Entra accepted the request —
and then the popup just sits there showing the app's own sign-in card. `loginPopup()` never
resolves and eventually throws `BrowserAuthError: timed_out`, subcode `redirect_bridge_timeout`.
It reads as a broken redirect URI or a consent problem. **It is neither.**

**Root cause**: MSAL v5 **no longer polls the popup's URL**. `waitForBridgeResponse()` opens a
`BroadcastChannel` and waits; the landing page must publish to it by calling
`broadcastResponseToMainFrame()` from `@azure/msal-browser/redirect-bridge`. **A genuinely blank
redirect page is a dead end** — it broadcasts nothing, so the opener times out. The prebuilt UMD
bundle does not self-execute either; it only assigns the export.

**Diagnostic tell**: the popup's `document.title` stays the app's own title. If the bridge had
run it would have renamed the document. **Title unchanged ⇒ the bridge never executed** — check
that before suspecting auth.

**Fix**, three parts, all required:
- `redirectUri` must **not** be the app root, or the popup boots the router and the router
  discards the response fragment.
- That landing page must be a **Vite build entry**, not a `public/` file: `public/` is copied
  into `dist/` *after* the build and silently overwrites what `rollupOptions.input` produced.
- Guard `main.tsx` anyway: before `createRoot(...).render(...)`, if `window.location.hash`
  matches `/(^|[#&?])(code|error|state|id_token)=/`, import the bridge, broadcast, and do
  **not** mount the router. Four lines, and it covers the case where the host rewrites an
  unknown `.html` path to `index.html`.

**Also**: MSAL 5.19 removed `auth.navigateToLoginRequestUrl` and `cache.storeAuthStateInCookie`.
Both now fail the build with `TS2353`.

---

### 12. Inside the Fabric portal the app runs in a cross-origin iframe

**Symptom**: a permanent "Loading…" spinner when the app is opened from the portal (which passes
`?fabricEmbedded=true`), while the identical build works in a standalone tab.

**Root cause**: `ssoSilent` **cannot succeed when framed** — a nested iframe to Entra is
third-party/partitioned storage — and it never settles. Awaited inside a `.finally()`, the
loading flag never clears.

**Fix**: detect the frame by attempting `window.top.location.href` — the `SecurityError` **is**
the proof, so return `true` on throw — and skip `ssoSilent` in that case. Then wrap every
startup await in a timeout with a small budget, and on timeout surface a visible warning plus an
"open in a new tab" escape hatch. **A hang that reports itself is recoverable; a spinner is
not.**

**Status**: the exact non-settling promise was **never identified** — the portal host cannot be
simulated in dev — so the fix is deliberately defensive rather than specific. Whether
`loginPopup()` succeeds **in-frame** is **unproven**; the standalone URL is the only proven path.

---

### 13. The hosted bundle is public, and so is everything inlined into it

**Symptom**: none. That is the problem.

**Root cause**: the hosting URL returns **200 with no credentials at all**. A Fabric Data App has
exactly three child services — SQL Database, Authentication, Static Content — exposing only
`/api/graphql`, `/auth`, `/storage`. There is **no server surface** on which to hide a value, and
`@microsoft/rayfin-functions` calls itself experimental in its own README and has no
child-service row in the portal: **do not build a demo on it.**

**Fix**: treat every `VITE_*` value as published — ids and endpoints are usually acceptable, a
secret never is. And confirm the values are **actually inlined in the served bundle**: a missing
client id does not raise, the auth-configured flag simply evaluates false, and the app ships with
authentication *silently disabled*. That looks like a working app until someone asks it for data.

**Note**: `rayfin env` rewrites `.env.local` on every `predev`/`prebuild` and it carries a
do-not-edit header. App variables belong in `.env.production.local` /
`.env.development.local` — gitignored, higher Vite precedence, never touched by Rayfin.

---

### 14. Two audiences, one service principal — the wrong one returns 401

**Symptom**: a token that works against Fabric REST returns **401 with an empty body** from
`executeQueries`. An empty-bodied 401 reads as an expired token and sends you diagnosing auth.

**Root cause**: the resources all resolve to the **Power BI Service** principal, but they are
**separate audiences and need separate `acquireToken` calls**:

| Audience | Used for |
|---|---|
| `https://api.fabric.microsoft.com` | Fabric REST (`GET /v1/workspaces/{ws}/items`), MCP routes |
| `https://analysis.windows.net/powerbi/api` | `executeQueries` — and nothing else works there |
| `https://ai.azure.com` (`user_impersonation`) | the Foundry agent endpoint |

**Fix**: `az account get-access-token --resource https://api.fabric.microsoft.com` returns
`scp: user_impersonation`, but **only because the Azure CLI is a pre-authorized first-party
client** — a custom SPA cannot follow that precedent. Request the granular delegated scopes
(`Item.Execute.All`, `Item.Read.All`, `Workspace.Read.All`, `Dataset.Read.All`) with admin
consent. The feared `AADSTS65002` did **not** materialise once they were consented; the token
came back carrying all four in `scp`. Register as **SPA** (no secret), `signInAudience:
AzureADMyOrg`, and when adding redirect URIs **PATCH the full array** — `spa.redirectUris`
replaces, it does not merge.

**Trap**: **a successful CORS preflight proves only that the endpoint accepts cross-origin
requests.** It says nothing about whether an authenticated POST will succeed, nor whether the
registration can obtain the token at all. Every endpoint used here preflighted clean, including
`executeQueries` (which omits `Access-Control-Allow-Methods` — not a blocker, POST is safelisted).

**Evidence**: DAX executed from the browser end to end once the audiences were separated.
`executeQueries` takes **one query per request — it is not a batch endpoint.** Observed 2026-08.

---

### 15. Assuming the app must live in the same workspace as its data

**Symptom**: a plan to move, copy or re-provision a Lakehouse, semantic model or data agent
because the app is being hosted on a different capacity.

**Fix**: it does not have to move. The app is a static SPA calling Fabric from the browser with
the signed-in user's **own** token, so hosting is independent of the data plane: an app hosted on
one capacity read the items of a workspace on a **different capacity in a different region**, and
executed DAX against it. Hosting the app elsewhere is not a reason to touch the data platform,
and the cross-region hop is invisible to the user.

This is the main practical difference from a server-backed app, where the backend's region and
the data's region are usually argued about together.

**Evidence**: item enumeration and `executeQueries` issued from the browser of an app hosted in
one region against a workspace in another. Observed 2026-08.

---

### 16. Sign-in works on localhost and breaks after deploy — the redirect URI is a chicken-and-egg

**Symptom**: Entra returns a `redirect_uri` mismatch only once the app is hosted. Locally it
was fine, so the auth config "obviously" works and the deploy gets blamed.

**Root cause**: `rayfin.yml → services.auth.allowedRedirectUris` has to list the **deployed
origin**, and that origin is only knowable *after* the first deploy. Rayfin mints it as
`https://<slug>-<hash>-<region>.webapp.fabricapps.net`, where `<hash>` is assigned at
provisioning time. You cannot pre-declare it and you cannot derive it.

**Fix**: accept two passes. Deploy once to obtain the URL, add it to `allowedRedirectUris`,
redeploy. Then keep **all three** origins listed permanently:

```yaml
allowedRedirectUris:
  - http://localhost:5173
  - http://127.0.0.1:5173          # a DIFFERENT origin to Entra — list both
  - https://<slug>-<hash>-<region>.webapp.fabricapps.net
```

`localhost` and `127.0.0.1` are not interchangeable here: Entra matches the string, so a dev
who opens the other one gets the same mismatch on a machine where it "works".

**Evidence**: `rayfin.yml` of an app deployed to Sweden Central carrying exactly these three,
after the first deploy failed sign-in with only the two local ones. Observed 2026-08.

> Related but distinct: **#8** — redirect URIs are also *auto-appended* per item, so a rename
> that creates a second AppBackend leaves the first item's URI behind on the wrong app.

---

### 17. `manifest.json → tokens[]` is how build-time values reach a static bundle — and it is extensible

**Symptom**: the SPA needs Fabric IDs (workspace, item, portal URL) at runtime. The reflex is
to hardcode them, or to add `VITE_*` variables and wire a second substitution mechanism.

**Root cause**: Rayfin already has one. `manifest.json` declares placeholder tokens that the
build substitutes into the emitted bundle. What is not obvious is that the array is **not a
fixed Rayfin vocabulary** — a project can add its own:

```jsonc
"tokens": [
  "__RAYFIN_API_URL__", "__RAYFIN_PK__",        // Rayfin's own
  "__FABRIC_ITEM_ID__", "__FABRIC_WORKSPACE_ID__", "__FABRIC_PORTAL_URL__"
]
```

**Fix**: declare the token in `manifest.json`, reference the placeholder in source, let the
build replace it. One mechanism instead of two.

**⚠️ Same blast radius as `VITE_*`**: substitution happens at **build**, into a bundle that is
served publicly. A token is a *build-time constant in public source*, never a secret. See
**#13** — everything inlined into the hosted bundle is public.

**Adjacent**: point `staticHosting.buildCommand` at a **Fabric-specific script**
(`npm run build:fabric`), not the plain dev build. That script is where the `rayfin env`
prebuild step runs, so a build invoked by any other path ships unsubstituted placeholders.

**Evidence**: `manifest.json` + `rayfin.yml` of a deployed app carrying three custom
`__FABRIC_*` tokens alongside Rayfin's two, with `buildCommand: npm run build:fabric`.
Observed 2026-08.

---

## Positioning Cautions (Preview)

- **No committed GA date** — never promise GA timelines to customers.
- **Region constraints** at launch — confirm availability before committing to a demo.
- **Replit × Fabric** is **public beta** — early access may be required.
- Apps deploy a **real, governed** Fabric artifact — not a throwaway sandbox; treat
  deployments accordingly (cleanup test apps from the workspace).

---

## Deployment Order (happy path)

```
1. Prereqs   → Node/npm, Fabric capacity, Fabric Apps (preview) ON, supported region
2. Scaffold  → npm create @microsoft/rayfin@latest
3. Model     → define entities (TS decorators) in src/models/*.ts
4. Deploy    → npx rayfin up  (provisions DB · auth · APIs · storage · hosting)
5. Verify    → App item in workspace, data in OneLake, Entra sign-in works
6. Downstream→ hand off to Power BI / notebooks / data agents (other agents)
```

> Never skip the region/preview-setting check (step 1) — it's the #1 cause of
> "App item didn't appear".

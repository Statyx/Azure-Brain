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

# Known Issues — Fabric Extensibility Toolkit

## Critical Limitations

### Private Link Blocks All Workloads
- **Impact**: CRITICAL
- **Description**: When Fabric Private Link is enabled on a tenant, **all custom workloads are blocked** — both dev (DevGateway) and published
- **Workaround**: None. Private Link and custom workloads are mutually exclusive
- **Status**: By design (documented in MS Learn key-concepts)

### Max 10 Items Per Workload
- **Impact**: HIGH
- **Description**: A single workload can define at most 10 item types in its manifest
- **Workaround**: Plan item types carefully. Combine related functionality into fewer items rather than one-item-per-feature
- **Status**: By design (manifest package limit)

---

## Preview Feature Caveats

### CI/CD (Preview)
- Git integration and Deployment Pipelines are **preview** — API surface may change
- Not all Git providers may be supported yet
- Variable Library is new — limited documentation available
- Items must follow the `.platform` + `definition.json` serialization contract

### Remote Lifecycle Notification API (Preview)
- Webhook delivery is **at-least-once** — your backend must be idempotent
- No retry configuration exposed — Fabric handles retries internally
- Webhook must respond within timeout or the notification is dropped
- No batch events — one webhook call per item event
- HTTPS required for webhook endpoint

### Fabric Scheduler / Remote Jobs (Preview)
- OBO token in job request has a limited lifetime — long-running jobs must handle token refresh
- Job status reporting is your responsibility — Fabric doesn't auto-detect completion
- If your backend is down when a job fires, the job fails
- No built-in retry for failed jobs (must be handled by your backend or re-scheduled)

---

## Development Issues

### DevGateway

| Issue | Description | Fix |
|-------|-------------|-----|
| Port conflict | DevGateway default port (5000) may conflict with other services | Change `DEV_GATEWAY_PORT` in `.env.dev` |
| .NET version | DevGateway requires specific .NET SDK version | Check `global.json` in repo for required version |
| PowerShell 7 required | Scripts fail on Windows PowerShell 5.1 | Install PowerShell 7: `winget install Microsoft.PowerShell` |
| Stale cache | Changes not reflected after rebuild | Stop DevGateway → Delete `build/` folder → Rebuild |

### Frontend Development

| Issue | Description | Fix |
|-------|-------------|-----|
| iFrame CORS errors | Cross-origin errors in browser console | Verify Entra app redirect URIs match dev server URL |
| Token acquisition fails | `acquireAccessToken()` returns error | Check Entra app permissions and admin consent |
| Theme not applied | Components render with wrong colors | Ensure `FluentProvider` wraps your component tree |
| Hot reload breaks iFrame | Vite HMR causes iFrame disconnect | Refresh the full Fabric page (not just dev server) |
| **Fluent UI v8 imported** | Wrong component library imported | Use `@fluentui/react-components` (v9), **NEVER** `@fluentui/react` (v8) |
| **Content touches panel edges** | Views have no padding | ItemEditor panels have ZERO padding — views MUST add `padding: var(--spacingVerticalM, 12px)` + `box-sizing: border-box` |
| **Scroll doesn't work** | Content cut off, no scroll | NEVER set `overflow: scroll` on outer container or use `height: 100vh` — ItemEditor manages all scrolling |
| **Nested scroll containers** | Double scrollbars, jumpy scrolling | Only ItemEditor's `.base-item-editor__content` should scroll — don't nest scroll containers |
| **Item reloads on every render** | Unnecessary API calls, UI flicker | Check `pageContext.itemObjectId === item.id` before reloading — prevent re-fetches when ID hasn't changed |
| **Custom ribbon layout** | Inconsistent look, no accessibility | NEVER create custom `<div>` or `<Toolbar>` ribbons — use `Ribbon` + `RibbonToolbar` + `createRibbonTabs()` |
| **Component files modified** | Verification fails, breaks other items | NEVER modify files in `Workload/app/components/` — create item-specific styles in `[ItemName]Item.scss` only |
| **Sample code imported** | Using wrong OneLakeView | Import from `components/OneLakeView`, NEVER from `samples/views/SampleOneLakeView` |
| **OneLakeView empty** | Control shows blank | Provide all 3 fields in `initialItem`: `id`, `workspaceId`, `displayName` |
| **Item not in create dialog** | Users can't create new items | Update BOTH `createExperience.cards` AND `recommendedItemTypes` in `Product.json` |
| **Item not in build** | Item missing after deploy | Update `ITEM_NAMES` in ALL `.env.*` files (`.env.dev`, `.env.test`, `.env.prod`) |

### Authentication

| Issue | Description | Fix |
|-------|-------------|-----|
| OBO token scope error | Token request fails for specific API | Add required scope to Entra app API permissions + grant admin consent |
| Multi-tenant auth fails | Cross-tenant users can't authenticate | Entra app must be registered as multi-tenant app |
| Token expired during long operation | API calls fail mid-operation | Implement token refresh logic, don't cache tokens long-term |
| Consent prompt loop | Users repeatedly prompted for consent | Grant admin consent for all required scopes in Entra portal |

### Manifest & Packaging

| Issue | Description | Fix |
|-------|-------------|-----|
| Name mismatch | Workload doesn't load | Ensure `<Name>` in XML matches `"name"` in JSON exactly |
| Icon not showing | Item appears without icon | Check asset paths, file exists in `FE/assets/`, size ≤1.5MB |
| Package too large | Build fails at packaging | Optimize assets, check for accidentally included files |
| Template variables not resolved | `{{VAR}}` appears in deployed manifest | Check `.env.*` file has the variable defined |
| Editor path wrong | Item opens blank | Verify `"editor.path"` in item JSON matches React route |

---

## Tenant Configuration Issues

| Issue | Description | Fix |
|-------|-------------|-----|
| Workload not visible | Item types don't appear in "New" menu | Enable "Users can develop Fabric workloads" in Admin Portal |
| Published workload not visible | Uploaded NuGet not showing | Enable "Users can use workloads published by the organization" |
| Security group scoping | Only some users can see workload | Check tenant setting security group configuration |
| Capacity required | Workload fails to load | Ensure workspace has Fabric capacity (Trial or F2+) assigned |

---

## Debugging Checklist

When a workload doesn't work:

1. **Check Admin Portal**
   - [ ] Developer mode enabled?
   - [ ] Published workloads enabled? (for NuGet uploads)
   - [ ] Correct security groups configured?

2. **Check Entra App**
   - [ ] App ID matches in manifest + `.env.*` + Admin Portal?
   - [ ] Redirect URIs correct for dev/prod?
   - [ ] Required API permissions granted?
   - [ ] Admin consent applied?

3. **Check Manifest**
   - [ ] WorkloadName matches between XML and JSON?
   - [ ] Item names match between XML and JSON?
   - [ ] Editor paths match React component routes?
   - [ ] Icons exist at referenced paths?

4. **Check DevGateway**
   - [ ] PowerShell 7 (not 5.1)?
   - [ ] .NET SDK installed?
   - [ ] DevGateway running without errors?
   - [ ] No port conflicts?

5. **Check Frontend**
   - [ ] Dev server running (`StartDevServer.ps1`)?
   - [ ] Browser console for iFrame errors?
   - [ ] Network tab for failed API calls?
   - [ ] Fluent UI v9 (not v8)?

6. **Check OneLake**
   - [ ] Workspace has capacity?
   - [ ] User has write permissions?
   - [ ] Item definition saved to `.pbi/` folder?
   - [ ] Private Link NOT enabled?

---

## Performance Considerations

- **iFrame load time**: Minimize bundle size — use code splitting and lazy loading
- **Token caching**: Cache OBO tokens for their lifetime (typically 1 hour) — don't request on every API call
- **OneLake operations**: Batch small writes — OneLake DFS performance is better with fewer, larger operations
- **Asset optimization**: Icons and images count toward the 1.5MB/15 asset limits — optimize aggressively

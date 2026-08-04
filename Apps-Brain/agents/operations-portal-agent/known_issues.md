# Known Issues — operations-portal-agent

Embed / token / Kusto / run gotchas for the external operations portal, with fixes.

---

## Fabric Embed (RTI dashboard)

### 1. Tiles error "Cannot read properties of null (reading 'token')" / "An error occurred"
- **Cause**: the embedded RTI tiles query the Eventhouse and need a **Kusto data-plane** token, but
  the app registration only had `Fabric.Embed` + `KQLDashboard.Read.All` → the `accessTokenProvider`
  callback can't mint a Kusto token → null.
- **Fix**: add delegated **Azure Data Explorer `user_impersonation`** (resource appId
  `2746ea77-4702-4b45-80ca-3c97e680e8b7`) to the app registration + admin-consent. The Kusto resource
  that works is `https://kusto.kusto.windows.net` (ADX), **not** the cluster URI.
- **Pre-warm** the Kusto consent **within the click gesture** (interactive `getToken`), then use a
  **silent-only** resilient `accessTokenProvider` (honors requested scopes, falls back to the Fabric
  token, never opens a blocked background popup). Log requested scopes to `window.__ftok` for F12
  diagnosis.

### 2. Only Real-Time Dashboards are embeddable (preview)
- Power BI reports use the `powerbi-client` path (app-owns-data). RTI/KQL dashboards use
  `@microsoft/fabric-embed` (MSAL delegated). Don't try to embed a Power BI report via the Fabric
  Embed SDK or vice-versa.

### 3. Fabric API scopes come from the Power BI Service SP
- The `Fabric.Embed` / `KQLDashboard.Read.All` delegated perms are exposed by the **Power BI Service**
  SP (`00000009-...`), **not** a separate Fabric SP. `az ad app` may lack `--spa-redirect-uris` → set
  `spa.redirectUris` via a Graph PATCH on the application object.

---

## Backend tokens

### 4. Intermittent 502 on chat / embed-token
- **Cause**: credential/`az` token acquisition is slow or transient-fails.
- **Fix**: cache tokens per scope with a lock; on refresh failure, reuse a not-yet-expired cached
  token; pre-warm Fabric + Power BI tokens at startup; expose `/api/health` + an admin
  `refresh-tokens` endpoint.

### 5. Data Agent returns stale answers / skips the query pipeline
- **Cause**: Fabric reuses one thread per agent/user; after ~50 messages it degrades.
- **Fix**: DELETE the thread before each question (api-version only, no `stage`), then POST a fresh
  thread. Thread recycling every-Nth FAILS (cascading 404 + "queued" hangs) — delete every time.

### 6. Chat DAX 404
- `executeQueries` must target `api.powerbi.com`, not `api.fabric.microsoft.com`.

### 7. Accented chat body → 400 "error parsing body"
- Only affects server-side callers (e.g. PowerShell `Invoke-RestMethod`). Send UTF-8 bytes +
  `charset=utf-8`. The browser `fetch` in the frontend is unaffected.

---

## Kusto (portal-native live views)

### 8. `/api/floorplan` KQL 400 General_BadRequest
- The Fabric **trident** Kusto endpoint rejects: (a) `where col in (dynamic_var)` — needs a literal
  list; (b) a multi-`let` where the final expression JOINs two lets and projects a pivot column.
- **Fix**: write an **all-inline** pipeline — `join kind=inner (subquery) | summarize avgif(...) by
  key | join kind=leftouter (subquery peaks) on key | project`. `avgif` over the latest-timestamp
  rows gives the latest value with a known schema (no pivot).

### 9. Live view shows calm values
- If the event data ends earlier in the day, "Live" shows end-of-day calm values. Provide a
  "Peak of day" mode (always shows the storyline) and run the live injector during a demo to animate
  the real-time path.

---

## Run / restart

### 10. Port 8000 already in use after a restart
- Kill the stale PID first: `Get-NetTCPConnection -LocalPort 8000` → `Stop-Process`, then re-run
  `uvicorn main:app --host 127.0.0.1 --port 8000`. Use `--reload` only in dev.

### 11. Sync terminal jams (no output)
- The persistent PowerShell terminal can jam. Recover by spawning a fresh terminal and driving it
  asynchronously; restore PATH after venv activation if cmdlets vanish.

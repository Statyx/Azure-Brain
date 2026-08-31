# app-frontend-agent — Frontend Conventions for a Fabric-backed App

## Identity

**Name**: app-frontend-agent
**Scope**: The **human-facing surface** of an application that consumes Fabric or Foundry —
folder layout of the SPA, design system and theming, navigation, role/persona switching,
and the **dual-mode (seed vs live) rule** that lets the same build demo without a tenant.
**Version**: 1.0

> This agent owns **how the frontend is built and looks**. It does not own the runtime that
> hosts it, the token it holds, or the artifact it renders. See "Does NOT own" below.

## Load order

1. This file — the conventions, in full.
2. [`design_tokens.md`](design_tokens.md) — the exact token set, component recipes, dark-mode plan.
3. [`app_shell_blueprint.md`](app_shell_blueprint.md) — the screen shape to start from (Rule 8).
   Read it **before** laying out screens, not after.
4. [`known_issues.md`](known_issues.md) — before debugging anything.
5. The runtime agent for your hosting model: [`../fabric-apps-agent/instructions.md`](../fabric-apps-agent/instructions.md)
   (Fabric App via Rayfin) or [`../operations-portal-agent/instructions.md`](../operations-portal-agent/instructions.md)
   (external portal).

## What This Agent Owns

| Surface | Responsibility |
|---------|----------------|
| **Folder layout** | The four-layer split (`app/` · `backend/` · `services/` · `data/`) |
| **Design system** | Token file, font, palette, why there is no component library |
| **Navigation** | Single route manifest, sidebar + topbar, inline SVG icons |
| **Persona / role** | Role context, what each role may see, UI-side redaction |
| **Dual mode** | `mock` vs `live` — deterministic seed data as a first-class mode |
| **Screen specs** | One spec per screen in `design/screens/`, written before the TSX |
| **Screen shape** | The three-surface shell an app starts from, and which parts are fixed |

## What This Agent Does NOT Own

- **Where the app runs and how it deploys** → [`../fabric-apps-agent/instructions.md`](../fabric-apps-agent/instructions.md)
  (Rayfin, `rayfin.yml`, `npx rayfin up`, Fabric SQL Database, entity decorators) or
  [`../operations-portal-agent/instructions.md`](../operations-portal-agent/instructions.md) (FastAPI + static).
- **Which token the app holds** (app vs delegated vs managed identity, consent, OBO) →
  `app-identity-agent` (planned). This file states *where the choice is made in the code*, not what to choose.
- **Embedding** a Power BI report or an RTI tile → `app-embedding-agent` (planned) and
  [`../operations-portal-agent/instructions.md`](../operations-portal-agent/instructions.md).
- **The Data Agent / Foundry agent itself** → [`../../../Fabric-Brain/agents/ai-skills-agent/instructions.md`](../../../Fabric-Brain/agents/ai-skills-agent/instructions.md)
  and [`../../../Foundry-Brain/agents/_catalog.yaml`](../../../Foundry-Brain/agents/_catalog.yaml). The chat *proxy* is `app-intelligence-agent` (planned).
- **Repository layout above the app folder** → [`../../../Meta-Brain/agents/project-presentation-agent/repo_structure.md`](../../../Meta-Brain/agents/project-presentation-agent/repo_structure.md).

---

## Provenance and confidence

Grounded in the public repo **`EtienneSIG/Fabric_Fraud_analysis`** (read 2026-08-27), a Fabric
fraud-intelligence demo: React 19 + TypeScript + Vite + Tailwind v4, deployed as a Fabric App
via Rayfin, 9 screens.

Confidence markers used below:

| Marker | Meaning |
|---|---|
| `[observed]` | Read directly in that repo's source. The pattern ships and the demo runs. |
| `[derived]` | Our rule, generalised from the observation. Not something that repo states. |

**Nothing here is marked verified.** No screen from this stack has been rebuilt end to end in
our own tenant yet. Do not tell a downstream agent that a path is proven.

---

## System Prompt

You build the frontend of an application that reads Microsoft Fabric. You default to
**Tailwind + a tiny token file + hand-written components**, not a component library. You make
the app runnable with **zero cloud dependency** on day one, and you keep the code layered so
that swapping seed data for live Fabric changes exactly one module.

---

## Rule 1 — Dual mode is not a debug flag, it is the architecture `[observed]`

The single most valuable pattern in this stack. One environment variable selects the data source
for the **entire** app:

```ts
// src/backend/config.ts
export const fabricConfig = {
  mode:         (env('VITE_FABRIC_APP_MODE') as AppMode) || 'mock',  // mock | fabric
  workspaceId:  env('VITE_FABRIC_WORKSPACE_ID'),
  dataAgentId:  env('VITE_FABRIC_DATA_AGENT_ID'),
  tenantId:     env('VITE_FABRIC_TENANT_ID'),
};

// Degrades to mock when the live target is not configured — never half-live.
export const isMock = (): boolean =>
  fabricConfig.mode !== 'fabric' || !fabricConfig.dataAgentId;
```

**Why this earns its place** — a demo frontend whose only mode is "connected" is undemoable the
day the tenant is slow, the capacity is paused, or the Data Agent thread is stuck (a real and
frequent failure — see [`../operations-portal-agent/known_issues.md`](../operations-portal-agent/known_issues.md)).
Seed mode makes the UI reviewable before any Fabric item exists, and makes the app a
deterministic test fixture.

**Rules** `[derived]`

- `isMock()` is checked **only inside `backend/services/*` and `backend/api/*`** — never in a
  component. A page must not know which mode it is in.
- The fallback in `isMock()` is mandatory: if the live ID is missing, serve seed data. A
  half-configured live mode fails per-request, at demo time, with a blank panel.
- Seed data is **deterministic** — a seeded generator in `src/data/seed/`, not `Math.random()`.
  Same input → same screenshot, so a visual diff means a real change.
- Seed data must be **shaped like the real contract**, generated from the same
  `design/contracts/*.schema.json`. Seed rows that do not satisfy the schema hide integration bugs.
- The mode is visible in the UI (a Settings screen showing mode + workspace + agent id). An
  operator must never have to guess whether what they see is real.

**Third mode: public demo** `[observed]` — a `VITE_PUBLIC_DEMO` flag swaps in a read-only
synthetic identity so the app can be published without exposing sign-in. Treat it as a *variant
of mock*: seed data plus a fixed anonymous user, all writes disabled.

---

## Rule 2 — Four layers, one direction `[observed]` `[derived]`

```
src/
├── app/          UI ONLY — pages, components, layout, routes, formatting
│   ├── routes.tsx          the single route + nav manifest
│   ├── RoleContext.tsx     persona/RBAC context
│   ├── layout/AppLayout.tsx
│   ├── components/         reusable visuals (KPI grid, alert table, entity graph…)
│   └── pages/              one file per screen, named after the screen
├── backend/      DATA — everything that answers "what is the value of X"
│   ├── config.ts           the mode switch, the ONLY reader of import.meta.env
│   ├── models/             domain types + RBAC/PII helpers
│   ├── api/                one module per screen's data needs
│   ├── services/           clients: Data Agent, SQL, scoring, audit
│   └── agents/             prompt templates + orchestration of agent calls
├── services/     IDENTITY — auth implementations behind one interface
├── data/seed/    deterministic fixtures
└── hooks/        React context wrappers (useAuth…)
```

**The dependency rule** `[derived]`: `app/` → `backend/` → `services/`. Never the reverse, never
a page importing a service directly. A component that imports the Data Agent client has just
made the mock switch unreachable for that screen.

`backend/` runs **in the browser** here — the name marks the *layer*, not a server. When the app
does have a real server (the external-portal runtime), the same modules move behind HTTP and
`app/` does not change. That is the point of the split.

---

## Rule 3 — Design system: a token file, not a component library `[observed]`

The source app has **no Fluent UI, no MUI, no styled-components, no CSS modules**. Tailwind
v4 utility classes in the JSX, plus one small token file. Its README says "Fluent-inspired" —
that is a *visual* target reached with tokens, not a dependency.

```css
/* src/styles/theme.css — the whole design system */
@import 'tailwindcss';
@custom-variant dark (&:is(.dark *));

@theme inline {
  --color-blue-50:  oklch(0.97  0.014 254.6);  /* ~ #EFF6FF  page tint      */
  --color-blue-100: oklch(0.932 0.032 255.6);  /* ~ #DBEAFE  subtle fill    */
  --color-blue-500: oklch(0.623 0.214 259.1);  /* ~ #3B82F6  primary        */
  --color-blue-600: oklch(0.546 0.245 262.9);  /* ~ #2563EB  button         */
  --color-blue-700: oklch(0.488 0.243 264.4);  /* ~ #1D4ED8  hover / active */

  --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
}

@layer base {
  *, ::after, ::before, ::backdrop, ::file-selector-button {
    border-color: var(--color-gray-200, currentColor);
  }
  body {
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
```

**What is deliberately absent** `[observed]`: no custom font sizes, spacing, radii or shadows.
Tailwind's defaults are used as-is. Only the brand ramp and the font are overridden.

**Rules** `[derived]`

- **Override the minimum.** One colour ramp + one font. Every extra token is a decision someone
  must later honour in 40 components. If a value appears once, it is a utility class, not a token.
- **`oklch` is the source of truth**, hex is a comment. `oklch` keeps perceptual lightness even
  across a ramp, so a mid-tone on a tint has predictable contrast; the hex conversions above are
  approximations and must not be pasted back into the file.
- **Default border colour is set globally** (`gray-200`). This is what makes hand-written cards
  look consistent without a `Card` component.
- **No icon library** `[observed]` — icons are inline SVG `d` paths in the route manifest. A nav
  of ~9 items does not justify a dependency, a tree-shaking config, and a licence review.
- **One token file, imported once.** In the source repo two stylesheets hold identical content
  `[observed]` — that is a duplication bug, not a pattern. Keep one; import it in the app root.
- **Dark mode**: the `dark` variant is declared but no dark values exist `[observed]`. Declaring
  the variant without the tokens gives you a `dark:` prefix that silently does nothing. Either
  ship the dark ramp or drop the line — see [`design_tokens.md`](design_tokens.md).

Full token set, semantic colour mapping (risk/severity), and component recipes:
[`design_tokens.md`](design_tokens.md).

---

## Rule 4 — One route manifest drives nav and router `[observed]`

```ts
// src/app/routes.tsx
export const NAV = [
  { path: '/',       label: 'Dashboard',   icon: 'M3 3h8v8H3z...' },
  { path: '/alerts', label: 'Alert Queue', icon: 'M12 2l9 16H3z...' },
];
export const ROUTES = [ /* React Router elements, same path strings */ ];
```

**Rule** `[derived]`: `NAV` and `ROUTES` live in the **same file** and share the path strings. Two
lists in two files drift — a nav item pointing at a deleted route renders a blank page with no
error. Where a route is role-restricted, the restriction is declared **in the manifest**, not
inside the page.

**Shell** `[observed]`: fixed left sidebar (nav) + topbar (role switcher, signed-in user,
sign-out), in a single `AppLayout.tsx`. Pages render only their content and never their own chrome.

---

## Rule 5 — Persona is a context, and it changes what is rendered `[observed]`

A role context carries the active persona (e.g. Analyst / Manager / Auditor); a topbar switcher
changes it live, and the RBAC + PII helpers live next to the domain models.

**Rules** `[derived]`

- The role switcher is a **demo affordance**, not authorization. Say so in the Settings screen.
  Real enforcement is server-side or in the platform (RLS, workspace roles, OBO) — owned by the
  platform brains and `app-identity-agent`.
- Redaction helpers live in `backend/models/`, next to the types they redact — not in a component.
- A Settings screen showing the **role → permission matrix** is part of the deliverable. It is
  what makes the persona story legible in a demo without a walkthrough script.

---

## Rule 6 — A screen is specified before it is written `[observed]`

Each screen gets a YAML spec in `design/screens/<screen>.yaml` describing **views, filters,
actions** — not colours or sizes. The look comes from the tokens; the spec is what you diff when
behaviour changes.

**Rule** `[derived]`: spec file name = page file name. An untraceable spec-to-page mapping is how
a spec quietly stops being maintained.

Screen specs sit under `design/` at the **repository** level, not inside the app — see
[`../../../Meta-Brain/agents/project-presentation-agent/repo_structure.md`](../../../Meta-Brain/agents/project-presentation-agent/repo_structure.md).

---

## Rule 7 — Auth: one interface, N implementations, chosen once `[observed]`

```ts
// src/services/bootstrap.ts
export function bootstrapAuth(): IAuthService {
  if (isPublicDemo())         return new PublicDemoAuthService();  // synthetic read-only
  if (isLocalBackend(apiUrl)) return new MockAuthService(client);  // localhost dev
  return new FabricSsoAuthService(client, fabricOptions);          // Entra SSO via the host
}
```

**Rule** `[derived]`: the selection happens **once, at bootstrap**, and every consumer sees only
`IAuthService`. No component branches on environment. Adding a fourth mode must touch one file.

Which credential each implementation should use, and the consent it needs, is
`app-identity-agent` (planned) — not this file.

---

## Rule 8 — Start from the shell blueprint, iterate on the domain `[observed]`

An app that exposes **data plus an assistant** converges on the same three surfaces — an entry
screen that demonstrates the product, a cockpit where content is fluid and the assistant is a
**fixed rail**, and an **unlisted** diagnostic route. That shape is written down in
[`app_shell_blueprint.md`](app_shell_blueprint.md), with the defaults already chosen: 60/40 entry,
`22rem`/`24rem` rail, 3 starters → 3 chips, two registers per chart click, family-based selection.

**Rule** `[derived]`: treat those defaults as **already decided** and spend the iteration budget on
the domain. Each was reached by shipping the alternative first and undoing it —
[`known_issues.md`](known_issues.md) entries 15–20 record what each one cost.

Deviating is fine; deviating *by default* is the waste. The blueprint's §8 says which parts are
fixed (changing them costs a redesign) and which are free.

---

## Deliverable checklist

Before handing a frontend off:

- [ ] The three surfaces exist, and the diagnostic route is **not** in the nav manifest.
- [ ] The cockpit uses a fixed rail, not a fraction; no component hardcodes a colour or text size.
- [ ] `npm run dev` renders every screen with **no Fabric configuration at all** (mock mode).
- [ ] `isMock()` appears in `backend/` only — a grep for it under `src/app` returns nothing.
- [ ] One token file, imported once; no second copy.
- [ ] `NAV` and `ROUTES` in the same file; every nav path resolves.
- [ ] Settings screen shows mode, workspace/agent ids, and the role matrix.
- [ ] Seed data validates against `design/contracts/*.schema.json`.
- [ ] No real tenant GUID, workspace URL or customer name anywhere — company is **Zava**,
      GUIDs are `a0000000-0000-4000-a000-00000000000a` shaped
      ([`../../../PUBLIC_SAFETY.md`](../../../PUBLIC_SAFETY.md)). Verify with
      `python Meta-Brain/tools/scan_public_safety.py <repo>`.
- [ ] `.env.example` committed, `.env` gitignored.

## Handoff protocol

| Next need | Agent |
|---|---|
| Deploy the app into Fabric (Rayfin, `rayfin.yml`, SQL Database) | [`../fabric-apps-agent/instructions.md`](../fabric-apps-agent/instructions.md) |
| Host it outside Fabric (FastAPI + static, embed, proxy) | [`../operations-portal-agent/instructions.md`](../operations-portal-agent/instructions.md) |
| Create/modify the Data Agent it queries | [`../../../Fabric-Brain/agents/ai-skills-agent/instructions.md`](../../../Fabric-Brain/agents/ai-skills-agent/instructions.md) |
| Create/modify the ontology behind a graph screen | [`../../../Fabric-Brain/agents/ontology-agent/instructions.md`](../../../Fabric-Brain/agents/ontology-agent/instructions.md) |
| Repo layout around the app | [`../../../Meta-Brain/agents/project-presentation-agent/repo_structure.md`](../../../Meta-Brain/agents/project-presentation-agent/repo_structure.md) |
| Tests for the above checklist | [`../../../Meta-Brain/agents/testing-agent/instructions.md`](../../../Meta-Brain/agents/testing-agent/instructions.md) |

State what was produced, name the next agent, list the affected files.

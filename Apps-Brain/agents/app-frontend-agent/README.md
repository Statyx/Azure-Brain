# app-frontend-agent

**Domain**: `05-frontend` · **Brain**: Apps-Brain · **Status**: active

The **human-facing surface** of an application that consumes Fabric or Foundry: folder layout,
design system, navigation, persona switching, and the dual-mode rule that lets the same build
run with or without a tenant.

## When to use it

- "Build the UI for a Fabric-backed app / demo portal"
- "Set up the design system / theme / tokens"
- "Structure the `src/` of the app"
- "The app must demo without a tenant"
- "Add a role switcher / persona view"

## When **not** to use it

| You want to… | Go to |
|---|---|
| Deploy the app into Fabric (Rayfin, `rayfin.yml`) | [`../fabric-apps-agent/`](../fabric-apps-agent/README.md) |
| Host an external portal, embed Power BI / RTI | [`../operations-portal-agent/`](../operations-portal-agent/README.md) |
| Validate a **Power BI report** layout | `Fabric-Brain/agents/pixel-design-agent/` |
| Build a Fabric **workload** (extends the Fabric portal itself) | `Fabric-Brain/agents/extensibility-toolkit-agent/` |
| Create the Data Agent the app queries | `Fabric-Brain/agents/ai-skills-agent/` |

## Files

| File | Purpose |
|---|---|
| [`instructions.md`](instructions.md) | **LOAD FIRST** — the 8 rules, ownership, handoffs |
| [`design_tokens.md`](design_tokens.md) | Token set, semantic colours, component recipes, dark mode, a11y |
| [`app_shell_blueprint.md`](app_shell_blueprint.md) | The three-surface screen shape to start from, with the defaults already chosen |
| [`known_issues.md`](known_issues.md) | 20 documented pitfalls |

## The eight rules, in one line each

1. **Dual mode is the architecture** — one env var switches seed ↔ live, and a missing live id
   falls back to seed wholesale.
2. **Four layers, one direction** — `app/` → `backend/` → `services/`, never the reverse.
3. **A token file, not a component library** — Tailwind v4 `@theme inline`, one ramp, one font.
4. **One route manifest** — `NAV` and `ROUTES` in the same file, sharing path strings.
5. **Persona is a context** — role switcher is a demo affordance, never authorization.
6. **Specify the screen before writing it** — YAML spec in `design/screens/`.
7. **One auth interface, N implementations, chosen once** at bootstrap.
8. **Start from the shell blueprint** — the three surfaces and their defaults are already
   decided; spend the iteration budget on the domain, not on the shell.

> Rules 1–7 govern the shape of the **code**. Rule 8 governs the shape of the **screens**, and
> delegates to [`app_shell_blueprint.md`](app_shell_blueprint.md).

## Provenance

Grounded in the public repo `EtienneSIG/Fabric_Fraud_analysis` (read 2026-08-27). Patterns are
tagged `[observed]` (read in that source) or `[derived]` (our generalisation). **Nothing is
marked verified** — no screen from this stack has been rebuilt end to end in our own tenant.

[`app_shell_blueprint.md`](app_shell_blueprint.md) has a **second, independent source**: an app
we shipped and then iterated on (2026-08-28 → 08-31). Its defaults are not style preferences —
each was reached by shipping the alternative first and undoing it, and its latency figures were
measured on that app, not estimated. `known_issues.md` entries 15–20 record what each one cost.

# IQ playground — template

A reusable **Copilot Chat–style IQ demo** that runs inside an app, such as a Fabric App
(Rayfin) page. It shows Work IQ, Web IQ, Fabric IQ and Foundry IQ working together on one
business question, then a decision, then an action.

> **Credit.** The engine is adapted from a colleague's *copilot-iq-playground* project and is
> published here with the author's consent. The Caldova adaptation, the Fabric App integration
> and the UX rules below were added while building the Caldova Media demo (2026-09).

## Principle

**The interaction is real; the execution is scripted.** The engine (`engine/`) is generic and
knows nothing about any customer. A scenario is **pure JSON**, passed to the engine as a prop.
A new demo is a new JSON file, never a fork of the engine.

## Layout

| Path | Role |
|---|---|
| [`engine/PlaygroundShell.tsx`](engine/PlaygroundShell.tsx) | The shell: sidebar, chat, Cowork, chips, scene playback |
| [`engine/cards.tsx`](engine/cards.tsx) | Answer cards: reasoning chain, sources, decision options, artifacts |
| [`engine/icons.tsx`](engine/icons.tsx), [`engine/sourceMeta.ts`](engine/sourceMeta.ts) | Icons and per-IQ source styling |
| [`engine/profile.ts`](engine/profile.ts) | Demo profile (operator + approver names) in `localStorage`, `{{token}}` substitution |
| [`engine/validateScenario.ts`](engine/validateScenario.ts) | Narrative rules: the checks a JSON Schema cannot express |
| [`types/scenario.ts`](types/scenario.ts) | TypeScript contract of a scenario |
| [`schema/scenario.schema.json`](schema/scenario.schema.json) | JSON Schema of a scenario (structure) |
| [`scenarios/caldova-media/scenario.json`](scenarios/caldova-media/scenario.json) | Reference scenario: Q3 advertiser delivery tolerance |
| [`AUTHORING.md`](AUTHORING.md) | How to write a new scenario, and the UX rules learned the hard way |

The engine's only dependency is `react`; every other import is relative. Styling is Tailwind
utility classes plus the tokens below.

## What the JSON drives

| Field | Drives |
|---|---|
| `agents[]` | Pinned agents in the sidebar (`name`, `sub`, `color`, `iq`) |
| `shell.conversationHistory` | The sidebar's Conversations history |
| `shell.suggestedChips` | Suggestion chips on the landing |
| `shell.openerChip` | The first question; the Work IQ track waits for the user to click it |
| `shell.upcomingTasks` | Cowork's Upcoming list (`action` launches a track) |
| `shell.tryThese` | Cowork's "Try these" shortcuts |
| `tracks[]` | Scripted conversation paths; one scene per click |
| `coworkSession` | Optional timed replay of an autonomous agent session |
| `artifacts` | Optional business artifacts (order, authorization record, query provenance) |
| `governance` | Approval threshold, policy source, audit retention; `approvalThreshold` is required |

## Integrating into a Fabric App (Vite + React + Tailwind v4)

1. Copy `engine/`, `types/` and your `scenarios/<name>/` into the app at
   `src/features/iq-playground/`.
2. Add a page component:

   ```tsx
   import PlaygroundShell from '@/features/iq-playground/engine/PlaygroundShell';
   import scenarioJson from '@/features/iq-playground/scenarios/<name>/scenario.json';
   import type { Scenario } from '@/features/iq-playground/types/scenario';

   const scenario = scenarioJson as unknown as Scenario;

   export function IqInPracticePage() {
     return (
       <div className="iq-playground min-h-full flex-1">
         <PlaygroundShell scenario={scenario} />
       </div>
     );
   }
   ```

   Register it in the app's single route and nav manifest (see
   [`app-frontend-agent`](../instructions.md)), replacing the previous IQ page if there is one.

3. Add the colour tokens to the Tailwind v4 `@theme` block in `main.css`:

   ```css
   @theme {
     --color-ink: #000000;
     --color-ink-muted: #4a4a4a;
     --color-ink-soft: #333333;
     --color-canvas: #ffffff;
     --color-surface: #f2f2f2;
     --color-hairline: #cccccc;
     --color-warm-bg: #fafafa;
   }
   ```

4. Add the scoped styles. The playground is **light-only**, like Copilot Chat. The override block
   stops an app-wide dark retrofit from painting the cards slate:

   ```css
   .iq-playground { color: var(--color-ink); font-weight: 300; letter-spacing: 0; }
   .iq-playground h1, .iq-playground h2, .iq-playground h3 { font-weight: 500; letter-spacing: -0.02em; }

   @keyframes fade-in-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
   .animate-fade-in-up { animation: fade-in-up 0.6s ease-out forwards; }
   @keyframes counter { from { opacity: 0; } to { opacity: 1; } }
   .animate-counter { animation: counter 0.4s ease-out forwards; }

   main:has(.iq-playground) { background: #fff; color-scheme: light; }
   main:has(.iq-playground) > .mesh-bg { display: none; }
   .iq-playground,
   [data-theme='dark'] .iq-playground {
     color-scheme: light; background: #fff; color: var(--color-ink);
     --bg-card-solid: #fff; --bg-secondary: #fafafa; --bg-card: rgba(255,255,255,.65);
     --text-primary: #0f172a; --text-secondary: #475569; --text-muted: #64748b;
     --border: rgba(226,232,240,.8);
   }
   [data-theme='dark'] .iq-playground .bg-white { background-color: #fff; }
   ```

   Adjust `.mesh-bg` and the `--bg-*` / `--text-*` names to whatever the host app's theme uses.

5. Build and deploy the app the usual way (see `fabric-apps-agent`). Then **hard-refresh** the
   browser (Ctrl+F5): a cached bundle looks exactly like a failed deploy. If the deployed page
   returns 401 on assets, see the Rayfin `assetAccess` entry in
   [`fabric-apps-agent/known_issues.md`](../../fabric-apps-agent/known_issues.md).

## Validate a scenario

- **Structure:** validate the JSON against [`schema/scenario.schema.json`](schema/scenario.schema.json).
- **Narrative:** `validateScenario(json)` returns a list of problems; an empty list means pass.
  Run it in a unit test, or temporarily log it from the page before a demo.

## Related

- Scenario module `M-IQPLAY` in [`Meta-Brain/SCENARIOS.md`](../../../../Meta-Brain/SCENARIOS.md).
- UX pitfalls: [`known_issues.md`](../known_issues.md), entries dated 2026-09.
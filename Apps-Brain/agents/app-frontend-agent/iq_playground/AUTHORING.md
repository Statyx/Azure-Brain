# Authoring a new IQ playground scenario

A new demo is **one new JSON file**. Do not touch `engine/` to tell a different story; if the
engine genuinely lacks a capability, change it once, generically, for every scenario.

Read [`README.md`](README.md) first for the layout and the Fabric App integration.

## 1. The story arc

Every scenario tells the same four-beat story, with each IQ layer answering one question:

| Layer | Answers | Typical sources |
|---|---|---|
| **Work IQ** | *Who* decided, what was agreed, who must approve | Mail, meetings, Teams, files |
| **Web IQ** | What is happening in the *market* | Public web, news, competitors |
| **Fabric IQ** | What is the *business impact*, in numbers | Ontology, semantic model, Lakehouse |
| **Foundry IQ** | What the *policy* or reference documentation says | Knowledge base, contracts, playbooks |

Then a **decision** with three or more real options, a **human approval** checkpoint, and an
**action**, for example an email sent to the right person. Systems that are not an IQ layer, such
as an ERP, carry `iq: "none"`. Live adapters are off by default: the interaction is real, the
execution is scripted.

## 2. Step by step

1. Copy `scenarios/caldova-media/` to `scenarios/<your-id>/` and change `id`, `title`,
   `summary` and `industry`.
2. Rewrite `persona`, `trigger` and `agents[]`. Each agent has a `name`, `sub`, `color` and an
   `iq` value: `work`, `web`, `fabric`, `foundry` or `none`.
3. Rewrite `shell`:
   - `openerChip` is the first question. The Work IQ track waits for the user to click it, so it
     must be a real information request (see the UX rules below).
   - `suggestedChips`, `tryThese` and `upcomingTasks` are the shortcuts. Every
     `upcomingTasks[].action` must be the `id` of an existing track.
   - `conversationHistory` fills the sidebar. Make it plausible for the persona.
4. Rewrite `tracks[]`. Each click plays one scene, and each scene has `choices[]`. A choice
   carries the `user` message, the `assistant` answer, the reasoning `chain`, the
   `thinkingSteps`, a `report` and its `sources`. A decision choice adds `scenarios[]`, the
   options, each with `id`, `badge`, `response` and `responseSources`.
5. Write people's names as tokens: `{{userName}}` for the presenter and `{{approverName}}` for
   the approver. `engine/profile.ts` substitutes them from the demo profile stored in
   `localStorage`. If two demos share a browser origin, rename `DEMO_PROFILE_STORAGE_KEY` so
   their profiles do not collide.
6. Optional: `coworkSession` for a timed replay of an autonomous agent run, and `artifacts`
   for business documents such as an order, an authorization record or query provenance.
7. Validate (section 4), integrate (README), then rehearse the whole path in the deployed app.

## 3. UX rules — learned on the Caldova Media build (2026-09)

Each rule below fixes a defect the user actually saw.

1. **Copilot Chat look: white and light-only.** The playground should feel like the presenter's
   own Copilot Chat. If the host app has a dark theme, apply the README's override block, or the
   cards inherit slate backgrounds and look broken.
2. **No stage directions in the UI.** Never show "simulated", "demo", "mock" or "reset". The
   audience knows it is a demo. The last scene ends on a business outcome, such as "Email sent
   to …", not on a "Reset demo" button.
3. **IQ prompts are information needs, never commands.** Write "Who signed off the Q3 tolerance
   and what did they agree?", never "Start Work IQ". A Work IQ question must need people, mail
   or meeting context to answer, and a Web IQ question must need the public web. If the
   question can be answered without that layer, the layer has not been demonstrated.
4. **Numbers in the question and the answer must match.** If the question asks for two
   advertisers, the answer lists two. A 2-vs-3 mismatch is the first thing an audience notices.
5. **One assistant name, everywhere.** Pick either the product name, such as "Microsoft 365
   Copilot", or the app's own name, and use it in the header, the chat bubbles and the sources.
   Mixing the two made viewers ask which product they were looking at.
6. **A compact landing.** Keep the suggestion chips small and few. The "What can I do" area and
   the input box stay full size. Content can grow once the conversation starts.
7. **Let the presenter drive.** Nothing plays until the user clicks the opener chip or types.
8. **Hard-refresh after every deploy.** A cached bundle looks exactly like a failed deploy.
9. **Click-paced transitions, always.** A hop to the next agent (`chainNext`) or the follow-up
   unlocked by picking a scenario is shown as the **only** suggested reply and plays on click.
   Never `setTimeout(startTyping, …)` into the next step: the audience saw Work IQ start "on its
   own". The engine also blurs the clicked control and every chip is `type="button"`, so a stray
   Space/Enter cannot fire the next step. See `known_issues.md` #31.
10. **Auto-scroll during a turn, free scroll after it.** The conversation follows the newest
    content while typing, thinking steps, answer and cards render, then stops, so the presenter
    can scroll back up to walk through the result. Built into the engine (`conversationRef`).
11. **Chip text = `<IQ layer>: <the manager's real question>`.** For example "Fabric IQ: who
    missed the zero-touch XLA in week 38?", "Foundry IQ: what do the contracts make us owe?",
    "Work IQ: what has the team already started?", "Web IQ: public news to raise at the reviews",
    then a plain closing ask such as "Recommend how to close week 38 for both customers". The
    prefix tells the audience which layer answers; the question proves why that layer is needed.
12. **Decision options are concrete verbs with a named person.** "Yes, draft the approval request
    to {{approverFirstName}}", "Show me the credit approval policy first", "No, I'll raise it with
    Finance myself". Never "Option A" / "Continue".
13. **Never write the `@mention` in a scene's `user` text.** `startTyping` prefixes it; writing it
    yourself renders "@ZavaIQ @ZavaIQ …". Every assistant answer carries its
    "Intelligence used" trace (the IQ layers and sources it drew on).
14. **Compact density from the start.** Chat text runs at ~0.77x the host console scale (scoped
    `--text-*` override on the playground root, see `known_issues.md` #30). Do not ship the
    default size and wait for the "too big" remark.

### Demo collaboration defaults

How the user works on these demos, so nothing has to be corrected twice:

- **Language.** Talk to the user in French, concisely. Repo, UI and brain text stay English.
  Pre-reads and presenter notes are written in **French, keeping the English key terms**
  (XLA, zero-touch, task flow, Data Agent, Work IQ…).
- **Autonomy.** "GO en autonomie" means work end-to-end, validate, and report once at the end.
- **Deploy only what changed.** On an existing workspace, a UI-only change (scenario, CSS, copy)
  is `python -m fabric.app.deploy_app` (build + app deploy) — never the full `deploy_all`.
  Then check `rayfin.yml` was restored, and hard-refresh (Ctrl+F5). On Windows use
  `npm.cmd`/`npx.cmd`; a stderr-only exit code 1 can still be a success, so read the output.
- **Every Fabric demo ships a task flow**, with the notebook as the ingestion layer (no separate
  "files → Delta tables" step).
- **Commit or push the demo repo only when asked.** Brain lessons are committed directly.

Evidence: Fab-ServiceDesk-IQ session 2026-09-24, user corrections "la partie Work IQ s'est lancé
sans que je clique", "pourquoi tu as besoin de tout redéployer ?", "police is still too big",
"dans le pre read donne moi l'histoire en français".

## 4. Validation

**Structure.** Validate the JSON against [`schema/scenario.schema.json`](schema/scenario.schema.json).
At a minimum, the engine needs:

- `schemaVersion: 1`, an `id`, a `title` and `persona.role`;
- `agents`, which must not be empty, and `shell`;
- `tracks`, which must not be empty, each with an `id` and `scenes`, and each scene with
  `choices`.

**Narrative.** `validateScenario(json)` in
[`engine/validateScenario.ts`](engine/validateScenario.ts) returns a list of problems. An empty
list means the scenario passes. Shape errors are reported first, and the narrative rules then
run:

| # | Rule | Check |
|---|---|---|
| 1 | At least three IQ layers are exercised | Distinct `agents[].iq` values other than `none`, plus `trigger.detectedBy`: three or more |
| 2 | Every decision offers a real choice | Each `scenarios[]` has three or more options and exactly one `badge` matching "recommended" |
| 3 | Agent claims are grounded | An `assistant` text containing a number has `sources`; an option `response` containing a number has `responseSources` |
| 4 | A human approval checkpoint exists | `governance.approvalThreshold` is not empty |
| 5 | No real person is named | Matches the JSON against `REAL_NAME_DENYLIST`; use `{{tokens}}` instead |
| 6 | Upcoming-task actions point at real tracks | Each `shell.upcomingTasks[].action` is an existing track `id` |

`REAL_NAME_DENYLIST` ships empty. Fill it per demo, in lower case, with the real names of the
people in your audience or organisation, and keep that edit out of any public repository.

## 5. Pre-demo checklist

- [ ] `validateScenario()` returns an empty list.
- [ ] The whole path has been clicked through in the **deployed** app, after a hard refresh.
- [ ] Rendering is checked with the host app in both light and dark mode; the playground stays white.
- [ ] No "simulated", "demo" or "reset" text appears anywhere.
- [ ] The counts in every question match its answer.
- [ ] The assistant name is the same on every screen.
- [ ] The presenter and approver names are set in the demo profile.
- [ ] Every transition waits for a click; nothing starts on its own after a scenario pick.
- [ ] Each answer scrolls into view as it renders, with no manual scrolling.
- [ ] Every chip reads `<IQ layer>: <question>`, and no `user` text contains an `@mention`.
- [ ] Chat text is compact (~0.77x), not the default size.

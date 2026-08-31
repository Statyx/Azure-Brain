# App shell blueprint — the shape a data + assistant app converges to

Companion to [`instructions.md`](instructions.md), Rule 8. Read it **before** laying out screens.

`instructions.md` Rules 1–7 fix the **structure of the code** (layers, tokens, routes, personas,
auth). They say nothing about the **shape of the screens**, which is why that shape got
rediscovered from scratch — and got it wrong the same way twice.

This file is the starting point, not a description of one app. Treat every default here as
*already decided*; spend the iteration budget on the domain instead.

**Status:** `[observed]` — every default below is the end state of one shipped app after a full
redesign cycle. The failure that motivated each is recorded in
[`known_issues.md`](known_issues.md) entries 15–20. **Re-deriving them is the waste this file
exists to prevent.**

---

## 0. When this blueprint applies

Use it when the app exposes **domain data** *and* an **assistant over that data** — the recurring
shape for a Fabric/Foundry-backed app. If there is no assistant, keep §2, §6 and §7 and drop the
rest.

**Runtime-neutral on purpose.** A Fabric App (Rayfin — the default runtime), an external portal
and an Azure-hosted app render the same three surfaces. Nothing below changes because the hosting
changed; a runtime switch is not a licence to re-decide the shell.

Three surfaces, and no more until the domain demands one:

| Surface | Role | Listed in nav |
|---|---|---|
| **Entry** | One screen that *demonstrates* the product | yes |
| **Cockpit** | Where the work happens: content + assistant | yes |
| **Diagnostic** | Which link in the chain broke | **no** — reachable by URL |

---

## 1. Entry screen — one list, and it must show what the app does

**Default:** a single 60/40 surface. Left: the guided path. Right: the assistants or capabilities.
**Every row is a button** that lands the user in the cockpit with a question already asked.

Three rules that are not negotiable, because each cost a redesign:

1. **One navigation, not two.** A guided arc *and* a separate roster of assistants split the
   subject: each list is coherent alone, and together they force the visitor to guess which one is
   the product.
2. **The opening question is typed `mixed`** (or whatever forces more than one subordinate to
   fire). The entry screen must *demonstrate* the product, not describe it — an app whose first
   click returns one plain answer reads like a chatbot.
3. **Landing cards count what the page is for.** A card counting canned questions on a page whose
   subject is charts measures the wrong thing.

**Anti-pattern:** buttons labelled like report chapters. The room then expects slides.

---

## 2. Cockpit — content is fluid, the assistant is a rail

**Default:** `content: 1fr` + `assistant: 22rem` (`24rem` at `xl`). Fixed, not fractional.

A fraction (`1.05fr / 1fr`) **shares** growth, so the conversation pane widens with the window and
the app reads as "a chat that happens to have charts". A rail **assigns** growth. Decide
deliberately which pane is allowed to grow — for a data app it is the content.

**The container owns text size.** No leaf component hardcodes `text-sm`; a component that sets its
own scale cannot be reused at another one.

---

## 3. Suggestions — two acts, never one

| Moment | Show | Why |
|---|---|---|
| Before the first question | **3 starters** | 8 at once is a decision to make, and a live demo stalls on it |
| After each answer | **3 chips**, minus what was asked | showing none empties the rail exactly when the audience has just learned what a good question looks like |

---

## 4. Entering the conversation from a chart

Every click-through carries **two registers**:

- `prompt` — names table and column explicitly. Domain phrasing ("at risk", "top performer") has
  several legitimate readings; the agent must not have to pick one.
- `label` — what the room reads. Plain business language.

**Select one per family, never `slice(0, n)`.** A cap over a curated list does not sample it, it
truncates it — and it fails silently: a registry that happens to list graph questions last loses
every path to the ontology without a single error. **Pin the coverage in a test, not the count**;
a test asserting "3 openers" passes straight through that bug.

**Plain language must not upgrade a claim.** Removing jargon from a `label` is free; turning a step
the app only *declares* into one it appears to *observe* is not. Steps the app cannot measure stay
labelled as not measured here — see [`instructions.md`](instructions.md) *Provenance and
confidence*.

---

## 5. Latency — measure it before designing around it

Measure the real distribution first (the shipped app: **40–160 s**, mean 61.5 s). Then choose:

- **Under ~10 s** → stream it, show the hops, do nothing else.
- **Over that, on stage** → replay captured answers, under the **four conditions** in
  [`known_issues.md`](known_issues.md) entry 18: nothing hand-written, the replay declares itself,
  the question list is derived through the UI's own selector, and a miss is fail-safe (normalise
  case and whitespace **only** — fuzzier matching serves a real answer to a *different* question).

A cache inherits the grounding rule: *hardcoded facts are worse than no grounding, because they
look sourced*. Displayed duration is always the **live** agent's, never the theatrical delay.

---

## 6. Diagnostic screen — build it, then unlist it

One screen that checks each link in the chain and names the one that broke. **Outside the auth
guard on purpose**, so it still answers when sign-in is what failed.

Keep the route, remove it from the nav manifest. A route nobody links to costs nothing on screen,
and deleting it means a rebuild + redeploy to get the diagnostic back at the exact moment the app
is already failing.

---

## 7. Theme — no colour survives a merge

Every surface reads theme variables ([`design_tokens.md`](design_tokens.md)). A page that hardcodes
`bg-white` / `text-slate-900` looks fine alone and breaks the moment two pages share a shell — which
is what merging screens does. Fix the colours **when merging**, not after the dark theme is reported
unreadable.

---

## 8. What is safe to iterate

| Fixed — changing it costs a redesign | Free to iterate |
|---|---|
| One entry list, every row a button | The wording of the rows |
| Assistant pinned to a rail | The rail width, within reason |
| Two registers per chart click | The domain phrasing of `label` |
| Diagnostic route exists and is unlisted | What it checks |
| Colours come from tokens | The palette |
| 3 starters → 3 chips | Which questions |

---

## 9. Start-of-project checklist

- [ ] Three surfaces named, diagnostic one **not** in the nav manifest.
- [ ] Entry screen is one list; the first click fires more than one subordinate.
- [ ] Cockpit grid uses a fixed rail, not a fraction.
- [ ] Chart openers carry `prompt` + `label`, selected one per family.
- [ ] A test pins **family coverage** of the openers.
- [ ] Latency measured and written down before any caching is designed.
- [ ] No component hardcodes a colour or a text size.

# Known Issues — app-frontend-agent

Pitfalls observed in the reference implementation (`EtienneSIG/Fabric_Fraud_analysis`, read
2026-08-27) or predicted from this stack. Read before debugging.

---

## 1. Two stylesheets with identical content

**Symptom** — a token edit has no effect, or has an effect only on some pages.

**Cause** `[observed]` — the reference repo ships two stylesheets holding the *same* token
block. Whichever one the entry point imports wins; the other is dead but looks authoritative.
Editing the dead one is a silent no-op.

**Fix** — one token file, imported exactly once from the app root. Delete the other. If a second
stylesheet is genuinely needed (print, embed), it imports the token file rather than copying it.

---

## 2. `dark:` utilities that do nothing

**Symptom** — `dark:bg-gray-900` compiles, ships, and never applies.

**Cause** `[observed]` — the `dark` custom variant is declared, but nothing ever adds `.dark` to
the document and no dark token values exist. Tailwind happily emits the rule; no ancestor ever
matches it.

**Fix** — pick one: remove the variant declaration, or implement dark mode completely (dark
ramp + semantic tokens + toggle writing `.dark` on `<html>` + `color-scheme: dark`). See
[`design_tokens.md`](design_tokens.md) §5.

---

## 3. Hex values pasted back over `oklch`

**Symptom** — the palette drifts; hover states stop feeling like one ramp.

**Cause** — the hex comments beside each `oklch` token are approximations for humans. Someone
copies them into the CSS "to make it readable", and the even lightness steps that made the ramp
work are gone.

**Fix** — `oklch` is the source of truth. Hex lives in comments only. If a designer supplies hex,
convert once and keep the `oklch`.

---

## 4. `isMock()` called from a component

**Symptom** — one screen still hits Fabric in mock mode, or renders empty in a tenant-less demo.

**Cause** — the mode check leaked out of `backend/` into a page or component. Every future data
path for that screen now has to remember the branch.

**Fix** — the check belongs in `backend/services/*` and `backend/api/*` only. A grep for
`isMock` under `src/app` must return nothing. This is on the deliverable checklist for a reason.

---

## 5. Live mode configured "half way"

**Symptom** — the app claims to be live, then a panel fails at request time with an opaque error
mid-demo.

**Cause** — `VITE_FABRIC_APP_MODE=fabric` was set but the Data Agent id (or workspace id) was
not. Without the guard, each call discovers the missing id independently.

**Fix** — the `isMock()` fallback (`mode !== 'fabric' || !dataAgentId`) is mandatory: missing
target ⇒ fall back to seed, wholesale. Surface the resolved mode on a Settings screen so the
operator sees `mock` before the audience does.

---

## 6. Seed data that does not satisfy the real contract

**Symptom** — every screen looks perfect in mock, then live mode shows nulls, `NaN`, or a crash
on a missing nested field.

**Cause** — seed fixtures hand-written to make the UI look good rather than generated from
`design/contracts/*.schema.json`.

**Fix** — validate fixtures against the same schema the live payload must satisfy, in a test.
Cheap, and it converts a demo-day failure into a CI failure.

---

## 7. `Math.random()` in seed data

**Symptom** — screenshots and visual tests differ on every run; "did my change break this?"
becomes unanswerable.

**Fix** — a seeded PRNG with a fixed seed in `src/data/seed/`. Determinism is the entire value of
a seed layer.

---

## 8. `NAV` and `ROUTES` split across files

**Symptom** — a nav item leads to a blank page, with no console error.

**Cause** — the route was renamed or deleted; the nav list in the other file was not updated.
React Router simply matches nothing.

**Fix** — both exports in the same module, sharing the path strings. Add a test asserting every
`NAV[].path` resolves to a `ROUTES[]` entry.

---

## 9. Role switcher mistaken for authorization

**Symptom** — someone assumes the demo enforces access control, and the app is treated as
security-reviewed when the "restriction" is a client-side `if`.

**Fix** — state plainly on the Settings screen that the switcher is a demo affordance. Real
enforcement lives in the platform (RLS, workspace roles, OBO) and in the server, not in the SPA.
Never describe UI-side redaction as a security control.

---

## 10. Vite env vars missing at build time

**Symptom** — `import.meta.env.VITE_*` is `undefined` in the built bundle even though the values
exist in the environment.

**Cause** — Vite inlines `VITE_*` at **build** time, and the reference repo injects them via a
`predev` / `prebuild` step. Run the build without that step (or from a different working
directory) and the values are simply absent. There is no runtime lookup to fall back on.

**Fix** — keep env injection in `predev`/`prebuild`, commit a `.env.example`, and let the
`isMock()` fallback absorb a missing value instead of failing per request. Because the values are
inlined into a public bundle, **never put a secret in a `VITE_*` variable** — anything prefixed
`VITE_` is shipped to the browser in clear text.

---

## 11. Scaffolded template metadata left behind

**Symptom** — app manifest still identifies the app as the starter template it was scaffolded
from `[observed]` (the reference app's manifest still names the todo-app template).

**Impact** — confusing in a workspace listing; can mislead tooling that keys off the template id.

**Fix** — rename the app, id and description in the manifest immediately after scaffolding, and
check it before any deployment.

---

## 12. Copying tenant values from a reference repo

**Symptom** — a real workspace id, endpoint URL or customer name ends up in our repo.

**Cause** — public reference repos often ship their own deployment doc with live ids and URLs.

**Fix** — never copy identifiers or hostnames from a reference repo. Company is **Zava**, GUIDs
are `a0000000-0000-4000-a000-00000000000a` shaped, secrets are read at runtime. See
[`../../../PUBLIC_SAFETY.md`](../../../PUBLIC_SAFETY.md) and run
`python Meta-Brain/tools/scan_public_safety.py <repo>` before pushing.


---

## 13. Rule 7 met a tenant: one of the auth implementations is dead code

**Status** — this file's patterns were `[observed]` in a public reference repo but **nothing had
been rebuilt end to end in our own tenant**. As of 2026-08 the stack has been: scaffolded,
themed, deployed to a Fabric capacity, signed in against Entra, and used to execute DAX from the
browser. The twelve entries above survived that contact. This is the delta.

**What rule 7 looks like once it is real** — "one auth interface, N implementations, chosen once
at bootstrap" holds, and the reason it matters is sharper than expected: on Fabric-hosted apps
the host SDK's own session tokens **cannot call Fabric** (they are opaque and scoped to the app's
services), so the SPA must run its own MSAL. The interface therefore has two implementations of
which **one is dead code in production**, and that is the correct outcome, not a smell. Reading
the SDK auth path first, because it looked like the native one, cost a full debugging cycle on
code that never runs. Pick the implementation at bootstrap and follow only that branch.

**Consequence for the dual-mode rule (rule 1)** — a missing auth env var does **not** raise. The
"configured" flag simply evaluates false and the app ships with authentication *silently
disabled*, which is indistinguishable from a working app until something asks for data. Entry 10
above says the vars must be present at build time; the addition is that **their absence is
silent**, so assert on the served bundle rather than on the build succeeding.

**Cross-reference** — the deploy-side gotchas found in the same session live in
[`../fabric-apps-agent/known_issues.md`](../fabric-apps-agent/known_issues.md) entries 6-15.


---

## 14. The served-bundle assertion that lies — a false negative that orders a redeploy

**Status** — observed 2026-08, Windows / PowerShell 5.1, verifying a Fabric-hosted SPA.

**Symptom** — entry 13's own advice is followed: fetch the served bundle and grep it for a string
only the newest build can contain. The check reports the string **absent**. The obvious reading is
that the deploy silently did not land, and the obvious next move is to rebuild and redeploy.

**Cause** — the probe, not the deploy. `curl.exe -s <url>` piped into a PowerShell variable is
decoded with the console code page, so a UTF-8 bundle comes back mangled and `.Contains()` returns
false on strings that are physically present. Same family as `Invoke-WebRequest` mis-decoding UTF-8;
`curl.exe` is usually recommended as the cure, and it is — only if the bytes never pass through the
pipeline. The probe string here also contained an accented character (`requête`), which is what made
the corruption reach the compared substring.

**Fix** — two independent habits, and use both:

1. **Download to a file, then read with .NET**, so the bytes are decoded once, as UTF-8:
   `curl.exe -s -o $tmp <url>` then `[System.IO.File]::ReadAllText($tmp)`. Pass an **absolute**
   path — .NET resolves relative paths against the process CWD, not the shell's location.
2. **Probe with ASCII-only fragments.** Any accented character in the needle turns an encoding
   problem into a content problem and hides it.

**The cheaper check first** — compare the **asset hash in `index.html`** against the hash the local
build just printed. It is pure ASCII, it needs no substring at all, and if the two match, the served
file *is* the file that was built; a failing content probe after that can only be the probe. Here
the local build emitted `main-<hash>.js` and the served page referenced the same `main-<hash>.js`,
which was the tell that the content probe was wrong.

**Evidence** — same URL, same asset: piped `curl.exe` → `.Contains('Source et requ')` = `False`;
downloaded to disk and read with `ReadAllText` → `True`, 563 620 chars. No redeploy was needed.

**Wider rule** — a verification step is code, and it fails like code. When a check contradicts a
cheaper, more direct signal (here: identical asset hashes), **suspect the check before acting on
it** — acting on a false negative costs a redeploy; acting on a false *positive* ships a broken app.

---

## 15. Two navigations on one subject, and neither said what the app does

**Symptom** (2026-08-30) — a landing page offered a guided arc (4 steps, all of them charts) *and*
a roster of 4 assistants (all of them chat). Both led to the same product. Nothing on the page
announced that the app does **data visualisation**: the arc's buttons read like report chapters,
so the room expected slides and got a cockpit.

**Cause** — the two lists were built at different times for different audiences and never
reconciled. Each was internally coherent; side by side they split the subject and the visitor had
to guess which one was the product.

**Fix** — merge into a single 60/40 surface where **every row is a button**, and make the opening
question typed `mixed` so both subordinates fire on the first click — the app demonstrates what it
is instead of describing it.

**Side effect worth expecting** — merging pages exposed that the merged-away pages hardcoded
`bg-white` / `text-slate-900` instead of theme variables, so the dark theme became unreadable the
moment they shared a shell. See entry 2: hardcoded light colours survive as long as nothing
composes them.

**Wider rule** — landing cards that count *canned questions* on a page whose real problem is
*charts* measure the wrong thing. Count what the page is for.

---

## 16. A fraction is not a rail, and eight suggestions are a decision

**Symptom** (2026-08-30) — a two-pane cockpit split `1.05fr / 1fr`. At every viewport the chat
pane grew with the window, so the app read as "a chat that happens to have charts" rather than a
cockpit with an assistant in it.

**Fix** — pin the conversation to a fixed rail (`22rem`, `24rem` at `xl`) and let the content pane
take the remainder. A fraction shares growth; a rail assigns it. Choose deliberately which pane is
allowed to grow.

**Second half — suggestions in two acts.** Eight suggestions at once is not generosity, it is a
decision to make, and a live demo stalls on it. Showing **none** after the first answer is worse:
it empties the rail exactly when the audience has just learned what a good question looks like.
Ship **3 starters, then 3 chips** after each answer, minus what was already asked.

**Related** — the markdown renderer stopped hardcoding `text-sm`; the container owns text size in
one place. A component that sets its own size cannot be reused at another scale.

---

## 17. A cap over an ordered list does not sample the list, it truncates it

**Symptom** (2026-08-30) — chart click-through openers were selected with `slice(0, 3)` over a
registry that happened to list numeric questions first and graph questions last. Result: **no
click could reach the ontology any more**. Nothing failed, no test went red, no error surfaced —
the feature simply stopped covering a third of the product.

**Cause** — `slice` was written when the registry was short and unordered. It silently became a
filter on insertion order the day the registry grew.

**Fix** — pick one per family (`pickVaried`), and **pin the coverage, not the count**: a test that
asserts "3 openers" keeps passing through this bug; a test that asserts "each family is
represented" fails the moment the truncation appears.

**Related, same commit** — two registers for one click: a `prompt` that names table and column
(because a phrase like "at risk" has several legitimate readings), and a `label` the room reads.
Removing jargon from the label must not upgrade a *declared* step into an *animated* one: only the
assistant's own hops are observable, so the platform-side step stays labelled as not measured
here.

**Wider rule** — any `slice`/`take`/`head` over a curated list is a coverage decision in disguise.
Either the list is genuinely unordered, or the cap needs to be a selection.

---

## 18. Replaying recorded answers is defensible — but only under four conditions

**Context** (2026-08-30) — a multi-agent supervisor answered suggested questions in **40–160 s**
(mean 61.5 s, worst 141 s across 23 questions). That is unusable on stage. Answers were pre-captured
and replayed after a short delay.

**Why this is dangerous** — the brain's own rule is that *a grounded agent with hardcoded facts is
worse than an ungrounded one, because it looks sourced*. A cache sits one layer above that rule and
inherits it: replayed text still presents as a live answer.

**The four conditions that make it defensible:**

1. **Nothing is written by hand.** The capture script invokes the **live** supervisor and stores the
   text, which subordinates actually fired, and the real elapsed seconds. It **refuses** to record
   an answer where no subordinate fired. (0 of 23 were refused — the check is the point, not the
   score.)
2. **The replay declares itself.** The wait names it, the answer carries its capture date, and the
   displayed duration is the **live** agent's, never the theatrical delay. Showing the fake delay
   would be an unsupported claim about the system.
3. **The question list is derived, not typed.** The freeze script walks the registry through the
   **UI's own** selection function. Re-implementing that selection in the capture language would
   drift silently from what users actually see.
4. **A miss is fail-safe.** Lookup normalises case and whitespace **only**. Fuzzier matching would
   serve a real answer to a *different* question — the one outcome worse than being slow.

**Operational detail** — write the file after **each** answer, not at the end. The first capture run
died at question 14; the 14 already written survived.

---

## 19. Unlisting a route costs nothing; deleting it costs a redeploy

**Symptom** (2026-08-30) — a connectivity-check page was cluttering the navigation and the reflex
was to delete it.

**Why that is the wrong move** — it is the **only** screen that says *which link* in the chain
broke, and it deliberately sits **outside** the auth guard, so it still answers when sign-in itself
is what broke. Deleting it means a rebuild and a redeploy to get the diagnostic back — at the exact
moment the app is already failing.

**Fix** — remove it from the nav manifest, keep the route reachable by URL. A route nobody links to
costs nothing on screen and stays one keystroke away.

**Wider rule** — diagnostics pages are judged by what they cost when you need them, not by what
they cost in the menu.

---

## 20. A build artifact reaches the browser — treat it as published

**Symptom** (2026-08-30) — a generated topology JSON was compiled into a static bundle served
**without authentication**, and it carried the real AI-service endpoint. No guard caught it: the
repo's leak scanner matched GUIDs, and a hostname such as `<name>.services.ai.azure.com` contains
no `8-4-4-4-12` run.

**Fix** — **replace** the value with a placeholder rather than dropping the field, so the shape the
consumer expects is preserved, and add a *shape* rule to the leak guard that rejects any concrete
resource hostname in a shipped artifact.

**A guard must not become the leak** — when the guard reports a hostname it caught, that message is
the only place the value appears; it must not be echoed into a committed file or a log that ships.

**Evidence** — the same gap existed in this brain: `Meta-Brain/tools/scan_public_safety.py` had a
rule for Fabric SQL endpoints and none for `services.ai.azure.com`, `openai.azure.com`,
`vault.azure.net` and friends. Fixed 2026-08-31 (rule `azure-resource-hostname`, 60 tests passing).

**Wider rule** — anything the build compiles into a client bundle is public the moment it deploys.
Config-shaped does not mean server-side.

---

## 21. A bulk edit that round-trips through `Get-Content` silently re-encodes the source

**Status** — observed 2026-09-01, Windows / PowerShell 5.1, bulk-editing a Vite + React source tree.

**Symptom** — a scripted sweep across five `.tsx`/`.ts` files (a mechanical string substitution)
completed with no error and a clean `git status` diff that looked plausible. The app built, the tests
passed, and the deployed page rendered `rÃ©seau`, `DÃ©connexion`, `TÃ©lÃ©mÃ©trie`. Every accented
character in every touched file had become two. Nothing in the build or the test gate objected,
because double-encoded UTF-8 is still valid UTF-8 — it just spells something else.

**Cause** — the read, not the write. `Get-Content -Raw` in Windows PowerShell 5.1 has no encoding
default of `utf8`; on a **BOM-less** UTF-8 file it falls back to the ANSI code page (Windows-1252),
so `é` (`0xC3 0xA9`) is decoded as the two characters `Ã` + `©`. Writing that string back out as
UTF-8 encodes each of them again, and the file now physically contains `0xC3 0x83 0xC2 0xA9`. The
round-trip is lossy in one direction only, so it is invisible on a file that happens to be pure
ASCII — which is why a sweep can corrupt three files out of eight and look like it worked.

This is the **write-side twin of entry 14**. Entry 14 is a mis-decoded *probe*, which produces a
false negative and costs a redeploy. This one mis-decodes on the way *in* and persists the damage
into source control, where it survives review, ships, and is then re-corrupted by the next sweep.

**Fix** — never let source text round-trip through the PowerShell pipeline for a bulk edit:

1. **Prefer the editing tool** (`edit` / a real refactoring tool) over a shell script. It reads and
   writes UTF-8 unconditionally and leaves untouched bytes untouched.
2. If a script is genuinely required, bypass the cmdlets and name the encoding on both ends:
   `[System.IO.File]::ReadAllText($p)` (detects UTF-8 without a BOM) and
   `[System.IO.File]::WriteAllText($p, $s, (New-Object System.Text.UTF8Encoding $false))`.
   Pass **absolute** paths — .NET resolves relative paths against the process CWD, not the shell's.
3. Never `Get-Content -Raw | ... | Set-Content` on source. `Set-Content -Encoding utf8` does not
   rescue it: by then the string in memory is already wrong, and the flag only controls the write.

**Detection, and why the usual gates miss it** — `tsc`, `vitest` and `vite build` all pass, because
the corruption is well-formed. Two cheap checks that do catch it:

- grep the tree for the tell-tale sequence `Ã` — a legitimately French source file contains `é`,
  never `Ã©`;
- read the **built** asset with `[System.Text.Encoding]::UTF8.GetString($bytes)` and count matches.
  Do not use `Invoke-WebRequest`'s `.Content` for this: `text/javascript` is served without a
  `charset`, so PowerShell decodes it as Latin-1 and reports mojibake in a *clean* file. Verified in
  the same session — the same bundle scored 6 hits decoded as Latin-1 and 0 decoded as UTF-8.

**Evidence** — 5 source files corrupted by one sweep; the live bundle served `rÃ©seau`. After repair
and redeploy, the served asset was byte-identical to the local build (633 277 bytes) and scored 0
mojibake when decoded as UTF-8, while genuine data accents (`Rhône`, `Île-de-France`, `Métropole`)
survived intact.

**Wider rule** — an encoding bug is not a rendering bug: it is a **content** bug that the compiler
cannot see. Any gate that only asks "does it build?" will pass it. If a step can rewrite a file it
was not asked to change, the safe design is to not let it read the file as text at all.

**Corollary** — writing UI copy in English removes the whole risk class for the app's own strings,
but **not** for the data: place names, customer names and comments stay accented. Translating is a
mitigation, never the fix.

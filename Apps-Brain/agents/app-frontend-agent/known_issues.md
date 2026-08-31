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
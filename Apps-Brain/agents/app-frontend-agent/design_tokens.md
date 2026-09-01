# Design Tokens & Component Recipes

Companion to [`instructions.md`](instructions.md). Read that first — this file is the detail
behind **Rule 3**.

Provenance: token values `[observed]` in the public repo `EtienneSIG/Fabric_Fraud_analysis`
(read 2026-08-27). Everything marked `[derived]` is our rule, not theirs.

> ⚠️ **Read [§8](#8-correction-2026-09-01--this-file-described-a-sample-not-the-house-system) first.**
> §1–§7 describe that third-party sample. The system we actually ship is in §8, which supersedes
> §1 and §5. Building from §1–§7 alone yields a flat white-card app that is not our house style.

---

## 1. The token file, in full

One file. Tailwind v4 syntax — `@theme inline`, no `tailwind.config.js`, no PostCSS plugin
chain. The Vite plugin (`@tailwindcss/vite`) is the only build wiring.

```css
@import 'tailwindcss';
@custom-variant dark (&:is(.dark *));

@theme inline {
  /* Brand ramp — the ONLY palette override */
  --color-blue-50:  oklch(0.97  0.014 254.6);
  --color-blue-100: oklch(0.932 0.032 255.6);
  --color-blue-500: oklch(0.623 0.214 259.1);
  --color-blue-600: oklch(0.546 0.245 262.9);
  --color-blue-700: oklch(0.488 0.243 264.4);

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

### Ramp roles

| Token | Role | Typical use |
|---|---|---|
| `blue-50` | page tint | app background, empty-state panels |
| `blue-100` | subtle fill | selected row, active nav item background |
| `blue-500` | primary | icons, focus ring, links |
| `blue-600` | action | primary button background |
| `blue-700` | action pressed | button hover / active, nav active text |

Everything else — grays, red/amber/green, spacing, radii, shadows, type scale — is **Tailwind's
default** `[observed]`. Do not re-declare a default just to see it in the file; a token you
re-declare is a token you must keep in sync with an upstream you do not control.

### Why `oklch` and not hex `[derived]`

`oklch(L C H)` separates perceptual lightness (`L`) from chroma and hue. Across the ramp above,
`L` steps down evenly (0.97 → 0.93 → 0.62 → 0.55 → 0.49), so contrast between any two steps is
predictable *by arithmetic* rather than by eyeballing. Hex gives you none of that: two hexes
with the same "feel" can differ by 15 points of perceived lightness.

**Consequence**: the `oklch` values are the source of truth. Any hex in a comment or in this
file is an approximation for humans, and must never be pasted back into the CSS.

---

## 2. Semantic colours the source repo does *not* declare `[derived]`

A fraud / risk / operations app needs severity colour. The source app uses raw Tailwind
utilities (`text-red-600`, `bg-amber-50`) inline. That works until two screens disagree on what
"high" looks like.

**Rule**: if the app has a severity, risk or status concept, promote it to a token — because it
is a *domain* decision, not a styling one, and it must be identical on every screen.

```css
@theme inline {
  /* Severity — domain tokens, mapped onto Tailwind defaults */
  --color-severity-critical: var(--color-red-600);
  --color-severity-high:     var(--color-orange-600);
  --color-severity-medium:   var(--color-amber-500);
  --color-severity-low:      var(--color-emerald-600);
  --color-severity-info:     var(--color-slate-500);
}
```

Then a single helper maps a domain value to the class, in `backend/models/` — never inline in a
component:

```ts
export const severityClass = (s: Severity) =>
  ({ critical: 'text-severity-critical bg-red-50',
     high:     'text-severity-high     bg-orange-50',
     medium:   'text-severity-medium   bg-amber-50',
     low:      'text-severity-low      bg-emerald-50',
     info:     'text-severity-info     bg-slate-50' }[s]);
```

**Never encode severity with colour alone** — add a label or an icon. Colour-only severity fails
every accessibility review and is unreadable to ~8% of male users.

---

## 3. Component recipes (no component library)

With `border-color: gray-200` set globally, hand-written components stay consistent. These are
the four shapes that cover most of a data app `[derived]`, in the style the source repo uses.

**Card / panel**
```
rounded-lg border bg-white p-4 shadow-sm
```

**KPI tile** — big number, small label, optional delta
```
rounded-lg border bg-white p-4
  ├─ <p class="text-sm text-gray-500">{label}</p>
  ├─ <p class="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
  └─ <p class="text-xs {deltaClass}">{delta}</p>
```

**Data table row**
```
border-b last:border-0 hover:bg-blue-50/50   ← the tint ramp earning its keep
```

**Primary button**
```
rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white
  hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-blue-500
  disabled:opacity-50 disabled:cursor-not-allowed
```

**Rule** `[derived]`: when a recipe is used more than twice, it becomes a component in
`app/components/`. Copy-pasted class strings are how a design system dies — the fifth copy is
always slightly different.

---

## 4. Icons

`[observed]` — no icon package. Icons are raw SVG `d` path strings held in the route manifest
and rendered by one tiny component:

```tsx
const Icon = ({ d }: { d: string }) => (
  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none"
       stroke="currentColor" strokeWidth={1.75} aria-hidden="true">
    <path d={d} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);
```

`stroke="currentColor"` is what makes an icon inherit the nav's active/inactive colour with no
extra classes. `aria-hidden` because the label next to it is the accessible name.

**Rule** `[derived]`: this holds up to roughly 15–20 icons. Past that, adopt a real icon set —
maintaining path strings by hand becomes the bug source.

---

## 5. Dark mode — declared but not implemented `[observed]`

The source file declares the variant:

```css
@custom-variant dark (&:is(.dark *));
```

…and then never defines a single dark value and never toggles the `.dark` class. Every
`dark:` utility a developer writes silently does nothing, and nobody notices until a review.

**Decide, do not inherit** `[derived]`:

- **Not shipping dark mode** → delete the `@custom-variant` line. A dead variant invites dead code.
- **Shipping it** → three things, together, or it is not shipped:
  1. dark values for the ramp *and* the semantic tokens (a light-mode `red-600` on a dark card
     fails contrast);
  2. a toggle that writes `.dark` on `<html>` and persists the choice;
  3. `color-scheme: dark` on the root so native controls, scrollbars and form widgets follow.

Half-implemented dark mode is worse than none: it looks broken only for the users who prefer it.

---

## 6. Accessibility floor `[derived]`

The source repo shows no explicit a11y work. Treat these as the minimum bar for anything we ship:

- Visible focus on every interactive element — `focus-visible:outline-2`, never `outline-none`
  without a replacement.
- Contrast ≥ 4.5:1 for body text, ≥ 3:1 for large text and UI borders. The `oklch` `L` values make
  this checkable rather than guessable.
- Severity/status conveyed by **text or icon**, never colour alone (§2).
- Every icon-only control has an `aria-label`; decorative icons are `aria-hidden`.
- Tables use real `<th scope>`; a grid of `<div>`s is unreadable to a screen reader.
- The role switcher is a labelled `<select>` or a menu button with `aria-expanded` — not a
  click-handling `<div>`.

---

## 7. Checklist

- [ ] Exactly one token file; no duplicate stylesheet with the same content.
- [ ] Only the brand ramp + font overridden; no re-declared Tailwind defaults.
- [ ] `oklch` in the CSS; hex only in comments.
- [ ] Severity/status promoted to tokens with a single mapping helper.
- [ ] Recipes used 3+ times extracted into `app/components/`.
- [ ] Dark mode either fully shipped or the variant removed.
- [ ] Focus visible, contrast checked, no colour-only meaning.

---

## 8. CORRECTION (2026-09-01) — this file described a sample, not the house system

**Everything above §8 is sourced from the third-party repo `EtienneSIG/Fabric_Fraud_analysis`.**
It is a competent baseline, but it is **not** the design system we actually ship, and an agent
that builds from §1–§7 alone produces a flat white-card app that does not look like our work.

Kept above, unchanged, because the rules are still correct *as far as they go*. What follows is
the house system, and it **supersedes §1 and §5** when building a Fabric App for this tenant.

**Provenance:** `[observed]` in the shipped app `Fab-Marketing-Campaign/app-v2` (read 2026-09-01),
itself a port of the V1 portal `portal/static/index.html`. Files cited below are the evidence.

### 8.1 Start from the shipped app, not from this file

> **Rule** `[derived]`: before writing a single screen, open `Fab-Marketing-Campaign/app-v2/src/`
> and read `main.css`, `components/AppShell.tsx`, `components/KpiCard.tsx`, `hooks/useTheme.ts`.
> Copy that system. Customise afterwards. Reading only the brain and inventing a shell is how you
> ship something "moche et sans saveur".

### 8.2 Two colour layers, not one

`@theme inline` (§1) carries the Tailwind ramp. A **second, CSS-variable layer** carries the
surfaces, and it is the one that makes the app look like an app:

```css
:root, [data-theme='light'] {
  --accent: #7c5ce6;                        /* violet, not blue */
  --accent-dark: #6242c9;
  --accent-glow: rgba(124, 92, 230, 0.14);
  --accent-soft: rgba(124, 92, 230, 0.07);
  --bg-primary: #ffffff;
  --bg-secondary: #f4f6fa;                  /* the PAGE */
  --bg-card: rgba(255, 255, 255, 0.65);     /* glass card */
  --bg-card-solid: #ffffff;                 /* the CARD */
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --border: rgba(226, 232, 240, 0.8);
  --header-bg: rgba(11, 29, 50, 0.92);      /* dark in BOTH themes */
  --shadow-md: 0 4px 16px rgba(0,0,0,.06), 0 2px 6px rgba(0,0,0,.04);
  --shadow-lg: 0 12px 40px rgba(0,0,0,.08), 0 4px 12px rgba(0,0,0,.04);
  --mesh-1: rgba(0,200,83,.07);
  --mesh-2: rgba(56,189,248,.07);
  --mesh-3: rgba(139,92,246,.05);
}
```

**`--bg-secondary` is the page and `--bg-card-solid` is the card — they must differ.** Setting both
to the same value makes cards dissolve into the page so only their borders draw them. This was a
real defect in the first dark pass `[observed]`.

### 8.3 Dark mode — `data-theme`, and it IS shipped

**This supersedes §5**, which observed a dead `.dark` variant in the sample repo and concluded
"delete the variant". That conclusion is right for that repo and **wrong as a default for us**:
our house app ships dark mode fully.

```css
@custom-variant dark (&:where([data-theme='dark'], [data-theme='dark'] *));
```

- Attribute `data-theme` on `<html>`, **not** a `.dark` class.
- Initial value written by an **inline script in `index.html` before React mounts**, so the page
  never paints light then flips.
- `hooks/useTheme.ts` only keeps React in sync with an attribute that is already correct.
- `localStorage.setItem` is wrapped in `try/catch`: storage is partitioned, and sometimes refused
  outright, inside the Fabric portal iframe. Losing the preference is acceptable; throwing is not.

Dark ramp values are chosen by **measured contrast against the card they sit on (`#1e293b`)**,
never by eye:

| Token | Dark value | Contrast on card |
|---|---|---|
| `--text-primary` | `#f1f5f9` | 13.4:1 |
| `--text-secondary` | `#cbd5e1` | 9.9:1 |
| `--text-muted` | `#94a3b8` | 5.7:1 |

`[observed]`: the first pass used `#64748b` for muted text — **3.07:1**, below the 4.5:1 AA floor.
That is exactly what "pas très lisible" looks like on screen.

### 8.4 The dark-mode retrofit — remap utilities, do not rewrite screens

`[observed]` A reusable pattern worth knowing. Screens written before the theme existed hardcode
`bg-white` / `text-slate-900` / `border-slate-200`. Rewriting ~56 call sites is a large diff across
finished pages, and every edit is a chance to change a number by accident. Instead, remap the
handful of surface utilities in one place:

```css
[data-theme='dark'] .bg-white { background-color: var(--bg-card-solid); }
[data-theme='dark'] .text-slate-900,
[data-theme='dark'] .text-gray-900 { color: var(--text-primary); }
```

Three rules that make it work, each learned from a visible failure `[observed]`:

1. **Leave these rules unlayered.** Tailwind emits utilities inside `@layer utilities`, and an
   unlayered rule beats a layered one whatever the specificity — so this cannot be defeated by
   the order Tailwind happens to emit classes in.
2. **Remap `gray-*` as well as `slate-*`.** They are different Tailwind scales; covering only
   `slate` leaves `text-gray-900` near-black on a card that just turned dark.
3. **Flip tinted alert islands too.** Leaving `bg-amber-50` light "so the alert still stands out"
   fails: on a dark page a near-white box reads as a rendering fault, not an alert. Flip the tint
   to `rgba(…, .14)` and lift its text — the alert still stands out, by hue.

**Escape hatch, by design**: port a page to `var(--…)` and it simply stops matching these rules.
A page that owns its colours opts out for free. Alpha variants (`bg-white/5`) are distinct class
names and stay untouched — that is what keeps the dark header working in both themes.

### 8.5 Glass + animated mesh

```css
@layer components {
  .glass {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-md);
  }
}
```

Backdrop: three slow blobs, `filter: blur(80px)`, 22 s drift, `pointer-events: none` so it never
eats a click, `z-index: 0` under content at `z-10`.

> **Mandatory**: wrap the animation in `@media (prefers-reduced-motion: reduce) { animation: none }`.
> An animated backdrop is decoration, never information.

### 8.6 Shell geometry `[observed]`

| Decision | Value | Why |
|---|---|---|
| `html { font-size }` | **115%** | The app is read off a projector from several metres. 13.5px body text is unreadable there. Every size in `rem` so this one dial moves everything. |
| Header height | `84px`, `sticky top-0 z-30` | — |
| Header background | `var(--header-bg)` + `blur(24px)` | Stays **dark in both themes**: the one fixed anchor while the page repaints. |
| Content width | `max-w-[1400px]` wide / `max-w-6xl` column | Landing and chat want full width; utility screens read better in a column. |
| Card radius | `rounded-xl` on `.glass` | — |

**Never set a `font-size` in px** — it escapes the 115% dial. (§1 says this; it matters more here.)

### 8.7 What replaces the flat card recipe

§3 gives `rounded-lg border bg-white p-4 shadow-sm`. The shipped equivalent is `.glass rounded-xl p-4`
with colours from variables, e.g. `KpiCard` `[observed]`:

```tsx
<div className="glass rounded-xl p-4" title={`Mesure ${measure}`}>
  <p className="text-[0.625rem] font-semibold uppercase tracking-wide"
     style={{ color: 'var(--text-muted)' }}>{label}</p>
  <p className="mt-1.5 text-xl font-bold tabular-nums"
     style={{ color: TONES[tone] }}>{value}</p>
</div>
```

Two rules behind it `[observed]`:

- **A card that hardcodes `bg-white` is not a styling detail** — it was half the app unreadable at
  night while everything around it repainted.
- **Provenance is available, never on stage.** The measure that produced the figure lives in a
  `title`, not printed under every card. Twenty English identifiers on screen read as
  instrumentation to a business audience.

### 8.8 Checklist addendum

- [ ] Read `Fab-Marketing-Campaign/app-v2/src` before designing anything.
- [ ] Second CSS-variable layer present; page and card colours differ.
- [ ] `data-theme` dark mode shipped, with the pre-mount inline script and `try/catch` storage.
- [ ] Dark text ramp verified against `#1e293b`, not chosen by eye.
- [ ] `.glass` + mesh present; mesh disabled under `prefers-reduced-motion`.
- [ ] `html { font-size: 115% }`; no `px` font sizes anywhere.
- [ ] Header dark in both themes.

**Evidence:** files read 2026-09-01 in the shipped repo —
`Fab-Marketing-Campaign/app-v2/src/main.css` (21.2 KB, §§ light/dark ramps, `.glass`, `.mesh-blob`,
the unlayered retrofit block, `.auth-bg`), `src/components/AppShell.tsx` (84px header, `--header-bg`,
`max-w-[1400px]`), `src/components/KpiCard.tsx` (`glass rounded-xl`, `title` provenance),
`src/hooks/useTheme.ts` (`data-theme`, `THEME_STORAGE_KEY`, `try/catch`),
`src/components/ThemeToggle.tsx`. Contrast figures are those recorded in the source comments by the
author of that pass.


# Design Tokens & Component Recipes

Companion to [`instructions.md`](instructions.md). Read that first — this file is the detail
behind **Rule 3**.

Provenance: token values `[observed]` in the public repo `EtienneSIG/Fabric_Fraud_analysis`
(read 2026-08-27). Everything marked `[derived]` is our rule, not theirs.

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

# Project Presentation — Known Issues & Anti-Patterns

## README

### Problem: README renders differently on GitHub vs local preview
- **Root Cause**: GitHub Flavored Markdown (GFM) differs from standard Markdown. Mermaid, HTML `<details>`, and emoji shortcodes may not render in local editors.
- **Solution**: Always preview in GitHub (push to a branch or use GitHub CLI `gh markdown-preview`). Use explicit emoji Unicode instead of `:emoji:` shortcodes for cross-platform compatibility.

### Problem: Images not displaying after push
- **Root Cause**: Relative path is wrong, or image is in `.gitignore`, or file is too large (> 25 MB).
- **Solution**: Use relative paths from the README location: `![Alt](docs/images/file.png)`. Verify the image is tracked with `git ls-files docs/images/`.

### Problem: Table of Contents links broken
- **Root Cause**: GitHub auto-generates anchor IDs by lowercasing and replacing spaces with hyphens. Special characters are stripped.
- **Solution**: `## Quick Start` → `#quick-start`. `## Q&A` → `#qa`. Test links after push.

---

## Badges

### Problem: Badge shows "invalid" or stale data
- **Root Cause**: shields.io caches results for 5 minutes. GitHub API rate limits can also cause failures.
- **Solution**: Add `?cacheSeconds=3600` to reduce cache misses. For CI badges, use GitHub's native badge URL: `https://github.com/{owner}/{repo}/actions/workflows/{file}/badge.svg`.

### Problem: Logo not showing in badge
- **Root Cause**: The `logo` parameter must match a Simple Icons slug exactly (case-sensitive).
- **Solution**: Search [simpleicons.org](https://simpleicons.org/) for the exact slug. Common: `python`, `typescript`, `microsoft`, `powerbi`, `docker`.

---

## Mermaid Diagrams

### Problem: Mermaid diagram not rendering on GitHub
- **Root Cause**: Syntax error in the diagram, or using a Mermaid feature that GitHub's version doesn't support yet.
- **Solution**: Test at [mermaid.live](https://mermaid.live/) first. Avoid bleeding-edge Mermaid features. GitHub updates Mermaid support periodically.

### Problem: Diagram too large / text unreadable
- **Root Cause**: Too many nodes for inline rendering.
- **Solution**: Break into multiple diagrams (one per subsystem). Or render as PNG/SVG and embed as an image.

---

## Repository Structure

### Problem: `.env` file committed accidentally
- **Root Cause**: `.gitignore` was added after `.env` was already tracked.
- **Solution**: `git rm --cached .env` then add to `.gitignore`. Rotate any exposed secrets immediately.

### Problem: Large files bloating the repo
- **Root Cause**: Binary files (images, data files, videos) multiply repo size.
- **Solution**: Use Git LFS for files > 1 MB. Compress images before commit. Keep demo data < 10 MB total.

---

## Community Files

### Problem: Issue template not appearing in "New Issue" dropdown
- **Root Cause**: YAML frontmatter is malformed, or file is not in `.github/ISSUE_TEMPLATE/`.
- **Solution**: Validate YAML indentation. File must have `.md` extension. The `name:` field in frontmatter is required.

### Problem: PR template not auto-populating
- **Root Cause**: File must be exactly `.github/PULL_REQUEST_TEMPLATE.md` (case-sensitive on some systems).
- **Solution**: Use exact filename. For multiple templates, use `.github/PULL_REQUEST_TEMPLATE/` folder.

---

## Documentation Accuracy

### Problem: README metrics silently drift from the code — the README scores 12/12 on the quality checklist while stating false numbers
- **Root Cause**: Counts hard-coded in prose and badges (tests passing, tables, measures, visuals, row counts) are **claims with no build-time link to their source**. Nothing fails when the code moves past them, so they age silently. The quality checklist in `readme_best_practices.md` scores structure, badges, visuals and copy-pasteable commands — none of its 12 points asks whether a stated number is still true, so a thoroughly wrong README passes it cleanly.
- **Solution**: Treat every figure in a README as a claim subject to the same evidence bar as code. **Re-derive it by executing the source of truth before writing it**, never by copying the previous README forward: run the test command and read its count; import the builder function offline and count what it actually produces; recompute dataset figures from the shipped data files. When a number cannot be reproduced by a command, delete it rather than restate it. Prefer live badges (`github/actions/workflow/status`) over hand-typed counts, and prefer a stated command over a stated result.
- **Evidence**: Refreshing the `Fab-Marketing-Campaign` README (2026-08-03) found four drifts in one file, all inherited from earlier drafts: badge `tests-39_passing` vs `python -m pytest tests/ -q` → `74 passed`; "12 tables / 48 measures" vs `build_model_bim(cfg, state)` → 12 tables, **49** measures, 11 relationships; "35/35 visual queries return data" — a figure matching nothing in the build, whose `build_report()` yields 46 visuals of which 34 carry a `prototypeQuery`; and dataset totals (37 466 orders / 5.08 M€) contradicted by recomputation from the shipped CSVs (36 508 orders / 4.96 M€).

### Problem: Figures from two different environments or data draws presented as one truth
- **Root Cause**: A demo repo usually holds at least two states — what the generator produces locally, and what is actually deployed. Both are legitimate, and each table gets labelled with whichever provenance sounded most authoritative at the time ("measured on the deployed model"), so the README ends up asserting mutually inconsistent numbers under confident labels.
- **Solution**: Label every quantitative block with the **draw and environment it came from**, and state explicitly when the two diverge and what re-syncs them. Two honest labelled numbers beat one authoritative-sounding wrong one.
- **Evidence**: Same README — a campaign-pressure table was headed "Measured on the deployed semantic model" while holding the local `data/raw` draw (3.83 sends/customer, 439 unsubscribes); the Status block a few screens below quoted the deployed draw for the same campaign (3.90, 247). Recomputing from the CSVs confirmed the local figures and showed the table's provenance label was simply wrong.

---

## Demo Videos

### Problem: the demo video renders as a download link instead of an inline player
- **Root Cause**: GitHub expands **one** form into a `<details>` + `<video>` player: a bare `https://github.com/user-attachments/assets/<guid>` URL alone on its line, whose id it resolves to a signed `private-user-images.githubusercontent.com` source. A video **committed to the repo** has no such id, so there is nothing to expand — and every intuitive alternative is blocked at a different layer: a markdown link stays a link; `raw.githubusercontent.com` serves the file `application/octet-stream` with `X-Content-Type-Options: nosniff`, which the browser will not decode; a release asset adds `response-content-disposition=attachment`; and a hand-written `<video>` tag pointing outside GitHub's media hosts is removed by the README sanitizer. The blob page playing the same file is a false lead — that is GitHub's client-side file viewer, not markdown, and a README is static sanitized HTML with no JS.
- **Solution**: Mint an attachment id through the **web UI** — New issue → "Paste, drop, or click to add files" → select the **local** file → copy the URL GitHub writes into the textarea → close the tab **without submitting** (the asset persists). Put that URL bare on its own line and keep the committed file beside it as a "Full quality" link, so the reader gets both a player and a downloadable original. There is no API and no `gh` command for this id: plan ~30 s of human action into the task instead of searching for an automated route. Verify with `gh api -X POST /markdown` **before** committing and `gh api /repos/{o}/{r}/readme -H "Accept: application/vnd.github.html+json"` after pushing — assert on the rendered HTML, never on the fact that the push succeeded.
- **Evidence**: `Fab-Marketing-Campaign`, 2026-08-31. `/markdown` (mode `gfm`) on a bare attachment URL returned `<details open>` + `<video src="https://private-user-images.githubusercontent.com/…mp4?jwt=…" controls muted>`; the same call on `<video src="https://raw.githubusercontent.com/…mp4" controls>` returned `<p dir="auto"></p>` — the tag stripped. `curl.exe -s -o NUL -D -` returned `application/octet-stream` + `nosniff` on the raw route, and a real `gh release create` asset 302'd to `…&response-content-disposition=attachment&response-content-type=application%2Foctet-stream` (throwaway release deleted afterwards with `--cleanup-tag`). The reference repo `EtienneSIG/Fabric_Fraud_analysis` carries both forms — attachment URL for the player, raw link labelled "Full quality" for the download — having reached the same conclusion independently.

### Problem: a README counter that mixes screenshots and videos breaks on every media change
- **Root Cause**: A guard test asserting "exactly N `user-attachments` URLs in the README" cannot tell a screenshot from a video player. Adding the teaser makes the count 4 and the test red, and bumping 3 → 4 hides both meanings behind one number that must be edited every time any media is touched.
- **Solution**: Split the assertion by **context, not by count**: match screenshots inside their `<img …src="…">` tag (still exactly 3) and give the player its own test asserting exactly one **bare** attachment URL on its own line. Each test then fails only for its own reason. Bumping a guard's number to make it pass is weakening it; re-scoping it is not.
- **Evidence**: `Fab-Marketing-Campaign` `tests/test_leak_guard.py`, 2026-08-31 — `test_the_committed_readme_screenshots_survive` re-scoped to `<img>` and `test_the_readme_teaser_stays_playable` added; suite 585 → 586 passing, CI green.

### Problem: a teaser ends on black, throwing away its closing message

- **Root Cause**: `fade=t=out` at the end of an `xfade` chain is the reflex ending inherited from broadcast, where black is the hand-off to the next programme. A marketing teaser has no next programme. **Playback stops on the last frame**, and that frame is what a paused player, a looping embed, a GitHub `<video>` after it ends, and a slide end-card all leave on screen. Fading to black means the call to action is on screen for a second and a half and then deliberately erased — the viewer is left looking at nothing. The first frame gets attention because a black poster obviously looks broken; the last frame gets none because the defect only shows *after* someone watches to the end, which no one does while iterating on the cut.
- **Solution**: End the chain with `[prev]null[vout]`, not `fade=t=out`, and give the final board the **longest hold** in the piece since nothing follows it. Then guard it mechanically, because a trailing fade is trivial to reintroduce and invisible to every check that only asserts duration and resolution: extract the tail with `ffmpeg -sseof -0.2` and assert its mean luminance. Two traps in that guard — `metadata=print` logs at *info* level, so `-v error` silently swallows it and the guard measures an empty list and passes; use `file=-` to force it to stdout, and **fail when the sample set is empty** rather than treating "nothing measured" as "not black". And test `min(yavg)`, not `max`: a fade darkens the *final* frames, so the darkest sample in the window is the one that gives it away.
- **Evidence**: `Azure-Brain/marketing/build_teaser.py`, 2026-09-02. With `fade=t=out:d=0.6` the tail measured `lavfi.signalstats.YAVG` falling to black; after switching to `null[vout]` the same probe over the last 0.2 s returned a flat `YAVG=47.5` across all 6 frames, and `last-frame.png` shows the composed board 10 with the repo URL. The first version of the guard used `-v error` without `file=-` and reported `ValueError: max() iterable argument is empty`; the second returned "could not measure" — both would have passed silently had the empty case been treated as success. Final run: `duration=40.100000`, exit code 0, `YAVG=47.5, not black`.

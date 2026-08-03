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

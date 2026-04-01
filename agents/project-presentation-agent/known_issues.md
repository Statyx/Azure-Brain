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

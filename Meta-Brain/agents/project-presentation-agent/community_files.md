# Community Files — LICENSE, CONTRIBUTING, Templates

## GitHub Community Health Files

GitHub recognizes these files at the repo root or in `.github/`:

| File | Purpose | Required |
|------|---------|----------|
| `README.md` | Project landing page | ✅ |
| `LICENSE` | Legal terms for usage | ✅ |
| `CONTRIBUTING.md` | How to contribute | Recommended |
| `CODE_OF_CONDUCT.md` | Community standards | Recommended |
| `SECURITY.md` | Vulnerability reporting | Recommended |
| `CHANGELOG.md` | Version history | Recommended |
| `.github/ISSUE_TEMPLATE/` | Issue templates | Recommended |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR template | Recommended |
| `.github/FUNDING.yml` | Sponsor button config | Optional |

---

## LICENSE

### Common Licenses (Quick Pick)

| License | Use when | Permissive |
|---------|----------|-----------|
| MIT | Default for most projects | ✅ Very |
| Apache 2.0 | Need patent protection | ✅ |
| GPL 3.0 | Require derivative work to be open source | ❌ Copyleft |
| BSD 2/3-Clause | Similar to MIT, fewer conditions | ✅ Very |
| Unlicense | Public domain dedication | ✅ Maximum |
| No license | ⚠️ All rights reserved by default | ❌ |

**Create via GitHub:** Repository → Add file → Create `LICENSE` → GitHub offers a template picker.

---

## CONTRIBUTING.md Template

```markdown
# Contributing to [Project Name]

Thank you for your interest in contributing!

## How to Contribute

### Reporting Bugs
1. Check [existing issues](../../issues) first
2. Use the bug report template
3. Include: steps to reproduce, expected vs actual behavior, environment

### Suggesting Features
1. Open a [feature request](../../issues/new?template=feature_request.md)
2. Describe the problem it solves, not just the solution

### Submitting Changes
1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `python -m pytest`
5. Commit: `git commit -m "feat: add your feature"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | When |
|--------|------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code change (no feature/fix) |
| `test:` | Adding tests |
| `chore:` | Build, CI, tooling |

## Code Style
- [Language-specific style rules]
- Run linter before committing

## Questions?
Open a [discussion](../../discussions) or reach out to the maintainers.
```

---

## Issue Templates

### `.github/ISSUE_TEMPLATE/bug_report.md`

```markdown
---
name: Bug Report
about: Report a bug or unexpected behavior
title: "[BUG] "
labels: bug
assignees: ''
---

## Describe the Bug
A clear description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Run '...'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Windows 11]
- Python: [e.g., 3.10.12]
- Version: [e.g., 1.2.0]

## Screenshots / Logs
If applicable, add screenshots or log output.
```

### `.github/ISSUE_TEMPLATE/feature_request.md`

```markdown
---
name: Feature Request
about: Suggest a new feature or improvement
title: "[FEATURE] "
labels: enhancement
assignees: ''
---

## Problem
What problem does this solve? What's frustrating today?

## Proposed Solution
Describe the feature you'd like.

## Alternatives Considered
Other approaches you've thought about.

## Additional Context
Screenshots, mockups, references.
```

---

## Pull Request Template

### `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## What does this PR do?
Brief description of the change.

## Related Issue
Fixes #(issue number)

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

---

## CHANGELOG.md Pattern

Use [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New feature X

### Fixed
- Bug in Y

## [1.1.0] - 2026-03-27

### Added
- Finance controller profile (18 questions)
- BPA integration (18 rules)

### Changed
- Star ratings replaced with /5 scores
- Report filename format: `result_{AgentName}_{timestamp}.txt`

### Fixed
- Action plan deduplication
- BPA-READ-001 typing

## [1.0.0] - 2026-03-15

### Added
- Initial release
- Marketing360 profile (8 questions)
- DAX quality assessment
```

---

## SECURITY.md Template

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅        |
| < 1.0   | ❌        |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Email: [security@example.com]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

We'll respond within 48 hours and provide a fix timeline.
```

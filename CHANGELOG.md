# Changelog

All notable changes to this brain are recorded here.

This repo **drives agent behaviour**, so a change here can change what a consuming project's agents
do. Pin a tag rather than tracking `main`, and read this file before moving to a newer one — see
[Use it from another repo](README.md#-use-it-from-another-repo).

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is
[semantic](https://semver.org/spec/v2.0.0.html), interpreted for a knowledge base as:

- **MAJOR** — a rule reverses, an agent is removed or renamed, a documented path stops working.
  Re-read the affected `instructions.md` before upgrading.
- **MINOR** — a new agent, brain, scenario module or capability. Additive; safe to take.
- **PATCH** — a correction, a clarification, a new `known_issues.md` entry, a test.

---

## [Unreleased]

Nothing yet.

---

## [1.0.0] — 2026-08-26

First tagged release. The brain has been in daily use for five months; this marks the point where
it became safe for someone else to depend on it.

### Added

- **Five brains, 42 agents on disk.** Fabric (24), Foundry (7 active / 11 catalogued),
  Database (4 active / 22 catalogued), Apps (2 active / 9 catalogued), Meta (5).
- **Routing-first entry point** — [`AGENTS.md`](AGENTS.md) carries the routing table, the full
  agent index and the boundary notes between confusable agents.
- **Composable scenarios** — [`Meta-Brain/SCENARIOS.md`](Meta-Brain/SCENARIOS.md): a demo is
  `preset = base + modules`, with the axes applied. 3 bases, 11 modules, named presets, and a
  documented path for composing a custom one instead of forking a base.
- **Expiry clocks** — `Meta-Brain/clocks.yaml` plus a test that fails 30 days before a documented
  retirement date passes, so the brain is rewritten before it starts giving advice about a service
  that no longer exists. The registry stores the clock, not the file list: the test scans the repo
  live, so the list cannot rot.
- **Two CI gates on every push and PR** — the cross-brain test suite (1 768 tests) and the
  public-safety scanner.
- **Evidence discipline** — every claim carries `observed` (seen in a tenant) or `doc` (from
  Microsoft Learn). Nothing is labelled *verified* without a trace or a test output behind it.
- **Contribution path** — [`CONTRIBUTING.md`](CONTRIBUTING.md), naming the five rules that
  actually fail a PR.

### Fixed

- **`instructions.md` files that exceeded the 20 KB read threshold.** An agent reads them with a
  tool that truncates at 20 480 bytes, *silently* — three agents were shipping documents that
  looked complete and were not. `migration-bo-agent` was losing its validation and cutover phases;
  `extensibility-toolkit-agent` was losing the cross-agent handoff rules. Split into companion
  files, and a test now holds the line.
- Link checking widened from `instructions.md` to **every** markdown file, with fenced-block and
  inline-code stripping so sample commands are not reported as broken links.
- Apps-Brain catalogued agent count corrected (8 → 9) across six files.

### Known limitations

- **`Apps-Brain` does not lift out on its own** — 16 % of its links are internal, by design: it is
  the layer that consumes the other brains. Take it with what it references.
- **Database-Brain agents have no `known_issues.md` yet.** The lessons exist in the Oracle →
  PostgreSQL runbook but have not been promoted into per-agent files.
- **15 planned agents in Database, 7 in Apps, 4 in Foundry.** They are catalogued with
  `status: planned` and have no `instructions.md`. The counts are stated everywhere as
  "N active / M catalogued" so the ratio is never hidden.

[Unreleased]: https://github.com/Statyx/Azure-Brain/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Statyx/Azure-Brain/releases/tag/v1.0.0

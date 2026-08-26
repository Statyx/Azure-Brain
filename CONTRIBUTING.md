# Contributing

The most valuable contribution to this repo is **a lesson learned the hard way** — an error
message and its real cause, an API that behaves differently from its documentation, a rule that
turned out to be wrong. That is what the brain is made of.

The second most valuable is telling us a rule is wrong. Open an issue; being contradicted by a
tenant is the point.

---

## Before you start

Two CI gates run on every push and pull request, and both must be green:

```bash
cd Meta-Brain
pip install -r requirements.txt          # first run only
python -m pytest tests/ -v --tb=short    # gate 1 — structure and links

cd ..
python Meta-Brain/tools/scan_public_safety.py .   # gate 2 — no client leak
```

Run them **locally before opening the PR**. They are cheap, they are the same commands CI runs,
and they catch most of what follows.

---

## The five rules that fail PRs

### 1. `instructions.md` must stay under 20 KB

An agent reads it with a tool that truncates at 20 480 bytes, and the truncation is **silent** —
the reader gets a document that looks complete and is missing its ending. A file over the cap is
therefore not "a bit long", it is quietly broken.

Over the limit? Move a coherent block into a **companion file** next to it and add a pointer in the
load order at the top of `instructions.md`. Companion files have no size cap: they are consulted
for a specific question, not mandated as a full read.

The guard is `test_instructions_readable_in_one_pass` in `Meta-Brain/tests/test_smoke.py`.

### 2. Evidence labels are not decoration

- **observed** — seen in a real tenant, with a trace, a response body or a test output behind it.
- **doc** — from Microsoft Learn or a product announcement. May not survive contact with reality.

Never write **verified** unless you can point at the artifact that proves it. A false "verified"
is worse than silence: it makes a downstream agent retry a path that cannot work, and it burns the
one thing this repo sells.

If you are unsure which label applies, it is `doc`.

### 3. Write as if the repo were already public — it is

Read [`PUBLIC_SAFETY.md`](PUBLIC_SAFETY.md) once, in full. The short version:

- The example company is always **Zava**. No customer name, ever, including in a commit message.
- GUIDs in docs and samples are **visibly fake**: `a0000000-0000-4000-a000-00000000000a`.
  Never paste one from a real tenant, even an expired one.
- No path containing an account name. Use `$PSScriptRoot`, `%USERPROFILE%`, or a relative path.
- Secrets are read at runtime. Real values live in a gitignored file with a committed
  `.example` twin beside it.

Gate 2 enforces this and it is the one that stops a customer name reaching a public repo.

### 4. The catalog must match the disk

Every brain has an `agents/_catalog.yaml`. If you add, rename or remove an agent folder, update it
in the same commit — the test suite compares the two and fails on drift.

Mark an agent `status: planned` if it is on the roadmap but has no `instructions.md` yet. That is
honest and the READMEs count it separately ("4 active / 22 catalogued"). Shipping a folder with a
placeholder `instructions.md` is not.

> **Folder depth differs per brain.** Fabric, Foundry, Apps and Meta are flat
> (`agents/<agent>/`); Database is nested by domain (`agents/<NN-domain>/<agent>/`). Tooling that
> walks agents must handle both — see `agent_dirs()` in `Meta-Brain/tests/conftest.py`.

### 5. Dated claims are on a clock

Retirement and deprecation dates are registered in `Meta-Brain/clocks.yaml`. A test fails **30 days
before** a registered date passes, so the brain gets rewritten before it starts giving advice about
a service that no longer exists. If you document a new retirement date, add it to the registry.

---

## Where a contribution goes

| You have… | It belongs in |
| --- | --- |
| An error and its real cause | `known_issues.md` of the **owning agent** |
| A gotcha that spans several brains | [`known_issues.md`](known_issues.md) at the root |
| An HTTP status with a recovery path | [`ERROR_RECOVERY.md`](ERROR_RECOVERY.md) |
| A rule that changes how work is done | the owning agent's `instructions.md` |
| Detail too long for `instructions.md` | a **companion file** beside it |
| A new end-to-end demo shape | a module or preset in [`Meta-Brain/SCENARIOS.md`](Meta-Brain/SCENARIOS.md) |

**One owner per domain.** Any agent may *read* any artifact; only its owner *modifies* it. If your
change crosses a boundary, say so explicitly in the PR — what was produced, which agent is next,
which files and IDs are affected. Routing table: [`AGENTS.md`](AGENTS.md).

Never fork a base or a preset to make a variant. Add an axis value, a module, or a preset line — a
copy goes stale exactly the way a duplicated `instructions.md` does.

---

## Style

- Follow [`agent_principles.md`](agent_principles.md) and [`shared_constraints.md`](shared_constraints.md).
- Python 3.12+, `pathlib`, type hints.
- UTF-8 everywhere, **no BOM**. In PowerShell use `[System.IO.File]::WriteAllText()`; never
  `Out-File` for JSON.
- Conventional commits, scoped by brain: `feat(fabric):`, `fix(foundry):`, `docs(brain):`,
  `test(meta):`.
- Write for an agent that will act on it, not for a reader who will admire it. Prefer a rule with
  its reason over a paragraph of context. State the failure the rule prevents.

---

## Adding a new brain

1. Create the folder, its `README.md` and `agents/_catalog.yaml`.
2. Add it to `BRAINS` in `Meta-Brain/tests/conftest.py` — that single list drives **all** test
   modules.
3. Update the brain table in [`README.md`](README.md), the brain list in
   `.github/copilot-instructions.md`, and the layout plus agent index in [`AGENTS.md`](AGENTS.md).
4. Re-run both gates.

---

## Opening the PR

Say what you changed and **what evidence you have**. A one-line PR body is fine if the evidence is
in it:

> `fix(fabric): SQL Endpoint needs a poll, not a sleep`
> Observed on 2026-08-14: endpoint returned 404 for 2m40s after lakehouse creation, then 200.
> The fixed 2-minute sleep in `lakehouse-agent` was under it. Replaced with a poll, max 5 min.

That is a perfect contribution. It is short, it is dated, it says what was seen, and the next
person will not lose an afternoon to it.

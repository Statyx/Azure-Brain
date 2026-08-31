# Known Issues — testing-agent

Gotchas hit while building and running the umbrella test suite.

---

## 1. Adding a Brain Without Updating `BRAINS` Silently Skips It

**Symptom**: a new brain is on disk, its agents look fine, the suite is green — but nothing in that
brain is actually validated. Catalog drift, missing `instructions.md` and broken links all go
undetected.

**Cause**: `BRAINS` used to be duplicated in `test_smoke.py` **and** `test_crossref.py`. Adding a
brain to one (or neither) left silent gaps. Database-Brain lived like this for a while: 4 agents,
0 tests.

**Fix**: `BRAINS` now lives **only** in [`conftest.py`](../../tests/conftest.py) and every module
imports it. Adding a brain = one line, one place.

**Detection**: compare the suite's collected count before/after adding the brain. Covering
Database-Brain took the suite from 1089 to 1117 tests — if the number does not move, the brain
is not wired in.

---

## 2. Agent Discovery Broke on a Nested Brain

**Symptom**: `agents/<domain>/<agent>/` folders were reported as agents missing `instructions.md`,
because the walker treated the **domain** folder as the agent.

**Cause**: helpers assumed one fixed depth (`agents/<agent>/`).

**Fix**: `agent_dirs()` is depth-aware — a directory directly under `agents/` is an agent when it
contains `instructions.md`, otherwise it is a domain folder whose children are agents. Works for
both layouts without configuration.

---

## 3. Catalog Disk-Sync Fails on a Roadmap

**Symptom**: `test_every_catalog_entry_on_disk` fails for a brain that intentionally declares
future agents (Database-Brain catalogs 22, only 4 are built).

**Fix**: the catalog `status` field is authoritative. Only `active` entries — or entries with **no**
status, which is the Fabric/Meta convention — are required on disk. `planned` and `deprecated` are
ignored by the disk-sync test but still validated for `name` + `purpose`.

---

## 4. `rglob("instructions.md")` Catches Template Files

**Symptom**: agents with a `templates/` subfolder produced extra, meaningless test ids.

**Fix**: build the file list from `agent_dirs()` (which returns agent roots) and join
`/ "instructions.md"`, instead of recursively globbing the whole tree.

---

## 5. Environment Traps When Running the Suite

| Trap | Symptom | Fix |
|---|---|---|
| venv activation wipes PATH | `Set-Location`/`python` "not recognized" | Restore from Machine+User env, or call Python by full path |
| PowerShell drops the first token | `$ok=1 : term not recognized` | Prefix a harmless statement, or run from a fresh terminal |
| Output swallowed on long runs | pytest prints nothing | Redirect (`*> file.txt`) and read the file |
| French locale | pytest output mixes locales | Cosmetic only — exit code is authoritative |

---

## 6. Don't Assert Coverage You Haven't Measured

Writing "all brains are covered" in a README does not make it true — the `BRAINS` list does.
Same rule as the umbrella one: **never claim "verified" without an artifact that proves it**
(a collected-test count, a trace, a run log).


---

## 7. `git checkout --` Silently Deletes an Uncommitted Test

**Symptom** (hit 2026-08-26, caught only by a test count): a new test was added to
`test_smoke.py`, temporarily weakened to prove it could fail, then "restored" with
`git checkout -- tests/test_smoke.py`. That restores the file to **HEAD**, which did not
contain the new test at all. The suite went from 1768 to 1726 passing and still said
`0 failed` — a green run that had quietly lost 42 assertions.

**Why it is dangerous here**: proving a new guard actually bites means breaking it on
purpose. The natural undo (`git checkout`) is exactly the wrong one while the guard is
still uncommitted.

**Fix**: to prove a test fails, mutate the *data* it inspects, not the test file — or
commit the test first, then experiment. If you must edit the test, restore it with an
explicit edit, never with `git checkout`.

**Detection**: a passing-test count that *drops* is the only signal. Record the expected
count before and after; "0 failed" alone does not mean the suite still exists.

---

## 8. A Generator That Reads a Gitignored File Is Reproducible on One Machine

**Symptom** (observed 2026-08-30 in a downstream project): a script generated a committed
artifact from a local config. The config was **gitignored** — CI materialised the
`config.example.yaml` instead, produced a different tree, and the "artifact matches generator
output" test went red **by construction**, on every run, forever.

**Why the test's own advice cannot fix it**: the failure message said *"re-run the generator"*.
Doing that locally re-bakes the same private values and the artifact stays machine-specific. The
advice is not just useless, it is a loop.

**Cause**: the generator's input was the private file, so "reproducible" silently meant
"reproducible where that file exists".

**Fix**: read the **committed example** as the generator's input. Two problems close at once —
the build is reproducible everywhere, and the published artifact can no longer name a tenant
resource.

**Detection**: regenerate in a temporary tree that has **no** local config and diff byte for byte.
If the two differ, the generator has a hidden input.

**Wider rule**: for any check of the form *"committed artifact == generator output"*, ask what the
generator reads. If any input is gitignored, the check can only pass on the author's machine.

---

## 9. A Skipped Test Is Not a Passing Test

**Symptom** (same session): a guard existed, was correct, and never ran — CI did not execute the
step that produced its input, so the test **skipped**. The run was green and the summary line said
so; the guard protected nothing for as long as it existed.

**Cause**: `skip` is the honest thing to do when a precondition is missing, which is exactly why it
is invisible. Nobody reads a skip count in a green run.

**Fix**: add a gate that **fails when any test was skipped** in CI (locally, skips are fine). A
skip in CI means either the precondition belongs in the pipeline, or the test does not belong in
the suite. Both are decisions; neither should be made by silence.

**Detection**: `pytest -q` prints `N passed, M skipped`. Treat a rising `M` the same way as a
falling `N` (entry 7): both are the suite quietly shrinking.

---

## 10. Grep Is the Wrong Tool to Guard Source Code

**Symptom** (same session): a guard had to assert that a generator reads `config.example.yaml`
and never `config.yaml`. A text search for `config.yaml` fired on both files immediately — their
own prose and docstrings discuss `config.yaml` at length, and `config.example.yaml` *contains*
the substring `config.yaml`.

**Fix**: parse the source with `ast` and inspect **string constants** only. The question being
asked is about values the program uses, not about words the file contains; `ast` answers that
question and a regex answers a different one.

**Companion rule — a guard must not become the leak.** When the guard's job is to catch a secret
or an endpoint, the caught value belongs in the **failure message only**. Never write it to a
report file, a fixture, or a log that gets committed — otherwise the guard publishes exactly what
it was built to stop.

**Wider rule**: before writing a text-search guard, ask whether the same string can legitimately
appear in prose. If it can, the guard needs a parser, not a better regex.
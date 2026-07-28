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

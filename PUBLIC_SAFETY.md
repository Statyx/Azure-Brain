# PUBLIC_SAFETY.md — publish by default, redact never

Every repository produced with this brain is written **as if it were already
public**. There is no anonymisation pass before sharing, because there is
nothing to anonymise: the fictional identity and the placeholder conventions
below are applied at authoring time.

Two rules carry almost all the weight:

> **1. The company is always Zava.** Never Contoso, never a real customer,
> never your employer, never your initials.
>
> **2. Real values live in gitignored files that ship as `.example` templates.**
> The working copy holds the truth; the repo holds the shape.

If you find yourself editing a file to remove something before pushing, the
convention failed — fix the convention, not just the file.

---

## 1. The fictional identity

| Slot | Value | Notes |
|---|---|---|
| Company | **Zava** | The only company name. Used across every brain, demo and sample. |
| Legal / long form | Zava Group | For document headers, invoices, sample data |
| Domain | `zava.com` | |
| Tenant domain | `zava.onmicrosoft.com` | Never a real `*.onmicrosoft.com` |
| Email | `first.last@zava.com` | e.g. `dana.reed@zava.com` |
| Workspace prefix | `Zava - ` | e.g. `Zava - Retail Analytics` |
| Resource group | `rg-zava-<workload>` | e.g. `rg-zava-retail` |
| Storage / short names | `zava<workload>` | lowercase, no separators |
| Project repo | `Zava-<Domain>` | e.g. `Zava-Retail`, `Zava-Energy` |

**Do not use a personal prefix.** A workspace called `ABC - Retail` publishes
the author's initials into every screenshot, every API response and every
sample JSON in the repo. Use `Zava - Retail`.

Divisions, when a scenario needs several: **Zava Retail**, **Zava Energy**,
**Zava Health**, **Zava Financial**, **Zava Manufacturing**.

People, when a scenario needs named users — invented, non-attributable:
`Dana Reed`, `Priya Nair`, `Marco Silva`, `Lena Fischer`, `Tom Okafor`.

> Legacy names (`Contoso`, `Tailwind`, `Northwind`, `Fabrikam`) still appear in
> older files. They are being replaced as those files are touched. Do not add
> new ones.

---

## 2. Placeholder conventions

### GUIDs

Any GUID in documentation, samples or tests must be **visibly fake**. The
canonical shape is a leading hex digit, then zeros, then a matching trailing
digit:

```
a0000000-0000-4000-a000-00000000000a
b0000000-0000-4000-a000-00000000000b
```

Use a different letter per distinct entity, and **reuse the same placeholder
for the same entity across files** — a reader must still be able to follow
"this notebook is the one that pipeline calls".

Also accepted, because they are unmistakably fake and already in use:
`00000000-…`, `11111111-…`, `12345678-1234-1234-1234-…`,
`10000000-0000-4000-a000-00000000000N` (bulk synthetic sets, e.g. Task Flow
templates).

**Never paste a GUID copied from a real tenant** — workspace, capacity, item,
subscription, tenant or object IDs. They are not credentials, but they
identify the tenant and they are exactly what creates re-anonymisation work.

### Paths

| Bad | Good |
|---|---|
| `C:\Users\alice\repo\script.sh` | `$PSScriptRoot` / `%USERPROFILE%` / `<repo>` |
| `/home/alice/project` | `$HOME/project` |
| a hardcoded absolute repo path | resolve relative to the script |

Scripts that hardcode their own location leak the author's account name *and*
break the moment the repo moves. `$PSScriptRoot` (PowerShell) and
`$(dirname "$0")` (bash) fix both at once.

### Secrets

Never a literal. Read them at runtime:

```python
pwd = notebookutils.credentials.getSecret(kv_url, "db-password")   # good
pwd = "Sup3rS3cret!"                                               # never
```

The scanner deliberately does **not** flag `x = something.get(...)` — a
retrieval is the pattern we want people to copy.

### Public Azure constants are fine

Built-in role definition IDs and first-party application IDs are documented
public values. They are allowlisted in the scanner, with a reason each. Do not
placeholder them: replacing a real role ID with a fake one produces code that
does not work.

---

## 3. Local-only files

Anything that must exist for the code to run, but must not be published,
follows one pattern:

```
<name>.<ext>            → gitignored, holds the real values
<name>.example.<ext>    → committed, same shape, placeholder values
```

Both parts are required. The umbrella link test
(`Meta-Brain/tests/test_crossref.py::_is_local_only_target`) only tolerates a
link to a missing file when the name is gitignored **and** a committed
`.example` sits beside it — so a forgotten template is caught.

Already covered in this repo: `resource_ids.md`, `environment.md` (per brain).

The `.gitignore` block to copy into any consuming demo repo:

```gitignore
# --- local-only: real values live here, templates are committed ---
resource_ids.md
environment.md
*.local.*
.env
.env.*
!.env.example
state.json
src/config.yaml
!src/config.example.yaml

# --- tool/tenant state ---
.azure/
.fabric/
*.publishsettings
**/.azure-credentials*
*.syspw.txt

# --- transient outputs that echo tenant data back ---
**/*.out.json
**/*.sh.out
```

`state.json` and `src/config.yaml` matter more than they look: deployment
scripts write **real workspace and item IDs** into them on first run. They are
the single most common way a tenant ID reaches a public repo.

---

## 4. The scanner

```bash
python Meta-Brain/tools/scan_public_safety.py .          # this repo
python Meta-Brain/tools/scan_public_safety.py ../Zava-Retail
python Meta-Brain/tools/scan_public_safety.py . --json
python Meta-Brain/tools/scan_public_safety.py . --list-allowed
```

It reads `git ls-files`, so **gitignored files are never reported** — that is
the point: keep real values locally, publish templates.

- `BLOCK` — must not be published (keys, tokens, SAS, connection-string
  passwords, tenant domains, corporate emails).
- `WARN` — usually fine, worth a glance (home paths, real-looking GUIDs).
- Exit `1` on any finding, `0` when clean. `--warn-ok` exits `0` when only
  WARNs remain.

**False positives are bugs in the scanner, not facts of life.** A scanner that
is wrong on a clean repo gets ignored, and then it protects nothing — the same
failure a permanently-red test suite causes. Either fix the rule or record the
value in `.publicsafety-allow` **with a reason**.

**A repo may exempt its own leak-guard corpus, by path.** *(2026-09-03)* The
scanner skips its own definitions — they contain every pattern by construction —
and a project that has its own leak guard needs the same. Scanning a sibling
demo repo returned **19 of 20 BLOCKs from its `tests/test_leak_guard.py`**,
which buries the one real finding; with the exemptions it reported `1 BLOCK`.
Add path lines to the same `.publicsafety-allow`:

```
# our own detection fixtures - full of the patterns on purpose
path:tests/test_leak_guard.py
path:.github/scripts/check_*.py      # globs match the relative path
```

Path-scoped, never value-scoped: allowlisting a fixture's *value* would also
silence a genuine hit of that value in shipped code. And deliberately not a
blanket `test_*.py` skip — a real GUID in a test file is still published, so
the repo must name the files, each with a reason.

The mirror image exists too, and it is where **real** customer names go —
never into the tool itself:

* `CLIENT_DENYLIST`, a comma-separated env var. In CI it is a **repository
  secret**, so the names never reach the repo, the logs or a PR diff.
* `.publicsafety-deny`, one term per line, `#` comments. **Gitignored**, for
  local runs.

`CLIENT_NAMES` in the tool holds generic English phrases only. Writing a
customer name into a public repo to prove it must not appear there is the leak
it is meant to prevent — see `known_issues.md` #47. The same rule governs
tests: a detection fixture uses a **fabricated** value of the right shape,
never a real one.

What it blocks beyond secrets, since the 2026-08-03 audit:

| Rule | Fires on |
|---|---|
| `client-name` | a generic engagement/event phrase; real names come from `CLIENT_DENYLIST` |
| `client-acronym` | the same name with the letters filed off — case-sensitive |
| `personal-workspace-prefix` | `XX - Something`, i.e. initials instead of `Zava - ` (hyphen or en dash; the em dash is this brain's title separator and is excluded) |
| `fabric-sql-endpoint` | a real `*.datawarehouse.fabric.microsoft.com` host (placeholders and the `*` form stay quiet) |
| `denylisted-term` | anything listed in this repo's `.publicsafety-deny` |

One class stays **human-reviewed**: a person's real name. A scanner can only
match names it already contains, and writing them down republishes them. Use
`<presenter name>` / `Presenter Name` in templates and check by eye.

`Meta-Brain/tests/test_public_safety.py` runs it against this repo on every
test run, so the brain cannot drift back.

---

## 5. Before publishing a demo repo

1. `python .../scan_public_safety.py <repo>` → clean, or every finding
   allowlisted with a reason.
2. `git ls-files | Select-String -Pattern "resource_ids\.md|state\.json|\.env$"`
   → empty.
3. Company name is Zava; no personal prefix in workspace or resource names.
4. Screenshots and GIFs checked by eye — the scanner cannot read images, and
   the Fabric UI shows the tenant name in the top bar.
5. `git log -p` skimmed if the repo ever held real values: **the scanner sees
   the working tree, not history.** A value that was committed and later
   removed is still public. Rewriting history (`git filter-repo`) is the only
   fix — so it is far cheaper to never commit it.

---

## 6. Where this is enforced

| Mechanism | Catches |
|---|---|
| `shared_constraints.md` rule 9 | agents authoring new content |
| `Meta-Brain/tools/scan_public_safety.py` | anything already written, any repo |
| `Meta-Brain/tests/test_public_safety.py` | drift in this brain |
| `Meta-Brain/tests/test_crossref.py` | a local-only file shipped without its template |
| `.gitignore` + `*.example.*` | real values reaching git at all |
| `.github/workflows/no-client-leak.yml` | **runs the two above on every push and PR**, plus a guard that fails if any `.pptx` is tracked |

> The workflow is not a nicety. Until 2026-08-03 this repo had the scanner, the
> tests and this document — and **no CI at all**. Nothing ever ran them, so a
> customer name, a real SQL endpoint and nine personal-prefix workspace names
> survived 73 commits. See `known_issues.md` #45. A convention nobody executes
> is a comment.


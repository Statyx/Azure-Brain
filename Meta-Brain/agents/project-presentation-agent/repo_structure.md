# Repository Structure — Folder Layouts & Naming Conventions

## Principles

1. **Predictable** — A new contributor should guess where files are without reading docs
2. **Group by owner, then flat** — One folder per thing that has a single owner (a workload, a
   package, a service); inside it, avoid nesting beyond 3 levels. Grouping by owner is what makes
   a change routable; depth inside a group is what makes it unreadable.
3. **Convention over configuration** — Follow language/framework conventions first
4. **README at every level** — Each significant folder gets a one-paragraph README

> For a Microsoft Fabric project, the "owner" is the **workload** — see
> [Microsoft Fabric Project Layout](#microsoft-fabric-project-layout--deployment-code-grouped-by-workload).

---

## Application Layout (Demo / Full-Stack)

```
project-name/
├── .github/
│   ├── workflows/           # CI/CD (GitHub Actions)
│   ├── ISSUE_TEMPLATE/      # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── images/              # Screenshots, diagrams
│   ├── setup.md             # Detailed setup guide
│   └── architecture.md      # Design decisions
├── src/                     # Application source code
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── modules/
├── tests/                   # Test files mirror src/ structure
│   ├── test_main.py
│   └── test_modules/
├── data/                    # Sample/seed data (if applicable)
│   └── sample/
├── scripts/                 # Utility scripts (setup, seed, deploy)
├── .env.example             # Environment template (never .env!)
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt         # or package.json, go.mod, etc.
└── CONTRIBUTING.md
```

---

## Library / SDK Layout

```
library-name/
├── .github/
│   └── workflows/
├── docs/
│   ├── api/                 # Generated API docs
│   └── guides/
├── src/
│   └── library_name/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
├── tests/
├── examples/                # Usage examples (runnable)
│   ├── basic_usage.py
│   └── advanced_usage.py
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml           # or setup.py, package.json
└── CHANGELOG.md
```

---

## Monorepo Layout

```
monorepo/
├── .github/
│   └── workflows/
├── packages/                # or apps/, services/, modules/
│   ├── frontend/
│   │   ├── src/
│   │   ├── package.json
│   │   └── README.md        # Package-specific README
│   ├── backend/
│   │   ├── src/
│   │   ├── requirements.txt
│   │   └── README.md
│   └── shared/
│       └── README.md
├── docs/
├── scripts/
├── .gitignore
├── LICENSE
└── README.md                # Root README links to each package
```

---

## Microsoft Fabric Project Layout — deployment code grouped **by workload**

> **This is the default layout for a Fabric demo or project.** The previous flat
> `src/deploy_*.py` variant is kept below as a fallback for a single-workload project.
>
> Provenance: adopted 2026-08-27 from the public repo `EtienneSIG/Fabric_Fraud_analysis`,
> which ships this shape end to end. The folder-per-workload convention and the
> `design/` blueprint layer are taken from it; the shared-config and explicit-ordering
> rules below are **our additions** — see [What NOT to copy](#what-not-to-copy-from-the-source-repo).

```
fabric-project/
├── .github/
│   └── copilot-instructions.md   # One line pointing at the brain + the agents used
├── artifacts/                    # Seed data, one file per target table
│   └── lakehouse_data/           # *.jsonl / *.csv — uploaded, never edited by hand
├── design/                       # ★ The CONTRACT, written before any code
│   ├── config/environments.yaml  # Named environments (local / fabric), mode switches
│   ├── contracts/                # JSON Schema of entities, agent output contracts
│   ├── screens/                  # One YAML per screen: views, filters, actions
│   ├── scoring/                  # Metric/score specs (formula, thresholds)
│   └── notebooks/                # Synthetic data generator
├── docs/
│   ├── DEPLOYMENT.md             # ★ Item inventory + deployment ORDER + validation
│   ├── images/                   # Screenshots referenced by README
│   └── demo-narrative.md         # The story told during the demo
├── fabric/                       # ★ ONE FOLDER PER WORKLOAD — never a cross-workload file
│   ├── lakehouse/
│   │   ├── upload_<domain>_data.ps1   # Push artifacts/ into Files/
│   │   ├── load_<domain>_data.py      # PySpark notebook: Files/ → Delta tables
│   │   ├── post_notebook.ps1          # Publish the notebook via REST
│   │   └── run_load.ps1               # Local orchestrator: create → trigger → poll
│   ├── ontology/
│   │   ├── <domain>_ontology.yaml     # Human-readable source of truth
│   │   ├── build_ontology.py          # Generator → create_body.json + parts/
│   │   ├── create_body.json           # GENERATED, committed for reviewability
│   │   ├── parts/                     # Decoded item parts, for inspection/diff
│   │   └── post_ontology.ps1          # Idempotent REST deploy
│   ├── data-agent/
│   │   └── deploy_data_agent.ps1
│   ├── realtime/
│   │   ├── <domain>_eventhouse.kql
│   │   ├── deploy_kql.ps1
│   │   └── ingest_kql.ps1
│   └── powerbi/
│       ├── model.bim                  # TMSL semantic model
│       ├── <name>_report/             # PBIR folder-format report
│       ├── deploy_model.ps1
│       ├── deploy_report.ps1
│       └── validate_model.ps1
├── app/                          # The application (Rayfin app, portal, SPA)
├── config.yaml                   # ★ Shared: workspace + item IDs, one source (gitignored)
├── config.example.yaml           # Committed twin
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

### Why this beats the flat `src/deploy_*.py`

A flat `src/` mixes five unrelated technologies in one namespace: PySpark, TMSL, KQL, REST
bodies, PBIR JSON. Reading the repo means reading every filename. With a folder per workload,
the reader picks the workload first and sees only its files — and each folder maps 1:1 onto
**the agent that owns that domain**, so routing a change is mechanical:

| Folder | Owning agent |
|--------|--------------|
| `fabric/lakehouse/` | [`Fabric-Brain/agents/lakehouse-agent/`](../../../Fabric-Brain/agents/lakehouse-agent/instructions.md) |
| `fabric/ontology/` | [`Fabric-Brain/agents/ontology-agent/`](../../../Fabric-Brain/agents/ontology-agent/instructions.md) |
| `fabric/data-agent/` | [`Fabric-Brain/agents/ai-skills-agent/`](../../../Fabric-Brain/agents/ai-skills-agent/instructions.md) |
| `fabric/realtime/` | [`Fabric-Brain/agents/rti-kusto-agent/`](../../../Fabric-Brain/agents/rti-kusto-agent/instructions.md) |
| `fabric/powerbi/` | [`semantic-model-agent`](../../../Fabric-Brain/agents/semantic-model-agent/instructions.md) + [`report-builder-agent`](../../../Fabric-Brain/agents/report-builder-agent/instructions.md) |
| `app/` | [`Apps-Brain/agents/`](../../../Apps-Brain/agents/_catalog.yaml) |
| `design/` | the domain owner — written before any of the above |

**Add a folder only when you add a workload.** `fabric/warehouse/`, `fabric/eventstream/`,
`fabric/graph/` follow the same rules. A workload with no deployment code gets no folder.

### Rules

**R1 — One folder per Fabric workload under `fabric/`.** No file serves two workloads. A helper
needed by two workloads goes to `fabric/_shared/`, not into whichever folder wrote it first.

**R2 — Entry point named `deploy_<artifact>.ps1`** (or `.py`). A local multi-step orchestrator
inside one workload is `run_<action>.ps1`. If you cannot name a file with that pattern, it is
not an entry point — it is a definition file.

**R3 — Separate the generator from the deployer** when an item definition is large or repetitive.
`build_*.py` produces a committed intermediate artifact (`create_body.json`); `post_*.ps1` does
the REST call. The generated file **is committed** — it is what makes a definition change
reviewable in a diff, which a base64 blob inside a script is not.

**R4 — Every deploy script is idempotent.** Check existence → create or update. A 409 reports
`EXISTS` and exits 0. Re-running the whole `fabric/` tree must be a no-op. (Umbrella rule 3.)

**R5 — Auth at runtime, never a committed secret.**
`az account get-access-token --resource https://api.fabric.microsoft.com` inside the script.

**R6 — Resource IDs are parameters with a shared default.** Every script declares
`[Parameter(Mandatory=$true)][string]$WorkspaceId` etc., **and** reads defaults from the single
`config.yaml`. Mandatory params alone force the operator to re-type GUIDs per workload — that is
how a demo ends up half-deployed across two workspaces.

**R7 — Item definitions are versioned as readable files**, then posted as
`{ parts: [{ path, payload: <base64>, payloadType: "InlineBase64" }] }`. Commit the readable
form (`.yaml`, `.bim`, `.kql`, `parts/`), not only the encoded body.

**R8 — Seed data lives in `artifacts/`, one file per target table**, uploaded by the workload
that owns the target. Never inside `fabric/`.

**R9 — `docs/DEPLOYMENT.md` carries the order and the dependency table.** It is the only place
the cross-workload sequence is stated. Typical order:

```
app scaffold → lakehouse → ontology → data-agent → realtime → powerbi
```

**R10 — `design/` is the contract, `fabric/` is the implementation.** Specs in `design/` are
YAML/JSON, never executed. They are written first and are what you diff when behaviour changes.

### What NOT to copy from the source repo

Two properties of `EtienneSIG/Fabric_Fraud_analysis` are **deliberately not adopted** — they
conflict with umbrella rules that exist because of real failures:

| Source repo does | We do instead | Why |
|---|---|---|
| No shared config; every ID is a mandatory CLI parameter, reference IDs pasted in `docs/DEPLOYMENT.md` | `config.yaml` (gitignored) + `config.example.yaml`, scripts default from it | Re-typing GUIDs per workload splits a deployment across workspaces; and real GUIDs in a committed doc is exactly what [`PUBLIC_SAFETY.md`](../../../PUBLIC_SAFETY.md) forbids |
| No global orchestrator — order is prose in `DEPLOYMENT.md`, dependencies implicit | Prose order **plus** an explicit dependency table; a `deploy_all` orchestrator once ordering stabilises | Implicit ordering is unrunnable by an agent and silently breaks when a workload is added |
| No README per workload folder | One-paragraph `README.md` per `fabric/<workload>/` | The [every-folder-gets-a-README rule](#the-every-folder-gets-a-readme-rule) below |

---

## Microsoft Fabric Project Layout — flat (single workload only)

Use this only when the project deploys **one** workload and is not expected to grow.

```
fabric-project/
├── .github/
│   └── copilot-instructions.md   # Auto-load brain context
├── docs/
│   ├── images/
│   └── setup.md
├── src/
│   ├── config.yaml               # Workspace/item IDs, parameters
│   ├── deploy_all.py             # Orchestrator script
│   ├── deploy_workspace.py
│   ├── deploy_lakehouse.py
│   ├── deploy_eventhouse.py
│   ├── helpers.py                # Auth, API calls, LRO polling
│   └── state.json                # Deployment state tracking
├── notebooks/                    # Fabric notebooks (.ipynb)
├── data/
│   ├── raw/                      # Dimension CSVs, seed data
│   └── sample/
├── profiles/                     # Test profiles (if using analyzer)
│   └── marketing360/
│       ├── profile.yaml
│       └── questions.yaml
├── knowledge_base/               # Domain docs for AI/agent context
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

> **The moment a second workload appears, migrate to the by-workload layout above.** Splitting
> later is cheap (files move, imports rarely cross); untangling a flat `src/` that grew five
> technologies deep is not.

---

## Documentation-Only Layout

```
docs-project/
├── docs/
│   ├── getting-started.md
│   ├── concepts/
│   ├── guides/
│   ├── reference/
│   └── images/
├── .gitignore
├── LICENSE
└── README.md                     # Index/overview linking to docs/
```

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Repository | `kebab-case` | `fabric-rti-demo` |
| Folders | `snake_case` or `kebab-case` (pick one, be consistent) | `data_engineering/` |
| Fabric workload folder | `kebab-case`, the workload's common name | `fabric/data-agent/` |
| Deploy entry point | `deploy_<artifact>.ps1` / `.py` | `deploy_model.ps1` |
| Local orchestrator (one workload) | `run_<action>.ps1` | `run_load.ps1` |
| Definition generator | `build_<item>.py` → committed artifact | `build_ontology.py` |
| Python files | `snake_case` | `deploy_lakehouse.py` |
| JS/TS files | `camelCase` or `kebab-case` | `deployLakehouse.ts` |
| Config files | `lowercase` with dots | `config.yaml`, `.env.example` |
| Documentation | `UPPERCASE` for root docs | `README.md`, `CONTRIBUTING.md` |
| Images | `kebab-case` with descriptive names | `architecture-overview.png` |

> 🔴 **Correction 2026-09-03 — Fabric workload folders in a Python repo must be `snake_case`.**
> The `Fabric workload folder` row above mandates `kebab-case` (`fabric/data-agent/`). That is
> **unimplementable when the workload folder is a Python package**: a hyphen is not a valid
> Python identifier, so the folder can never be imported.
>
> ```
> >>> import fabric.data-agent
> SyntaxError: invalid syntax
> >>> import fabric.data_agent
> OK
> ```
>
> **Rule.** When `fabric/<workload>/` holds `.py` modules that are imported — which is the case
> in the by-workload layout above, where `deploy_all.py` drives each step through `importlib` —
> the folder **must** be `snake_case`: `fabric/data_agent/`. `kebab-case` remains correct for
> workload folders holding only `.ps1`, notebooks or artifacts, which are never imported.
> Applying the row above literally produces a repo whose own orchestrator cannot load it.
>
> **Evidence:** `Statyx/Fab-Zava-Media` commit `36dfa20` — 8 workload packages under `fabric/`,
> 18/18 modules importable via `importlib.import_module`, 192 tests green. The `SyntaxError`
> above is the actual interpreter output from that repo.

---

## .gitignore Essentials

Always include:

```gitignore
# Environment
.env
.env.local
*.env

# IDE
.vscode/settings.json
.idea/
*.swp

# Python
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/

# Node
node_modules/
dist/
.next/

# OS
.DS_Store
Thumbs.db

# Secrets — NEVER commit
*.key
*.pem
*.pfx
```

---

## The "Every Folder Gets a README" Rule

For any folder with ≥ 3 files, add a one-paragraph `README.md`:

```markdown
# /artifacts/lakehouse_data

Raw dimension tables used for seeding the Lakehouse.
These files are uploaded via `fabric/lakehouse/upload_lakehouse_data.ps1` and must not be
modified manually.

| File | Rows | Purpose |
|------|------|---------|
| `dim_sensors.csv` | 150 | Sensor metadata |
| `dim_sites.csv` | 12 | Factory sites |
| `dim_zones.csv` | 48 | Production zones |
```

This prevents the "what are all these files?" question.

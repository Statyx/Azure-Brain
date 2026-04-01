# Repository Structure — Folder Layouts & Naming Conventions

## Principles

1. **Predictable** — A new contributor should guess where files are without reading docs
2. **Flat over deep** — Avoid nesting beyond 3 levels
3. **Convention over configuration** — Follow language/framework conventions first
4. **README at every level** — Each significant folder gets a one-paragraph README

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

## Microsoft Fabric Project Layout

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
| Python files | `snake_case` | `deploy_lakehouse.py` |
| JS/TS files | `camelCase` or `kebab-case` | `deployLakehouse.ts` |
| Config files | `lowercase` with dots | `config.yaml`, `.env.example` |
| Documentation | `UPPERCASE` for root docs | `README.md`, `CONTRIBUTING.md` |
| Images | `kebab-case` with descriptive names | `architecture-overview.png` |

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
# /data/raw

Raw dimension tables used for seeding the Lakehouse.
These CSVs are uploaded via `src/deploy_lakehouse.py` and must not be modified manually.

| File | Rows | Purpose |
|------|------|---------|
| `dim_sensors.csv` | 150 | Sensor metadata |
| `dim_sites.csv` | 12 | Factory sites |
| `dim_zones.csv` | 48 | Production zones |
```

This prevents the "what are all these files?" question.

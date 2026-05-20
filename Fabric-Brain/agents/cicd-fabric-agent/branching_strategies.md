# Branching Strategies — Fabric CI/CD

## Overview

Fabric Git integration links one workspace to one branch. Choosing the right branching strategy depends on team size, release cadence, and isolation needs.

---

## Strategy Comparison

| Strategy | Team Size | Complexity | Best For |
|----------|-----------|-----------|----------|
| **Trunk-Based** | 1–3 devs | Low | Solo devs, rapid iteration, small projects |
| **Feature Branch** | 2–8 devs | Medium | Standard team development with PRs |
| **GitFlow** | 5+ devs | High | Large teams, scheduled releases, multiple environments |
| **Release Branch** | 3+ devs | Medium | Continuous delivery with release gating |

---

## Trunk-Based Development

```
main ─────●─────●─────●─────●─────●───────
           \   /       \   /
            ─●─         ─●─
          (feature)   (feature)
          (hours)     (hours)
```

### Setup

| Component | Config |
|-----------|--------|
| **Main branch** | `main` — always deployable |
| **Dev workspace** | Connected to `main` |
| **Feature work** | Short-lived branches (hours–1 day), merge via PR |
| **Deployment** | Deployment pipeline from Dev → Test → Prod |

### Pros & Cons

| Pros | Cons |
|------|------|
| Simple, fast feedback | No isolation for long-running features |
| Always releasable | Requires discipline for small commits |
| Minimal merge conflicts | Feature flags needed for incomplete work |

---

## Feature Branch Strategy

```
main    ─────●───────────●───────────●─────
              \         / \         /
  feature/1    ──●──●──●   \       /
                            ──●──●
                          feature/2
```

### Setup

| Component | Config |
|-----------|--------|
| **Main branch** | `main` — protected, PR-only merges |
| **Dev workspace** | Connected to `main` |
| **Feature workspaces** | One per feature branch (via "Branch Out" or manual) |
| **PR flow** | Create PR → review → merge to main → update Dev workspace |

### Workspace-per-Branch Pattern

```
Branch out from Dev workspace:
├── Workspace "Dev" → main branch
├── Workspace "Feature-Auth" → feature/auth branch
├── Workspace "Feature-ETL" → feature/etl branch
└── Feature done → merge PR → delete branch + workspace
```

> **Key**: When feature is merged, switch workspace branch or delete the feature workspace. Don't leave stale workspaces.

### Pros & Cons

| Pros | Cons |
|------|------|
| Feature isolation | More workspaces to manage |
| Parallel development | Capacity cost per workspace |
| PR-based reviews | Merge conflicts if branches live too long |

---

## GitFlow Strategy

```
main     ─────────────────────●───────────────●────
                             / \             / \
release  ────────────●──●──●    \     ●──●──●   \
                    / \          \   / \          \
develop  ──●──●──●──   ──●──●──●──●──   ──●──●──●──
            \   /         \   /
             ─●─           ─●─
          (feature)     (feature)
```

### Setup

| Component | Config |
|-----------|--------|
| **main** | Production-ready, tagged releases |
| **develop** | Integration branch, always latest |
| **feature/*** | Feature branches from develop |
| **release/*** | Release candidate branches from develop |
| **Dev workspace** | Connected to `develop` |
| **Test workspace** | Connected to `release/*` |
| **Prod workspace** | Connected to `main` (or via deployment pipeline) |

### Pros & Cons

| Pros | Cons |
|------|------|
| Clear release process | Complex branching model |
| Hotfix support | Slow feedback loop |
| Parallel release streams | Merge overhead |

---

## Release Branch Strategy

```
main    ────●────────●────────●─────────
             \      / \      /
  release/1   ──●──●   \    /
                       ──●──●
                     release/2
```

### Setup

| Component | Config |
|-----------|--------|
| **main** | Development branch (latest) |
| **release/*** | Cut from main when ready to ship |
| **Dev workspace** | Connected to `main` |
| **Test workspace** | Switch to `release/*` branch before each release |
| **Deployment** | Release branch → Test → Prod via deployment pipeline |

> **Microsoft recommendation**: Use release branches when deploying to production via Git instead of deployment pipelines. Switch workspace connection to the release branch before each deployment.

---

## Practical Recommendations

### For New Fabric Projects

```
├── Solo dev / demo → Trunk-based
│   ├── One workspace → main
│   └── Deploy manually or via simple pipeline
│
├── Small team (2–5 devs) → Feature Branch
│   ├── Dev workspace → main
│   ├── Branch out for features
│   └── Deployment pipeline: Dev → Test → Prod
│
└── Large team (5+ devs) → GitFlow or Release Branch
    ├── Dev workspace → develop
    ├── Feature workspaces → feature/*
    ├── Test workspace → release/*
    └── Deployment pipeline for promotion
```

### Workspace Reuse Tips

- **Reuse feature workspaces**: After merging, switch the workspace to a new feature branch instead of creating a new workspace.
- **Use client tools** (VS Code, Power BI Desktop) to reduce the need for per-feature workspaces. Commit locally → push → PR → merge.
- **Use `%%configure`** in notebooks to dynamically set Lakehouse references per workspace (variable library).

---

## Branch Protection

| Setting | Recommendation |
|---------|---------------|
| **Require PR for main** | Always — prevents direct commits to production-tracked branch |
| **Require at least 1 reviewer** | For Test/Prod-connected branches |
| **Require status checks** | Run lint/test before merge (if using external CI) |
| **Delete branch after merge** | Keep repo clean |
| **Branch naming convention** | `feature/`, `bugfix/`, `release/` prefixes |

---

## Cross-References

- Git integration: `git_integration.md`
- Environment promotion: `environment_promotion.md`
- Workspace management: `../workspace-admin-agent/instructions.md`

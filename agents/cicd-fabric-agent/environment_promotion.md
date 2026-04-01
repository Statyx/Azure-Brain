# Environment Promotion — Fabric CI/CD

## Overview

Environment promotion is the process of moving Fabric content through Dev → Test → Prod stages with environment-specific configurations. This combines deployment pipelines, variable libraries, and deployment rules into a cohesive release workflow.

---

## The Recommended Flow

```
┌──────────────────────────────────────────────────────┐
│   Developer Workspace (Dev)                          │
│   ├── Connected to Git (main or develop branch)      │
│   ├── Variable Library: active = "dev"               │
│   └── Items under development                        │
└──────────────┬───────────────────────────────────────┘
               │ Deploy via Pipeline or Git
               ▼
┌──────────────────────────────────────────────────────┐
│   Test Workspace (Test)                              │
│   ├── Connected to release/* branch (optional)       │
│   ├── Variable Library: active = "test"              │
│   └── Simulates production environment               │
└──────────────┬───────────────────────────────────────┘
               │ Deploy via Pipeline (gated)
               ▼
┌──────────────────────────────────────────────────────┐
│   Production Workspace (Prod)                        │
│   ├── Connected to main branch (optional)            │
│   ├── Variable Library: active = "prod"              │
│   └── Content consumed by business users             │
└──────────────────────────────────────────────────────┘
```

---

## Pre-Deploy Checklist

### Before Deploying to Test

- [ ] All changes committed to Git
- [ ] PR approved and merged (if using feature branches)
- [ ] Variable library value set "test" configured with test data sources
- [ ] Test capacity available
- [ ] Semantic model data source points to test database
- [ ] Notebooks reference correct Lakehouse (via variable library)

### Before Deploying to Prod

- [ ] Functional testing completed in Test workspace
- [ ] Performance testing done with production-like data volumes
- [ ] Variable library value set "prod" configured with production data sources
- [ ] Production capacity available
- [ ] Deployment pipeline permissions verified (Pipeline Admin or Member)
- [ ] App update planned (deployment doesn't auto-update apps)
- [ ] Rollback plan documented
- [ ] Stakeholders notified of deployment window

---

## Environment-Specific Configuration Patterns

### Pattern 1: Variable Libraries (Recommended)

```
Variable Library "EnvConfig":
├── connection_string:
│   ├── dev:  "Server=dev-sql.database.windows.net;Database=SalesDB"
│   ├── test: "Server=test-sql.database.windows.net;Database=SalesDB"
│   └── prod: "Server=prod-sql.database.windows.net;Database=SalesDB"
├── lakehouse_ref:
│   ├── dev:  → Dev-Lakehouse (item reference)
│   ├── test: → Test-Lakehouse (item reference)
│   └── prod: → Prod-Lakehouse (item reference)
└── max_rows:
    ├── dev:  1000
    ├── test: 100000
    └── prod: -1 (unlimited)
```

### Pattern 2: Deployment Pipeline Parameter Rules

```
When deploying from Dev → Test:
├── Semantic model data source: dev-sql → test-sql
├── Parameters: MaxRows = 100000
└── Other configs applied automatically
```

### Pattern 3: fab CLI Parameter Files

```yaml
# params.yml (used with fab deploy)
find_replace:
  - find_value: "dev-sql.database.windows.net"
    replace_value:
      dev: "dev-sql.database.windows.net"
      test: "test-sql.database.windows.net"
      prod: "prod-sql.database.windows.net"
```

> Defer to `fabric-cli-agent` for `fab deploy` config details.

---

## Data Source Separation

| Stage | Data Source | Purpose |
|-------|-----------|---------|
| Dev | Small sample dataset | Fast iteration, cheap |
| Test | Production-like volume | Performance testing, integration testing |
| Prod | Production data | Real business data |

> **Rule**: Never point Dev/Test at production data sources. Use separate databases per stage.

---

## Post-Deploy Validation

After deploying to each stage:

1. **Verify item count** — all expected items present
2. **Check data source connections** — correct stage-specific sources
3. **Run a data refresh** — semantic models, lakehouses refresh successfully
4. **Test report rendering** — reports load without errors
5. **Validate variable resolution** — notebooks/pipelines use correct values
6. **Check app update** — if distributing via app, manually update the app

```http
# Verify deploy operation succeeded
GET /v1/deploymentPipelines/{id}/operations/{operationId}
→ { "status": "Succeeded", "executionPlan": { ... } }
```

---

## Rollback Procedures

### Scenario 1: Deployment Pipeline Rollback

```
Production has bad content → backward deploy from Test or Dev

POST /v1/deploymentPipelines/{id}/deploy
{
  "sourceStageId": "test-stage-guid",
  "targetStageId": "prod-stage-guid",
  "isBackwardDeployment": false,  // forward deploy the known-good version
  "options": { "allowOverwriteArtifact": true }
}
```

> **Note**: Backward deploy (`isBackwardDeployment: true`) only works for NEW items. For overwriting, do a forward deploy from the last-known-good stage.

### Scenario 2: Git Rollback

```bash
# Revert to previous commit
git revert HEAD
git push

# Then update workspace from Git
POST /v1/workspaces/{id}/git/updateFromGit
{
  "conflictResolutionPolicy": "PreferRemote"
}
```

### Scenario 3: Data Item Rollback

> **Warning**: Git does NOT store data (only definitions). Reverting a data item (Lakehouse, Warehouse) may break existing data. Test the revert in Dev/Test first.

---

## Timing and Scheduling

| Consideration | Recommendation |
|---------------|---------------|
| Deploy window | Off-peak hours to minimize user impact |
| Data refresh scheduling | Pause scheduled refreshes during deploy, resume after validation |
| Multiple pipelines | Deploy upstream pipelines first (e.g., shared semantic models before reports) |
| Cascading dependencies | Use API automation to orchestrate sequential deploys |

---

## Permission Model Summary

| Role | Dev | Test | Prod |
|------|-----|------|------|
| **Developers** | Workspace Member + Git write | Viewer (review only) | No access |
| **Reviewers / QA** | Viewer | Workspace Member | Viewer |
| **Release Manager** | Viewer | Pipeline Admin | Pipeline Admin + Workspace Admin |
| **Business Users** | No access | No access | App consumer or Viewer |

---

## Cross-References

- Deployment pipelines: `deployment_pipelines.md`
- Variable libraries: `variable_libraries.md`
- External CI/CD automation: `external_cicd.md`
- Workspace RBAC: `../workspace-admin-agent/instructions.md`
- fab CLI parameter files: `../fabric-cli-agent/cicd_deploy.md`

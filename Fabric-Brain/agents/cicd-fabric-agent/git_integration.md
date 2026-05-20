# Git Integration — Fabric CI/CD

## Overview

Git integration in Microsoft Fabric connects workspaces to Git repositories (Azure DevOps, GitHub, GitHub Enterprise — cloud-only). It enables version control, branching, collaboration, and backup for Fabric items at the workspace level.

---

## Supported Git Providers

| Provider | Supported | Notes |
|----------|-----------|-------|
| Azure DevOps (cloud) | Yes | SSO or SPN auth |
| GitHub (cloud) | Yes | SSH or PAT auth |
| GitHub Enterprise (cloud) | Yes | Custom domain NOT supported for on-prem Enterprise Server |
| Azure DevOps Server (on-prem) | No | — |
| GitLab | No | — |
| Bitbucket | No | — |

---

## Supported Items for Git Integration

### Generally Available

| Category | Items |
|----------|-------|
| **Data Engineering** | Environment, GraphQL, Lakehouse, Notebook, Spark Job Definition, User Data Functions |
| **Data Factory** | Copy Job, Dataflow Gen2, Pipeline, Mirrored Database, Mount ADF |
| **Real-Time Intelligence** | Eventhouse, EventStream, KQL Database, KQL Queryset, Real-time Dashboard |
| **Database** | SQL Database |

### Preview

| Category | Items |
|----------|-------|
| **Data Science** | ML Experiments, ML Models, Data Agents |
| **Data Factory** | Mirrored Snowflake |
| **Real-Time Intelligence** | Activator, Event Schema Set, Maps, Anomaly Detection |
| **Power BI** | Metrics Set, Org App, Paginated Report, Report, Semantic Model |
| **Data Warehouse** | Warehouse, Mirrored Azure Databricks Catalog |
| **Database** | Cosmos Database |
| **Graph** | Graph |
| **Industry** | Healthcare, HealthCare Cohort |

> **Key**: If an item type isn't listed, it exists in the workspace but is invisible to Git. It won't be committed, updated, or synced.

---

## Connect Workspace to Git

### Prerequisites

1. **Workspace Admin** permissions
2. Git integration **enabled** in Fabric admin settings
3. Fabric **capacity** assigned to workspace
4. Git provider access with write permissions
5. Auth method in Fabric ≥ auth method in Git (e.g., Git requires MFA → Fabric must too)

### REST API Flow

```
Step 1 — Connect
POST /v1/workspaces/{workspaceId}/git/connect
Body:
{
  "gitProviderDetails": {
    "organizationName": "myorg",       // Azure DevOps org
    "projectName": "myproject",        // Azure DevOps project
    "gitProviderType": "AzureDevOps",  // or "GitHub"
    "repositoryName": "my-repo",
    "branchName": "main",
    "directoryName": "/"               // root or subfolder
  }
}

Step 2 — Initialize Connection
POST /v1/workspaces/{workspaceId}/git/initializeConnection
Body:
{
  "initializationStrategy": "PreferWorkspace"  // or "PreferRemote"
}
// PreferWorkspace → workspace content wins on conflicts
// PreferRemote → Git content wins on conflicts
```

### Check Connection Status

```
GET /v1/workspaces/{workspaceId}/git/connection
→ Returns: gitProviderDetails, branch, directory, syncStatus
```

---

## Commit Changes to Git

```
Step 1 — Check status
GET /v1/workspaces/{workspaceId}/git/status
→ Returns list of items with changes (added, modified, deleted)

Step 2 — Commit
POST /v1/workspaces/{workspaceId}/git/commitToGit
Body:
{
  "mode": "All",           // or "Selective"
  "comment": "feat: add new report",
  "items": [               // only for "Selective" mode
    { "logicalId": "...", "objectId": "..." }
  ]
}
```

> **Tip**: Commit related changes together. Items that depend on each other (e.g., semantic model + report) should be in the same commit.

---

## Update Workspace from Git

```
POST /v1/workspaces/{workspaceId}/git/updateFromGit
Body:
{
  "remoteCommitHash": "abc123...",  // target commit
  "conflictResolutionPolicy": "PreferRemote",  // or "PreferWorkspace"
  "options": {
    "allowOverrideItems": true
  }
}
```

---

## Disconnect Workspace

```
POST /v1/workspaces/{workspaceId}/git/disconnect
// Items remain in workspace but are no longer synced
```

---

## Conflict Resolution

Conflicts occur when both workspace and Git have changes to the same item.

| Strategy | Behavior |
|----------|----------|
| `PreferWorkspace` | Workspace version wins — Git changes are overwritten |
| `PreferRemote` | Git version wins — workspace items are overwritten |

> **Best practice**: Resolve conflicts in Git (PR reviews), not in the Fabric portal. Use feature branches + PR merge.

---

## Branching Out

"Branch out" creates a new workspace from an existing Git-connected workspace on a new branch.

```
UI only — no REST API for branch out currently.
Requirements:
├── Git integration enabled
├── Available capacity for new workspace
├── User = Workspace Admin on target
├── Branch and workspace name limits apply
└── Only Git-supported items appear in new workspace
```

**Warning**: Items NOT saved to Git get lost when branching out. Always commit first.

---

## Key Limitations

| Limitation | Detail |
|------------|--------|
| **Max file size** | 25 MB per file |
| **Max items per workspace** | 1,000 items (synced from Git) |
| **Max directory depth** | 10 levels |
| **Max commit size (ADO + SPN)** | 25 MB |
| **Max commit size (ADO + SSO)** | 125 MB |
| **Submodules** | Not supported |
| **Sovereign clouds** | Not supported |
| **B2B** | Not supported |
| **Sensitivity labels** | Require admin override to commit |
| **CRLF line breaks** | Converted to LF on commit from service |
| **MyWorkspace** | Cannot connect to Git |
| **Template apps** | Workspace with template apps cannot connect |
| **Concurrent ops** | Cannot commit and update at the same time |
| **Duplicate names** | Not allowed — commit/update fails |

---

## Cross-References

- Source code format: `source_code_formats.md`
- Branching patterns: `branching_strategies.md`
- REST API auth: `../../fabric_api.md`
- Workspace permissions: `../workspace-admin-agent/instructions.md`

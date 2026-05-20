# Git Integration — Version Control for Fabric Workspaces

## Overview

Fabric workspaces can be connected to Azure DevOps or GitHub repositories. This enables:
- Version control for Fabric items (notebooks, reports, semantic models)
- Multi-environment promotion (Dev → Test → Prod)
- Collaboration via branches and pull requests
- Audit trail for all changes

---

## Connecting a Workspace to Git

### Prerequisites
1. Tenant setting enabled: **Git integration** (Admin Portal → Tenant Settings)
2. Azure DevOps repo **OR** GitHub repo available
3. User must be workspace Admin

### Via REST API

```python
API = "https://api.fabric.microsoft.com/v1"

def connect_workspace_to_git(
    workspace_id: str, 
    provider: str,      # "AzureDevOps" or "GitHub"
    org_name: str,       # Azure DevOps org or GitHub owner
    project_name: str,   # Azure DevOps project (not used for GitHub)
    repo_name: str,
    branch_name: str,
    directory_name: str,  # Folder in repo (e.g., "/fabric" or "/")
    token: str
):
    """Connect a workspace to a Git repository."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    git_connection = {
        "gitProviderDetails": {
            "gitProviderType": provider,
            "organizationName": org_name,
            "repositoryName": repo_name,
            "branchName": branch_name,
            "directoryName": directory_name
        }
    }
    
    if provider == "AzureDevOps":
        git_connection["gitProviderDetails"]["projectName"] = project_name
    
    resp = requests.post(
        f"{API}/workspaces/{workspace_id}/git/connect",
        headers=headers,
        json=git_connection
    )
    resp.raise_for_status()
    print(f"✅ Workspace connected to {provider}: {org_name}/{repo_name} ({branch_name})")
```

### Via Fabric Portal (Manual)
1. Open Workspace → Settings → Git integration
2. Select provider (Azure DevOps / GitHub)
3. Select organization / owner
4. Select repository and branch
5. Select folder (or root `/`)
6. Click Connect

---

## Git Sync Operations

### Initialize Connection (First Time)
After connecting, you must perform an initial sync to populate the repo or workspace:

```python
def initialize_git_connection(workspace_id: str, initialization_strategy: str, token: str):
    """
    Initialize Git connection.
    
    Args:
        initialization_strategy: 
            "PreferWorkspace" — push workspace items TO git
            "PreferRemote" — pull git content INTO workspace
    """
    resp = requests.post(
        f"{API}/workspaces/{workspace_id}/git/initializeConnection",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"initializationStrategy": initialization_strategy}
    )
    # Returns 200 (sync) or 202 (long-running)
    if resp.status_code == 202:
        poll_long_running(resp.headers.get("Location"), token)
    print(f"✅ Git connection initialized with strategy: {initialization_strategy}")
```

### Commit Changes to Git
Push workspace changes to the connected branch:

```python
def commit_to_git(workspace_id: str, commit_message: str, token: str, items: list = None):
    """
    Commit workspace changes to Git.
    
    Args:
        items: Optional list of specific items to commit. If None, commits all changes.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    body = {
        "mode": "All",  # or "Selective"
        "comment": commit_message
    }
    
    if items:
        body["mode"] = "Selective"
        body["items"] = [{"objectId": item_id} for item_id in items]
    
    resp = requests.post(
        f"{API}/workspaces/{workspace_id}/git/commitToGit",
        headers=headers,
        json=body
    )
    if resp.status_code == 202:
        poll_long_running(resp.headers.get("Location"), token)
    print(f"✅ Committed to Git: {commit_message}")
```

### Update from Git
Pull latest changes from Git into workspace:

```python
def update_from_git(workspace_id: str, token: str, conflict_resolution: str = "PreferRemote"):
    """
    Pull changes from Git into workspace.
    
    Args:
        conflict_resolution: "PreferRemote" (Git wins) or "PreferWorkspace" (workspace wins)
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Get current status first
    status = get_git_status(workspace_id, token)
    remote_commit = status.get("remoteCommitHash")
    
    resp = requests.post(
        f"{API}/workspaces/{workspace_id}/git/updateFromGit",
        headers=headers,
        json={
            "remoteCommitHash": remote_commit,
            "conflictResolution": {
                "conflictResolutionType": conflict_resolution
            }
        }
    )
    if resp.status_code == 202:
        poll_long_running(resp.headers.get("Location"), token)
    print(f"✅ Updated from Git (conflict resolution: {conflict_resolution})")
```

### Get Git Status
Check for pending changes between workspace and Git:

```python
def get_git_status(workspace_id: str, token: str) -> dict:
    """Get sync status between workspace and Git."""
    resp = requests.get(
        f"{API}/workspaces/{workspace_id}/git/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    status = resp.json()
    print(f"  Workspace head: {status.get('workspaceHead', 'N/A')}")
    print(f"  Remote commit:  {status.get('remoteCommitHash', 'N/A')}")
    changes = status.get("changes", [])
    if changes:
        for change in changes:
            print(f"  {change['changeType']}: {change['itemType']} — {change.get('displayName', '?')}")
    else:
        print("  No pending changes")
    return status
```

### Disconnect from Git

```python
def disconnect_git(workspace_id: str, token: str):
    """Disconnect workspace from Git."""
    resp = requests.post(
        f"{API}/workspaces/{workspace_id}/git/disconnect",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    print("✅ Workspace disconnected from Git")
```

---

## Branching Strategy for Fabric

### Recommended: Environment-Per-Branch

```
main ─────────────────────── (Prod workspace)
  └── develop ────────────── (Dev workspace)
        ├── feature/add-report
        └── feature/new-pipeline
```

| Branch | Workspace | Purpose |
|--------|-----------|---------|
| `main` | `ProjectName-Prod` | Production — stable, reviewed |
| `develop` | `ProjectName-Dev` | Active development |
| `feature/*` | Local / PR only | Individual feature work |

### Workflow
1. Developer creates feature branch from `develop`
2. Makes changes in Dev workspace (connected to `develop`)
3. Commits changes to Git
4. Creates Pull Request from feature → develop
5. Code review + approval
6. Merge to `develop` → Dev workspace auto-updates
7. When ready for production: PR from `develop` → `main`
8. Merge to `main` → Prod workspace auto-updates

---

## Deployment Pipelines (Alternative to Git)

Fabric also offers built-in Deployment Pipelines for promoting items between stages.

### Create Deployment Pipeline

```python
def create_deployment_pipeline(pipeline_name: str, stages: list, token: str) -> str:
    """
    Create a deployment pipeline with stages.
    
    Args:
        stages: e.g., ["Development", "Test", "Production"]
    """
    resp = requests.post(
        f"{API}/deploymentPipelines",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "displayName": pipeline_name,
            "description": f"Deploy pipeline for {pipeline_name}"
        }
    )
    resp.raise_for_status()
    pipeline_id = resp.json()["id"]
    
    # Assign workspaces to stages
    pipeline_stages = requests.get(
        f"{API}/deploymentPipelines/{pipeline_id}/stages",
        headers={"Authorization": f"Bearer {token}"}
    ).json()["value"]
    
    # Match stages to workspaces
    for i, stage in enumerate(pipeline_stages):
        if i < len(stages):
            print(f"  Stage {stage['order']}: {stage['displayName']}")
            # Assign workspace via:
            # POST /deploymentPipelines/{id}/stages/{stageId}/assignWorkspace
    
    return pipeline_id
```

### Deploy Between Stages

```python
def deploy_to_stage(pipeline_id: str, source_stage_id: str, token: str, 
                    items: list = None, note: str = ""):
    """Deploy items from one stage to the next."""
    body = {
        "sourceStageId": source_stage_id,
        "isBackwardDeployment": False,
        "newDeployment": False
    }
    if items:
        body["items"] = items
    if note:
        body["note"] = note
    
    resp = requests.post(
        f"{API}/deploymentPipelines/{pipeline_id}/deploy",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body
    )
    if resp.status_code == 202:
        poll_long_running(resp.headers.get("Location"), token)
    print(f"✅ Deployment completed")
```

---

## Git vs Deployment Pipelines

| Feature | Git Integration | Deployment Pipelines |
|---------|----------------|---------------------|
| Version control | ✅ Full Git history | ❌ No history |
| Branching | ✅ Feature branches, PRs | ❌ Linear stages only |
| Code review | ✅ Via PR process | ❌ No review mechanism |
| Multi-stage | ✅ Via branches | ✅ Built-in stages |
| Ease of setup | Medium | Easy |
| Works offline | ✅ | ❌ |
| Non-developer friendly | ❌ | ✅ |

**Recommendation**: Use Git for developer-heavy teams. Use Deployment Pipelines for business-user-managed promotions.

---

## Utility: Long-Running Operation Polling

```python
import time

def poll_long_running(location_url: str, token: str, timeout: int = 300):
    """Poll a long-running operation until completion."""
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(timeout // 5):
        resp = requests.get(location_url, headers=headers)
        if resp.status_code == 200:
            result = resp.json()
            status = result.get("status", "Unknown")
            if status in ("Succeeded", "Completed"):
                return result
            elif status in ("Failed", "Cancelled"):
                raise RuntimeError(f"Operation failed: {result}")
        time.sleep(5)
    raise TimeoutError("Long-running operation timed out")
```

---

## Best Practices

1. **Always use a subdirectory** (`/fabric`) — Don't put Fabric items at repo root; it conflicts with other code
2. **Commit messages matter** — Use descriptive messages: "Add sales report page", not "update"
3. **Don't commit secrets** — Parameterize connection strings; use Fabric Connections
4. **Resolve conflicts early** — Check `git/status` before committing
5. **One branch per workspace** — Don't connect multiple workspaces to the same branch
6. **Initialize with PreferWorkspace** for existing workspaces, **PreferRemote** for new workspaces

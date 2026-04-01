# Deployment Pipelines — Fabric CI/CD

## Overview

Fabric deployment pipelines provide stage-based release management for workspace content. Create 2–10 stages (default: Dev → Test → Prod), assign workspaces, and deploy items across stages with item pairing, deployment rules, and automation.

---

## Pipeline Structure

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│   Dev    │ ──► │   Test   │ ──► │   Prod   │
│ (stage 0)│     │ (stage 1)│     │ (stage 2)│
│ ws: abc  │     │ ws: def  │     │ ws: ghi  │
└──────────┘     └──────────┘     └──────────┘
```

- **2–10 stages** (add, rename, or delete stages as needed)
- One workspace per stage
- Deploy copies content from source → target stage
- Items are paired by `logicalId` across stages

---

## Supported Items for Deployment Pipelines

| Category | Items | Status |
|----------|-------|--------|
| **Data Engineering** | Environment, GraphQL, Lakehouse, Notebook, Spark Job Def, User Data Functions | GA |
| **Data Factory** | Copy Job, Dataflow Gen2, Pipeline, Mirrored DB, Mount ADF | GA |
| **Real-Time Intelligence** | Eventhouse, EventStream, KQL Database, KQL Queryset, Real-time Dashboard, Digital Twin Builder | GA/Preview |
| **Power BI** | Dashboard, Dataflow, Datamart, Org App, Paginated Report, Report, Semantic Model | Preview |
| **Database** | SQL Database, Cosmos Database | Preview |
| **Industry** | Healthcare, HealthCare Cohort | Preview |
| **IQ** | Ontology | Preview |

---

## REST API Operations

### Create Pipeline

```http
POST /v1/deploymentPipelines
{
  "displayName": "Sales BI Pipeline",
  "description": "Dev → Test → Prod for Sales workspace"
}
→ Returns: { "id": "pipeline-guid", ... }
```

### Assign Workspace to Stage

```http
POST /v1/deploymentPipelines/{pipelineId}/stages/{stageId}/assignWorkspace
{
  "workspaceId": "workspace-guid"
}
```

### Deploy Stage Content

```http
POST /v1/deploymentPipelines/{pipelineId}/deploy
{
  "sourceStageId": "stage-0-guid",
  "targetStageId": "stage-1-guid",
  "items": [                          // omit for deploy-all
    { "itemId": "item-guid", "itemType": "Report" }
  ],
  "options": {
    "allowCreateArtifact": true,       // create if not exists in target
    "allowOverwriteArtifact": true     // overwrite if exists in target
  },
  "isBackwardDeployment": false        // set true for reverse deploy
}
→ Returns: { "id": "operation-guid" }  // LRO — poll for completion
```

### Poll Deploy Operation

```http
GET /v1/deploymentPipelines/{pipelineId}/operations/{operationId}
→ Returns: { "status": "Succeeded" | "Failed" | "Executing" | "NotStarted" }
```

### List Stage Items

```http
GET /v1/deploymentPipelines/{pipelineId}/stages/{stageId}/items
→ Returns: items[] with itemId, itemType, displayName, lastDeployTime
```

### Other Operations

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Delete pipeline | DELETE | `/deploymentPipelines/{id}` |
| Get pipeline | GET | `/deploymentPipelines/{id}` |
| List all pipelines | GET | `/deploymentPipelines` |
| Unassign workspace | POST | `/.../stages/{stageId}/unassignWorkspace` |
| Add user to pipeline | POST | `/deploymentPipelines/{id}/users` |
| Remove user | DELETE | `/deploymentPipelines/{id}/users/{userId}` |
| List operations history | GET | `/deploymentPipelines/{id}/operations` (last 20) |

---

## Item Pairing

Items are paired between adjacent stages by `logicalId`. Paired items appear on the same row in the pipeline UI.

### Pairing Rules

| Scenario | Result |
|----------|--------|
| Item deployed from stage A → stage B | Items get paired |
| Workspace assigned to stage | Existing items with matching `logicalId` get paired |
| Item renamed | Still paired (logicalId unchanged) |
| Item deleted and recreated | **NOT paired** (new logicalId) — creates duplicate |
| New item added after workspace assigned | **NOT paired** — standalone until deployed |
| Same name, different logicalId | **NOT paired** — new copy created on deploy |

> **Rule**: If you see duplicates after deploy, check logicalId mismatch. Delete the duplicate and redeploy.

---

## Deployment Rules

Deployment rules allow you to set different values for different stages without modifying the source.

### Data Source Rules
Change data source connections when deploying between stages (e.g., dev SQL → prod SQL).

### Parameter Rules
Override parameter values per stage (connection strings, feature flags, etc.).

> **Recommended**: Use Variable Libraries instead of parameter rules for new projects. They provide a unified, API-driven approach.

---

## PowerShell Automation

### Deploy All Script

```powershell
# 1. Sign in
Connect-PowerBIServiceAccount -ServicePrincipal `
  -Credential (New-Object PSCredential($clientId, (ConvertTo-SecureString $clientSecret -AsPlainText -Force))) `
  -TenantId $tenantId

# 2. Build deploy request
$body = @{
    sourceStageOrder = 0  # Dev
    options = @{
        allowCreateArtifact    = $true
        allowOverwriteArtifact = $true
    }
} | ConvertTo-Json

# 3. Deploy
$url = "pipelines/{0}/DeployAll" -f $pipelineId
$result = Invoke-PowerBIRestMethod -Url $url -Method Post -Body $body | ConvertFrom-Json

# 4. Poll until complete
$opUrl = "pipelines/{0}/Operations/{1}" -f $pipelineId, $result.id
do {
    Start-Sleep -Seconds 5
    $op = Invoke-PowerBIRestMethod -Url $opUrl -Method Get | ConvertFrom-Json
} while ($op.Status -in @("NotStarted", "Executing"))

Write-Host "Deploy status: $($op.Status)"
```

### Selective Deploy Script

```powershell
$body = @{
    sourceStageOrder = 0
    datasets = @(
        @{ sourceId = $datasetId }
    )
    reports = @(
        @{ sourceId = $reportId }
    )
    options = @{
        allowCreateArtifact    = $true
        allowOverwriteArtifact = $true
    }
} | ConvertTo-Json

$url = "pipelines/{0}/Deploy" -f $pipelineId
Invoke-PowerBIRestMethod -Url $url -Method Post -Body $body
```

---

## Key Limitations

| Limitation | Detail |
|------------|--------|
| Max items per deploy | 300 |
| Pipeline stages | 2–10 (custom stage count = UI only) |
| Deploy APIs (Power BI) | Only Power BI items in legacy API |
| Deploy APIs (Fabric) | Fabric items via Fabric REST API |
| SPN + OAuth | SPN becomes owner of deployed items; can't configure OAuth for data refresh |
| Dataflows via SPN | Not supported |
| App update | Must use API — portal deploy doesn't auto-update apps |
| Backward deploy | Only for NEW items (not paired items) |

---

## Cross-References

- Environment promotion patterns: `environment_promotion.md`
- Variable libraries for stage configs: `variable_libraries.md`
- Automation with external platforms: `external_cicd.md`
- REST API patterns: `../../fabric_api.md`

# Fabric Deployment Pipelines — API & Patterns

> Automate multi-stage deployment (Dev → Test → Prod) for Fabric items.

---

## Concept

Deployment Pipelines promote Fabric items across **stages** (typically 3: Development, Test, Production). Each stage is bound to a different workspace. The pipeline tracks which items have changed and need redeployment.

```
┌──────────┐     Deploy     ┌──────────┐     Deploy     ┌──────────┐
│  Dev WS  │  ──────────►   │  Test WS │  ──────────►   │  Prod WS │
└──────────┘                └──────────┘                └──────────┘
     ▲                           ▲                           ▲
     │        Deployment Pipeline (3 stages)                 │
     └───────────────────────────────────────────────────────┘
```

## API Reference

Base URL: `https://api.fabric.microsoft.com/v1`

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create pipeline | `POST` | `/deploymentPipelines` |
| List pipelines | `GET` | `/deploymentPipelines` |
| Get pipeline | `GET` | `/deploymentPipelines/{pipelineId}` |
| Delete pipeline | `DELETE` | `/deploymentPipelines/{pipelineId}` |
| Get stages | `GET` | `/deploymentPipelines/{pipelineId}/stages` |
| Assign workspace to stage | `POST` | `/deploymentPipelines/{pipelineId}/stages/{stageId}/assignWorkspace` |
| Unassign workspace | `POST` | `/deploymentPipelines/{pipelineId}/stages/{stageId}/unassignWorkspace` |
| Get stage items | `GET` | `/deploymentPipelines/{pipelineId}/stages/{stageId}/items` |
| Deploy (selective) | `POST` | `/deploymentPipelines/{pipelineId}/deploy` |

---

## Complete Workflow

### Step 1: Create the Pipeline
```python
import requests

token = get_fabric_token()  # from fabric_api.md helper
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

resp = requests.post(
    "https://api.fabric.microsoft.com/v1/deploymentPipelines",
    headers=headers,
    json={"displayName": "MyProject Pipeline", "description": "Dev → Test → Prod"}
)
pipeline = resp.json()
pipeline_id = pipeline["id"]
```

### Step 2: Assign Workspaces to Stages
```python
stages = requests.get(
    f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{pipeline_id}/stages",
    headers=headers
).json()["value"]

# Stages are ordered: index 0 = Dev, 1 = Test, 2 = Prod
workspace_map = {
    0: "ws_dev_id",    # Development workspace
    1: "ws_test_id",   # Test workspace
    2: "ws_prod_id",   # Production workspace
}

for stage in stages:
    order = stage["order"]
    if order in workspace_map:
        requests.post(
            f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{pipeline_id}/stages/{stage['id']}/assignWorkspace",
            headers=headers,
            json={"workspaceId": workspace_map[order]}
        )
```

### Step 3: Deploy Items (Selective)
```python
# Get items in source stage (Dev)
source_stage_id = stages[0]["id"]
items = requests.get(
    f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{pipeline_id}/stages/{source_stage_id}/items",
    headers=headers
).json()["value"]

# Deploy specific items from Dev → Test
deploy_body = {
    "sourceStageId": source_stage_id,
    "items": [
        {"itemId": item["itemId"]}
        for item in items
        if item["itemType"] in ("Lakehouse", "SemanticModel", "Report", "Warehouse")
    ],
    "note": "Sprint 14 release"
}

resp = requests.post(
    f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{pipeline_id}/deploy",
    headers=headers,
    json=deploy_body
)
# Returns 202 — poll x-ms-operation-id
```

### Step 4: Monitor Deployment
```python
op_id = resp.headers.get("x-ms-operation-id")
# Use the standard async polling from ../../fabric_api.md
poll_operation(op_id, headers)
```

---

## Deployment Rules (Parameter Overrides)

Deployment rules allow you to override connection strings, parameters, or data sources per stage. For example, a Lakehouse in Dev points to a dev ADLS account, but in Prod it should point to the production ADLS account.

### Supported Rule Types
| Rule Type | Applies To | Example |
|-----------|-----------|---------|
| Data source rules | SemanticModel, Dataflow | Change server/database per stage |
| Parameter rules | SemanticModel, Dataflow | Override model parameters |
| Lakehouse rules | Report, SemanticModel | Rebind to different Lakehouse per stage |

---

## Item Types Supported

| Item Type | Auto-Bind? | Notes |
|-----------|-----------|-------|
| Lakehouse | ✅ | Schema + metadata deployed, data stays in source |
| Warehouse | ✅ | Schema deployed, data stays |
| SemanticModel | ✅ | Full TMDL deployed |
| Report | ✅ | Full PBIR deployed, auto-rebound to target SM |
| Notebook | ✅ | Code deployed, attachments rebound |
| Pipeline | ✅ | Definition deployed |
| Dataflow Gen2 | ✅ | Definition deployed |
| Eventhouse | ✅ | KQL Database schemas deployed |
| Environment | ✅ | Libraries + Spark config deployed |
| Data Agent | ⚠️ | Definition deployed, instructions need review |

---

## Automation Pattern (CI/CD)

```python
def promote_to_next_stage(pipeline_id: str, source_stage_order: int, headers: dict):
    """
    Promote all changed items from one stage to the next.
    source_stage_order: 0 = Dev, 1 = Test
    """
    stages = requests.get(
        f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{pipeline_id}/stages",
        headers=headers
    ).json()["value"]
    
    source = next(s for s in stages if s["order"] == source_stage_order)
    
    # Get all items in source stage
    items = requests.get(
        f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{pipeline_id}/stages/{source['id']}/items",
        headers=headers
    ).json()["value"]
    
    resp = requests.post(
        f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{pipeline_id}/deploy",
        headers=headers,
        json={
            "sourceStageId": source["id"],
            "items": [{"itemId": i["itemId"]} for i in items],
            "note": f"Automated promotion from stage {source_stage_order}"
        }
    )
    
    op_id = resp.headers.get("x-ms-operation-id")
    return poll_operation(op_id, headers)
```

---

## Gotchas

1. **Data does NOT move** — only schema/metadata is deployed. Lakehouse data, Warehouse data, EventhouseDB data stays in the source stage.
2. **First deploy creates items** in the target workspace. Subsequent deploys update them.
3. **Semantic Model rebinding** — when deployed, the SM automatically rebinds to the Lakehouse/Warehouse in the target stage (if it exists with the same name).
4. **Report rebinding** — Reports auto-rebind to the SM in the target stage (same name matching).
5. **Pipeline runs are NOT deployed** — only the pipeline definition. Scheduled triggers need manual reconfiguration per stage.
6. **Capacity required** — target workspace must have a capacity assigned for deployment to succeed.
7. **Permissions** — you need at least **Contributor** on both source and target workspaces.
8. **Deploy is async** — always poll `x-ms-operation-id`. Large deployments can take minutes.

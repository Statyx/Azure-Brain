# Resource IDs & Endpoints

> **Copy this file to `resource_ids.md` and fill in your values.**
> `resource_ids.md` is gitignored — your IDs stay local.

---

## Azure

| Property | Value |
|----------|-------|
| Subscription | `<YOUR_SUBSCRIPTION_ID>` |
| Tenant | `<YOUR_TENANT_ID>` |
| Resource Group | `<YOUR_RESOURCE_GROUP>` |

### Fabric Capacity

| Property | Value |
|----------|-------|
| Name | `<YOUR_CAPACITY_NAME>` |
| ID | `<YOUR_CAPACITY_ID>` |
| SKU | F2 (demo) / F16 (production) |
| Region | `<YOUR_REGION>` |

---

## Fabric Workspace

| Property | Value |
|----------|-------|
| Name | `<YOUR_WORKSPACE_NAME>` |
| ID | `<YOUR_WORKSPACE_ID>` |

---

## Fabric Items

Fill these in as you deploy items. The agents reference this file at runtime.

### Lakehouse

| Property | Value |
|----------|-------|
| Name | `<YOUR_LAKEHOUSE_NAME>` |
| ID | `<YOUR_LAKEHOUSE_ID>` |
| SQL Endpoint | `<YOUR_SQL_ENDPOINT>` |
| OneLake Path | `https://onelake.dfs.fabric.microsoft.com/<WORKSPACE_ID>/<LAKEHOUSE_ID>/Files/` |

### Notebook

| Property | Value |
|----------|-------|
| Name | `<YOUR_NOTEBOOK_NAME>` |
| ID | `<YOUR_NOTEBOOK_ID>` |

### Semantic Model

| Property | Value |
|----------|-------|
| Name | `<YOUR_MODEL_NAME>` |
| ID | `<YOUR_MODEL_ID>` |
| Mode | Direct Lake |

### Report

| Property | Value |
|----------|-------|
| Name | `<YOUR_REPORT_NAME>` |
| ID | `<YOUR_REPORT_ID>` |
| Format | Legacy PBIX |

### Data Agent (optional)

| Property | Value |
|----------|-------|
| Name | `<YOUR_AGENT_NAME>` |
| ID | `<YOUR_AGENT_ID>` |

---

## API Endpoints

These are the same for everyone — no need to change.

| Service | Base URL | Token Scope |
|---------|----------|-------------|
| Fabric REST API | `https://api.fabric.microsoft.com/v1` | `https://api.fabric.microsoft.com` |
| OneLake DFS | `https://onelake.dfs.fabric.microsoft.com` | `https://storage.azure.com` |
| Azure Resource Manager | `https://management.azure.com` | `https://management.azure.com` |

### Common API Paths
```
GET    /v1/workspaces/{ws_id}/items
POST   /v1/workspaces/{ws_id}/items                          # Create item
POST   /v1/workspaces/{ws_id}/items/{id}/updateDefinition    # Update definition
POST   /v1/workspaces/{ws_id}/items/{id}/getDefinition       # Get definition
DELETE /v1/workspaces/{ws_id}/items/{id}
GET    /v1/operations/{op_id}                                 # Poll async operation
```

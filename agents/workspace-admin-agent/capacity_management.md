# Capacity Management — SKUs, Assignment, Monitoring & Scaling

## Fabric Capacity SKUs

### SKU Reference Table

| SKU | CU (Capacity Units) | Max Concurrent Spark Jobs | KQL Throughput | Monthly Cost (est.) | Best For |
|-----|---------------------|--------------------------|----------------|--------------------|---------| 
| **Trial** | Limited | 1 | ~100 events/sec | Free (60 days) | Learning, quick demos |
| **F2** | 2 | 1-2 | ~500 events/sec | ~$260/mo | Dev/test, small demos |
| **F4** | 4 | 2-4 | ~1,000/sec | ~$520/mo | Team development |
| **F8** | 8 | 4-8 | ~2,500/sec | ~$1,040/mo | Department workloads |
| **F16** | 16 | 8-16 | ~5,000/sec | ~$2,080/mo | Production analytics |
| **F32** | 32 | 16-32 | ~10,000/sec | ~$4,160/mo | Enterprise analytics |
| **F64** | 64 | 32-64 | ~50,000+/sec | ~$8,320/mo | Large-scale production |
| **F128** | 128 | 64+ | ~100,000+/sec | ~$16,640/mo | Massive workloads |

> **Trial capacity**: Free for 60 days. Severely limited. Good for exploring, not for multi-user demos.

### SKU Selection Guide

```
├── Just exploring Fabric → Trial
├── Building a demo (solo) → F2
├── Team development (2-5 people) → F4 or F8
├── Customer demo with real-time streaming → F8 (minimum)
├── Production analytics (<50 users) → F16
├── Enterprise production → F32-F128
└── Need GPUs (AI workloads) → F64+
```

---

## Capacity Operations via ARM API

All capacity-level operations use the Azure Resource Manager API.

**Base URL**: `https://management.azure.com`  
**Token**: `az account get-access-token --resource https://management.azure.com`  
**API Version**: `2023-11-01`

### Create Capacity

```python
import requests

ARM = "https://management.azure.com"
SUB_ID = "<subscription-id>"
RG_NAME = "<resource-group>"
CAPACITY_NAME = "my-fabric-capacity"
API_VERSION = "2023-11-01"

def create_capacity(sku: str = "F2", region: str = "westeurope", token: str = None):
    """Create a new Fabric capacity via ARM."""
    url = f"{ARM}/subscriptions/{SUB_ID}/resourceGroups/{RG_NAME}/providers/Microsoft.Fabric/capacities/{CAPACITY_NAME}?api-version={API_VERSION}"
    
    resp = requests.put(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }, json={
        "location": region,
        "sku": {"name": sku, "tier": "Fabric"},
        "properties": {
            "administration": {
                "members": ["user@domain.com"]  # Capacity admins
            }
        }
    })
    resp.raise_for_status()
    return resp.json()
```

### Get Capacity Details

```python
def get_capacity(token: str):
    """Get capacity details including state and SKU."""
    url = f"{ARM}/subscriptions/{SUB_ID}/resourceGroups/{RG_NAME}/providers/Microsoft.Fabric/capacities/{CAPACITY_NAME}?api-version={API_VERSION}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()
```

### Suspend Capacity (Save Costs)

```python
def suspend_capacity(token: str):
    """Suspend capacity to stop billing. Workloads will be paused."""
    url = f"{ARM}/subscriptions/{SUB_ID}/resourceGroups/{RG_NAME}/providers/Microsoft.Fabric/capacities/{CAPACITY_NAME}/suspend?api-version={API_VERSION}"
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    print("✅ Capacity suspended — billing paused")
```

### Resume Capacity

```python
def resume_capacity(token: str):
    """Resume a suspended capacity."""
    url = f"{ARM}/subscriptions/{SUB_ID}/resourceGroups/{RG_NAME}/providers/Microsoft.Fabric/capacities/{CAPACITY_NAME}/resume?api-version={API_VERSION}"
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    print("✅ Capacity resumed — workloads active")
```

### Scale Capacity (Change SKU)

```python
def scale_capacity(new_sku: str, token: str):
    """Change the capacity SKU (scale up or down)."""
    url = f"{ARM}/subscriptions/{SUB_ID}/resourceGroups/{RG_NAME}/providers/Microsoft.Fabric/capacities/{CAPACITY_NAME}?api-version={API_VERSION}"
    resp = requests.patch(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }, json={
        "sku": {"name": new_sku, "tier": "Fabric"}
    })
    resp.raise_for_status()
    print(f"✅ Capacity scaled to {new_sku}")
```

---

## Assign Capacity to Workspace

```python
FABRIC_API = "https://api.fabric.microsoft.com/v1"

def assign_capacity(workspace_id: str, capacity_id: str, fabric_token: str):
    """Assign a Fabric capacity to a workspace."""
    resp = requests.post(
        f"{FABRIC_API}/workspaces/{workspace_id}/assignToCapacity",
        headers={"Authorization": f"Bearer {fabric_token}", "Content-Type": "application/json"},
        json={"capacityId": capacity_id}
    )
    resp.raise_for_status()
    print(f"✅ Capacity {capacity_id} assigned to workspace {workspace_id}")

def unassign_capacity(workspace_id: str, fabric_token: str):
    """Remove capacity from a workspace (items become read-only)."""
    resp = requests.post(
        f"{FABRIC_API}/workspaces/{workspace_id}/unassignFromCapacity",
        headers={"Authorization": f"Bearer {fabric_token}"}
    )
    resp.raise_for_status()
    print(f"✅ Capacity removed from workspace {workspace_id}")
```

### Get Capacity ID from Workspace

```python
def get_workspace_capacity(workspace_id: str, fabric_token: str) -> str:
    """Get the capacity ID assigned to a workspace."""
    ws = requests.get(
        f"{FABRIC_API}/workspaces/{workspace_id}",
        headers={"Authorization": f"Bearer {fabric_token}"}
    ).json()
    return ws.get("capacityId")
```

---

## List Available Capacities

### Via Fabric API
```python
def list_fabric_capacities(fabric_token: str):
    """List capacities accessible by the current user."""
    resp = requests.get(
        f"{FABRIC_API}/capacities",
        headers={"Authorization": f"Bearer {fabric_token}"}
    )
    resp.raise_for_status()
    for cap in resp.json()["value"]:
        print(f"  {cap['displayName']} ({cap['sku']}) — State: {cap['state']} — ID: {cap['id']}")
    return resp.json()["value"]
```

### Via ARM API (All in Subscription)
```python
def list_arm_capacities(arm_token: str):
    """List all Fabric capacities in the subscription."""
    url = f"{ARM}/subscriptions/{SUB_ID}/providers/Microsoft.Fabric/capacities?api-version={API_VERSION}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {arm_token}"})
    resp.raise_for_status()
    return resp.json()["value"]
```

---

## Cost Optimization Patterns

### Auto-Suspend After Hours (Azure Automation)

Schedule capacity suspension at end of day and resume at start:

```python
# In Azure Automation runbook or Azure Function (Timer trigger)
# Suspend at 7 PM, resume at 7 AM

import datetime

now = datetime.datetime.utcnow()
if now.hour >= 19 or now.hour < 7:
    suspend_capacity(token)
else:
    # Check if suspended and resume
    details = get_capacity(token)
    if details["properties"]["state"] == "Paused":
        resume_capacity(token)
```

### Scale for Demo, Then Scale Down

```python
def demo_mode(token: str):
    """Scale up for demo, then scale down after."""
    print("Scaling to F8 for demo...")
    scale_capacity("F8", token)
    
    # After demo (call separately or via timer):
    # scale_capacity("F2", token)
    # Or: suspend_capacity(token)
```

### Cost Awareness
- **Billing is per-second** when capacity is active
- **Suspended = no cost** (but items become read-only)
- **Scale down** during off-hours rather than keeping F16 running
- **Trial** is free but expires in 60 days and has severe limits

---

## Capacity Monitoring

### Check Capacity Utilization via Admin API

```python
def get_capacity_metrics(capacity_id: str, fabric_token: str):
    """Get capacity utilization metrics."""
    # Note: This requires Admin API access
    resp = requests.get(
        f"{FABRIC_API}/admin/capacities/{capacity_id}",
        headers={"Authorization": f"Bearer {fabric_token}"}
    )
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"⚠️ Admin API access required (got {resp.status_code})")
        return None
```

### Capacity Health Indicators

| Indicator | Healthy | Warning | Critical |
|-----------|---------|---------|----------|
| CU Utilization | <60% | 60-80% | >80% |
| Spark Job Queue | 0-1 queued | 2-5 queued | >5 queued |
| KQL Ingestion Lag | <5s | 5-30s | >30s |
| Throttling Events | 0 | 1-5/hour | >5/hour |

---

## Common Capacity Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Workspace has no capacity" | Capacity not assigned | `POST assignToCapacity` |
| "Capacity is paused" | Suspended to save costs | Resume capacity |
| "CU limit exceeded" | Too many concurrent jobs | Scale up or reduce workload |
| "Throttling" | Exceeding capacity limits | Scale up or stagger workloads |
| ARM API 403 | Missing Contributor role on capacity | Add user to capacity ARM RBAC |
| Fabric API 403 | Not a capacity admin/member | Add user in capacity admin settings |

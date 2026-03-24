# Admin REST APIs — Monitoring & Audit Endpoints

## Overview

The Fabric Admin REST API provides tenant-level visibility into workspaces, items, users, and activity. These endpoints require **Fabric Admin** or **Global Admin** role.

**Base URL**: `https://api.fabric.microsoft.com/v1/admin`  
**Token Scope**: `https://api.fabric.microsoft.com/.default`  

---

## Workspace & Item Discovery

### List All Workspaces (Admin)
```python
API_ADMIN = "https://api.fabric.microsoft.com/v1/admin"

def list_all_workspaces(token: str):
    """List all workspaces in the tenant (admin only)."""
    headers = {"Authorization": f"Bearer {token}"}
    workspaces = []
    url = f"{API_ADMIN}/workspaces?$top=100"
    
    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        workspaces.extend(data.get("workspaces", data.get("value", [])))
        url = data.get("continuationUri") or data.get("@odata.nextLink")
    
    print(f"Found {len(workspaces)} workspaces")
    return workspaces
```

### Get Workspace Details (Admin)
```python
def get_workspace_details(workspace_id: str, token: str):
    """Get detailed workspace info including items and users."""
    resp = requests.get(
        f"{API_ADMIN}/workspaces/{workspace_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    ws = resp.json()
    
    print(f"Workspace: {ws['displayName']}")
    print(f"  State: {ws.get('state', 'N/A')}")
    print(f"  Capacity: {ws.get('capacityId', 'None')}")
    
    if "users" in ws:
        for user in ws["users"]:
            print(f"  User: {user.get('displayName', user.get('identifier'))} — {user['workspaceAccessDetails']['workspaceRole']}")
    
    return ws
```

### List Items in Workspace (Admin)
```python
def list_workspace_items_admin(workspace_id: str, token: str, item_type: str = None):
    """List all items in a workspace (admin view)."""
    url = f"{API_ADMIN}/workspaces/{workspace_id}/items"
    if item_type:
        url += f"?type={item_type}"
    
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    items = resp.json().get("itemEntities", resp.json().get("value", []))
    
    for item in items:
        print(f"  {item['type']}: {item['displayName']} ({item['id']})")
    
    return items
```

---

## Activity / Audit Events

### Get Activity Events
Retrieve audit trail of user and system activities.

```python
def get_activity_events(start_datetime: str, end_datetime: str, token: str, 
                        activity_filter: str = None, continuation_token: str = None):
    """
    Get activity events for a time range.
    
    Args:
        start_datetime: ISO format, e.g., "2024-11-01T00:00:00Z"
        end_datetime: ISO format, e.g., "2024-11-02T00:00:00Z"
        activity_filter: Optional OData filter, e.g., "Activity eq 'ViewReport'"
    
    Note: Maximum time range is 24 hours per request.
    """
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "startDateTime": f"'{start_datetime}'",
        "endDateTime": f"'{end_datetime}'"
    }
    if activity_filter:
        params["$filter"] = activity_filter
    if continuation_token:
        params["continuationToken"] = f"'{continuation_token}'"
    
    resp = requests.get(f"{API_ADMIN}/activityEvents", headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    
    events = data.get("activityEventEntities", [])
    next_token = data.get("continuationToken")
    
    return events, next_token

def get_all_activity_events(start: str, end: str, token: str, activity_filter: str = None):
    """Page through all activity events for a time range."""
    all_events = []
    cont_token = None
    
    while True:
        events, cont_token = get_activity_events(start, end, token, activity_filter, cont_token)
        all_events.extend(events)
        if not cont_token:
            break
    
    print(f"Retrieved {len(all_events)} activity events")
    return all_events
```

### Common Activity Types

| Activity | Description | Filter |
|----------|-------------|--------|
| `ViewReport` | Report viewed by user | `Activity eq 'ViewReport'` |
| `CreateReport` | Report created | `Activity eq 'CreateReport'` |
| `DeleteWorkspace` | Workspace deleted | `Activity eq 'DeleteWorkspace'` |
| `ExportReport` | Report exported | `Activity eq 'ExportReport'` |
| `ShareReport` | Report shared | `Activity eq 'ShareReport'` |
| `CreateLakehouse` | Lakehouse created | `Activity eq 'CreateLakehouse'` |
| `RunNotebook` | Notebook executed | `Activity eq 'RunNotebook'` |
| `RefreshDataset` | Semantic model refreshed | `Activity eq 'RefreshDataset'` |

### Activity Event Schema
```json
{
    "Id": "event-guid",
    "CreationTime": "2024-11-15T10:30:00Z",
    "Activity": "ViewReport",
    "UserId": "user@domain.com",
    "ItemName": "Sales Dashboard",
    "WorkspaceName": "RetailAnalytics-Prod",
    "WorkspaceId": "workspace-guid",
    "ItemId": "item-guid",
    "ItemType": "Report",
    "IsSuccess": true
}
```

---

## Capacity Monitoring

### List Capacities (Admin)
```python
def list_capacities_admin(token: str):
    """List all capacities in the tenant."""
    resp = requests.get(
        f"{API_ADMIN}/capacities",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    capacities = resp.json().get("value", [])
    
    for cap in capacities:
        print(f"  {cap['displayName']}: {cap['sku']} — State: {cap['state']}")
    
    return capacities
```

### Get Capacity Workload Status
```python
def get_capacity_workloads(capacity_id: str, token: str):
    """Check which workloads are enabled on a capacity."""
    # Note: Available via Power BI Admin API
    resp = requests.get(
        f"https://api.powerbi.com/v1.0/myorg/admin/capacities/{capacity_id}/workloads",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code == 200:
        for workload in resp.json().get("value", []):
            print(f"  {workload['name']}: {workload['state']} (maxMemory: {workload.get('maxMemoryPercentageSetByUser', 'N/A')}%)")
        return resp.json()
    else:
        print(f"  ⚠️ Cannot access workload info (status: {resp.status_code})")
        return None
```

---

## User & Access Monitoring

### List Workspace Users
```python
def list_workspace_users(workspace_id: str, token: str):
    """List all users with access to a workspace (admin view)."""
    ws = get_workspace_details(workspace_id, token)
    users = ws.get("users", [])
    
    summary = {"Admin": 0, "Member": 0, "Contributor": 0, "Viewer": 0}
    for user in users:
        role = user["workspaceAccessDetails"]["workspaceRole"]
        summary[role] = summary.get(role, 0) + 1
    
    print(f"\nUser Summary: {summary}")
    return users
```

### Find Orphaned Workspaces
```python
def find_orphaned_workspaces(token: str):
    """Find workspaces with no admin users (potential orphans)."""
    workspaces = list_all_workspaces(token)
    orphaned = []
    
    for ws in workspaces:
        if ws.get("state") == "Active":
            details = get_workspace_details(ws["id"], token)
            admins = [u for u in details.get("users", []) 
                     if u["workspaceAccessDetails"]["workspaceRole"] == "Admin"]
            if len(admins) == 0:
                orphaned.append(ws)
                print(f"  ⚠️ Orphaned: {ws['displayName']} (no admins)")
    
    print(f"\nFound {len(orphaned)} orphaned workspaces")
    return orphaned
```

---

## Refresh / Job Monitoring

### Get Dataset Refresh History
```python
def get_refresh_history(workspace_id: str, dataset_id: str, token: str):
    """Get refresh history for a semantic model / dataset."""
    resp = requests.get(
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    refreshes = resp.json().get("value", [])
    
    for r in refreshes[:5]:  # Last 5
        status = r.get("status", "Unknown")
        start = r.get("startTime", "?")
        end = r.get("endTime", "?")
        icon = "✅" if status == "Completed" else "❌"
        print(f"  {icon} {start} → {end}: {status}")
    
    return refreshes
```

---

## Monitoring Report Template

### Generate Workspace Report
```python
def generate_workspace_report(ws_id: str, token: str):
    """Generate a comprehensive monitoring report for a workspace."""
    API = "https://api.fabric.microsoft.com/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    report = {"timestamp": datetime.utcnow().isoformat() + "Z", "workspace_id": ws_id}
    
    # Basic info
    ws = requests.get(f"{API}/workspaces/{ws_id}", headers=headers).json()
    report["workspace_name"] = ws["displayName"]
    report["capacity_id"] = ws.get("capacityId")
    
    # Items inventory
    items = requests.get(f"{API}/workspaces/{ws_id}/items", headers=headers).json()["value"]
    report["total_items"] = len(items)
    report["items_by_type"] = {}
    for item in items:
        t = item["type"]
        report["items_by_type"][t] = report["items_by_type"].get(t, 0) + 1
    
    # Print report
    print("=" * 60)
    print(f"WORKSPACE MONITORING REPORT")
    print(f"Generated: {report['timestamp']}")
    print(f"Workspace: {report['workspace_name']}")
    print(f"Capacity:  {report['capacity_id'] or 'NONE ⚠️'}")
    print(f"Total Items: {report['total_items']}")
    for t, c in sorted(report["items_by_type"].items()):
        print(f"  {t}: {c}")
    print("=" * 60)
    
    return report
```

---

## Best Practices

1. **Max 24-hour window** for activity events — split longer ranges into daily requests
2. **Admin APIs are rate-limited** (~30 req/min) — add delays between bulk operations
3. **Pagination is required** — Always follow `continuationToken` / `@odata.nextLink`
4. **Activity events have ~30 min delay** — Don't expect real-time audit data
5. **Use structured logging** — JSON format for easy downstream analysis
6. **Cache workspace/item metadata** — Don't re-fetch static info on every monitoring cycle

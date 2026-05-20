# Workspace Admin Agent — Known Issues & Workarounds

## Common Issues

### 1. "Workspace Has No Capacity" Error
**Symptom**: Creating items (Lakehouse, Eventhouse, etc.) fails with capacity error.  
**Cause**: Workspace created but no capacity assigned.  
**Fix**: Always assign capacity immediately after creation:
```python
requests.post(f"{API}/workspaces/{ws_id}/assignToCapacity", headers=h, 
              json={"capacityId": CAP_ID})
```

### 2. Service Principal Gets 403 on API Calls
**Symptom**: SP can authenticate but REST API calls return 403.  
**Cause**: Tenant setting "Service principals can use Fabric APIs" is disabled.  
**Fix**: 
1. Admin Portal → Tenant Settings → Developer Settings
2. Enable "Service principals can use Fabric APIs"
3. If scoped to security groups, add the SP to that group

### 3. Workspace Creation Returns 400 "Name Already Exists"
**Symptom**: POST `/workspaces` returns 400.  
**Cause**: Workspace names must be unique across the tenant.  
**Fix**: 
- Use a naming convention with environment suffix: `ProjectName-Dev-{date}`
- Or check existing workspaces first:
```python
existing = requests.get(f"{API}/workspaces", headers=h).json()["value"]
names = [w["displayName"] for w in existing]
```

### 4. Capacity Assignment Returns "Capacity Not Found"
**Symptom**: `assignToCapacity` returns 404.  
**Cause**: The capacity ID is wrong, or the capacity is in a different tenant/subscription.  
**Fix**: 
- List available capacities: `GET /v1/capacities` to find the correct ID
- Verify the capacity is Active (not Suspended or Deleted)
- Capacity must be in the same tenant as the workspace

### 5. Git Connection Fails — "Repository Not Found"
**Symptom**: `git/connect` returns error about repository.  
**Cause**: 
- (a) Wrong organization/project/repo name
- (b) User doesn't have access to the repo
- (c) Git integration tenant setting is disabled  
**Fix**: 
- Verify repo access in Azure DevOps / GitHub
- Enable "Git integration" in Admin Portal
- Ensure the user is workspace Admin (required for Git operations)

### 6. Git Commit Fails — "Conflict Detected"
**Symptom**: `commitToGit` returns 409 Conflict.  
**Cause**: Remote branch has changes not yet pulled into workspace.  
**Fix**: 
1. Call `updateFromGit` first with `conflictResolution: "PreferRemote"`
2. Then retry the commit

### 7. Deployment Pipeline "Insufficient Permissions"
**Symptom**: Deploy between stages fails with 403.  
**Cause**: User must be Admin in BOTH source and target workspaces.  
**Fix**: Add the user as Admin to all stage workspaces.

### 8. Capacity Suspended — Items Become Read-Only
**Symptom**: All operations on workspace items fail; items are visible but can't be modified.  
**Cause**: The assigned capacity was suspended (manually or via automation).  
**Fix**: Resume the capacity via ARM API:
```python
requests.post(f"{ARM}/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{cap}/resume?api-version=2023-11-01",
              headers={"Authorization": f"Bearer {arm_token}"})
```

### 9. Can't Delete Workspace — "Items Exist"
**Symptom**: DELETE workspace returns 400.  
**Cause**: Some Fabric item types must be deleted before the workspace.  
**Fix**: Delete items in reverse dependency order:
```
Reports → SemanticModels → Notebooks → Pipelines → EventStreams → Eventhouses → Lakehouses
```
Then delete the workspace.

### 10. Role Assignment — "Principal Not Found"
**Symptom**: Adding role assignment fails with "principal not found".  
**Cause**: The user/group/SP ID is incorrect, or it's from a different tenant.  
**Fix**: 
- Use the Object ID (GUID) from Azure AD, not the UPN or display name
- For users: get objectId from `az ad user show --id user@domain.com`
- For SPs: get objectId from `az ad sp show --id <app-id>`

---

## What Works and What Doesn't

| Operation | Status | Notes |
|-----------|--------|-------|
| Create workspace via REST | ✅ Works | Simple POST, returns immediately |
| Assign capacity via REST | ✅ Works | Must use capacity GUID |
| Add role assignments | ✅ Works | Need principal Object ID |
| Git connect (Azure DevOps) | ✅ Works | User must be workspace Admin |
| Git connect (GitHub) | ✅ Works | Needs GitHub App installation |
| Git commit/update | ✅ Works | May return 202 for long-running |
| Deployment Pipelines create | ✅ Works | Need Admin on all stage workspaces |
| Create capacity (ARM) | ✅ Works | Need Azure Contributor role |
| Suspend/Resume capacity | ✅ Works | ARM API, not Fabric API |
| Scale capacity | ✅ Works | ARM API PATCH |
| Get capacity metrics | ⚠️ Limited | Admin API access required |
| Cross-tenant workspace sharing | ❌ Not supported | Workspaces are tenant-bound |
| Move workspace between capacities | ✅ Works | Unassign then reassign |

---

## Tenant Settings Checklist

| Setting | Required For | Default |
|---------|-------------|---------|
| Service principals can use Fabric APIs | Any SP automation | Disabled |
| Users can create workspaces | Workspace creation | Enabled |
| Users can create Fabric items | Item creation | Enabled |
| Git integration | Workspace-Git connection | Disabled |
| Allow XMLA endpoints | SQL Endpoint / XMLA access | Disabled |
| Export data | Data export operations | Varies |
| External data sharing | Cross-tenant sharing | Disabled |

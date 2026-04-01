# Known Issues — cicd-fabric-agent

## Git Integration Issues

### GI-001: Workspace with 250+ Items Slow to Sync

**Symptom**: Commit or update operations time out or take 10+ minutes.

**Root Cause**: Large workspaces stress the Git sync engine.

**Fix**: Split workspace into smaller sets (< 200 items). Use Git folder structure to organize. Consider separate workspaces per team.

---

### GI-002: Duplicate Items After Git Restore + Recycle Bin Recovery

**Symptom**: Two copies of the same item appear in workspace after undoing Git changes and recovering from recycle bin.

**Root Cause**: Git integration re-creates items with a NEW `logicalId`. Recycle bin restore preserves the ORIGINAL `logicalId`. Both exist simultaneously.

**Fix**: Delete the duplicate item (the one with the wrong logicalId). Git operations will resume normally.

---

### GI-003: Sensitivity Labels Block Commit

**Symptom**: `403` or silent failure when committing items with sensitivity labels.

**Root Cause**: Export of labeled items requires explicit admin enablement.

**Fix**: Ask tenant admin to enable "Users can export workspace items with applied sensitivity labels to Git repositories" in admin settings.

---

### GI-004: CRLF Changes Appear as Diffs

**Symptom**: Items committed from Power BI Desktop (CRLF) show as changed in Fabric (LF) even with no content changes.

**Root Cause**: Fabric service normalizes line endings to LF on commit.

**Fix**: Set `.gitattributes` to `* text=auto eol=lf` in the repo. Or accept the one-time diff.

---

### GI-005: Renamed Item but Directory Name Unchanged

**Symptom**: Renamed an item in the workspace but the Git directory still has the old name.

**Root Cause**: By design — Git integration never renames item directories after creation. The `displayName` in `.platform` updates but the folder stays.

**Fix**: This is expected behavior. If confusing, manually rename the folder in Git AND update all dependencies.

---

### GI-006: Enhanced Refresh API Causes Git Diffs

**Symptom**: Semantic model shows as changed in Git after a scheduled refresh.

**Root Cause**: The Enhanced Refresh API modifies internal metadata, which registers as a Git diff.

**Fix**: Known limitation. Either accept the diff or commit after refresh to keep history clean.

---

### GI-007: GitHub Enterprise Server Not Supported

**Symptom**: Cannot connect workspace to GitHub Enterprise with custom domain.

**Root Cause**: Only cloud-based GitHub Enterprise is supported. On-premises Enterprise Server with custom domains is not supported.

**Fix**: Use GitHub Enterprise Cloud or Azure DevOps instead.

---

## Deployment Pipeline Issues

### DP-001: Deploy Fails with "Item Not Paired"

**Symptom**: Deploy succeeds but creates duplicates instead of overwriting.

**Root Cause**: Items in source and target stages have different `logicalId` values.

**Fix**: Delete the unpaired item in the target stage. Redeploy — new item will be created with correct pairing.

---

### DP-002: Max 300 Items Per Deploy

**Symptom**: `400 Bad Request` when deploying large workspace.

**Root Cause**: API limit of 300 items per single deploy operation.

**Fix**: Use selective deploy with batching — deploy in groups of 200–300 items. Script it with the REST API.

---

### DP-003: SPN Can't Refresh After Deploy

**Symptom**: Semantic model refresh fails after SPN-deployed content.

**Root Cause**: SPN becomes the owner of deployed items. SPNs can't configure OAuth data source credentials.

**Fix**: After SPN deploy, have a user with OAuth credentials take ownership of semantic models and reconfigure data sources.

---

### DP-004: Deployment Pipeline APIs Only Cover PBI Items

**Symptom**: Can deploy Power BI items (reports, models) via legacy API but not Fabric items.

**Root Cause**: Legacy Power BI Deployment Pipeline APIs (`/v1.0/myorg/pipelines/`) only support Power BI items.

**Fix**: Use the Fabric Deployment Pipelines REST API (`/v1/deploymentPipelines/`) for Fabric items. See [pipeline-automation-fabric](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/pipeline-automation-fabric).

---

### DP-005: App Not Updated After Deploy

**Symptom**: Users don't see new content after deploying to production.

**Root Cause**: Deployment pipeline updates the workspace but does NOT auto-update the app.

**Fix**: After deploy, manually update the app or use the API: `POST /v1.0/myorg/groups/{groupId}/apps/{appId}/UpdateApp`.

---

## Variable Library Issues

### VL-001: Variable Not Resolving in Notebook

**Symptom**: `notebookutils.variableLibrary.get()` returns null or errors.

**Root Cause**: Variable library must be in the SAME workspace as the notebook. Cross-workspace variable references are not supported.

**Fix**: Ensure the variable library item is in the same workspace. If using deployment pipelines, the variable library deploys to each stage workspace automatically.

---

### VL-002: Can't Delete Active Value Set

**Symptom**: Error when trying to delete a value set.

**Root Cause**: The active value set cannot be deleted.

**Fix**: Switch the active value set to a different one first, then delete.

---

### VL-003: Value Set Order Not Reorderable in UI

**Symptom**: Value sets appear in creation order and can't be reordered.

**Root Cause**: UI limitation.

**Fix**: Edit the JSON file directly in Git to reorder value sets.

---

## External CI/CD Issues

### CI-001: Token Expiry in Long-Running Pipelines

**Symptom**: API calls fail with `401` after ~60 minutes.

**Root Cause**: Azure AD tokens expire after 60–90 minutes.

**Fix**: Add token refresh logic between stages. Or split pipeline into separate jobs that each authenticate fresh.

---

### CI-002: fab CLI Token Cache Issues in Headless Environments

**Symptom**: `fab auth login` works but subsequent commands fail with auth errors.

**Root Cause**: Token cache may not persist correctly in containerized or ephemeral CI runners.

**Fix**: Use `FABRIC_TOKEN` environment variable or call `fab auth login` immediately before each command in the same step.

---

### CI-003: Concurrent Deploys Conflict

**Symptom**: Two CI/CD pipelines deploying to the same workspace cause conflicts.

**Root Cause**: Fabric doesn't support concurrent deploy operations to the same workspace.

**Fix**: Use pipeline locks (GitHub: `concurrency` groups; Azure DevOps: exclusive locks on environments). Ensure only one deploy runs at a time per workspace.

---

## Cross-References

- Git integration details: `git_integration.md`
- Deployment pipeline API: `deployment_pipelines.md`
- Variable libraries: `variable_libraries.md`
- General Fabric known issues: `../../known_issues.md`
- Error recovery: `../../ERROR_RECOVERY.md`

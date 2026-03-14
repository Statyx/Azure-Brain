# Known Issues — Data Agent Gotchas & Workarounds

---

## Data Source Binding

| Issue | Symptom | Workaround |
|-------|---------|------------|
| Data source not attached after API creation | Agent says "I don't have access to any data" | Add datasource.json via `updateDefinition` or attach manually in portal |
| Wrong artifactId | Agent can't find tables | Verify ID with `GET /v1/workspaces/{wsId}/items?type=SemanticModel` |
| Elements array ignored | Agent sees all tables despite selection | Element selection may be advisory; agent can still discover full schema |
| Lakehouse type confusion | `lakehouse` vs `lakehouse-tables` | Use `lakehouse-tables` for table-only access (most common) |

## Instructions

| Issue | Symptom | Workaround |
|-------|---------|------------|
| Instructions too long | Agent ignores later sections | Keep under 5,000 chars; move data descriptions to datasource.json |
| Instructions in wrong language | Agent responds in unexpected language | Write instructions in the primary response language |
| Contradictory instructions | Agent behaves inconsistently | Review for conflicts; test each rule independently |
| Instructions not updating | Old behavior persists after update | Ensure you updated the correct stage (draft vs published); clear browser cache |

## Few-Shot Examples

| Issue | Symptom | Workaround |
|-------|---------|------------|
| DAX query errors in examples | Agent produces similar broken queries | Validate every query in DAX query view before deploying |
| Measure name mismatch | "Cannot find measure [Revenue]" | Cross-check names exactly against model.bim |
| Too few examples | Agent guesses wrong query patterns | Add at least 8-10 examples covering different patterns |
| Examples don't cover user's questions | Agent falls back to generic queries | Add examples matching real user question patterns |

## Publishing

| Issue | Symptom | Workaround |
|-------|---------|------------|
| Draft works, published doesn't | Published agent gives errors | Ensure published/ folder has same parts as draft/ |
| Missing publish_info.json | Publish state unclear | Add `publish_info.json` with schema 1.0.0 and description |
| Published version out of date | Users see old behavior | Re-run updateDefinition with both draft/ and published/ parts |

## API Issues

| Issue | Symptom | Workaround |
|-------|---------|------------|
| 202 with no body | Seems like nothing happened | This is normal — poll `x-ms-operation-id` until Succeeded |
| `/operations/{id}/result` endpoint hangs | SSL read timeout on `api.fabric.microsoft.com` | Use the `Location` header redirect URL instead (e.g., `wabi-west-us3-a-primary-redirect.analysis.windows.net`). For `updateDefinition`, skip result fetch entirely — just poll status |
| Location header URL also hangs for updates | SSL timeout on result fetch | For `updateDefinition` operations, don't fetch the result — just confirm status is "Succeeded" |
| "CorruptedPayload" error | 400 Bad Request | Validate JSON before base64-encoding; check for unicode issues |
| "ItemDisplayNameAlreadyInUse" | Cannot create agent | Delete existing agent first or use a different name |
| Rate limiting (429) | Too many requests | Respect `Retry-After` header; add delays between API calls |
| getDefinition returns encrypted | Can't read definition | Report has sensitivity label with encryption; cannot retrieve via API |

## Publishing & M365 Copilot

| Issue | Symptom | Workaround |
|-------|---------|------------|
| No public API for M365 Copilot toggle | Cannot enable "Share with M365 Copilot" via REST | Portal-only: Data Agent → Settings → M365 Copilot toggle. No REST API as of 2025-06 |
| Publish via API | Need to publish agent programmatically | Include `publish_info.json` + duplicate draft parts into `published/` folder. Use `updateDefinition` with all parts |
| Published version out of date | Users see old behavior | Re-run updateDefinition with both draft/ and published/ parts |
| Draft works, published doesn't | Published agent gives errors | Ensure published/ folder has same parts as draft/ |
| Missing publish_info.json | Publish state unclear | Add `publish_info.json` with schema 1.0.0 and description |

## Portal vs API Differences

| Feature | Portal | REST API |
|---------|--------|----------|
| Create agent | ✅ UI wizard | ✅ POST /items |
| Set instructions | ✅ Text editor | ✅ stage_config.json |
| Add data source | ✅ Browse & select | ⚠️ Must know artifactId/workspaceId |
| Add few-shots | ✅ Interactive Q&A | ✅ fewshots.json |
| Publish | ✅ One-click | ✅ Add published/ parts + publish_info.json |
| Test agent | ✅ Chat interface | ❌ No API chat endpoint yet |
| Select elements | ✅ Checkbox tree | ✅ elements array in datasource.json |

**Key insight**: The portal is better for testing and element selection. The API is better for automation and version control. Use both.

---

## Debugging Checklist

When a Data Agent doesn't work as expected:

1. **Check data source**: Is the correct semantic model/lakehouse attached?
2. **Check instructions**: Are they in the right stage (draft vs published)?
3. **Check few-shots**: Do all queries execute correctly in DAX query view?
4. **Check names**: Do measure/column names match the model exactly (case-sensitive)?
5. **Check permissions**: Does the agent's identity have read access to the data source?
6. **Check capacity**: Is the workspace on a Fabric capacity that supports Data Agents?
7. **Try in portal**: Open the agent in Fabric portal and test interactively
8. **getDefinition round-trip**: Retrieve the definition and verify all parts are present

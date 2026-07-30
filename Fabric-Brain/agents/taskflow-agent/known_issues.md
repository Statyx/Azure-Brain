# Known Issues — Task Flows

## API & Automation

| Issue | Impact | Workaround |
|-------|--------|------------|
| **No REST API** | Cannot create/modify task flows programmatically | Generate `.json` template → import via portal |
| **No Fabric CLI support** | `fab` has no task flow commands | Portal only |
| **No item type `TaskFlow`** | Cannot `POST /items` with type `TaskFlow` | Portal-only creation |
| **JSON import = portal only** | No API endpoint for import | Must use Fabric portal UI |
| **JSON import fails with special chars** | Portal parser rejects Unicode chars (arrows, em-dashes, accented letters) | Use ASCII only in names/descriptions; save as UTF-8 without BOM |
| **JSON schema undocumented** | MS Learn docs don't show the import/export JSON schema | Use `type`/`id`(GUID)/`edges`(`source`/`target`) — NOT `taskType`/`connectors`/`startTaskId`. Export a sample flow from portal to verify |
| **Invalid task `type` value causes "Unable to parse the file" (root-caused 2026-06)** | Portal returns "Error importing your file — Unable to parse the file uploaded" even though the JSON is valid, ASCII, no BOM. Root cause: an unsupported `type` string. The schema shape (`{tasks:[{type,id,name,description}],edges:[{source,target}],name,description}`) IS correct — confirmed against a real portal export | Use ONLY the exact lowercase type values from a real export: `get data`, `store data`, `prepare data`, `track data`, `analyze and train data` (NOT `analyze and train`), `visualize`. `general`/`mirror data`/`distribute`/`develop` were NOT seen in the RTI export — verify before use. Activator/alerting tasks export as `track data`. When in doubt, build a flow in the portal and **export** to read the current valid values |
| **`prepare data` is a valid type — added to the confirmed list 2026-07-30** | The entry above previously listed only 5 confirmed values, so `prepare data` looked risky and got avoided in favour of `general` | `prepare data` imports cleanly and renders as *"Prepare data"* on the canvas. Confirmed 2026-07-30 on a successfully imported flow (`Fab-Marketing-Campaign`, task "Semantic Model - SM_Marketing_Analytics"). Still unconfirmed by export: `general`, `mirror data`, `distribute data`, `develop data` |

## Design & Behavior

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Unconnected tasks move on new task add** | Adding a new task resets positions of unconnected tasks | Connect ALL tasks with connectors BEFORE adding new ones |
| **One task flow per workspace** (SUPERSEDED 2026-07-30 — see Corrections) | Cannot have multiple task flows | Use task flow names/descriptions to document sections. No longer a constraint — Fabric now supports multiple canvases |
| **Item assigned to one task only** | Cannot assign same item to multiple tasks | Choose the most relevant task for multi-purpose items |
| **Export doesn't include item assignments** | Imported flows require manual item re-assignment | Document assignments separately |
| **No undo** | Deleting connectors/tasks is immediate | Export before making major changes |

## Item Creation from Tasks

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Cannot create paginated reports** from tasks | Not supported | Create in workspace, then assign to task |
| **Cannot create dataflows Gen1** from tasks | Not supported | Create in workspace, then assign to task |
| **Cannot create semantic models** from tasks | Not supported | Create in workspace, then assign to task |
| **Reports require published semantic model** | Creating a report from a task needs a published model first | Publish model, then create report from task |

## Visual

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Connectors don't represent data flow** | Users may confuse visual arrows with actual data connections | Document that connectors are logical only |
| **Task type change doesn't update name** | Changing type keeps old name/description | Manually update name after type change |
| **Resize preferences per user/workspace** | Different team members see different sizes | Standard team guideline for task flow visibility |

## Corrections

Rules above that were true when written but no longer hold. The original row is kept in place
and marked SUPERSEDED rather than deleted, so an agent that memorised it still finds the update.

### 2026-07-30 — Multiple task flow canvases per workspace are now supported

**Supersedes:** "One task flow per workspace" (Design & Behavior).
**What changed:** Fabric now lets a workspace hold several task flow canvases, each with its own
task flow, so separate workstreams no longer have to share one canvas.
**Impact on guidance:** stop advising teams to encode sections into a single flow's
names/descriptions as a workaround — split them into canvases instead.
**Evidence:** MS Learn documents it as current behaviour in
`fabric/fundamentals/task-flow-overview` ("A workspace can have one or more task flow canvases")
with a dedicated page `fabric/fundamentals/task-flow-multiple-canvases`.
**Status:** documentation-confirmed, not reproduced in the portal in this session.

### 2026-07-30 — `prepare data` confirmed as a valid task type

**Extends:** the "Invalid task `type` value" row (API & Automation).
**What changed:** nothing in the product — the brain's confirmed-values list was simply
incomplete, which made `prepare data` look unsafe.
**Evidence:** a generated flow using `prepare data` imported without error and the task renders
as *"Prepare data"* on the canvas (`Fab-Marketing-Campaign` workspace, 2026-07-30).
**Still unconfirmed by a real export:** `general`, `mirror data`, `distribute data`,
`develop data`. Verify by exporting before relying on them.

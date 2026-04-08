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

## Design & Behavior

| Issue | Impact | Workaround |
|-------|--------|------------|
| **Unconnected tasks move on new task add** | Adding a new task resets positions of unconnected tasks | Connect ALL tasks with connectors BEFORE adding new ones |
| **One task flow per workspace** | Cannot have multiple task flows | Use task flow names/descriptions to document sections |
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

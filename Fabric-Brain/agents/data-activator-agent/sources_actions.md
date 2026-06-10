# Sources & Actions — Entity Schemas

A Reflex definition needs **exactly one Source** entity and **one or more Action** steps
(inside the rule's `ActStep`). This file documents the supported source and action types.

---

## Sources (pick exactly one)

All sources attach to the Container via `parentContainer.targetUniqueIdentifier` (for
hand-authored pull flows). The SourceEvent (`timeSeriesView-v1`, type `"Event"`) references the
Source by `entityId`.

### 1. `kqlSource-v1` — Eventhouse / KQL Database (or external ADX)
The most common source for RTI alerting. **Return all data from the query — do not pre-filter
the alert condition** (the rule steps do the detection).

- Must include `eventhouseItem`, `metadata`, and `queryParameters`.
- **Fabric Eventhouse/KQL DB**: `eventhouseItem: { itemId, workspaceId, itemType: "KustoDatabase" }`.
- **External ADX/Kusto**: `eventhouseItem: { clusterHostName, databaseName }`.
- **Time axis**: when the query results have a reasonable timestamp column, use `eventTimeSettings`
  plus `DURATION_START`/`DURATION_END` query parameters, and declare them in the KQL:
  ```kusto
  declare query_parameters(startTime:datetime, endTime:datetime);
  ```
- **Snapshot mode** (`queryParameters: []`, no `eventTimeSettings`, no time filtering): only when the
  data has no timestamp column and each row is current state.
- ✅ **Run the KQL directly against the target first** and confirm columns, timestamp field, and row shape.

### 2. `eventstreamSource-v1` — Fabric Eventstream
Do **not** hand-author this source. First create/update the Eventstream with an **Activator
destination** (defer to `rti-eventstream-agent`), then read the Activator definition and continue
from the auto-created `eventstreamSource-v1` + SourceEvent entities. In public readback those
sink-created entities can appear **without** an explicit `parentContainer`.

### 3. `realTimeHubSource-v1` — Real-Time Hub
Subscribes to workspace event types via Real-Time Hub. Use the `rthSubscriptions` container
payload type for the Container when this is the source. References workspace event subscriptions.

### 4. `digitalTwinBuilderSource-v1` — Digital Twin Builder / Ontology
- `connection` is an item ref `{ itemId, workspaceId, itemType }` where `itemType` is
  `DigitalTwinBuilder` or `Ontology`.
- `query.queryString` is a **JSON-string payload**, NOT KQL.
- ✅ Run the DTB/Ontology query directly first and confirm columns, key fields, and timestamp field.
- Prefer `eventTimeSettings` + `DURATION_START`/`DURATION_END` when rows include a timestamp.
  Unlike KQL, those duration parameters are applied as **DTB endpoint URL query params**, not inside the query body.
- Ontology entity types / GQL are owned by `agents/ontology-agent/` — defer modeling there.

### Container payload type must match the source
| Source | Container payload type |
|---|---|
| KQL | `kqlQueries` |
| Real-Time Hub | `rthSubscriptions` |
| Eventstream | the service-created type already present in readback |

---

## Actions (inside the rule's `ActStep`)

### 1. `TeamsMessage`
Sends a Teams message. Supports dynamic content from event fields.
- Inline mixed-content fragments in `headline` / `optionalMessage` use `AttributeReference`
  with `type: "complex"`.
- Structured `additionalInformation` entries use `NameReferencePair` + `AttributeReference` /
  `EventFieldReference` with `type: "complexReference"` and `name: "reference"`.
- Preserve these field-specific reference shapes from working readback — they are easy to get wrong.

### 2. `EmailMessage`
Sends an email. Subject/body support the same dynamic field-reference shapes as Teams.

### 3. `FabricItemInvocation`
Runs a Fabric item when the rule fires: **Pipeline, Notebook, Spark job definition, Dataflow, or
UDF / Function Set**.

- Requires a **standalone `fabricItemAction-v1` entity** (Step 6 of the assembly procedure),
  attached to the Container via `parentContainer`.
- In the rule's `FabricItemBinding`, set `fabricJobConnectionDocumentId` to that
  `fabricItemAction-v1.uniqueIdentifier`.
- UDF gotchas: `itemType` vs readback `FunctionSet`, `subitemId`, canonical `parameterType`
  mapping, and the dynamic parameter shape — preserve from working readback.
- The action *targets* (pipelines, notebooks) are authored by `orchestrator-agent` /
  `lakehouse-agent`; this agent only wires the invocation.

---

## Action entity (Python sketch)

```python
def make_fabric_item_action(container_guid, item_id, workspace_id, item_type):
    """Standalone fabricItemAction-v1 entity for a FabricItemInvocation rule."""
    return {
        "uniqueIdentifier": new_guid(),
        "payload": {
            "parentContainer": {"targetUniqueIdentifier": container_guid},
            "fabricItem": {"itemId": item_id, "workspaceId": workspace_id, "itemType": item_type},
            # plus parameter mappings per target type — see UDF gotchas above
        },
        "type": "fabricItemAction-v1",
    }
```

> Always validate the wired source by running its query directly, and prefer transition-based
> detectors (see `rule_conditions.md`) so the action does not fire repeatedly while a condition holds.

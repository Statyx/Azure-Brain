# Rule Conditions — Templates, Detectors, Steps

Two rule template types live inside a `timeSeriesView-v1` entity's `definition.instance`
(always a JSON string). Pick the right one for the scenario.

| Template | When to use | Steps |
|---|---|---|
| `AttributeTrigger` | Monitor an attribute value (numeric, text, boolean, aggregation) | `ScalarSelectStep` → `ScalarDetectStep` → (`DimensionalFilterStep`)* → `ActStep` |
| `EventTrigger` | Fire on event occurrence (state, change, heartbeat) | `FieldsDefaultsStep` → (`EventDetectStep`)+ → (`DimensionalFilterStep`)* → `ActStep` |

> `EventTrigger` has **no** `ScalarSelectStep`/`ScalarDetectStep`. Use it when acting on events directly.
> Hand-authored flows use `templateVersion: "1.2.4"`. Eventstream sink-created readbacks may use `"1.1"`.

---

## AttributeTrigger

Monitors a single value attribute and fires when a detection condition is met.

### Step pipeline
1. **ScalarSelectStep** — selects the value attribute to watch (references the Value Attr by `entityId`).
2. **ScalarDetectStep** — the detection condition (detector + operands). See detectors below.
3. **DimensionalFilterStep** (optional, repeatable) — restrict to a subset (e.g. only `Region = "EMEA"`).
4. **ActStep** — the action to run (Teams / Email / FabricItemInvocation). See `sources_actions.md`.

### Detectors (choose transition over steady-state by default)

| Detector | Type | Fires when |
|---|---|---|
| `NumberBecomes` | transition ✅ | value crosses into a number/comparison (e.g. becomes > 30) |
| `NumberEntersOrLeavesRange` | transition ✅ | value enters or leaves a range |
| `LogicalBecomes` | transition ✅ | boolean becomes true/false |
| `TextBecomes` | transition ✅ | text becomes / starts matching |
| `IsGreaterThan` | steady-state ⚠️ | value stays above a threshold (fires repeatedly) |
| `IsLessThan` | steady-state ⚠️ | value stays below a threshold |
| `IsOutsideRange` | steady-state ⚠️ | value stays outside a range |

> **Default to transition detectors.** Treat ordinary wording ("is greater than", "is below",
> "is outside the range") as "notify me when it *crosses into* that state". Only use steady-state
> detectors when the user explicitly asks for repeated firing while the value stays in the state
> ("notify me every time it is greater than 30", "fire on every evaluation while above 30") or
> when a downstream occurrence/windowing pattern depends on that semantics.

### Occurrence & time windows (optional)
`ScalarDetectStep` can carry occurrence/window options — e.g. "fire only if the condition holds
for N consecutive evaluations" or "aggregate over a time window before detecting". Use these to
de-noise alerts. Aggregation (avg/min/max/count over a window) is configured on the value
attribute or the detect step depending on the template version.

---

## EventTrigger

Fires per event without modeling an Object/attribute graph. Reads raw event fields directly.

### Step pipeline
1. **FieldsDefaultsStep** — declares default field references read from the SourceEvent.
2. **EventDetectStep** (one or more) — the event detection: `state`, `change`, or `heartbeat`.
3. **DimensionalFilterStep** (optional, repeatable).
4. **ActStep** — the action.

### Detection modes
| Mode | Fires when |
|---|---|
| `state` | a field reaches/holds a given state |
| `change` | a field value changes |
| `heartbeat` | no event arrives within an expected interval (absence detection) |

---

## Rule entity envelope (Python)

```python
def make_rule_entity(name, container_guid, instance_template,
                     object_guid=None):
    """Build a timeSeriesView-v1 Rule entity. object_guid only for AttributeTrigger."""
    payload = {
        "name": name,
        "description": "Created by: Azure-Brain data-activator-agent",  # required for clarity
        "parentContainer": {"targetUniqueIdentifier": container_guid},
        "definition": {
            "type": "Rule",
            "instance": stringify_instance(instance_template),  # JSON STRING
            "settings": {"shouldRun": True, "shouldApplyRuleOnUpdate": False},
        },
    }
    if object_guid:  # AttributeTrigger binds to the Object
        payload["parentObject"] = {"targetUniqueIdentifier": object_guid}
    return {
        "uniqueIdentifier": new_guid(),
        "payload": payload,
        "type": "timeSeriesView-v1",
    }
```

### Settings
- `shouldRun: true` → rule starts in the **started / running** state (default).
- `shouldRun: false` → only when the user asks for a stopped rule, or for a safe verification/eval
  workflow that must avoid side effects.
- `shouldApplyRuleOnUpdate: false` → do not retroactively evaluate on update (default).

---

## Critical reminders
- `definition.instance` is a **JSON string** — `json.dumps()`, never a nested object, never PowerShell.
- Wrap every rule template in the full entity envelope (above) — never emit a raw template object.
- Every step in `instance.steps[]` needs its own `id` GUID.
- AttributeTrigger → set both `parentObject` (Object) and `parentContainer` (Container).
- EventTrigger → set `parentContainer` only; omit `parentObject` unless explicitly required.

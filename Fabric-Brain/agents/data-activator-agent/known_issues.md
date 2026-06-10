# Known Issues — Data Activator (Reflex)

## 1. `definition.instance` must be a JSON string
**Symptom**: Rule import fails / invalid expression graph / silent no-op.
**Cause**: `instance` was emitted as a nested JSON object instead of a JSON-encoded string.
**Fix**: `json.dumps(template, separators=(",", ":"))`. Wrap the template in the full
`timeSeriesView-v1` entity envelope. Never use PowerShell `ConvertTo-Json`.

## 2. Missing step `id` GUIDs
**Symptom**: Backend translation produces an invalid expression graph; rule never fires.
**Cause**: One or more steps in `instance.steps[]` have no `id`.
**Fix**: Give every step a fresh `id` GUID — translators use the step ID as the output node ID.

## 3. Duplicate `uniqueIdentifier`
**Symptom**: Corrupted definition; cross-references resolve to the wrong entity.
**Cause**: Reused a GUID across entities.
**Fix**: `str(uuid.uuid4())` for every entity. When changing a GUID, update every
`targetUniqueIdentifier` / `entityId` that references it.

## 4. `getDefinition` returns 411 or empty
**Symptom**: HTTP 411 Length Required, or no definition returned.
**Cause**: `getDefinition` is a **POST** and needs a body; the empty body was omitted.
**Fix**: Always send `--body '{}'` (or JSON `{}` in requests). It may also return **202 LRO** —
poll the `Location` header before decoding.

## 5. Wrong endpoint (`/items` instead of `/reflexes`)
**Symptom**: 404 / item not found on create or definition calls.
**Cause**: Used the generic `/items` endpoint.
**Fix**: Use `/workspaces/{ws}/reflexes` (and `/reflexes/{id}/getDefinition|updateDefinition`).

## 6. Alert fires repeatedly ("alert spam")
**Symptom**: Continuous notifications while a value stays above a threshold.
**Cause**: A steady-state detector (`IsGreaterThan`, `IsLessThan`, `IsOutsideRange`) was used.
**Fix**: Switch to a transition detector (`NumberBecomes`, `NumberEntersOrLeavesRange`,
`LogicalBecomes`). Treat casual wording as "notify me when it crosses into that state".

## 7. KQL source pre-filtered the condition
**Symptom**: Rule never sees data it should act on, or behaves inconsistently.
**Cause**: The alert threshold/condition was baked into the KQL query.
**Fix**: Return all rows from KQL; let the rule's detect + dimensional-filter steps handle it.
Run the KQL directly first to confirm columns, timestamp, and row shape.

## 8. Wrong token audience → 401
**Symptom**: 401 Unauthorized on `az rest` / REST calls.
**Cause**: Token acquired for the wrong resource.
**Fix**: Acquire the token for `https://api.fabric.microsoft.com` (the project's
`get_fabric_token()` already does this). Scope: `Reflex.ReadWrite.All` or `Item.ReadWrite.All`.

## 9. Reusing a display name right after deletion
**Symptom**: Create fails with a name conflict shortly after deleting a reflex.
**Cause**: Soft-deleted items hold their name for several minutes.
**Fix**: Use a unique name, or hard-delete first (`?hardDelete=true`).

## 10. `getDefinition` blocked on sensitivity-labeled items
**Symptom**: `getDefinition` fails for an item with an encrypted sensitivity label.
**Cause**: Definitions of items with encrypted labels cannot be read.
**Fix**: Remove/adjust the label out of band, or manage the rule in the Fabric UI.

## 11. PowerShell mangles the request body
**Symptom**: Malformed JSON, broken nested strings, escaped-quote errors.
**Cause**: Built `ReflexEntities.json` or the request body in PowerShell, or passed inline JSON to
`az rest --body`.
**Fix**: Build everything in Python (`json.dumps` + base64). If you must use `az rest`, write the
body to a UTF-8 file and pass `--body @path`.

## 12. Eventstream source hand-authored from scratch
**Symptom**: Source/SourceEvent entities don't bind; events never reach the rule.
**Cause**: Tried to hand-author `eventstreamSource-v1`.
**Fix**: Create/update the Eventstream with an Activator destination first (via
`rti-eventstream-agent`), then read back the auto-created source + SourceEvent and continue.
Preserve the existing `templateVersion` (often `1.1`) from readback.

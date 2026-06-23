# Known Issues & Gotchas — Ontology Agent

---

## Tenant Admin Settings

These must be enabled in **Fabric Admin Portal → Tenant settings** before ontology features work:

| Setting | Required For | Default |
|---------|-------------|---------|
| Ontology (preview) | Ontology items | Off (preview) |
| Graph (preview) | Graph Model, Graph Query Set | Off (preview) |
| Copilot and Azure OpenAI Service | Data Agent with Ontology source | Off |
| Users can create and share Data agent item types | Data Agent | Off |
| Real-Time Intelligence | Eventhouse / KQL Database (for TimeSeries bindings) | Off |

> After enabling, wait **5–10 minutes** for propagation.

---

## Capacity Requirements

| Feature | Minimum SKU | Notes |
|---------|------------|-------|
| Ontology | F2 | Preview feature ([Learn](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-use-ontology-mcp-server#prerequisites)) |
| Graph Model | F2 | Preview feature |
| Graph Query Set | F2 | Preview feature |
| Ontology MCP server | F2 | **Confirmed by Learn** — "a paid F2 or higher Fabric capacity" |
| Data Agent (Ontology source) | *unverified* | A specific SKU floor for a Data Agent *bound to an ontology source* is **not documented on Learn**. Test on your capacity; do not assume F64. |

> The MCP-server path (consuming the ontology from an agent) works on **F2+**. The capacity floor for a Data Agent item bound to an ontology source is unconfirmed — verify empirically rather than trusting a hard-coded number.

---

## Common Issues

### 1. Binding Validation Error on updateDefinition

**Symptom**: `updateDefinition` returns 400 with "binding validation error".

**Root causes**:
- Source table doesn't exist yet (Lakehouse/KQL tables not created)
- Property IDs in binding don't match entity type definition
- Column names in binding don't match actual table columns (case-sensitive)
- `entityIdParts` not set on the entity type

**Fix**: 
1. ALWAYS create Lakehouse tables and KQL tables **before** deploying the Ontology
2. Verify column names exactly match between source tables and property bindings
3. Ensure every entity type has `entityIdParts` set

### 2. Duplicate Entities in Graph

**Symptom**: The graph shows duplicate nodes for the same entity.

**Cause**: Non-deterministic GUIDs for data bindings → each re-push creates new bindings.

**Fix**: Use `DeterministicGuid()` with unique seed strings. Same seed = same GUID = same binding ID = no duplicates.

```powershell
function DeterministicGuid([string]$seed) {
    $hash = [System.Security.Cryptography.MD5]::Create().ComputeHash(
        [System.Text.Encoding]::UTF8.GetBytes($seed))
    return ([guid]::new($hash)).ToString()
}
```

### 3. Graph Model is Empty

**Symptom**: Ontology deployed successfully, but Graph Model shows no nodes/edges.

**Causes**:
- Ontology has no relationships (entity types only — need at least one relationship)
- Bindings reference tables that don't exist or are empty
- Graph Model not refreshed after ontology update

**Fix**: Add at least one relationship type with a valid contextualization, then refresh the Graph Model.

### 4. Graph Query Set Has No Queries

**Symptom**: Created a Graph Query Set via API but it's empty.

**Cause**: Graph Query Sets **cannot have queries pushed via API**. The API only creates the item.

**Fix**: Open the Graph Query Set in the Fabric portal UI and add GQL queries manually.

### 5. updateDefinition Returns 404

**Symptom**: `POST .../updateDefinition` returns 404.

**Fix**: Try both endpoint formats:
```powershell
# Format 1 (standard)
POST /v1/workspaces/{wsId}/items/{itemId}/updateDefinition

# Format 2 (typed endpoint)
POST /v1/workspaces/{wsId}/ontologies/{itemId}/updateDefinition
```

### 6. ConvertTo-Json Crashes on Large Ontologies

**Symptom**: PowerShell 5.1 `ConvertTo-Json` silently truncates or crashes on large ontology definitions (50+ parts).

**Fix**: Build the JSON string manually:
```powershell
$partsJson = ($parts | ForEach-Object {
    '{"path":"' + $_.path + '","payload":"' + $_.payload + '","payloadType":"InlineBase64"}'
}) -join ','
$bodyStr = '{"definition":{"parts":[' + $partsJson + ']}}'
```

### 7. Data Agent Can't Query Ontology

**Symptom**: Data Agent created with Ontology source but returns no results or errors.

**Causes**:
- Insufficient capacity (verify empirically — no documented SKU floor for this path)
- Ontology bindings are invalid
- Graph Model not generated

**Fix**: Verify ontology bindings, ensure the Graph Model exists, then rule out capacity by testing on a larger SKU if the smaller one fails.

### 8. TimeSeries Binding Missing timestampColumnName

**Symptom**: TimeSeries binding fails or timeseries data not available.

**Cause**: `timestampColumnName` not set in the binding configuration.

**Fix**: Always include `timestampColumnName` in TimeSeries bindings:
```json
{
    "dataBindingConfiguration": {
        "dataBindingType": "TimeSeries",
        "timestampColumnName": "Timestamp",
        ...
    }
}
```

### 9. Contextualization FK Column Not Found

**Symptom**: Relationship created but contextualization fails validation.

**Cause**: The `sourceColumnName` in `sourceKeyRefBindings` or `targetKeyRefBindings` doesn't match any column in the `dataBindingTable`.

**Fix**:
1. Verify the FK column exists in the specified table
2. Check for naming patterns: `FromXxxId`, `PerformedByXxxId`, `ReportedByXxxId`
3. Column names are case-sensitive — verify exact spelling

### 10. Ontology Generated from Semantic Model is Incomplete

**Symptom**: Using "Generate Ontology" from a Semantic Model creates some entity types but misses relationships or gets wrong keys.

**Fix**: The UI generator provides a starting point only. After generation:
1. Verify `entityIdParts` on each entity type
2. Add missing relationships manually
3. Configure contextualizations (FK mappings) by hand
4. Add TimeSeries bindings if needed (the generator only creates NonTimeSeries from Lakehouse)

---

## Deployment Order (Strict)

Always follow this sequence — ontology items depend on previous steps:

```
1. Lakehouse → CSV upload → Spark notebook creates Delta tables
2. Eventhouse → KQL Database → KQL tables (via Kusto REST)
3. Ontology → entity types + data bindings + relationships + contextualizations
4. Graph Model → auto-generated from Ontology (refresh if needed)
5. Graph Query Set → create via API → add queries in UI
6. Data Agent → source = Ontology (capacity floor unverified — test on your SKU)
```

> **Never skip steps.** Deploying step 3 before steps 1–2 causes binding validation errors.

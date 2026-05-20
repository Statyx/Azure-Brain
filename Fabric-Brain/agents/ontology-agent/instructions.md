# Ontology Agent — Instructions

## System Prompt

You are an expert at designing, deploying, and querying Microsoft Fabric Ontologies. You understand entity types, properties, data bindings (NonTimeSeries + TimeSeries), relationships, contextualizations, Graph Models, Graph Query Sets (GQL), and Data Agents that use an Ontology as their source.

**Before any ontology work**, load this file plus `entity_types_bindings.md`, `relationships_contextualizations.md`, and `graph_queries.md`.

---

## Mandatory Rules

### Rule 1: Ontology Depends on Data — Deploy Data First
The Ontology binds to existing tables. **Never deploy an Ontology before its data sources exist.**

Strict order:
1. Lakehouse → CSV upload → Spark notebook creates Delta tables
2. Eventhouse → KQL Database → KQL tables created via Kusto REST
3. **Then** Ontology → entity types + data bindings + relationships + contextualizations
4. Graph Model → auto-generated from Ontology
5. Graph Query Set → created via API, queries added in UI
6. Data Agent → source = Ontology

> Deploying an Ontology before tables exist causes binding validation errors that are hard to debug.

### Rule 2: Use Deterministic GUIDs for Idempotent Deployments
Every data binding and contextualization needs a GUID. Use deterministic GUIDs from seed strings so re-pushing the same definition doesn't create duplicates.

```powershell
function DeterministicGuid([string]$seed) {
    $hash = [System.Security.Cryptography.MD5]::Create().ComputeHash(
        [System.Text.Encoding]::UTF8.GetBytes($seed))
    return ([guid]::new($hash)).ToString()
}
```

Seed conventions:
- `"NonTimeSeries-{entityTypeId}"` — for Lakehouse bindings
- `"TimeSeries-{entityTypeId}"` — for KQL bindings
- `"Ctx-{relationshipId}"` — for contextualizations

### Rule 3: ID Allocation Must Be Deterministic
Use a fixed ID range scheme so entity types, properties, and relationships are always reproducible:

| Range | Purpose |
|-------|---------|
| 1001 – 1099 | Entity Type IDs |
| 2001 – 2999 | Property IDs (100 per entity type: 2001–2099 for entity 1001, 2101–2199 for entity 1002, etc.) |
| 3001 – 3099 | Relationship Type IDs |
| 4001 – 4099 | Timeseries Property IDs |

### Rule 4: Entity Types Must Have entityIdParts
Every entity type MUST declare `entityIdParts` — the property IDs that form its unique key. Without this, bindings will fail silently or produce duplicate instances.

### Rule 5: Column Names Must Match Exactly
Data binding `sourceColumnName` values must **exactly** match the column names in the source table (Lakehouse or KQL). Case matters. Verify column names against the actual table before building bindings.

---

## Decision Trees

### "I need to create an Ontology"
```
├── Do the source tables exist?
│   ├── NO → Deploy Lakehouse + KQL tables first (→ orchestrator-agent / rti-kusto-agent)
│   └── YES → Proceed
├── Do you have the domain model?
│   ├── YES → Build entity types manually from the domain model
│   │   └── Define: entity type ID, properties, entityIdParts, displayNamePropertyId
│   └── NO → Generate from Semantic Model
│       └── Fabric UI → Semantic Model → "Generate Ontology" → then customize
├── Does the entity have real-time (streaming) data?
│   ├── YES → Add timeseriesProperties + TimeSeries binding (KQL)
│   └── NO → NonTimeSeries binding (Lakehouse) only
├── Are there relationships between entities?
│   ├── YES → Build relationship types + contextualizations
│   │   └── Determine FK strategy: FK in source table or FK in target table?
│   └── NO → Flat ontology (entity types only)
└── Push via updateDefinition (all parts in one atomic call)
```

### "I need to query the Ontology / Graph"
```
├── Is it a graph traversal query (entity relationships)?
│   ├── YES → GQL via Graph Query Set
│   │   ├── Graph Model exists? → Write GQL MATCH patterns
│   │   └── No Graph Model → Refresh from Ontology first
│   └── NO → Use KQL for time-series or SQL for Lakehouse tables directly
├── Is it a natural-language query over the Ontology?
│   └── YES → Data Agent with Ontology source
│       └── Requires F64 capacity (will NOT work on Trial or F2)
└── Is it an operational monitoring query?
    └── YES → Operations Agent (KQL-based) → see rti-kusto-agent
```

### "I need to update an existing Ontology"
```
├── Adding a new entity type?
│   └── Add to definition parts + create its data bindings → re-push via updateDefinition
├── Adding a new relationship?
│   └── Add relationship type + contextualization → re-push via updateDefinition
├── Changing property types or names?
│   └── Re-push entire definition (updateDefinition is idempotent with deterministic GUIDs)
└── Changing data source tables?
    └── Update binding sourceTableProperties → re-push via updateDefinition
```

---

## Ontology Definition Structure

The definition is pushed as Base64-encoded JSON parts via `updateDefinition`:

```
.platform                                         → metadata + config
definition.json                                   → empty ({})
EntityTypes/{id}/definition.json                  → entity type schema
EntityTypes/{id}/DataBindings/{guid}.json         → data source binding
RelationshipTypes/{id}/definition.json            → relationship schema
RelationshipTypes/{id}/Contextualizations/{guid}.json → FK mapping
```

All parts are assembled into a single `updateDefinition` POST call — this is **atomic**.

---

## API Quick Reference

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create Ontology item | POST | `/v1/workspaces/{wsId}/items` with `type: "Ontology"` |
| Push full definition | POST | `/v1/workspaces/{wsId}/items/{ontId}/updateDefinition` |
| Get Ontology | GET | `/v1/workspaces/{wsId}/items/{ontId}` |
| Delete Ontology | DELETE | `/v1/workspaces/{wsId}/items/{ontId}` |
| Create Graph Query Set | POST | `/v1/workspaces/{wsId}/items` with `type: "GraphQLApi"` |
| Create Data Agent (ontology) | POST | `/v1/workspaces/{wsId}/dataAgents` |
| Push Data Agent definition | POST | `/v1/workspaces/{wsId}/dataAgents/{agentId}/updateDefinition` |

---

## Part Assembly Pattern (PowerShell)

```powershell
function ToBase64([string]$text) {
    [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($text))
}

$parts = @()

# .platform
$platformJson = '{"$schema":"...","config":{"version":"2.0","logicalId":"..."},"metadata":{"type":"Ontology","displayName":"MyOntology"}}'
$parts += @{ path = ".platform"; payload = (ToBase64 $platformJson); payloadType = "InlineBase64" }

# definition.json (always empty)
$parts += @{ path = "definition.json"; payload = (ToBase64 "{}"); payloadType = "InlineBase64" }

# Entity types + bindings
foreach ($et in $entityTypes) {
    $parts += @{ path = "EntityTypes/$($et.id)/definition.json"; payload = (ToBase64 ($et | ConvertTo-Json -Depth 10)); payloadType = "InlineBase64" }
    $parts += @{ path = "EntityTypes/$($et.id)/DataBindings/$($et.bindGuid).json"; payload = (ToBase64 ($et.binding | ConvertTo-Json -Depth 10)); payloadType = "InlineBase64" }
    if ($et.tsBindGuid) {
        $parts += @{ path = "EntityTypes/$($et.id)/DataBindings/$($et.tsBindGuid).json"; payload = (ToBase64 ($et.tsBinding | ConvertTo-Json -Depth 10)); payloadType = "InlineBase64" }
    }
}

# Relationships + contextualizations
foreach ($rel in $relationships) {
    $parts += @{ path = "RelationshipTypes/$($rel.id)/definition.json"; payload = (ToBase64 ($rel | ConvertTo-Json -Depth 10)); payloadType = "InlineBase64" }
    $parts += @{ path = "RelationshipTypes/$($rel.id)/Contextualizations/$($rel.ctxGuid).json"; payload = (ToBase64 ($rel.ctx | ConvertTo-Json -Depth 10)); payloadType = "InlineBase64" }
}

# Build JSON manually (PS 5.1 ConvertTo-Json crashes on large payloads)
$partsJson = ($parts | ForEach-Object {
    '{"path":"' + $_.path + '","payload":"' + $_.payload + '","payloadType":"InlineBase64"}'
}) -join ','
$bodyStr = '{"definition":{"parts":[' + $partsJson + ']}}'

# Push
Invoke-WebRequest -Uri "$apiBase/workspaces/$WorkspaceId/items/$OntologyId/updateDefinition" `
    -Method POST -Headers $headers -Body $bodyStr
```

---

## Typical Part Counts

| Ontology Size | Entity Types | Relationships | Total Parts |
|---------------|-------------|---------------|-------------|
| Small (5 entities) | ~15 parts | ~10 parts | ~27 |
| Medium (13 entities) | ~30 parts | ~30 parts | ~62 |
| Large (25+ entities) | ~55 parts | ~50+ parts | ~107+ |

---

## Authentication

```powershell
# Fabric API token (PowerShell)
$fabricToken = (Get-AzAccessToken -ResourceUrl "https://api.fabric.microsoft.com").Token

# Headers
$headers = @{
    "Authorization" = "Bearer $fabricToken"
    "Content-Type"  = "application/json"
}
```

```python
# Python
from azure.identity import AzureCliCredential
credential = AzureCliCredential()
token = credential.get_token("https://api.fabric.microsoft.com/.default").token
```

---

## Error Recovery

| Error | Cause | Fix |
|-------|-------|-----|
| Binding validation error | Source table doesn't exist or column name mismatch | Deploy Lakehouse/KQL tables first; verify column names exactly |
| 404 on updateDefinition | Wrong endpoint format | Try both `/items/{id}/updateDefinition` and `/{itemType}s/{id}/updateDefinition` |
| 400 on updateDefinition | Malformed JSON or missing required fields | Check `entityIdParts`, `displayNamePropertyId`, property IDs |
| Duplicate entities in graph | Non-deterministic GUIDs | Use `DeterministicGuid()` with unique seed strings |
| Graph Model empty | Ontology has no relationships | Add at least one relationship type with contextualization |
| Data Agent can't query | Wrong capacity | Data Agent with ontology source requires **F64** minimum |

---

## Cross-References

| Topic | Agent | File |
|-------|-------|------|
| Lakehouse tables (source for NonTimeSeries bindings) | orchestrator-agent | `ingestion.md` |
| KQL tables (source for TimeSeries bindings) | rti-kusto-agent | `eventhouse_kql.md` |
| KQL language for time-series queries | rti-kusto-agent | `kql_language.md` |
| Data Agent instruction writing | ai-skills-agent | `instruction_writing_guide.md` |
| Data Agent definition structure | ai-skills-agent | `definition_structure.md` |
| Fabric REST API patterns | root | `fabric_api.md` |
| Tenant admin settings for ontology | ontology-agent | `known_issues.md` |

# Known Issues & Gotchas — Fabric RTI

## Tenant Admin Settings

These settings must be enabled in the **Fabric Admin Portal** → **Tenant settings** before RTI features work:

| Setting | Required For | Default |
|---------|-------------|---------|
| Real-Time Intelligence | Eventhouse, KQL Database | Off |
| Real-Time Intelligence Data Hub | Data Hub integration | Off |
| Ontology (preview) | Ontology items | Off (preview) |
| Graph (preview) | Graph Model, Graph Query Set | Off (preview) |
| AI Skills and Email (preview) | Operations Agent | Off (preview) |
| Users can try Microsoft Fabric paid features | Trial capacity | Off |
| **Copilot and Azure OpenAI Service** | Data Agent, Operations Agent | Off |

> After enabling, wait 5-10 minutes for propagation.

## Capacity Requirements

| Feature | Minimum SKU | Notes |
|---------|------------|-------|
| Eventhouse / KQL Database | F2 | Trial may work |
| KQL Dashboard | F2 | Trial may work |
| Ontology | F2 | Preview feature |
| Graph Model | F2 | Preview feature |
| Graph Query Set | F2 | Preview feature |
| Operations Agent | F2 | Trial may work |
| Data Agent (Ontology source) | **F64** | Will NOT work on Trial or lower |
| Semantic Model (Direct Lake) | F2 | Trial may work |

## API Limitations

| Item Type | Create via API | Push Definition via API | Notes |
|-----------|---------------|------------------------|-------|
| Eventhouse | ✅ | N/A | Auto-creates KQL Database |
| KQL Database | ✅ (auto) | N/A | Created with Eventhouse |
| KQL Tables | ✅ (Kusto REST) | N/A | Use `.create-merge table` |
| KQL Dashboard | ✅ | ✅ | `RealTimeDashboard.json` |
| Ontology | ✅ | ✅ | Entity types + bindings |
| Graph Model | ❌ | ❌ | Auto-generated from Ontology |
| Graph Query Set | ✅ (create only) | ❌ | **Queries must be added in UI** |
| Data Agent | ✅ | ✅ | Source = Ontology or Semantic Model |
| Operations Agent | ✅ | ✅ | **Knowledge Source must be added in UI** |
| Semantic Model | ✅ (Fabric API) | ✅ | TMDL or TMSL definition |

## Common Issues

### 1. KQL Token Scope
**Problem**: Token acquired for `https://api.fabric.microsoft.com` fails on Kusto REST API.

**Fix**: Try token resources in this order:
1. `{queryServiceUri}` (the actual cluster URI)
2. `https://kusto.kusto.windows.net`
3. `https://help.kusto.windows.net`

```powershell
$tokenResources = @($queryServiceUri, "https://kusto.kusto.windows.net", "https://help.kusto.windows.net")
foreach ($res in $tokenResources) {
    try {
        $kustoToken = (Get-AzAccessToken -ResourceUrl $res).Token
        break
    } catch { continue }
}
```

### 2. Inline Ingestion Size Limit
**Problem**: `.ingest inline` fails with large payloads.

**Fix**: Batch ingestion into ~50 rows per command (~64KB max payload). Loop over batches:
```powershell
$batchSize = 50
for ($i = 0; $i -lt $rows.Count; $i += $batchSize) {
    $batch = $rows[$i..([math]::Min($i + $batchSize - 1, $rows.Count - 1))]
    $inlineData = ($batch | ForEach-Object { $_ -join "," }) -join "`n"
    $cmd = ".ingest inline into table $tableName <| $inlineData"
    Invoke-KustoMgmt -Query $cmd ...
}
```

### 3. SQL Endpoint Provisioning Delay
**Problem**: After creating a Lakehouse, the SQL endpoint isn't immediately available.

**Fix**: Poll for the SQL endpoint with retries:
```powershell
$maxRetries = 20
for ($r = 0; $r -lt $maxRetries; $r++) {
    $sqlEp = (Invoke-FabricApi -Uri "$base/workspaces/$wsId/items?type=SQLEndpoint").value |
        Where-Object { $_.displayName -eq $lakehouseName }
    if ($sqlEp) { break }
    Start-Sleep -Seconds 10
}
```

### 4. Operations Agent Knowledge Source
**Problem**: The API creates the Operations Agent but it can't query the KQL database.

**Fix**: After API deployment, manually add the KQL Database as a Knowledge Source in the Fabric portal. There is no API to configure data sources for Operations Agents.

### 5. Graph Query Set Queries
**Problem**: Created a Graph Query Set via API but it has no queries.

**Fix**: Graph Query Sets don't support pushing query content via API. Open the item in Fabric portal and add GQL queries manually.

### 6. updateDefinition 404/400
**Problem**: `POST .../updateDefinition` returns 404 or 400.

**Fix**: Some item types use a different endpoint format. Try both:
```powershell
# Format 1 (standard)
POST /workspaces/{wsId}/items/{itemId}/updateDefinition

# Format 2 (typed endpoint)
POST /workspaces/{wsId}/{itemType}s/{itemId}/updateDefinition
```

### 7. ConvertTo-Json Crashes on Large Payloads
**Problem**: PowerShell 5.1's `ConvertTo-Json` silently truncates large JSON or crashes on deep nesting.

**Fix**: Build JSON string manually for the `updateDefinition` body:
```powershell
$partsJson = ($parts | ForEach-Object {
    '{"path":"' + $_.path + '","payload":"' + $_.payload + '","payloadType":"InlineBase64"}'
}) -join ','
$bodyStr = '{"definition":{"parts":[' + $partsJson + ']}}'
```

### 8. Ontology Binding Validation
**Problem**: Ontology deployment fails with "binding validation error".

**Root causes**:
- Property IDs in binding don't match entity type definition
- Source table doesn't exist yet (Lakehouse tables not created)
- Column names in binding don't match actual table columns

**Fix**: ALWAYS create Lakehouse tables and KQL tables BEFORE deploying the Ontology. Verify column names exactly match between source tables and property bindings.

### 9. KQL Database Not Ready After Eventhouse Creation
**Problem**: KQL table creation fails immediately after Eventhouse creation.

**Fix**: The auto-created KQL Database needs time to provision. Poll until ready:
```powershell
do {
    Start-Sleep -Seconds 5
    $kqlDb = (Invoke-FabricApi -Uri "$base/workspaces/$wsId/items?type=KQLDatabase").value |
        Where-Object { $_.displayName -eq $eventhouseName }
} while (-not $kqlDb)
```

### 10. DeterministicGuid Collisions
**Problem**: Two different seed strings produce the same MD5-derived GUID.

**Fix**: Use descriptive, unique seed strings with prefixes:
```
"NonTimeSeries-{entityTypeId}"
"TimeSeries-{entityTypeId}"
"Ctx-{relationshipId}"
```

## Deployment Order (Strict)

Always follow this sequence — items depend on previous steps:

```
1. Lakehouse (+ wait for SQL Endpoint)
2. Data Ingestion (CSVs → Delta tables via Spark notebook)
3. Eventhouse (auto-creates KQL Database)
4. KQL Tables (via Kusto REST mgmt API)
5. EventStream (Custom Endpoint source → KQL Database destinations)
6. Data Injection (Event Hub SDK → EventStream → KQL tables)
7. Semantic Model (Direct Lake over Lakehouse)
8. KQL Dashboard (tiles query KQL Database)
9. Ontology (binds to both Lakehouse + KQL Database)
10. Graph Query Set (manual queries in UI)
11. Data Agent (source = Ontology)
12. Operations Agent (+ manual Knowledge Source)
```

---

## EventStream Issues

### 11. EventStream Custom Endpoint Connection String NOT Available via API
- **Problem**: No REST API endpoint exposes the Custom Endpoint connection string.
- **Tried**: `GET /eventstreams/{id}`, `getDefinition`, topology API, various undocumented paths — all 404 or omit it.
- **Fix**: Get it manually from Fabric portal → EventStream → Custom Endpoint → connection details.

### 12. EventStream Destination `itemId` Must Be KQL Database ID
- **Problem**: Using Eventhouse ID as `itemId` in destination configuration fails silently.
- **Fix**: Always use the **KQL Database ID** (`GET /workspaces/{wsId}/kqlDatabases`), NOT the Eventhouse ID.

### 13. EventStream Topology API
- **Endpoint**: `GET /v1/workspaces/{wsId}/eventstreams/{esId}/topology`
- **Returns**: Sources, streams, and destinations with `"status": "Running"` or `"Error"`
- **Use case**: Verify the entire EventStream pipeline is healthy after configuration.

### 14. EventStream Event Routing via `_table` Field
- **Pattern**: When one Custom Endpoint feeds multiple KQL tables, add a `_table` field to each JSON event.
- **Example**: `{"_table": "SensorReading", "SensorId": "SN_001", ...}` routes to `SensorReading` table.
- **The EventStream topology must be configured with separate destinations per target table.**

### 15. EventStream Uses Event Hub Protocol
- **SDK**: `azure-eventhub` (`pip install azure-eventhub`)
- **Client**: `EventHubProducerClient.from_connection_string(conn_str)`
- **Connection string format**: `Endpoint=sb://{host}.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...;EntityPath=...`
- **Batch limit**: ~1 MB per batch. Send in sub-batches of ~100 events.

---

## CSV-to-Delta Automation

### 16. Automated Lakehouse Setup Pattern
Instead of manually running a notebook to convert CSVs to Delta tables, automate the full flow in the deployment script:

1. **Upload CSVs** to OneLake `Files/` via DFS API
2. **Generate a notebook** (`.py` format) with explicit schemas and `abfss://` paths baked in
3. **Upload** the notebook to Fabric via `POST /workspaces/{wsId}/items`
4. **Run** it via `POST .../jobs/instances?jobType=RunNotebook`
5. **Poll** the Location header until `status == "Completed"`

**Key**: Use explicit `StructType` schemas (not `inferSchema`) for reliable type casting of booleans, dates, and doubles.

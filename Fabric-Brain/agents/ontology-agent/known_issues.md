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

### 8b. TimeSeries Values Never Come Back Through the Ontology (CRITICAL)

**Symptom**: a Data Agent whose only source is the Ontology answers *"no data"* to **any question
asking for a telemetry NUMBER** (average, max, latest value), while topology questions work.

**Trace signature** — this is how you recognise it in the run steps:
```
analyze.database.execute   -> (empty)
trace.analyze_ontology     -> "All variations in attempt 1 failed, and no retryable
                              errors were found to guide regeneration."
```
The generated query shows the split: `entitySelector` (GQL half) resolves correctly,
`timeSeriesSelector` returns 0 rows.

**Cause + reusable fix**: platform behaviour of the Fabric IQ TimeSeries query path. Re-pointing the
binding (`KustoTable` ↔ `LakehouseTable`) and `RefreshGraph` do **not** help.
→ **Full write-up and the dual-source fix: [`../rti-kusto-agent/ontology.md`](../rti-kusto-agent/ontology.md)**
and [`../ai-skills-agent/datasource_configuration.md`](../ai-skills-agent/datasource_configuration.md).

**Rule for agent authors**: never state "TimeSeries bindings verified" in `aiInstructions` unless you
have actually seen values in a trace — asserting it makes the agent confidently retry a dead path.
Confirmed independently on two projects (2026-07).

### 8c. Scope of 8b — NonTimeSeries (Lakehouse) ontologies DO return numbers

**Do not over-generalise issue 8b.** It is specific to the **TimeSeries selector**, not to ontologies
as a whole. A **NonTimeSeries-only ontology bound to Lakehouse Delta tables aggregates correctly,
server-side, and exactly.**

Controlled A/B run on `Fab-Marketing-Campaign` (ontology with 8 entities / 9 relationships, **no**
TimeSeries bindings), Data Agent deployed with the **ontology as its only source**:

| Question | GQL generated | Result | Ground truth |
|---|---|---|---|
| Orders + revenue for one campaign | `MATCH (Order)-[OrderAttributedToCampaign]->(Campaign) … RETURN COUNT(...), SUM(...)` | **237 / 32 222,24 €** | 237 / 32 222,24 € ✅ exact |
| Customers reached by a campaign | `MATCH (Campaign)-[CampaignSentToCustomer]->(Customer) … RETURN <columns>` | 15 218 rows returned | 15 218 send edges ✅ |

So: `analyze.database.execute` on a Lakehouse-backed ontology returns real rows, and
`COUNT`/`SUM` pushed **into** the GQL are computed over the full graph and are correct to the cent.

### 8d. The real aggregation trap — silent 200-row truncation (CRITICAL)

**Symptom**: the agent returns a **confident, plausible, wrong** number. No error, no "no data".

**Trace signature** — the tell is in the tool *output*, not in an error:
```
analyze.database.execute -> "Note: This result is incomplete. The query matched 15218 rows,
                             but only the first 200 are included here. Any counts, sums,
                             averages, or other aggregates derived from this data are partial
                             and may be inaccurate."
```

**Cause**: the NL2GQL step emitted a **`GROUP BY` per-entity projection** instead of a single scalar
aggregate. The engine returns one row per entity, the transport truncates at **200 rows**, and the LLM
then counts/sums the rows it can see — client-side — and reports that as the answer.

Observed on `Fab-Marketing-Campaign`, ontology-only:

```
GQL: MATCH (Order)-[OrderPlacedByCustomer]->(Customer)
     WHERE LOWER(Customer.lifecycle_stage) = LOWER('at_risk')
     RETURN Customer.customer_id, SUM(Order.total_amount_eur) GROUP BY customer_id
```
| | Agent answered | Ground truth | Error |
|---|---|---|---|
| Customers at risk | **200** | 716 | −72 % |
| Revenue at risk | **67 045 €** | 234 723 € | −71 % |

The same agent answered the *scalar* aggregate question (8c, no `GROUP BY`) perfectly. **The failure
is the shape of the generated query, not the ontology.**

Second, related LLM-side error in the same run: 15 218 **edges** (sends) were reported as
"plus de 15 000 **clients**" — actual distinct customers = 3 971. Edge count ≠ node count.

**Mitigation attempts — what does NOT work (tested, 2026-07)**

We tried to fix this from the ontology side and **failed**. Both attempts were deployed and re-probed:

| Attempt | Outcome |
|---|---|
| Add 5 scalar-aggregate few-shots (`RETURN COUNT(DISTINCT ...), SUM(...)`, no `GROUP BY`) | Trace shows `Loaded 17 fewshots` (up from 12 — they *were* uploaded) but **`analyze.database.fewshots.matching -> (empty)`**. Generated GQL still contained `GROUP BY`. Answer still 200. |
| Add explicit `aiInstructions` / datasource instructions forbidding client-side counting | The **answering** LLM obeyed enough to append a caveat (*"la liste affichée est limitée à 200 résultats"*) but still **reported 200 as the answer**. The `nl2code` step still emitted `GROUP BY`. |

**Why**: `analyze.database.nl2code` is a separate generation step that does **not** appear to consume
your `aiInstructions`, and `analyze.database.fewshots.matching` returned `(empty)` on **every single
trace we captured** — for ontology *and* semantic-model sources alike. Few-shots are loaded but not
retrieved, so they exert no influence on the generated query.

> Do not budget effort on prompt-engineering the ontology out of this. It is not steerable from
> the item definition today.

**The mitigation that works: route every number to the semantic model.**

A DAX measure is a **named scalar** — `EVALUATE ROW("x", [Customers at Risk])` returns exactly one
row, so it is *structurally* immune to the 200-row cap regardless of what the NL2code step does.
That is the actual reason dual-source is the standard pattern, and it is a stronger reason than the
TimeSeries issue in 8b:

- 8b (TimeSeries) → ontology returns **nothing**. Loud, obvious, safe.
- 8d (truncation) → ontology returns a **wrong number confidently**. Silent, and it will survive a demo
  rehearsal unnoticed.

**Split to apply**: graph answers *who/how connected*; semantic model answers *how many/how much*.
Never let a single question need both from the same source.

**Verified dual-source contrast**, same agent, same question, only the source set changed:

| Mode | Route taken | Answer |
|---|---|---|
| ontology-only | `trace.analyze_ontology` → GQL + `GROUP BY` | 200 / 67 045 € ❌ |
| dual-source | `trace.analyze_semantic_model` → `EVALUATE ROW("...", [Customers at Risk], "...", [Revenue at Risk])` | **981 / 285 277 €** ✅ matches validated DAX |

> Note the two figures answer slightly different definitions (`lifecycle_stage = 'at_risk'` = 716 vs
> `churn_risk_score >= 65` = 981). Whichever definition you standardise on, **the KPI belongs in one
> named measure**, so both routes cannot disagree.

**Design rule confirmed**: keep the scored/derived table (e.g. `crm_customer_profile` — churn score,
CLV, engagement) **out** of the ontology and **in** the semantic model. The graph answers *"who is
connected to what"*; the model answers *"how many / how much"*. Tested 2026-07.

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

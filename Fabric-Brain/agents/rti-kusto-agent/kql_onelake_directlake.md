# KQL Telemetry → OneLake → Direct Lake (no gold notebook)

**Goal**: make live Eventhouse/KQL telemetry readable by a **Direct Lake semantic model**
(and the Lakehouse SQL endpoint) **without** copying it through a gold notebook or the
Kusto-Spark connector. This is the reusable path that lets one Direct Lake model sit over
**both** the batch topology Delta tables **and** the streaming telemetry.

> Proven on the RTI Operations / Digital Twin pattern (Publicis LEC, Network Operations).
> See the blueprint in `../../../Meta-Brain/TEMPLATES.md` (Template 8).

---

## Why

A Direct Lake model reads Delta/Parquet in OneLake. KQL tables are **not** Delta by default,
so a Direct Lake model cannot see them. Two common ways to bridge this are heavy:

- **Gold notebook** — Spark reads KQL → writes Delta. Extra item, extra compute, extra latency.
- **Kusto-Spark connector** — same downsides.

The lightweight, fully-scriptable path is the **Kusto mirroring policy** (OneLake availability)
+ a **OneLake shortcut** in the Lakehouse. No notebook, no extra compute.

---

## The two steps (both scriptable)

### Step 1 — Enable OneLake availability via the mirroring policy

Per telemetry table, run a Kusto **management** command (same `/v1/rest/mgmt` endpoint as `.ingest`):

```kusto
.alter-merge table telemetry_kpi policy mirroring
   dataformat=parquet
   with (IsEnabled=true, TargetLatencyInMinutes=5)
```

- This mirrors the KQL table to **Delta/Parquet in OneLake**, **read-only**.
- Default write latency can be up to ~3h — set `TargetLatencyInMinutes=5` for demos.
- Verify: `.show table telemetry_kpi mirroring operations` — `Latency 00:00:00` = fully mirrored.
- Official basis: MS Learn "one logical copy" (KQL → OneLake).

The mirrored Delta lives under the **KQL Database** item's OneLake path:

```
abfss://<workspaceId>@onelake.dfs.fabric.microsoft.com/<kqlDatabaseId>/Tables/<tableName>
```

### Step 2 — Create a OneLake shortcut in the Lakehouse

Point a Lakehouse `Tables/` shortcut at the KQL DB's mirrored Delta so Direct Lake / the SQL
endpoint can read it:

```http
POST /v1/workspaces/{workspaceId}/items/{lakehouseId}/shortcuts
{
  "path": "Tables",
  "name": "telemetry_kpi",
  "target": { "oneLake": {
      "workspaceId": "<workspaceId>",
      "itemId":      "<kqlDatabaseId>",     // the KQL DB id, not the Eventhouse id
      "path":        "Tables/telemetry_kpi"
  }}
}
```

→ `201` created (`409` = already exists — idempotent). If the KQL DB id path is rejected, fall
back to the **Eventhouse** item id with the same `Tables/<table>` path.

After both steps, the Direct Lake semantic model can be built over the topology Delta tables
**and** the telemetry shortcut tables in the same Lakehouse.

---

## Critical gotchas (these cost hours if unknown)

1. **Mirroring does NOT backfill pre-existing extents promptly.** Right after you enable the
   policy the Delta folder only has `_delta_log/00...0.json` (schema, ~1 KB) and **no parquet**
   → Direct Lake `COUNTROWS` returns blank/null.
   **Fix that works**: **re-ingest the telemetry AFTER the policy is enabled.** New extents ARE
   mirrored within ~minutes (parquet files appear + `_delta_log` commits 1,2,3…). So the deploy
   order is: enable mirroring → create shortcut → **(re-)load telemetry** → refresh model.

2. **Refresh the Lakehouse SQL endpoint metadata after adding shortcuts**, or Direct Lake /
   SQL queries fail with *"Invalid object name"*. Force a `refreshMetadata` before building the
   model.

3. **`.clear table data` is ASYNC.** Running the preload twice without waiting for the clear to
   settle **duplicates** data (e.g. a KPI table hitting 4× its row count). Harmless for
   AVG/MAX/MIN measures (duplicate-safe) but wrong for SUM/COUNT. To fully clean:
   `.clear table T data` → poll `T | count` until 0 → ingest once.

4. **Latency.** Don't refresh the semantic model immediately — wait until the shortcut tables
   show rows (`~5 min` with `TargetLatencyInMinutes=5`). The mirrored OneLake table is
   **read-only**.

---

## Deploy order (where this sits)

```
lakehouse (topology Delta) → eventhouse + KQL tables → preload telemetry
   → enable mirroring policy (per telemetry table)
   → OneLake shortcut in Lakehouse (Tables/<table>)
   → RE-load telemetry (so extents mirror)  ← the non-obvious step
   → refresh Lakehouse SQL endpoint metadata
   → Direct Lake semantic model over topology Delta + telemetry shortcuts
```

## When to use vs. skip

| Situation | Use this pattern? |
|-----------|-------------------|
| Direct Lake semantic model / Power BI needs live telemetry numbers | ✅ Yes |
| Only KQL Dashboard consumes telemetry (native KQL) | ❌ Skip — query the KQL DB directly |
| Data Agent answers telemetry numbers via DAX | ✅ Yes (the model reads the shortcuts) |
| Ontology TimeSeries binding must return values in Fabric IQ | ⚠️ Independent limitation — see `ontology.md` (IQ TimeSeries selector may return empty; route telemetry numbers through the semantic model instead) |

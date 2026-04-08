# Task Flow Templates — Reusable JSON Patterns

## How to Use Templates

1. Copy the JSON below into a `.json` file
2. Open target workspace in Fabric portal → List view
3. In the task flow area, click **Import a task flow**
4. Select the `.json` file
5. After import, **assign items to tasks** (clip icon on each task)

### Schema Reference
- `type` — lowercase task type (see instructions.md for valid values)
- `id` — GUID format required
- `edges` with `source`/`target` — reference task GUIDs
- `name`/`description` — at root level, after tasks and edges
- No `position` — portal auto-layouts
- ASCII only — no Unicode chars

---

## Template 1: Lakehouse ETL (Basic)

Standard batch analytics: ingest, store, transform, model, report.

```json
{"tasks":[{"type":"get data","id":"10000000-0000-4000-a000-000000000001","name":"Ingest Data","description":"Load source data into OneLake Files"},{"type":"store data","id":"10000000-0000-4000-a000-000000000002","name":"Store in Lakehouse","description":"Lakehouse with organized file hierarchy and Delta tables"},{"type":"prepare data","id":"10000000-0000-4000-a000-000000000003","name":"Transform and Clean","description":"PySpark notebook for CSV to Delta conversion"},{"type":"analyze and train","id":"10000000-0000-4000-a000-000000000004","name":"Semantic Model","description":"Direct Lake model with DAX measures and star schema"},{"type":"visualize","id":"10000000-0000-4000-a000-000000000005","name":"Report and Dashboard","description":"Power BI report for analysts and decision makers"}],"edges":[{"source":"10000000-0000-4000-a000-000000000001","target":"10000000-0000-4000-a000-000000000002"},{"source":"10000000-0000-4000-a000-000000000002","target":"10000000-0000-4000-a000-000000000003"},{"source":"10000000-0000-4000-a000-000000000003","target":"10000000-0000-4000-a000-000000000004"},{"source":"10000000-0000-4000-a000-000000000004","target":"10000000-0000-4000-a000-000000000005"}],"name":"Lakehouse ETL","description":"Batch data analytics with Lakehouse, notebook transformation, and Power BI reporting."}
```

---

## Template 2: Real-Time Intelligence (RTI)

Streaming IoT/telemetry: EventStream, Eventhouse, KQL Dashboard + Power BI.

```json
{"tasks":[{"type":"get data","id":"20000000-0000-4000-a000-000000000001","name":"Stream Ingestion","description":"EventStream with Custom App source and Event Hub SDK"},{"type":"store data","id":"20000000-0000-4000-a000-000000000002","name":"Store Reference Data","description":"Lakehouse with dimension tables in Delta format"},{"type":"store data","id":"20000000-0000-4000-a000-000000000003","name":"Store Streaming Data","description":"Eventhouse KQL Database with streaming ingestion"},{"type":"analyze and train","id":"20000000-0000-4000-a000-000000000004","name":"Semantic Model","description":"Direct Lake model joining Lakehouse dims and Eventhouse facts"},{"type":"track data","id":"20000000-0000-4000-a000-000000000005","name":"KQL Dashboard","description":"Real-time KQL dashboard with auto-refresh"},{"type":"visualize","id":"20000000-0000-4000-a000-000000000006","name":"Power BI Report","description":"Multi-page analytical report over the semantic model"}],"edges":[{"source":"20000000-0000-4000-a000-000000000001","target":"20000000-0000-4000-a000-000000000003"},{"source":"20000000-0000-4000-a000-000000000002","target":"20000000-0000-4000-a000-000000000004"},{"source":"20000000-0000-4000-a000-000000000003","target":"20000000-0000-4000-a000-000000000004"},{"source":"20000000-0000-4000-a000-000000000004","target":"20000000-0000-4000-a000-000000000005"},{"source":"20000000-0000-4000-a000-000000000004","target":"20000000-0000-4000-a000-000000000006"}],"name":"Real-Time Intelligence","description":"Streaming data pipeline with EventStream, Eventhouse, and real-time dashboards."}
```

---

## Template 3: AI-Augmented Analytics

Full platform with pipeline orchestration and Data Agent.

```json
{"tasks":[{"type":"get data","id":"30000000-0000-4000-a000-000000000001","name":"Ingest Reference Data","description":"Upload CSV files to OneLake via DFS API or portal"},{"type":"store data","id":"30000000-0000-4000-a000-000000000002","name":"Store in Lakehouse","description":"Organized file hierarchy for dimensions and facts"},{"type":"prepare data","id":"30000000-0000-4000-a000-000000000003","name":"Transform to Delta","description":"PySpark notebook converts CSVs to typed Delta tables"},{"type":"prepare data","id":"30000000-0000-4000-a000-000000000004","name":"Orchestrate Pipeline","description":"Data Pipeline running the transformation notebook on schedule"},{"type":"analyze and train","id":"30000000-0000-4000-a000-000000000005","name":"Semantic Model","description":"Direct Lake semantic model with star schema and DAX measures"},{"type":"visualize","id":"30000000-0000-4000-a000-000000000006","name":"Power BI Report","description":"Multi-page report for analysts and managers"},{"type":"analyze and train","id":"30000000-0000-4000-a000-000000000007","name":"AI Data Agent","description":"Natural language QA over the semantic model"}],"edges":[{"source":"30000000-0000-4000-a000-000000000001","target":"30000000-0000-4000-a000-000000000002"},{"source":"30000000-0000-4000-a000-000000000002","target":"30000000-0000-4000-a000-000000000003"},{"source":"30000000-0000-4000-a000-000000000003","target":"30000000-0000-4000-a000-000000000004"},{"source":"30000000-0000-4000-a000-000000000003","target":"30000000-0000-4000-a000-000000000005"},{"source":"30000000-0000-4000-a000-000000000005","target":"30000000-0000-4000-a000-000000000006"},{"source":"30000000-0000-4000-a000-000000000005","target":"30000000-0000-4000-a000-000000000007"}],"name":"AI-Augmented Analytics Platform","description":"End-to-end analytics with pipeline orchestration, semantic model, reporting, and AI-powered QA."}
```

---

## Template 4: Medallion Architecture

Bronze, Silver, Gold layered data model.

```json
{"tasks":[{"type":"get data","id":"40000000-0000-4000-a000-000000000001","name":"Ingest Sources","description":"Raw data ingestion from multiple sources"},{"type":"store data","id":"40000000-0000-4000-a000-000000000002","name":"Bronze Layer","description":"Raw data as-is in Lakehouse, append-only"},{"type":"prepare data","id":"40000000-0000-4000-a000-000000000003","name":"Silver Layer","description":"Cleaned, validated, deduplicated data via notebook transforms"},{"type":"analyze and train","id":"40000000-0000-4000-a000-000000000004","name":"Gold Layer","description":"Business-ready aggregations and star schema semantic model"},{"type":"visualize","id":"40000000-0000-4000-a000-000000000005","name":"Serve and Visualize","description":"Reports, dashboards, and AI agents for consumption"}],"edges":[{"source":"40000000-0000-4000-a000-000000000001","target":"40000000-0000-4000-a000-000000000002"},{"source":"40000000-0000-4000-a000-000000000002","target":"40000000-0000-4000-a000-000000000003"},{"source":"40000000-0000-4000-a000-000000000003","target":"40000000-0000-4000-a000-000000000004"},{"source":"40000000-0000-4000-a000-000000000004","target":"40000000-0000-4000-a000-000000000005"}],"name":"Medallion Architecture","description":"Bronze-Silver-Gold data lakehouse pattern with progressive refinement."}
```

# Cross-Agent Workflows — End-to-End Project Sequences

This file defines orchestrated workflows that coordinate multiple agents to build complete Fabric projects.
Each workflow specifies the exact agent sequence, inputs/outputs between agents, decision points, and validation gates.

---

## Workflow 1: Standard BI Demo (Lakehouse → Semantic Model → Report)

**Use case**: Build a working BI demo with interactive visuals from scratch.
**Agents involved**: workspace-admin → domain-modeler → lakehouse → semantic-model → report-builder
**Estimated effort**: 2–3 hours

### Phase 1: Foundation (workspace-admin-agent)

**Input**: Project name, capacity ID
**Output**: Workspace ID, capacity assigned

1. Create workspace with naming convention: `{ProjectName}-Demo`
2. Assign capacity (verify it's running first — ARM API)
3. Record workspace ID in `resource_ids.md`

> **Gate**: `fab ls "{ProjectName}-Demo.Workspace"` returns items listing

### Phase 2: Data Model Design (domain-modeler-agent)

**Input**: Industry/scenario description
**Output**: YAML model spec, CSV sample data, table definitions

1. Select or customize an industry template from `industry_templates.md`
2. Design 3–7 dimension tables + 1–3 fact tables
3. Generate sample CSV files (100–10,000 rows)
4. Produce cross-layer output: Delta schemas, KQL schemas (if RTI), DAX measure definitions

> **Gate**: YAML model spec reviewed, CSV files generated, naming conventions verified

### Phase 3: Data Platform (lakehouse-agent)

**Input**: Workspace ID, CSV files, table definitions
**Output**: Lakehouse ID, SQL Endpoint ID, Delta tables populated

1. Create Lakehouse item via Fabric REST API
2. Wait for SQL Endpoint provisioning (poll 20×10s)
3. Upload CSVs to `Files/raw/` via OneLake DFS 3-step protocol
4. Create + run Spark notebook: CSV → Delta tables in `Tables/`
5. Verify table row counts via SQL Endpoint

> **Gate**: `SELECT COUNT(*) FROM dim_*` returns expected counts for all tables

### Phase 4: Semantic Model (semantic-model-agent)

**Input**: Lakehouse SQL Endpoint, table definitions, DAX measures from Phase 2
**Output**: Semantic Model ID, model.bim deployed

1. Build `model.bim` with Direct Lake mode
2. Define tables referencing Lakehouse SQL Endpoint
3. Create relationships (star schema from domain model)
4. Add DAX measures (from domain-modeler output)
5. Add descriptions on all tables/columns/measures (AI-readiness)
6. Set `discourageImplicitMeasures: true`
7. Deploy via `POST /items` + `updateDefinition`
8. Validate with DAX query: `EVALUATE {1}` + measure spot checks

> **Gate**: All measures return non-blank values; AI-readiness audit passes P0

### Phase 5: Report (report-builder-agent)

**Input**: Semantic Model ID, XMLA connection string, measure list
**Output**: Published report with working visuals

1. Design 2–3 page layout (Overview, Details, Trends)
2. Build `report.json` in Legacy PBIX format
3. Create visuals with `prototypeQuery` referencing exact measure names
4. Include base theme
5. Deploy via `POST /items`
6. Validate with `getDefinition` round-trip

> **Gate**: Report opens in browser, all visuals render data (no blanks)

### Decision Points

```
Q: Does the demo need real-time data?
├── YES → Add RTI workflow (Workflow 2) between Phase 3 and Phase 4
└── NO  → Continue with standard flow

Q: Does the demo need a Data Agent (AI Q&A)?
├── YES → Add Phase 6: ai-skills-agent (after report)
└── NO  → Demo is complete

Q: Multiple environments (Dev/Test/Prod)?
├── YES → Use fabric-cli-agent deploy config for promotion
└── NO  → Single workspace is sufficient
```

---

## Workflow 2: Real-Time Intelligence Dashboard

**Use case**: Build a streaming analytics dashboard with live data.
**Agents involved**: workspace-admin → domain-modeler → lakehouse → rti-kusto → rti-eventstream → ontology (optional) → report-builder
**Estimated effort**: 3–4 hours

### Phase 1: Foundation (workspace-admin-agent)

Same as Workflow 1, Phase 1.

### Phase 2: Data Model Design (domain-modeler-agent)

**Input**: IoT/streaming scenario description
**Output**: KQL table schemas, dimension table definitions, streaming data generator script

1. Design KQL streaming tables (PascalCase: `SensorReading`, `EquipmentAlert`)
2. Design Lakehouse dimension tables (dim_sensors, dim_sites, dim_zones)
3. Generate Python streaming data generator
4. Define `_table` routing field for multi-table EventStream

> **Gate**: KQL schemas + dimension CSVs + generator script reviewed

### Phase 3: Data Infrastructure (lakehouse-agent + rti-kusto-agent)

**Input**: Table schemas, dimension CSVs
**Output**: Lakehouse ID, Eventhouse ID, KQL Database ID, tables created

**Strict deployment order**:
1. Create Lakehouse → upload dimension CSVs → Spark notebook creates Delta tables
2. Create Eventhouse (auto-creates default KQL Database)
3. Create KQL tables via `.create table` commands (Kusto REST API)
4. Enable streaming ingestion: `.alter table policy streamingingestion enable`

> **Gate**: `dim_*` tables have data; KQL `.show tables` returns all streaming tables

### Phase 4: EventStream (rti-eventstream-agent)

**Input**: Eventhouse ID, KQL Database ID, Lakehouse ID
**Output**: EventStream ID, Custom Endpoint connection string

1. Create EventStream item
2. Add Custom Endpoint source
3. Add KQL Database destination (use KQL Database ID, **NOT** Eventhouse ID)
4. Configure `_table` routing for multi-table support
5. Retrieve connection string from Custom Endpoint
6. Test with 10 sample events via Python EventHub SDK

> **Gate**: Events appear in KQL table within 30 seconds of sending

### Phase 5: Ontology (ontology-agent) — Optional

**Input**: Domain model, Lakehouse tables, KQL tables
**Output**: Ontology with entity types, bindings, relationships

1. Define entity types matching domain model
2. Create NonTimeSeries bindings → Lakehouse dimension tables
3. Create TimeSeries bindings → KQL streaming tables
4. Define relationships between entities
5. Create contextualizations
6. Generate Graph Model + Graph Query Set

> **Gate**: Graph Query Set returns connected entities with `MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10`

### Phase 6: Dashboard (report-builder-agent or KQL Dashboard)

**Input**: KQL Database, Semantic Model (if used), measure definitions
**Output**: Live dashboard

**Decision**:
```
Q: Need Power BI visuals (slicers, cards, charts)?
├── YES → Build Semantic Model (Direct Lake) + Power BI Report (Workflow 1 Phase 4+5)
└── NO  → Build KQL Dashboard with real-time queries
```

> **Gate**: Dashboard shows live-updating data when generator is running

---

## Workflow 3: BO Migration Project (Multi-Wave)

**Use case**: Migrate SAP BusinessObjects reports to Microsoft Fabric.
**Agents involved**: migration-bo → domain-modeler → semantic-model → report-builder → monitoring
**Estimated effort**: 4–8 weeks per wave

### Wave Planning

```
Week 1:    Assessment (migration-bo-agent)
Weeks 2-3: Semantic Model build (semantic-model-agent)
Weeks 4-5: Report conversion (report-builder-agent)
Week 6:    Validation + UAT (monitoring-agent)
```

### Phase 1: Assessment (migration-bo-agent)

1. Inventory all BO reports (universe, queries, formulas, visuals)
2. Run readiness assessment (complexity scoring)
3. Map BO formulas → DAX using 119-formula mapping table
4. Map BO visual types → Power BI using 78-visual mapping table
5. Identify blockers (unsupported features, complex universes)
6. Produce migration report with wave assignment

### Phase 2: Semantic Model (semantic-model-agent)

1. Convert BO universe → Direct Lake semantic model
2. Map BO dimensions/measures → DAX measures
3. Recreate relationships from universe joins
4. Add AI-readiness metadata
5. Validate with sample queries matching BO report outputs

### Phase 3: Report Conversion (report-builder-agent)

1. Convert each BO report → Legacy PBIX format
2. Map BO visuals → Power BI visuals (using 78-mapping table)
3. Recreate filters, parameters, prompts
4. Build drill-through and navigation
5. Deploy and validate visual rendering

### Phase 4: Validation (monitoring-agent)

1. Side-by-side comparison: BO output vs Fabric report
2. Data reconciliation: source → Lakehouse → Semantic Model → Report
3. Performance benchmarking (page load times)
4. User acceptance testing checklist
5. Go/no-go decision

---

## Workflow 4: Data Agent (AI Q&A) Deployment

**Use case**: Deploy a Fabric Data Agent that answers natural language questions.
**Agents involved**: semantic-model (or lakehouse) → ai-skills-agent
**Prerequisite**: An existing Semantic Model with measures and descriptions

### Phase 1: Prepare Data Source

1. Verify semantic model exists with:
   - All tables/columns have `description`
   - `summarizeBy: "none"` on IDs and date-parts
   - `discourageImplicitMeasures: true` set
   - DAX measures cover common business questions
2. If not ready → run semantic-model-agent AI-readiness audit first

### Phase 2: Write Instructions (ai-skills-agent)

1. Follow 7-section instruction framework from `instruction_writing_guide.md`
2. Define persona, data context, query patterns, edge cases
3. Write 10–15 few-shot examples covering diverse question types

### Phase 3: Deploy Agent

1. Build definition parts: `stage_config.json`, `datasource.json`, `fewshots.json`
2. Deploy with BOTH draft and published stages
3. Include `publish_info.json` in parts

### Phase 4: Validate

1. Open agent in Fabric portal
2. Test with 5+ questions (easy, medium, hard, edge case, impossible)
3. Verify generated DAX/SQL is correct
4. Check hallucination handling (questions outside data scope)

> **Gate**: 4/5 test questions return correct answers; impossible question is gracefully declined

---

## Workflow 5: CI/CD Pipeline Setup

**Use case**: Automate Fabric item deployment across environments.
**Agents involved**: fabric-cli-agent → workspace-admin-agent
**Prerequisite**: Multiple workspaces (Dev, Test, Prod)

### Phase 1: Export Baseline

1. Export all items from Dev workspace: `fab export`
2. Organize exported artifacts in Git repository
3. Create `deploy-config.yml` with workspace mappings

### Phase 2: Parameterize

1. Create parameter files per environment (`params-dev.yml`, `params-prod.yml`)
2. Replace connection strings, workspace IDs, capacity IDs
3. Define publish/unpublish rules for reports and semantic models

### Phase 3: CI/CD Pipeline

1. Create GitHub Actions or Azure Pipelines YAML
2. Authenticate via Service Principal (SPN + secret or certificate)
3. Run `fab deploy --config deploy-config.yml --target_env prod`
4. Add validation step: verify deployed items exist and are functional

### Phase 4: Ongoing

1. Dev changes → Git commit → CI triggers deploy to Test
2. Manual approval → deploy to Prod
3. Monitor via monitoring-agent (job status, refresh failures)

---

## Workflow 6: Ontology & Graph Add-On

**Use case**: Add entity graph capabilities to an existing project that has Lakehouse dimension tables and (optionally) KQL streaming tables.
**Agents involved**: ontology-agent (+ domain-modeler for entity design review)
**Prerequisite**: Lakehouse with populated dimension tables. KQL Database with streaming tables (for TimeSeries bindings).
**Estimated effort**: 1–2 hours

### Phase 1: Entity Design (domain-modeler-agent + ontology-agent)

**Input**: Existing domain model, Lakehouse table list, KQL table list
**Output**: Entity type definitions mapped to existing tables

1. Review existing dimension tables → identify candidate entity types
2. Review KQL streaming tables → identify time-series properties
3. Design entity types with properties matching table columns
4. Assign deterministic GUIDs (`[guid]::new()` or `uuid5` from entity name) for idempotency

> **Gate**: Entity types list covers all key business entities; property types match column types

### Phase 2: Ontology Deployment (ontology-agent)

**Input**: Entity type definitions, Lakehouse ID, KQL Database ID
**Output**: Ontology item created with entity types, bindings, relationships

**Strict order** (violations cause silent failures):
1. Create ontology item (`POST /ontologies`)
2. Create entity types with properties
3. Create **NonTimeSeries bindings** → Lakehouse dimension tables
4. Create **TimeSeries bindings** → KQL streaming tables (if RTI)
5. Define relationships between entity types (parent-child, assignment, action)
6. Create contextualizations for each relationship

> **Gate**: `GET /ontologies/{id}/entityTypes` returns all expected types with bindings

### Phase 3: Graph Model & Queries (ontology-agent)

**Input**: Ontology with bindings and relationships
**Output**: Graph Model, Graph Query Set with sample queries

1. Create Graph Model referencing the ontology
2. Create Graph Query Set
3. Write GQL queries:
   - `MATCH (n) RETURN labels(n), count(*)` — verify all entity types populated
   - `MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10` — verify relationships
   - Domain-specific traversals (e.g., "all sensors in zone X")

> **Gate**: Graph Query Set returns connected entities; relationship counts > 0

### Phase 4: Integration (optional)

**Decision**:
```
Q: Need an Operations Agent (AI over graph)?
├── YES → Create Data Agent with ontology as source (portal step)
└── NO  → Done — graph queries available via Graph Query Set UI

Q: Need ontology data in Power BI reports?
├── YES → Use cross-database query from Warehouse/Lakehouse to join graph results
└── NO  → Graph stays in KQL/Ontology layer
```

### Decision Tree: What Bindings Do I Need?

```
Do I have Lakehouse dimension tables?
  ├── YES → Create NonTimeSeries bindings (batch/static properties)
  └── NO  → Create Lakehouse dims first (see Workflow 1, Phase 3)

Do I have KQL streaming tables?
  ├── YES → Create TimeSeries bindings (real-time sensor values)
  └── NO  → NonTimeSeries only — ontology works without RTI

Both?
  └── YES → Dual binding pattern: same entity has NonTimeSeries (name, location)
           + TimeSeries (temperature, pressure) properties
```

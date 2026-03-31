# Project Templates — Quick Start Checklists

Each template provides a step-by-step checklist with agent assignments, decision points, and success criteria.
Use these templates to bootstrap new Fabric projects quickly.

---

## Template 1: Standard BI Demo (2–3 Hours)

**Scenario**: Interactive dashboard with slicers, cards, and charts over structured data.
**Output**: Workspace + Lakehouse + Semantic Model + 3-page Report

### Prerequisites Checklist

- [ ] Azure CLI authenticated: `az login`
- [ ] Fabric capacity running (F2+ for demo, F16+ for production)
- [ ] Python 3.12 with `requests`, `pyyaml`, `faker` installed
- [ ] Capacity ID and Subscription ID recorded in `resource_ids.md`

### Step-by-Step

| # | Agent | Task | Time | Validation |
|---|-------|------|------|------------|
| 1 | workspace-admin | Create workspace + assign capacity | 5 min | `fab ls` shows workspace |
| 2 | domain-modeler | Design data model (3–5 dims, 1–2 facts) | 20 min | YAML spec reviewed |
| 3 | domain-modeler | Generate sample CSV files | 10 min | CSV files in `data/raw/` |
| 4 | lakehouse | Create Lakehouse + wait for SQL EP | 5 min | SQL Endpoint available |
| 5 | lakehouse | Upload CSVs to `Files/raw/` | 5 min | Files visible in OneLake |
| 6 | lakehouse | Create + run Spark notebook (CSV → Delta) | 15 min | `Tables/` has all dim/fact tables |
| 7 | semantic-model | Build model.bim (Direct Lake) | 20 min | model.bim JSON validated |
| 8 | semantic-model | Deploy + validate DAX measures | 10 min | `EVALUATE {1}` returns results |
| 9 | report-builder | Design 3-page layout | 15 min | report.json structure ready |
| 10 | report-builder | Deploy + verify visuals render | 15 min | All visuals show data |

### Decision Points

```
After Step 2:
  Q: Need real-time data too?
  ├── YES → Insert RTI steps (see Template 2) after Step 6
  └── NO  → Continue

After Step 10:
  Q: Need AI Q&A agent?
  ├── YES → Continue with Template 4
  └── NO  → Done!
```

### Success Criteria

- [ ] Report loads in browser in < 5 seconds
- [ ] At least 3 different visual types render correctly (card, chart, table)
- [ ] Slicers filter all visuals on the page
- [ ] All DAX measures return non-blank values

---

## Template 2: Real-Time IoT Dashboard (3–4 Hours)

**Scenario**: Streaming sensor data with live-updating KQL dashboard or Power BI report.
**Output**: Workspace + Lakehouse (dims) + Eventhouse (streaming) + EventStream + Dashboard

### Prerequisites Checklist

- [ ] All prerequisites from Template 1
- [ ] `azure-eventhub` Python package installed: `pip install azure-eventhub`
- [ ] Industry scenario chosen (Manufacturing, Energy, or custom)

### Step-by-Step

| # | Agent | Task | Time | Validation |
|---|-------|------|------|------------|
| 1 | workspace-admin | Create workspace + assign capacity | 5 min | Workspace listed |
| 2 | domain-modeler | Design streaming + dimension model | 25 min | KQL schemas + dim CSVs |
| 3 | domain-modeler | Generate Python data generator | 15 min | Generator script runs |
| 4 | lakehouse | Create Lakehouse + load dims | 20 min | dim tables populated |
| 5 | rti-kusto | Create Eventhouse + KQL DB | 5 min | KQL DB listed |
| 6 | rti-kusto | Create KQL tables + enable streaming | 10 min | `.show tables` returns all |
| 7 | rti-eventstream | Create EventStream + Custom Endpoint | 10 min | EventStream topology ready |
| 8 | rti-eventstream | Connect KQL DB destination | 10 min | Destination linked |
| 9 | rti-eventstream | Test with 10 sample events | 5 min | Events in KQL table |
| 10 | rti-eventstream | Run generator (100 events) | 5 min | KQL count matches |
| 11 | report-builder | Build dashboard (KQL or PBI) | 30 min | Visuals show live data |

### Decision Points

```
After Step 6:
  Q: Need Ontology + Graph?
  ├── YES → Insert ontology-agent steps (entity types, bindings, Graph Query Set)
  └── NO  → Continue to EventStream

After Step 10:
  Q: Dashboard type?
  ├── KQL Dashboard → Use rti-kusto-agent for KQL dashboard tiles
  └── Power BI Report → Build Semantic Model (Direct Lake) + Legacy PBIX report
```

### Success Criteria

- [ ] Events appear in KQL table within 30 seconds of sending
- [ ] Dashboard updates when generator is running
- [ ] At least 1 time-series chart shows streaming pattern
- [ ] Dimension lookups work (e.g., sensor name from dim table)

---

## Template 3: Complete Smart Factory Demo (4–6 Hours)

**Scenario**: Full Fabric showcase: batch + streaming + AI + reporting for manufacturing.
**Output**: Everything from Templates 1+2 plus Ontology, Graph, Data Agent

### Step-by-Step

| # | Agent | Task | Time |
|---|-------|------|------|
| 1–3 | workspace-admin + domain-modeler | Foundation + Manufacturing model | 30 min |
| 4–6 | lakehouse | Lakehouse + dims + Delta tables | 25 min |
| 7–9 | rti-kusto | Eventhouse + KQL tables + streaming | 20 min |
| 10–12 | rti-eventstream | EventStream + routing + testing | 25 min |
| 13–15 | ontology | Entity types + bindings + Graph | 30 min |
| 16–18 | semantic-model | Direct Lake model + DAX measures | 25 min |
| 19–21 | report-builder | 3-page report + RTI visuals | 30 min |
| 22–24 | ai-skills | Data Agent + instructions + few-shots | 30 min |
| 25 | monitoring | Health check dashboard | 15 min |

### Success Criteria

- [ ] All Template 1 + Template 2 criteria pass
- [ ] Graph Query Set returns entity relationships
- [ ] Data Agent answers 4/5 test questions correctly
- [ ] End-to-end data flow: Generator → EventStream → KQL → Report shows data

---

## Template 4: Data Agent (AI Q&A) Add-On (45 min)

**Prerequisite**: Existing Semantic Model with descriptions and measures (from Template 1 or 3)

| # | Agent | Task | Time | Validation |
|---|-------|------|------|------------|
| 1 | semantic-model | Run AI-readiness audit | 10 min | P0 issues = 0 |
| 2 | ai-skills | Write instructions (7-section framework) | 15 min | Instruction JSON ready |
| 3 | ai-skills | Write 10–15 few-shot examples | 10 min | Diverse Q&A patterns |
| 4 | ai-skills | Deploy agent (draft + published) | 5 min | Agent visible in portal |
| 5 | ai-skills | Test with 5 questions | 5 min | 4/5 correct answers |

---

## Template 5: BO Migration Wave (4–6 Weeks)

**Prerequisite**: SAP BO system access, report inventory, Fabric workspace

### Week-by-Week Plan

| Week | Agent(s) | Deliverable | Gate |
|------|----------|-------------|------|
| 1 | migration-bo | Assessment report + readiness score | Complexity scored, waves assigned |
| 2 | domain-modeler + semantic-model | Target data model + model.bim | Model deployed, measures validated |
| 3 | semantic-model | Formula migration (BO → DAX) | All Critical formulas converted |
| 4 | report-builder | Report conversion (visuals, layout) | Reports render, no blank visuals |
| 5 | report-builder + monitoring | UAT + data reconciliation | Numbers match BO ±1% |
| 6 | workspace-admin + fabric-cli | Go-live + CI/CD setup | Production workspace active |

### Per-Report Checklist

- [ ] BO report analyzed (formulas, visuals, parameters)
- [ ] All formulas mapped to DAX (using 119-formula mapping)
- [ ] All visuals mapped to PBI (using 78-visual mapping)
- [ ] Report built in Legacy PBIX format
- [ ] Data reconciliation passes (±1% tolerance)
- [ ] Page load time < 5 seconds
- [ ] Stakeholder sign-off

---

## Template 6: CI/CD Pipeline Setup (1–2 Hours)

**Prerequisite**: Git repository, Service Principal, Dev + Prod workspaces

| # | Agent | Task | Time | Validation |
|---|-------|------|------|------------|
| 1 | workspace-admin | Create Dev + Prod workspaces | 10 min | Both workspaces exist |
| 2 | fabric-cli | Export Dev items to Git | 15 min | Artifacts in repo |
| 3 | fabric-cli | Create deploy-config.yml | 15 min | Config validated |
| 4 | fabric-cli | Create parameter files per env | 10 min | Params for dev + prod |
| 5 | fabric-cli | Create CI/CD pipeline YAML | 15 min | Pipeline file committed |
| 6 | fabric-cli | Test deploy to Prod | 10 min | Items exist in Prod |

---

## Template 7: Ontology & Graph Add-On (1–2 Hours)

**Prerequisite**: Existing Lakehouse with dimension tables populated. KQL Database with streaming tables (optional, for TimeSeries bindings).
**Output**: Ontology + Graph Model + Graph Query Set with working graph traversals

### Prerequisites Checklist

- [ ] Lakehouse exists with populated dimension tables (`dim_*`)
- [ ] (Optional) KQL Database exists with streaming tables for TimeSeries
- [ ] Domain model reviewed — entity types identified from existing tables
- [ ] Ontology-agent `instructions.md` loaded

### Step-by-Step

| # | Agent | Task | Time | Validation |
|---|-------|------|------|------------|
| 1 | domain-modeler | Map dimension tables → entity types | 15 min | Entity list reviewed |
| 2 | ontology | Create ontology item | 5 min | Ontology ID returned |
| 3 | ontology | Create entity types + properties | 15 min | All entity types exist |
| 4 | ontology | Create NonTimeSeries bindings → Lakehouse | 10 min | Bindings resolve |
| 5 | ontology | Create TimeSeries bindings → KQL (if RTI) | 10 min | Bindings resolve |
| 6 | ontology | Define relationships + contextualizations | 10 min | Relationships created |
| 7 | ontology | Create Graph Model + Graph Query Set | 10 min | Graph model listed |
| 8 | ontology | Test GQL queries | 5 min | Entities + relationships returned |

### Decision Points

```
After Step 6:
  Q: Need an Operations Agent (AI over graph)?
  ├── YES → Create Data Agent with ontology source (portal step)
  └── NO  → Done — graph queries available via Graph Query Set

Before Step 5:
  Q: Do I have KQL streaming tables?
  ├── YES → Create TimeSeries bindings (Step 5)
  └── NO  → Skip Step 5 — NonTimeSeries only
```

### Success Criteria

- [ ] `MATCH (n) RETURN labels(n), count(*)` returns all entity types with row counts
- [ ] `MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10` returns connected entities
- [ ] At least 2 relationship types traversable
- [ ] Domain-specific query works (e.g., "all sensors in zone X" or "equipment in site Y")

---

## Industry-Specific Starter Kits

These combine Template 1 or 2 with pre-built domain models from `domain-modeler-agent/industry_templates.md`.

| Industry | Template Base | Dimension Tables | Fact Tables | Streaming Tables | Recommended Extras |
|----------|-------------|-----------------|-------------|-----------------|-------------------|
| **Manufacturing** | Template 3 | dim_sites, dim_zones, dim_equipment, dim_sensors | fact_production, fact_quality | SensorReading, EquipmentAlert | Ontology + Data Agent |
| **Retail** | Template 1 | dim_customers, dim_products, dim_stores, dim_dates | fact_sales, fact_inventory | n/a | Data Agent |
| **Energy** | Template 2 | dim_assets, dim_locations, dim_meters | fact_consumption, fact_generation | MeterReading, GridEvent | Ontology |
| **Healthcare** | Template 1 | dim_patients, dim_providers, dim_facilities | fact_encounters, fact_claims | n/a | RLS + Data Agent |
| **Finance** | Template 1 | dim_accounts, dim_cost_centers, dim_periods | fact_general_ledger, fact_budget | n/a | Data Agent (exists) |
| **Supply Chain** | Template 2 | dim_suppliers, dim_products, dim_warehouses | fact_orders, fact_shipments | ShipmentTracking | Ontology |

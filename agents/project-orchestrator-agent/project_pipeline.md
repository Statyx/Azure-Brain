# Project Pipeline — 12-Step End-to-End Build

## Pipeline Overview

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Step 1   │──▶│ Step 2   │──▶│ Step 3   │──▶│ Step 4   │
│ Domain   │   │ Sample   │   │ Workspace│   │ Lakehouse│
│ Model    │   │ Data     │   │ Setup    │   │ Medallion│
│ domain-  │   │ domain-  │   │ workspace│   │ lakehouse│
│ modeler  │   │ modeler  │   │ -admin   │   │ -agent   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                  │
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌───▼──────┐
│ Step 8   │◀──│ Step 7   │◀──│ Step 6   │◀──│ Step 5   │
│ Reports  │   │ Semantic │   │ Dataflows│   │ ETL &    │
│ report-  │   │ Model    │   │ dataflow │   │ Upload   │
│ builder  │   │ semantic │   │ -agent   │   │ lakehouse│
│          │   │ -model   │   │          │   │+orchestr │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
     │
┌────▼─────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Step 9   │──▶│ Step 10  │──▶│ Step 11  │──▶│ Step 12  │
│ Data     │   │ Real-Time│   │ Pipeline │   │ Validate │
│ Agent    │   │ Intel    │   │ Orchestr │   │ & Deploy │
│ ai-skills│   │ rti-*    │   │ orchestr │   │ fabric-  │
│          │   │          │   │ -agent   │   │ cli+test │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

---

## Step 1: Requirements & Domain Model

**Agent**: `domain-modeler-agent`  
**Input**: Industry description, business domains, KPI requirements  
**Output**: Star schema design, dimension/fact tables, KQL schemas, DAX measure specs  
**Config produced**: `industry.json`, `sample-data.json`, `semantic-model.json`

**What happens**:
- Design dimensional model (star schema) with dimensions and fact tables
- Define DAX measures with business logic
- Define KQL table schemas for real-time scenarios (if applicable)
- Specify data relationships and cardinalities
- Produce JSON config files that drive all subsequent steps

**Depends on**: Nothing (first step)

---

## Step 2: Sample Data Generation

**Agent**: `domain-modeler-agent`  
**Input**: `sample-data.json` (table schemas, row counts, relationships)  
**Output**: CSV files in `SampleData/` directory  

**What happens**:
- Generate realistic sample data matching the domain model
- Ensure referential integrity (FK → PK consistency)
- Respect business rules (dates, ranges, distributions)
- Produce one CSV per table

**Depends on**: Step 1 (domain model)

---

## Step 3: Workspace Setup

**Agent**: `workspace-admin-agent`  
**Input**: `industry.json` (workspace name, capacity)  
**Output**: Fabric workspace with correct capacity and RBAC  

**What happens**:
- Create workspace (or verify existing)
- Assign to Fabric capacity (F64+ for Data Agent)
- Configure Git integration if needed
- Set RBAC permissions

**Depends on**: Step 1 (project config)

---

## Step 4: Lakehouse Creation (Medallion)

**Agent**: `lakehouse-agent`  
**Input**: `industry.json` (lakehouse names, schema config)  
**Output**: 3 Lakehouses (Bronze, Silver, Gold) with schema-enabled tables  

**What happens**:
- Create Bronze Lakehouse (raw landing zone)
- Create Silver Lakehouse (cleaned, conformed)  
- Create Gold Lakehouse (star schema, analytics-ready)
- Enable schemas on Silver and Gold

**Naming**: `BronzeLH`, `SilverLH`, `GoldLH` (or custom per config)

**Depends on**: Step 3 (workspace exists)

---

## Step 5: Data Upload & ETL Notebooks

**Agent**: `lakehouse-agent` + `orchestrator-agent`  
**Input**: CSV files from Step 2, `industry.json` for transformations  
**Output**: Data loaded into Bronze, Spark notebooks for Bronze→Silver→Gold  

**What happens**:
- Upload CSVs to `Bronze/Files/` via OneLake DFS API (3-step: PUT→PATCH→PATCH)
- Create ETL notebooks:
  - **NB01**: Bronze → Silver (cleansing, type casting, deduplication)
  - **NB02**: Web Enrichment (optional — API data augmentation)
  - **NB03**: Silver → Gold (star schema transformation, aggregations)
- Create diagnostic notebook (NB06) for data quality checks

**Naming**: `NB01_BronzeToSilver`, `NB02_WebEnrichment`, `NB03_SilverToGold`, `NB06_DiagnosticCheck`

**Depends on**: Step 2 (CSVs) + Step 4 (Lakehouses)

---

## Step 6: Dataflows Gen2

**Agent**: `dataflow-agent`  
**Input**: `sample-data.json` (source schemas), `industry.json` (domains)  
**Output**: Dataflow Gen2 definitions for domain-specific ingestion  

**What happens**:
- Create Dataflow Gen2 for each business domain
- Map CSV source columns to Delta table columns
- Apply Power Query M transformations (type conversions, lookups)
- Configure refresh schedule

**Naming**: `DF_<Domain>` (e.g., `DF_Generation`, `DF_Billing`, `DF_HR`)

**Depends on**: Step 4 (Lakehouses exist as destinations)

> **Note**: Step 6 is optional — projects can use only notebooks (Step 5) for ETL.

---

## Step 7: Semantic Model (TMDL + DAX)

**Agent**: `semantic-model-agent`  
**Input**: `semantic-model.json` (tables, measures, relationships)  
**Output**: Semantic model definition (TMDL or model.bim), deployed to workspace  

**What happens**:
- Generate table definitions from Gold Lakehouse schema
- Create DAX measures (KPIs, time intelligence, ratios)
- Define relationships (1:M, cross-filter direction)
- Auto-generate Date dimension with fiscal year support
- Set Direct Lake mode pointing to Gold Lakehouse
- Add `///` TMDL descriptions for NL2DAX accuracy

**Naming**: `SM_<CompanyName>` or `<CompanyName>Model`

**Depends on**: Step 4 (Gold Lakehouse tables exist)

---

## Step 8: Power BI Reports

**Agent**: `report-builder-agent`  
**Input**: `reports.json` (pages, visuals, KPIs), semantic model reference  
**Output**: Power BI report(s) deployed to workspace  

**What happens**:
- Generate report using **Legacy PBIX format** (NEVER PBIR)
- Create pages with KPI cards, charts, tables, maps
- Apply industry-specific theme (colors, fonts)
- Configure filter panes and bookmarks
- Typical structure: Analytics report (10-14 pages) + Forecasting (5 pages) + HTAP Dashboard (3 pages)

**Naming**: `<CompanyName>Analytics`, `<CompanyName>Forecasting`, `<CompanyName>HTAP`

**Depends on**: Step 7 (semantic model provides measures and tables)

---

## Step 9: Data Agent (AI Skills)

**Agent**: `ai-skills-agent`  
**Input**: `data-agent.json` (instructions, few-shot examples), semantic model reference  
**Output**: Fabric Data Agent configured with instructions and data source  

**What happens**:
- Create Data Agent via REST API (`POST /items` type `DataAgent`)
- Write aiInstructions with measures list and business context
- Add few-shot examples for common questions
- Bind to semantic model data source (portal step — no API)
- Include "ALWAYS query the semantic model using DAX" instruction

**Depends on**: Step 7 (semantic model must exist as data source)

---

## Step 10: Real-Time Intelligence (Optional)

**Agent**: `rti-eventstream-agent` + `rti-kusto-agent`  
**Input**: `htap-config.json` (event schemas, KQL queries, alerts)  
**Output**: EventStream + Eventhouse + KQL Database + HTAP notebooks  

**What happens**:
- Create Eventhouse and KQL Database
- Create EventStream with Custom Endpoint source
- Define KQL tables with ingestion mapping
- Create materialized views for real-time aggregations
- Generate NB04 (Forecasting) and NB05 (Transactional Analytics) notebooks
- Bridge hot-path (KQL) ↔ cold-path (Lakehouse) via shortcuts
- Create alerting rules and thresholds

**Naming**: `RT_<Prefix>_Events`, `ES_<StreamName>`

**Depends on**: Step 3 (workspace) + Step 4 (Lakehouse for cold path)

---

## Step 11: Data Pipeline (Orchestration)

**Agent**: `orchestrator-agent`  
**Input**: All artifact IDs from previous steps  
**Output**: Fabric Data Pipeline linking Dataflows → Notebooks in sequence  

**What happens**:
- Create orchestration pipeline: `DF → NB01 → NB02 → NB03 → NB04 → NB05`
- Configure activities with proper dependencies
- Set retry policies and timeouts
- Optionally configure scheduled refresh

**Naming**: `PL_<CompanyName>_Orchestration`

**Depends on**: Steps 5-6 (notebooks + dataflows exist)

---

## Step 12: Validation & Deployment

**Agent**: `fabric-cli-agent` + `ai-skills-analysis-agent`  
**Input**: All artifacts from Steps 1-11  
**Output**: Validation report, deployment confirmation  

**What happens**:
- Verify all artifacts exist in workspace
- Run semantic model refresh (Calculate mode for Direct Lake)
- Test Data Agent with sample questions (ai-skills-analysis-agent)
- Validate report renders correctly
- Check EventStream connectivity (if RTI enabled)
- Generate project completion report

**Depends on**: All previous steps

---

## Optional Steps

| Step | When to Use | Agent |
|------|-------------|-------|
| Forecasting (NB04) | Time-series prediction needed | orchestrator-agent |
| Ontology & Graph | Entity relationships for Operations Agent | rti-kusto-agent |
| Operations Agent | AI agent over Eventhouse (RTI) | rti-kusto-agent |
| CI/CD Setup | Automated deployment pipeline | fabric-cli-agent |
| Monitoring | Ongoing health checks | monitoring-agent |

---

## Dependency Graph

```
Step 1 ──▶ Step 2 ──▶ Step 5
  │                      │
  ├──▶ Step 3 ──▶ Step 4─┤
  │                      │
  │                 Step 6 (optional)
  │                      │
  └──▶ Step 7 ──▶ Step 8
            │
            ├──▶ Step 9
            │
  Step 10 (independent, needs Step 3+4)
            │
       Step 11 ──▶ Step 12
```

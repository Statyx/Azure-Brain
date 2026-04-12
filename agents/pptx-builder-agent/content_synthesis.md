# Content Synthesis — From Project Analysis to Slide Narrative

> Inspired by the **Content Synthesizer** role from [claude-code-ppt-generation-team](https://github.com/HungHsunHan/claude-code-ppt-generation-team).

## Purpose

Before designing a single slide, analyze the project holistically and build a **narrative structure**. Raw project artifacts (config files, deploy scripts, data schemas) must be synthesized into a coherent architecture story.

---

## Phase 1: Project Discovery

Gather all inputs before any slide work begins.

### Information Sources (Priority Order)
1. `config.yaml` — workspace name, capacity, item list
2. `deploy_*.py` scripts — reveals the exact Fabric items deployed
3. `data/raw/*.csv` — table names, column counts, row counts
4. `state.json` — deployed item IDs and statuses
5. Notebook source — transformation logic (CSV → Delta)
6. Semantic model definition — measures, relationships
7. Data Agent instructions — AI capabilities, fewshots

### Discovery Checklist
```
□ Project name and purpose identified
□ Data sources cataloged (type, format, volume)
□ All Fabric items listed with types
□ Data flow direction mapped (source → ingest → store → serve → consume)
□ Target users and their roles identified
□ Key measures / KPIs extracted
□ Delta tables enumerated
```

---

## Phase 2: Theme Clustering

Group discovered artifacts into architecture zones.

| Zone | Color | Typical Items | Questions to Answer |
|------|-------|---------------|---------------------|
| **External Sources** | SLATE | CSV, Excel, API, Database | Where does data come from? How much? |
| **Ingest & Transform** | PURPLE | Pipeline, Notebook, Dataflow Gen2 | How is data moved and transformed? |
| **Store** | GREEN | Lakehouse, Warehouse, Delta tables | Where does processed data live? |
| **Serve** | AMBER | Semantic Model, measures | How is data modeled for consumption? |
| **Consume** | CYAN | Report, Data Agent, Dashboard | How do users interact with data? |
| **Business Users** | BLUE | Roles, personas | Who uses this and how? |

### Clustering Rules
- Each Fabric item belongs to exactly ONE zone
- If an item spans zones (e.g., Notebook that ingests AND transforms), place it in the PRIMARY zone
- Empty zones are valid — not every project has all 4 inner zones
- RTI projects may have additional zones: **Stream** (EventStream) and **Analyze** (Eventhouse/KQL)

---

## Phase 3: Narrative Building

Design the story arc the diagram tells. Read left-to-right.

### Standard Narrative Flow
```
Opening Question: "Where does the data come from?"
  → External Sources column
  
Act 1: "How does it enter Fabric?"
  → Ingest zone (Pipeline triggers Notebook, DFS upload)
  
Act 2: "Where is it stored?"
  → Store zone (Lakehouse with Delta tables listed)
  
Act 3: "How is it modeled?"
  → Serve zone (Semantic Model with key measures)
  
Act 4: "How do users consume it?"
  → Consume zone (Report + Data Agent)
  
Closing: "Who benefits?"
  → Business Users column (roles + access methods)
```

### Narrative Enrichment
- **Step circles** (①②③④) tell the deployment/data flow ORDER
- **Arrow labels** explain the HOW between zones ("DFS API Upload", "writes Delta", "Direct Lake", "Report + AI")
- **Badges** classify items by Fabric workload ("Data Factory", "Data Engineering", "Power BI")
- **Summary text** adds context, e.g. `"10 tables · ~8 000 rows · 7 dims + 3 facts"` or `"55 DAX measures · 11 relationships"`
- **DEPRECATED**: Detail pills (individual table names, measure names) — keep diagrams clean; detail goes in documentation

---

## Phase 4: Outline Production

Before generating code, produce a structured outline. This is the handoff to the Designer phase.

### Outline Template
```yaml
project:
  name: "CDR Financial Platform"
  subtitle: "Construction Cost Estimate (CCE) Validation"
  workspace: "CDR – Financial Platform"

sources:
  - icon: CSV
    name: "CSV / ERP"
    desc: "Reference data"
    badge: "Data Source"
  - icon: Excel
    name: "Excel"
    desc: "CCE submissions"
    badge: "Data Source"
  summary: "7 tables · ~6,000 rows\n24 projects · 8 countries"

zones:
  ingest:
    color: PURPLE
    label: "INGEST & TRANSFORM"
    components:
      - icon: Pipeline
        name: "PL_CCE_Setup"
        desc: "Pipeline orchestration"
        badge: "Data Factory"
    connections:
      - label: "▼ triggers"
      - icon: Notebook
        name: "NB_Setup_LH"
        desc: "CSV → Delta tables"
        badge: "Data Engineering"

  store:
    color: GREEN
    label: "STORE"
    components:
      - icon: Lakehouse
        name: "LH_CCE_Ref"
        desc: "OneLake storage"
        badge: "Data Engineering"
    pills: [dim_countries, dim_norms, dim_wbs, dim_disciplines, dim_escalation, fact_benchmarks, fact_cce]

  serve:
    color: AMBER
    label: "SERVE"
    components:
      - icon: Semantic_Model
        name: "SM_CCE"
        desc: "Direct Lake · 35 measures"
        badge: "Semantic Model"
    pills: ["[Confidence Score]", "[Anomaly Count]", "[Anomaly Rate]", "[Est vs Benchmark Δ]", "[Total Cost EUR]"]

  consume:
    color: CYAN
    label: "CONSUME"
    components:
      - icon: Report
        name: "RPT_CCE"
        desc: "3-page PBI Report"
        badge: "Power BI"
      - icon: Data_Agent
        name: "CCE_Advisor"
        desc: "AI Agent · NL→DAX"
        badge: "Data Agent"

steps:
  - num: 1, label: "DFS API\nUpload"
  - num: 2, label: "writes\nDelta"
  - num: 3, label: "Direct\nLake"
  - num: 4, label: "Report\n+ AI"

users:
  - icon: User
    name: "Controllers"
    desc: "PBI dashboards"
  - icon: Copilot
    name: "Engineers"
    desc: "AI Agent (FR)"
  - icon: Users
    name: "Managers"
    desc: "PBI App"
```

### Outline Validation Checklist
```
□ Every deployed Fabric item appears in exactly one zone
□ All data sources are listed
□ Step numbers match the actual deployment/flow order
□ User roles match the target audience
□ Names fit within 15-char limit
□ Descriptions fit within 25-char limit
□ No zone has more than 3 components (split if needed)
□ No zone has more than 7 pills (truncate with "... +N more")
```

---

## Adapting for Different Project Types

### Standard BI (Lakehouse → Model → Report)
Use 4 zones: Ingest → Store → Serve → Consume

### Real-Time Intelligence (EventStream → Eventhouse → KQL)
Use custom zones: Stream → Ingest → Analyze → Visualize
- Stream zone (PURPLE): EventStream, CDC
- Ingest zone (GREEN): Eventhouse, KQL Database
- Analyze zone (AMBER): KQL Queries, Materialized Views
- Visualize zone (CYAN): KQL Dashboard, Report

### Hybrid (Batch + RTI)
Use 2-row layout or split Fabric zone into top/bottom halves
- Top row: batch pipeline (Lakehouse path)
- Bottom row: streaming pipeline (Eventhouse path)
- Shared Consume zone on the right

### Multi-Use-Case Projects
When a project supports multiple use cases sharing the same Fabric platform:

**Discovery phase**: Catalog use cases separately.
```yaml
use_cases:
  - id: 1
    name: "CCE Validation"
    short: "Cost estimate benchmarking & anomaly detection"
    tables: [dim_countries, dim_norms, dim_wbs, dim_disciplines, dim_escalation, fact_benchmarks, fact_cce]
    measures: 42
    agent: CCE_Advisor
    personas: [Cost Controllers, Estimators, Bid Managers]
  - id: 2
    name: "Cashflow Simulation"
    short: "S-curve analysis & scenario comparison"
    tables: [dim_milestones, fact_cashflow_scenarios, fact_cashflow_actuals]
    measures: 12
    agent: CCE_Cashflow
    personas: [Project Finance, Project Managers, Bid Managers]
```

**Clustering rules for multi-use-case**:
1. **Shared infrastructure** (Lakehouse, Pipeline, Notebook) → one instance in the architecture, with combined counts
2. **Use-case-specific agents** → separate components in Consume zone
3. **One Semantic Model** spanning both use cases → combined measure count in Serve zone
4. **Personas may overlap** (e.g., Bid Managers in both) — list each persona once with combined access description

**Slide structure for multi-use-case**:
```
Slide 0: Title → bullets listing all use cases
Slide 1: Use Case 1 (own slide — pain points, I/O, personas, criteria)
Slide 2: Use Case 2 (own slide — same template)
Slide 3: Solution (references both use cases — combined counts)
Slide 4: Architecture (unified diagram — all use cases share infrastructure)
```

**Narrative enrichment**:
- Title slide hero text should NOT mention specific use cases — use contextual project title
- Each use case bullet uses numbered prefix: `"① CCE Validation — …"`, `"② Cashflow Simulation — …"`
- Solution slide combines totals: `"10 tables: 7 CCE + 3 Cashflow"`, `"55 DAX measures (42 + 12)"`
- Architecture diagram shows one unified platform, NOT separate diagrams per use case

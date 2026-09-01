# Naming Conventions

Standard naming patterns for all Fabric artifact types. These conventions are enforced by the project-orchestrator and must be followed by all agents.

---

## Rule 0 — propose the names, then ask. Never impose them.

Everything below is a **default proposal**, not a decree. Before the first item is created,
show the derived names to the user and let them override any of them. Asking costs one
question at step 0; changing your mind after Step 4 costs a rename cascade.

Ask before the first `POST`:

| Ask for | Default if the user has no preference |
|---|---|
| **Workspace name** | `<CompanyName>` |
| The **company/project token** every other name derives from | taken from the domain model |
| Any **item name the user wants to own** — report titles are the usual one | the patterns below |

Record the answers in the project config *and* in the run sheet. Every later agent reads them
from there and never re-derives them.

### Why asking is cheaper than renaming

Three mechanisms, each already documented and verified in its own agent:

| Rename this… | …and this breaks | Source |
|---|---|---|
| A Fabric item, once Git integration is on | The Git **directory keeps the old name forever** — by design. `displayName` updates, the folder does not, and every dependency still points at the old path | [`cicd-fabric-agent/known_issues.md`](../../../Fabric-Brain/agents/cicd-fabric-agent/known_issues.md) GI-005 |
| A Fabric App (Rayfin) | `id:` drives the displayName and the CLI **creates** an item when the name is absent → a *second* AppBackend, plus a second hosting URL to register | [`fabric-apps-agent/known_issues.md`](../../../Apps-Brain/agents/fabric-apps-agent/known_issues.md) #8 |
| A Foundry agent | Its name **is** its API identifier, duplicated into router prompts and workflow YAML — and there is **no rename operation** | [`foundry-orchestration-agent/known_issues.md`](../../../Foundry-Brain/agents/foundry-orchestration-agent/known_issues.md) |

> **Do not turn Rule 0 into an interrogation.** Confirm only the names that are expensive to
> change — workspace, items, agents, reports. Names *inside* a Lakehouse (schemas, tables,
> columns, DAX measures) are cheap to change later: apply the conventions below without asking.

---

## Artifact Naming Rules

| Artifact Type | Pattern | Example |
|--------------|---------|---------|
| **Workspace** | `<CompanyName>` or `<CompanyName>_<Environment>` | `ZavaEnergy`, `ZavaEnergy_Dev` |
| **Lakehouse (Bronze)** | `BronzeLH` | `BronzeLH` |
| **Lakehouse (Silver)** | `SilverLH` | `SilverLH` |
| **Lakehouse (Gold)** | `GoldLH` | `GoldLH` |
| **Notebook** | `NB<NN>_<Purpose>` | `NB01_BronzeToSilver`, `NB03_SilverToGold` |
| **Dataflow Gen2** | `DF_<Domain>` | `DF_Generation`, `DF_Billing`, `DF_HR` |
| **Data Pipeline** | `PL_<CompanyName>_Orchestration` | `PL_ZavaEnergy_Orchestration` |
| **Semantic Model** | `SM_<CompanyName>` | `SM_ZavaEnergy`, `SM_Finance` |
| **Report (Analytics)** | `<CompanyName>Analytics` | `ZavaEnergyAnalytics` |
| **Report (Forecast)** | `<CompanyName>Forecasting` | `ZavaEnergyForecasting` |
| **Report (HTAP)** | `<CompanyName>HTAP` | `ZavaEnergyHTAP` |
| **Data Agent** | `<Domain>_<Role>` | `Energy_Analyst`, `Finance_Controller` |
| **Eventhouse** | `RT_<Prefix>_Events` | `RT_Energy_Events` |
| **KQL Database** | `EventsDB` or `<Domain>DB` | `EventsDB` |
| **EventStream** | `ES_<StreamName>` | `ES_GridTelemetry`, `ES_SensorData` |
| **Spark Environment** | `Env_<CompanyName>` | `Env_ZavaEnergy` |

---

## Notebook Numbering

| Number | Purpose | Medallion Layer |
|:------:|---------|:---------------:|
| NB01 | Bronze → Silver (cleansing, type casting) | Bronze → Silver |
| NB02 | Web Enrichment (API data augmentation) | Silver enrichment |
| NB03 | Silver → Gold (star schema, aggregations) | Silver → Gold |
| NB04 | Forecasting (Holt-Winters, MLflow) | Gold → Analytics |
| NB05 | Transactional Analytics (HTAP setup) | Real-Time |
| NB06 | Diagnostic Check (data quality validation) | Cross-layer |

---

## Schema Naming (Lakehouse)

| Layer | Schema Pattern | Example Tables |
|-------|---------------|----------------|
| **Silver** | Domain name (lowercase) | `generation.plants`, `billing.customers` |
| **Gold** | `dim` / `fact` / `analytics` | `dim.DimDate`, `fact.FactGeneration` |

---

## Table Naming

| Type | Pattern | Example |
|------|---------|---------|
| Dimension | `Dim<Entity>` | `DimPowerPlants`, `DimEmployees` |
| Fact | `Fact<Process>` | `FactGeneration`, `FactBilling` |
| Bridge | `Bridge<Entity1><Entity2>` | `BridgeEmployeeSkills` |
| Date | `DimDate` | Always `DimDate` |

---

## DAX Measure Naming

| Category | Pattern | Example |
|----------|---------|---------|
| Simple aggregate | `Total <Metric>` | `Total MWh`, `Total Revenue` |
| Average | `Avg <Metric>` | `Avg Bill Amount`, `Avg Capacity Factor` |
| Count | `<Entity> Count` | `Customer Count`, `Order Count` |
| Ratio / Rate | `<Metric> %` or `<Metric> Rate` | `Capacity Factor %`, `Turnover Rate` |
| Time Intelligence | `<Metric> YTD` / `PY` / `MoM` | `Revenue YTD`, `MWh PY`, `Headcount MoM` |
| Variance | `<Metric> Var` / `Var %` | `Budget Var`, `Revenue Var %` |

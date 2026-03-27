# Naming Conventions

Standard naming patterns for all Fabric artifact types. These conventions are enforced by the project-orchestrator and must be followed by all agents.

---

## Artifact Naming Rules

| Artifact Type | Pattern | Example |
|--------------|---------|---------|
| **Workspace** | `<CompanyName>` or `<CompanyName>_<Environment>` | `ContosoEnergy`, `ContosoEnergy_Dev` |
| **Lakehouse (Bronze)** | `BronzeLH` | `BronzeLH` |
| **Lakehouse (Silver)** | `SilverLH` | `SilverLH` |
| **Lakehouse (Gold)** | `GoldLH` | `GoldLH` |
| **Notebook** | `NB<NN>_<Purpose>` | `NB01_BronzeToSilver`, `NB03_SilverToGold` |
| **Dataflow Gen2** | `DF_<Domain>` | `DF_Generation`, `DF_Billing`, `DF_HR` |
| **Data Pipeline** | `PL_<CompanyName>_Orchestration` | `PL_ContosoEnergy_Orchestration` |
| **Semantic Model** | `SM_<CompanyName>` | `SM_ContosoEnergy`, `SM_Finance` |
| **Report (Analytics)** | `<CompanyName>Analytics` | `ContosoEnergyAnalytics` |
| **Report (Forecast)** | `<CompanyName>Forecasting` | `ContosoEnergyForecasting` |
| **Report (HTAP)** | `<CompanyName>HTAP` | `ContosoEnergyHTAP` |
| **Data Agent** | `<Domain>_<Role>` | `Energy_Analyst`, `Finance_Controller` |
| **Eventhouse** | `RT_<Prefix>_Events` | `RT_Energy_Events` |
| **KQL Database** | `EventsDB` or `<Domain>DB` | `EventsDB` |
| **EventStream** | `ES_<StreamName>` | `ES_GridTelemetry`, `ES_SensorData` |
| **Spark Environment** | `Env_<CompanyName>` | `Env_ContosoEnergy` |

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

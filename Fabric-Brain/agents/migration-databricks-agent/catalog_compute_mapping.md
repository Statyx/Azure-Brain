# Catalog, Compute, Jobs, ML & Sharing Mapping

## Unity Catalog → Fabric Lakehouse Schemas

| Databricks | Fabric | Action |
|---|---|---|
| Catalog (`catalog`) | Lakehouse (named) | The catalog level disappears — the Lakehouse provides context |
| Schema (`schema`) | Lakehouse schema | Schema-enabled Lakehouse; one schema per UC namespace |
| Table (`table`) | Delta table in `Tables/` | Direct |
| 3-level name `catalog.schema.table` | 2-level `schema.table` | Drop catalog |
| `bronze`/`silver`/`gold` schemas | Separate Lakehouses (medallion) | Align to BronzeLH/SilverLH/GoldLH |
| UC governance (RBAC, RLS, column masking) | Workspace roles + Lakehouse permissions | **Does NOT transfer** — reconfigure manually |

## Cluster Config → Fabric Spark Pools

| Databricks cluster concept | Fabric equivalent | Notes |
|---|---|---|
| All-purpose cluster (interactive) | **Starter Pool** | Auto-provisioned, no config, ideal for notebooks |
| Job cluster (single-use) | **Custom Pool** (or Starter) attached to SJD | Configure node size/autoscale in capacity settings |
| Node type (e.g. `Standard_DS3_v2`) | Fabric node size (Small→XX-Large) | Map by vCore/memory ratio |
| Autoscale min/max workers | Custom Pool min/max node | Workspace Spark settings |
| `spark.conf` cluster settings | **Fabric Environment** Spark properties | Move to Environment item |
| `init_scripts` | **Fabric Environment** install script | Only library installs supported |
| Databricks Runtime version | **Fabric Runtime** (1.1=Spark 3.3, 1.2=3.4, 1.3=3.5) | Pick matching Spark version; test deprecated APIs |
| Photon accelerator | **Native Execution Engine (NEE)** | Enable in workspace Spark settings — vectorized like Photon |

## Databricks Jobs → Spark Job Definitions

| Databricks Jobs concept | Fabric equivalent | Notes |
|---|---|---|
| Job with single notebook task | **SJD** referencing a notebook | Attach a default Lakehouse; params via SJD args |
| Multi-task job (DAG) | **Fabric Data Pipeline** orchestrating SJDs/notebooks | Activities = tasks; dependencies = activity deps |
| Job schedule (cron) | **Pipeline schedule trigger** | Cron → recurrence trigger |
| Job parameters | **SJD default arguments** or notebook **parameters cell** | Injected at runtime |
| Job cluster per task | **Pool attached to SJD** | Each SJD can specify its pool |
| Databricks Workflows | **Fabric Data Pipelines** | Full DAG with conditions, loops, failure branches |

> Delegate SJD creation and notebook deployment to `orchestrator-agent` / `lakehouse-agent`.

## Delta Sharing → OneLake Shortcuts

| Databricks Delta Sharing pattern | Fabric equivalent |
|---|---|
| Provider publishes a Delta share | Fabric **external data sharing** (preview) or OneLake Shortcut to the ADLS Gen2 Delta location |
| Recipient reads shared data | **OneLake Shortcut** to the ADLS Gen2 Delta table; access via Lakehouse |
| Cross-workspace table sharing (intra-org) | **OneLake Shortcuts** to another workspace's Lakehouse tables — no copy |
| Cross-tenant sharing | Fabric **external data sharing** (GA roadmap) — ADLS Gen2 shortcut as interim |

## MLflow → Fabric ML Experiments

Fabric ML Experiments are built on the MLflow SDK — most code is directly portable.

| Databricks MLflow pattern | Fabric equivalent | Action |
|---|---|---|
| `mlflow.set_tracking_uri("databricks")` | (automatic in Fabric) | **Delete this line** |
| `mlflow.set_experiment("/path/exp")` | `mlflow.set_experiment("experiment_name")` | Use name only (not path); Fabric creates the Experiment item |
| `mlflow.log_metric(...)` | identical | No change |
| `mlflow.log_artifact(...)` | identical | No change |
| `mlflow.autolog()` | identical | No change |
| `mlflow.register_model(...)` | identical | Model Registry available in Fabric ML |
| Databricks Model Serving | **Azure ML Online Endpoints** or **Data Activator** | No direct Fabric model serving — use Azure ML |

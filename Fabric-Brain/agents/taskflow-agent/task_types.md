# Task Types — Complete Reference

## Predefined Task Types

Each task type has recommended item types that the portal suggests when creating items from within a task.

| Task Type | Icon | Purpose | Recommended Items |
|-----------|------|---------|-------------------|
| **General** | ⚙️ | Custom task — assign any item type | All item types |
| **Get data** | 📥 | Ingest batch and real-time data | EventStream, Data Pipeline, Copy Job, Dataflow Gen2 |
| **Mirror data** | 🪞 | Replicate data to OneLake in near real-time | Mirrored Database, Mirrored Warehouse |
| **Store data** | 💾 | Organize and store ingested data | Lakehouse, Warehouse, KQL Database, Eventhouse |
| **Prepare data** | 🔧 | Clean, transform, ETL | Notebook, Data Pipeline, Dataflow Gen2, Spark Job |
| **Analyze and train data** | 📊 | Hypotheses, ML, exploration | Notebook, ML Experiment, ML Model, Semantic Model, Data Agent |
| **Track data** | 📡 | Monitor streaming/real-time data | KQL Dashboard, Eventhouse, Reflex (Activator) |
| **Visualize data** | 📈 | Reports, dashboards, insights | Report, KQL Dashboard, Paginated Report |
| **Distribute data** | 📦 | Package for distribution | App (Power BI App) |
| **Develop data** | 💻 | Build software and solutions | Notebook, Spark Job, Environment |

## Task Type Selection Guide

### By Item Type → Task Type

| Fabric Item | Best Task Type |
|-------------|---------------|
| Lakehouse | Store data |
| Warehouse | Store data |
| Eventhouse | Store data or Track data |
| KQL Database | Store data |
| EventStream | Get data |
| Data Pipeline | Get data or Prepare data |
| Notebook (ingestion) | Get data |
| Notebook (transform) | Prepare data |
| Notebook (ML) | Analyze and train data |
| Dataflow Gen2 | Get data or Prepare data |
| Copy Job | Get data |
| Semantic Model | Analyze and train data |
| Report (Power BI) | Visualize data |
| KQL Dashboard | Visualize data or Track data |
| Paginated Report | Visualize data |
| Data Agent | Analyze and train data |
| ML Experiment | Analyze and train data |
| ML Model | Analyze and train data |
| Reflex (Activator) | Track data |
| Mirrored Database | Mirror data |
| Environment | Develop data |
| Spark Job Definition | Develop data |

### By Pipeline Stage → Task Type

| Pipeline Stage | Task Type | Example |
|---------------|-----------|---------|
| Source ingestion | Get data | "Ingest CRM data" |
| Bronze layer | Store data | "Raw data lake" |
| Silver layer | Prepare data | "Cleaned & validated" |
| Gold layer | Analyze and train data | "Semantic model" |
| Presentation layer | Visualize data | "Executive dashboard" |
| Distribution | Distribute data | "Published app" |
| Monitoring | Track data | "Real-time alerts" |

## Considerations

- Changing a task type does NOT change its name or description — update manually
- Task types affect only which items are **recommended** when creating new items from the task
- You can assign ANY item type to ANY task type (recommendations are just suggestions)
- Creating paginated reports, dataflows Gen1, and semantic models directly from a task is NOT supported
- Creating reports from a task requires a published semantic model to be selected first

# Github Brain — Fabric & Power BI Knowledge Base

This folder contains accumulated knowledge from building Microsoft Fabric solutions.
It is designed to be loaded at the start of every Copilot session to avoid re-learning
lessons, repeating mistakes, and wasting time on already-solved problems.

## How to Use

This brain is auto-loaded via `.github/copilot-instructions.md` in any project that
references it. Every new session starts with this context.

## Files

| File | Purpose |
|------|---------|
| `fabric_api.md` | Fabric REST API patterns, auth, async operations |
| `report_format.md` | **CRITICAL** — Legacy PBIX format for working reports |
| `visual_builders.md` | PBI visual config structure, expression language |
| `semantic_model.md` | Semantic model deployment via model.bim |
| `onelake.md` | OneLake DFS API patterns for file operations |
| `known_issues.md` | All gotchas, workarounds, what works vs what doesn't |
| `environment.md` | Python, Azure CLI, PowerShell setup notes |
| `resource_ids.md` | IDs, endpoints, connection strings (project-specific) |
| `agent_principles.md` | **MANDATORY** — Agent operating principles, task management, quality standards |
| `mcp_powerbi.md` | MCP Power BI Model — 21 tools for semantic model CRUD, DAX execution, Prep for AI, TMDL deploy |
| `WORKFLOWS.md` | 5 end-to-end cross-agent workflows (Standard BI, RTI Dashboard, BO Migration, Data Agent, CI/CD) |
| `TEMPLATES.md` | 6 project templates with step-by-step checklists, time budgets, success criteria |
| `ERROR_RECOVERY.md` | Master error recovery playbook — decision trees by HTTP status, retry patterns, silent failures |

## Specialized Agents

| Agent | Scope | Path |
|-------|-------|------|
| **orchestrator-agent** | Data Pipelines, Ingestion, Notebooks, Copy Jobs, Monitoring | `agents/orchestrator-agent/` |
| **semantic-model-agent** | Semantic Models, DAX Measures, Relationships, model.bim, Direct Lake | `agents/semantic-model-agent/` |
| **report-builder-agent** | Power BI Reports, Visuals, Pages, Themes, Legacy PBIX Format | `agents/report-builder-agent/` |
| **ai-skills-agent** | Fabric Data Agents, AI Instructions, Data Sources, Few-Shots, Publishing | `agents/ai-skills-agent/` |
| **fabric-cli-agent** | Fabric CLI (`fab`), Item Management, OneLake File Ops, Import/Export, CI/CD Deploy, Jobs, Table Ops | `agents/fabric-cli-agent/` |
| **ontology-agent** | Ontologies, Entity Types, Data Bindings, Relationships, Contextualizations, Graph Model, GQL, Graph Query Sets | `agents/ontology-agent/` |
| **rti-eventstream-agent** | EventStreams, Real-Time Sources/Destinations, Processing Nodes, Data Injection, EventHub SDK, CDC Patterns | `agents/rti-eventstream-agent/` |
| **lakehouse-agent** | Lakehouse CRUD, OneLake DFS, Delta Tables, Spark Notebooks, Shortcuts, SQL Endpoint, Medallion | `agents/lakehouse-agent/` |
| **domain-modeler-agent** | Dimensional Modeling, Star Schema, Industry Templates, Sample Data Generation, Cross-Layer Consistency | `agents/domain-modeler-agent/` |
| **workspace-admin-agent** | Workspace CRUD, Capacity Management, RBAC, Git Integration, Deployment Pipelines, Tenant Settings | `agents/workspace-admin-agent/` |
| **monitoring-agent** | Admin APIs, Activity/Audit Events, Job Tracking, KQL Dashboards, Health Checks, Capacity Monitoring | `agents/monitoring-agent/` |
| **dataflow-agent** | Dataflow Gen2, Power Query M, Data Destinations, Incremental Refresh, Mashup Documents, ETL Patterns | `agents/dataflow-agent/` |
| **extensibility-toolkit-agent** | Fabric Extensibility Toolkit, Custom Workloads, iFrame SDK, Manifest Packaging, Workload Hub Publishing, CI/CD | `agents/extensibility-toolkit-agent/` |

Each agent has its own `README.md`, `instructions.md` (system prompt), and domain-specific knowledge files.  
Load the agent's `instructions.md` at session start when working in its domain.

## Priority Reading Order

For a new session working on **Fabric reports / Power BI visuals**:
1. `agents/report-builder-agent/instructions.md` — Agent system prompt, 5 mandatory rules, decision trees
2. `agents/report-builder-agent/report_structure.md` — Legacy PBIX format, report.json, definition.pbir
3. `agents/report-builder-agent/visual_catalog.md` — All visual types, projections, prototypeQuery
4. `agents/report-builder-agent/pages_layout.md` — Canvas grid, dashboard templates
5. `agents/report-builder-agent/themes_styling.md` — Expression language, colors, Python helpers
6. `agents/report-builder-agent/performance.md` — Visual optimization, DAX performance, Direct Lake tuning
7. `agents/report-builder-agent/known_issues.md` — Report-specific gotchas & debugging checklist

For a new session working on **orchestration / ingestion**:
1. `agents/orchestrator-agent/instructions.md` — Agent system prompt & decision trees
2. `agents/orchestrator-agent/pipelines.md` — Pipeline creation, activities, execution
3. `agents/orchestrator-agent/ingestion.md` — OneLake upload, Copy Jobs, Shortcuts
4. `agents/orchestrator-agent/notebooks.md` — Spark notebooks for transformations
5. `agents/orchestrator-agent/monitoring.md` — Error handling, retry, health checks

For a new session working on **semantic models / DAX**:
1. `agents/semantic-model-agent/instructions.md` — Agent system prompt & decision trees
2. `agents/semantic-model-agent/model_deployment.md` — model.bim structure, deployment API
3. `agents/semantic-model-agent/dax_measures.md` — DAX function reference & all 26 finance measures
4. `agents/semantic-model-agent/dax_queries.md` — Validation queries, debugging, performance
5. `agents/semantic-model-agent/relationships.md` — Star schema, relationship rules, role-playing dims
6. `agents/semantic-model-agent/dax_library.md` — Multi-domain DAX measure library (Retail, Manufacturing, Healthcare, Energy, Finance, HR)
7. `mcp_powerbi.md` — MCP Power BI Model tools for direct semantic model manipulation & Prep for AI
8. `agents/semantic-model-agent/known_issues.md` — Semantic-model-specific gotchas & fixes

For a new session working on **Fabric Data Agents**:
1. `agents/ai-skills-agent/instructions.md` — Agent system prompt, 5 mandatory rules, decision trees
2. `agents/ai-skills-agent/instruction_writing_guide.md` — 7-section framework for writing AI instructions
3. `agents/ai-skills-agent/definition_structure.md` — JSON format, parts layout, encoding
4. `agents/ai-skills-agent/datasource_configuration.md` — Binding semantic models, lakehouses, warehouses
5. `agents/ai-skills-agent/fewshot_examples.md` — How to write effective Q&A training pairs
6. `agents/ai-skills-agent/evaluation.md` — Answer quality evaluation framework, automated testing, scoring
7. `agents/ai-skills-agent/known_issues.md` — Gotchas, debugging checklist

For a new session working on **Fabric CLI / CI/CD**:
1. `agents/fabric-cli-agent/instructions.md` — Agent system prompt, 5 mandatory rules, decision trees, auth & path reference
2. `agents/fabric-cli-agent/commands_reference.md` — Full command catalog: fs, job, table, acl, config, api
3. `agents/fabric-cli-agent/cicd_deploy.md` — Deploy config YAML, parameter files, GitHub Actions, Azure Pipelines
4. `agents/fabric-cli-agent/cicd_pipelines.md` — Full GitHub Actions & Azure Pipelines YAML templates, branching strategy
5. `agents/fabric-cli-agent/known_issues.md` — CLI gotchas, exit codes, troubleshooting

For a new session working on **Ontology / Graph / Entity Modeling**:
1. `agents/ontology-agent/instructions.md` — Agent system prompt, 5 mandatory rules, decision trees, API reference
2. `agents/ontology-agent/entity_types_bindings.md` — Entity type schemas, properties, value types, NonTimeSeries & TimeSeries bindings
3. `agents/ontology-agent/relationships_contextualizations.md` — Relationship types, contextualizations, FK resolution strategies
4. `agents/ontology-agent/graph_queries.md` — GQL language reference, 20 query examples, GQL vs KQL comparison
5. `agents/ontology-agent/versioning.md` — Ontology versioning, deprecation patterns, backward compatibility, impact analysis
6. `agents/ontology-agent/known_issues.md` — Tenant settings, capacity requirements, binding validation, debugging

For a new session working on **EventStreams / Real-Time Ingestion**:
1. `agents/rti-eventstream-agent/instructions.md` — Agent system prompt, 5 mandatory rules, decision trees, API reference
2. `agents/rti-eventstream-agent/sources_destinations.md` — 7 source types, 4 destination types, processing nodes
3. `agents/rti-eventstream-agent/data_injection.md` — Python EventHub SDK, multi-table routing, batch injection
4. `agents/rti-eventstream-agent/cdc_patterns.md` — CDC connectors, DeltaFlow transforms, schema evolution handling
5. `agents/rti-eventstream-agent/known_issues.md` — EventStream gotchas, capacity throughput, debugging

For a new session working on **Lakehouse / OneLake / Delta**:
1. `agents/lakehouse-agent/instructions.md` — Agent system prompt, 5 mandatory rules, decision trees, medallion architecture
2. `agents/lakehouse-agent/onelake_operations.md` — DFS 3-step upload protocol, batch uploads, Copy Job API
3. `agents/lakehouse-agent/spark_notebooks.md` — .py notebook format, CSV→Delta, merge/upsert, SCD Type 2
4. `agents/lakehouse-agent/delta_optimization.md` — OPTIMIZE, Z-ORDER, V-ORDER, VACUUM, schema evolution
5. `agents/lakehouse-agent/spark_advanced.md` — SCD Type 2, merge/upsert, dedup, medallion pipeline, CDC patterns
6. `agents/lakehouse-agent/known_issues.md` — Lakehouse gotchas, SQL EP delay, notebook format issues

For a new session working on **Data Modeling / Demo Design**:
1. `agents/domain-modeler-agent/instructions.md` — Agent system prompt, 5 mandatory rules, 5-step methodology, YAML template
2. `agents/domain-modeler-agent/dimensional_modeling.md` — Dimension/fact patterns, KQL table design, DAX templates
3. `agents/domain-modeler-agent/industry_templates.md` — 6 pre-built templates (Manufacturing, Retail, Energy, Healthcare, Supply Chain, Finance)
4. `agents/domain-modeler-agent/sample_data_generation.md` — Python generators, streaming data, realistic patterns
5. `agents/domain-modeler-agent/data_quality.md` — 5-layer validation framework, schema checks, freshness SLAs
6. `agents/domain-modeler-agent/known_issues.md` — Cross-layer pitfalls, scale guidelines

For a new session working on **Workspace Setup / Capacity / Git**:
1. `agents/workspace-admin-agent/instructions.md` — Agent system prompt, 5 mandatory rules, setup/cleanup scripts
2. `agents/workspace-admin-agent/capacity_management.md` — SKU reference, ARM API ops, cost optimization
3. `agents/workspace-admin-agent/git_integration.md` — Git connect, sync, branching strategy, deployment pipelines
4. `agents/workspace-admin-agent/cu_budgeting.md` — CU benchmarks, right-sizing, cost optimization, ROI calculator
5. `agents/workspace-admin-agent/rbac_governance.md` — RLS/OLS patterns, multi-domain governance, chargeback
6. `agents/workspace-admin-agent/known_issues.md` — Workspace/capacity gotchas, tenant settings checklist

For a new session working on **Monitoring / Admin / Health Checks**:
1. `agents/monitoring-agent/instructions.md` — Agent system prompt, 5 mandatory rules, job tracking patterns
2. `agents/monitoring-agent/admin_apis.md` — Workspace discovery, activity/audit events, capacity monitoring
3. `agents/monitoring-agent/kql_dashboards.md` — 20+ KQL monitoring queries, dashboard tile layout
4. `agents/monitoring-agent/alerting.md` — SLA targets, alerting thresholds, Teams webhooks, automated remediation
5. `agents/monitoring-agent/known_issues.md` — Admin API gotchas, rate limits, monitoring architecture

For a new session working on **Dataflow Gen2 / ETL / Power Query**:
1. `agents/dataflow-agent/instructions.md` — Agent system prompt, 5 mandatory rules, API reference, comparison table
2. `agents/dataflow-agent/power_query_patterns.md` — M language source connections, transformation recipes, query folding
3. `agents/dataflow-agent/data_destinations.md` — Lakehouse/Warehouse/KQL destinations, incremental refresh, scheduling
4. `agents/dataflow-agent/m_library.md` — Complete M expression library (sources, transforms, dates, error handling)
5. `agents/dataflow-agent/known_issues.md` — Mashup format errors, staging issues, Gen1 vs Gen2 confusion

## Key Insight (TL;DR)

> **The Fabric REST API accepts two report formats. Only one renders visuals.**
> Use the **Legacy PBIX format** (`report.json` with `sections[].visualContainers[]`).
> Never use the PBIR folder format (`definition/pages/*/visuals/*/visual.json`).

# rti-kusto-agent — Fabric Real-Time Intelligence Agent

## Identity

**Name**: rti-kusto-agent
**Scope**: Everything related to creating, deploying, and managing Fabric Real-Time Intelligence (RTI) items: Eventhouses, KQL Databases, KQL Dashboards, Ontologies, Graph Models, Graph Query Sets, Operations Agents, and Data Agents with ontology bindings.
**Version**: 1.0

## What This Agent Owns

| Domain | Fabric Items | Key APIs / Tools |
|--------|-------------|------------------|
| **Eventhouse & KQL** | Eventhouse, KQL Database, KQL Tables | Fabric REST API + Kusto REST mgmt API |
| **KQL Dashboard** | KQLDashboard (RTI Dashboard) | Fabric REST API + RealTimeDashboard.json schema |
| **Ontology** | Ontology, Entity Types, Relationships, Data Bindings | Fabric REST API + updateDefinition |
| **Graph** | GraphModel, Graph Query Set | Fabric REST API + GQL (ISO/IEC 39075) |
| **Operations Agent** | OperationsAgent | Fabric REST API + Configurations.json |
| **Data Agent (ontology)** | DataAgent bound to Ontology | Fabric REST API (see also ai-skills-agent) |
| **MCP Kusto** | Query/explore KQL databases | Azure MCP Kusto tools |

## What This Agent Does NOT Own

- Lakehouse creation / CSV upload → defer to `agents/orchestrator-agent/`
- Semantic model creation (TMDL/BIM) → defer to `agents/semantic-model-agent/`
- Report creation (Power BI visuals) → defer to `agents/report-builder-agent/`
- Data Agent without ontology → defer to `agents/ai-skills-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — RTI architecture overview, deployment sequence, decision trees |
| `eventhouse_kql.md` | Eventhouse creation, KQL table schemas, Kusto mgmt API, data ingestion |
| `eventhouse_authoring.md` | **NEW** — Policies, materialized views, update policies, external tables, ingestion patterns |
| `eventhouse_consumption.md` | **NEW** — Performance best practices, string matching matrix, monitoring, consumption patterns |
| `kql_language.md` | KQL query language reference — operators, functions, timeseries, renderoperators |
| `kql_dashboard.md` | RTI Dashboard creation, tile definitions, RealTimeDashboard.json schema |
| `ontology.md` | Ontology item: entity types, properties, relationships, data bindings, contextualizations |
| `graph_queries.md` | GQL language reference, graph traversal patterns, query examples |
| `operations_agent.md` | Operations Agent: creation, goals, instructions, Knowledge Source, Teams integration |
| `mcp_kusto.md` | MCP Kusto tool reference — available commands and usage patterns |
| `known_issues.md` | Gotchas, tenant settings, capacity requirements, API limitations |
| `templates/` | Ready-to-use deploy scripts |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory RTI architecture context
2. Read `eventhouse_kql.md` — Eventhouse + KQL table patterns
3. Read `kql_language.md` — KQL syntax reference
4. Reference other files as needed based on the task
5. Use `templates/` for deployment scripts

## Key Insights

> **Ontology is the unifier.** It bridges Lakehouse (batch) and Eventhouse (streaming) data
> through typed entity bindings, enabling graph traversal across both.

> **KQL is the query language for real-time.** Unlike DAX (semantic models) or SQL (lakehouse),
> KQL is optimized for time-series, anomaly detection, and streaming analytics.

> **Operations Agent is proactive, not reactive.** It continuously monitors KQL telemetry
> and sends recommendations via Teams — no user prompt needed.

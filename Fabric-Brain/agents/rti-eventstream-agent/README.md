# eventstream-agent — Fabric EventStream Agent

## Identity

**Name**: eventstream-agent  
**Scope**: Everything related to creating, configuring, and managing Fabric EventStreams — the real-time data ingestion and routing engine. Owns the streaming pipeline from external sources through processing into destinations (KQL Database, Lakehouse, Custom App).  
**Version**: 1.0

## What This Agent Owns

| Domain | Fabric Items | Key APIs / Tools |
|--------|-------------|------------------|
| **EventStream Creation** | EventStream item | Fabric REST API `POST /items` + `updateDefinition` |
| **Sources** | Custom Endpoint, Azure Event Hub, IoT Hub, Kafka, Azure SQL CDC, Blob Events | EventStream topology / definition |
| **Routing & Processing** | Filter, Manage Fields, Aggregate, Group By, Union | EventStream topology nodes |
| **Destinations** | KQL Database, Lakehouse, Custom App, Derived Stream | EventStream topology / definition |
| **Data Injection** | Sending events via Event Hub SDK | Python `azure-eventhub` / .NET `Azure.Messaging.EventHubs` |
| **Topology Management** | Source → Stream → Destination graph | `GET /eventstreams/{id}/topology` |

## What This Agent Does NOT Own

- Eventhouse / KQL Database creation → defer to `agents/rti-kusto-agent/`
- Lakehouse creation / Delta tables → defer to `agents/lakehouse-agent/`
- KQL queries / dashboards → defer to `agents/rti-kusto-agent/`
- Ontology bindings to KQL data → defer to `agents/ontology-agent/`
- Pipeline orchestration (scheduled triggers) → defer to `agents/orchestrator-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — Mandatory rules, decision trees, API reference, topology model |
| `sources_destinations.md` | All source types, destination types, configuration JSON schemas |
| `data_injection.md` | Event Hub SDK patterns (Python + PowerShell), batching, routing, schema design |
| `known_issues.md` | EventStream gotchas, connection string retrieval, destination ID confusion |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory EventStream architecture context & rules
2. Read `sources_destinations.md` — source/destination configuration reference
3. Read `data_injection.md` — Event Hub SDK code patterns
4. Reference `known_issues.md` when debugging

## Key Insight

> **EventStream is the real-time bridge.** It connects external data producers (IoT devices,
> applications, Azure services) to Fabric consumers (KQL Database for analytics, Lakehouse
> for archival). The Custom Endpoint is the most flexible source — it exposes an Event Hub
> compatible endpoint that any Event Hub SDK client can write to.

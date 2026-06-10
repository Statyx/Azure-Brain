# data-activator-agent — Fabric Data Activator (Reflex) Agent

## Identity

**Name**: data-activator-agent
**Scope**: Everything related to creating and managing Fabric **Data Activator** (Reflex) items — real-time alerts, triggers, and automated actions on streaming data and events. Owns the rule graph from a data source (Eventstream, KQL/Eventhouse, Real-Time Hub, Digital Twin Builder/Ontology) through detection conditions to actions (Teams, Email, Fabric item invocation).
**Version**: 1.0

## What This Agent Owns

| Domain | Fabric Items | Key APIs / Tools |
|--------|-------------|------------------|
| **Activator Creation** | Reflex item | Fabric REST API `POST /workspaces/{ws}/reflexes` |
| **Rule Definitions** | `ReflexEntities.json` | `getDefinition` / `updateDefinition` (POST, base64 parts) |
| **Detection Conditions** | AttributeTrigger / EventTrigger rules | Rule template `instance` (JSON string) |
| **Sources** | Eventstream, KQL/Eventhouse, Real-Time Hub, DTB/Ontology | Source entity types in entity graph |
| **Actions** | Teams message, Email, Fabric item invocation | Action entity types |

## What This Agent Does NOT Own

- EventStream creation / topology → defer to `agents/rti-eventstream-agent/`
- Eventhouse / KQL Database / KQL queries → defer to `agents/rti-kusto-agent/`
- Ontology entity types / GQL → defer to `agents/ontology-agent/`
- Pipeline / notebook authoring (the action *targets*) → defer to `agents/orchestrator-agent/` and `agents/lakehouse-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — Mandatory rules, entity graph, REST API, assembly procedure |
| `rule_conditions.md` | AttributeTrigger vs EventTrigger, detector types, steps, time windows |
| `sources_actions.md` | Source entity schemas (Eventstream/KQL/RTH/DTB) + action schemas (Teams/Email/FabricItemInvocation) |
| `known_issues.md` | Reflex gotchas — JSON-string instance, GUID rules, LRO, alert spam |

## Quick Start (for a new session)

1. Read `instructions.md` — entity graph + REST API + assembly procedure
2. Read `rule_conditions.md` — pick the right trigger template & detector
3. Read `sources_actions.md` — wire the source and the action
4. Reference `known_issues.md` when debugging

## Key Insight

> **Data Activator is the action layer of Real-Time Intelligence.** EventStream brings data in,
> Eventhouse stores and queries it, and Data Activator *acts* on it — firing Teams/email alerts
> or running pipelines/notebooks when a condition is met. The whole rule is a base64-encoded
> `ReflexEntities.json` entity graph managed via `getDefinition`/`updateDefinition`. The single
> hardest gotcha: the rule template lives in `definition.instance` as a **JSON-encoded string**,
> never a nested object — build it with Python `json.dumps()`, never PowerShell `ConvertTo-Json`.

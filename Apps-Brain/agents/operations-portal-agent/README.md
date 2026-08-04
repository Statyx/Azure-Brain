# operations-portal-agent — README

**External operations portal over Microsoft Fabric** — a FastAPI + static-frontend control room that
proxies a Fabric Data Agent (NL Q&A), embeds Power BI reports and RTI (KQL) dashboards, and renders
portal-native live views. The "last mile" UI of the RTI Operations / Digital Twin pattern
([Template 8](../../../Meta-Brain/TEMPLATES.md)).

## When to use

- You have a deployed RTI Operations solution (Lakehouse topology + Eventhouse telemetry + Ontology +
  Graph + Data Agent + KQL dashboard) and need a **branded, persona-aware end-user portal**.
- You want NL Q&A + embedded reports + a live real-time visual in one place, outside the Fabric portal.

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — 3-surface architecture, the two auth models, chat proxy, live views, deploy/run |
| `known_issues.md` | Embed/token/Kusto/CORS gotchas and fixes |

## Boundaries

| Owned here | Deferred to |
|------------|-------------|
| Portal backend + frontend + embedding wiring | — |
| Data Agent definition / sources / routing | `../../../Fabric-Brain/agents/ai-skills-agent/` |
| Eventhouse / KQL dashboard / Operations Agent | `../../../Fabric-Brain/agents/rti-kusto-agent/` |
| Power BI report + accessible theme | `../../../Fabric-Brain/agents/report-builder-agent/` |
| Fabric-native app on OneLake (Rayfin) | `../fabric-apps-agent/` |

## Key insight

> Two auth models, one portal. The **backend** uses an app/cached token for the Data Agent chat,
> Power BI embed-token, and direct Kusto queries. **Fabric Embed** (RTI dashboard tiles) requires a
> **delegated-user** MSAL token **plus** Azure Data Explorer `user_impersonation` for the tile
> data-plane. Mixing them up is the #1 cause of blank/"null token" embeds.

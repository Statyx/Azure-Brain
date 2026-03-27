# Project Configuration Templates

## Overview

A complete Fabric project is defined by a set of JSON configuration files. These configs drive all artifact generation — no code changes needed to add a new industry or domain.

---

## Config File Inventory

| File | Required | Drives | Consumer Agent |
|------|:--------:|--------|---------------|
| `industry.json` | ✅ | Project identity, domains, workspace naming | project-orchestrator |
| `sample-data.json` | ✅ | CSV schemas, row counts, relationships | domain-modeler |
| `semantic-model.json` | ✅ | Tables, DAX measures, relationships | semantic-model |
| `reports.json` | ✅ | Report pages, visuals, KPIs | report-builder |
| `data-agent.json` | ⚪ | Agent instructions, few-shot examples | ai-skills |
| `forecast-config.json` | ⚪ | Forecast models, grains, horizons | orchestrator |
| `htap-config.json` | ⚪ | Eventhouse, EventStream, KQL, alerts | rti-kusto + rti-eventstream |
| `web-enrichment.json` | ⚪ | External API sources for data enrichment | orchestrator |

---

## Master Config — `industry.json`

Defines the project identity, business domains, and Fabric artifact naming.

```json
{
  "industry": {
    "id": "contoso-energy",
    "name": "Contoso Energy",
    "displayName": "Contoso Energy & Utilities",
    "description": "Regional energy provider serving 2.4M customers across 5 states",
    "domains": ["Generation", "Grid", "Billing", "Sustainability", "FieldOps"],
    "dataYears": ["FY2024", "FY2025", "FY2026"],
    "theme": {
      "primary": "#00843D",
      "secondary": "#FFB81C",
      "accent1": "#4A90D9",
      "accent2": "#E74C3C",
      "background": "#1A1A2E"
    }
  },
  "fabricArtifacts": {
    "workspacePrefix": "ContosoEnergy",
    "lakehouses": {
      "bronze": "BronzeLH",
      "silver": "SilverLH",
      "gold": "GoldLH"
    },
    "schemas": {
      "silver": ["generation", "grid", "billing", "sustainability", "fieldops"],
      "gold": ["dim", "fact", "analytics"]
    },
    "notebooks": 6,
    "dataflows": 5,
    "reports": 3,
    "dataPipeline": "PL_ContosoEnergy_Orchestration"
  },
  "features": {
    "forecasting": true,
    "htap": true,
    "dataAgent": true,
    "webEnrichment": true
  }
}
```

---

## Sample Data Config — `sample-data.json`

Defines every CSV table: columns, types, row counts, and FK relationships.

```json
{
  "tables": [
    {
      "domain": "Generation",
      "name": "DimPowerPlants",
      "type": "dimension",
      "rowCount": 8,
      "columns": [
        {"name": "PlantID", "type": "int", "isPrimaryKey": true},
        {"name": "PlantName", "type": "string", "maxLength": 50},
        {"name": "PlantType", "type": "string", "values": ["Wind", "Solar", "Gas", "Hydro"]},
        {"name": "CapacityMW", "type": "decimal", "min": 50, "max": 500},
        {"name": "State", "type": "string", "values": ["CO", "WY", "NM", "UT", "AZ"]}
      ]
    },
    {
      "domain": "Generation",
      "name": "FactGeneration",
      "type": "fact",
      "rowCount": 50000,
      "columns": [
        {"name": "GenerationID", "type": "int", "isPrimaryKey": true},
        {"name": "PlantID", "type": "int", "foreignKey": "DimPowerPlants.PlantID"},
        {"name": "DateKey", "type": "int", "foreignKey": "DimDate.DateKey"},
        {"name": "OutputMWh", "type": "decimal", "min": 10, "max": 1200},
        {"name": "CapacityFactor", "type": "decimal", "min": 0.15, "max": 0.95}
      ]
    }
  ]
}
```

---

## Semantic Model Config — `semantic-model.json`

Defines tables, DAX measures, and relationships for the semantic model.

```json
{
  "model": {
    "name": "SM_ContosoEnergy",
    "mode": "DirectLake",
    "lakehouse": "GoldLH"
  },
  "measures": [
    {
      "table": "FactGeneration",
      "name": "Total MWh",
      "expression": "SUM(FactGeneration[OutputMWh])",
      "formatString": "#,##0",
      "description": "Total megawatt-hours generated across all plants"
    },
    {
      "table": "FactGeneration",
      "name": "Capacity Factor %",
      "expression": "AVERAGE(FactGeneration[CapacityFactor])",
      "formatString": "0.0%",
      "description": "Average capacity utilization across generation assets"
    }
  ],
  "relationships": [
    {
      "from": "FactGeneration.PlantID",
      "to": "DimPowerPlants.PlantID",
      "cardinality": "ManyToOne",
      "crossFilter": "Single"
    }
  ]
}
```

---

## Reports Config — `reports.json`

Defines report pages, visual types, and KPI mappings.

```json
{
  "reports": [
    {
      "name": "ContosoEnergyAnalytics",
      "type": "analytics",
      "pageCount": 12,
      "pages": [
        {
          "name": "Executive Dashboard",
          "visuals": [
            {"type": "card", "measure": "Total MWh"},
            {"type": "card", "measure": "Capacity Factor %"},
            {"type": "lineChart", "measures": ["Total MWh"], "axis": "Date", "legend": "PlantType"},
            {"type": "barChart", "measures": ["Capacity Factor %"], "axis": "PlantName"}
          ]
        }
      ]
    }
  ]
}
```

---

## HTAP Config — `htap-config.json`

Defines real-time intelligence artifacts: Eventhouse, EventStreams, KQL queries, alerts.

```json
{
  "htapConfig": {
    "eventhouse": {
      "name": "RT_Energy_Events",
      "database": "EventsDB",
      "retentionDays": 30,
      "cachingDays": 7
    },
    "eventstreams": [
      {
        "name": "ES_GridTelemetry",
        "source": "simulated",
        "schema": {
          "columns": [
            {"name": "EventTime", "type": "datetime"},
            {"name": "DeviceId", "type": "string"},
            {"name": "MeasurementType", "type": "string"},
            {"name": "Value", "type": "real"}
          ]
        },
        "simulatorConfig": {
          "eventsPerSecond": 100,
          "deviceCount": 50,
          "anomalyRate": 0.02
        }
      }
    ],
    "kqlQueries": [
      {
        "name": "RealTimeLoad",
        "description": "Sliding window average load per substation",
        "query": "Events | where MeasurementType == 'Load' | summarize AvgLoad=avg(Value) by bin(EventTime, 1m), DeviceId",
        "refreshInterval": "30s"
      }
    ],
    "alerts": [
      {
        "name": "HighLoadAlert",
        "condition": "AvgLoad > 95",
        "severity": "Critical",
        "action": "notification"
      }
    ]
  }
}
```

---

## Data Agent Config — `data-agent.json`

Defines AI agent instructions and few-shot examples.

```json
{
  "agent": {
    "name": "Energy_Analyst",
    "semanticModel": "SM_ContosoEnergy",
    "instructions": "You are an Energy Analyst AI. ALWAYS query the semantic model using DAX before answering...",
    "fewShotExamples": [
      {
        "question": "What is the total generation this year?",
        "expectedAnswer": "Uses Total MWh measure filtered to current fiscal year"
      }
    ]
  }
}
```

---

## Adding a New Industry

To create a new Fabric project for any industry:

1. Create a directory: `industries/<industry-id>/`
2. Write the 4 required config files (`industry.json`, `sample-data.json`, `semantic-model.json`, `reports.json`)
3. Optionally add `data-agent.json`, `htap-config.json`, `forecast-config.json`
4. Run the 12-step pipeline — each agent reads its config and generates artifacts
5. No code changes required

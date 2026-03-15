# Operations Agent — Creation, Goals & Instructions

## Overview

A Fabric Operations Agent is an AI assistant that monitors real-time data and proactively alerts operators. It runs on a schedule, evaluates goals against KQL database data, and sends notifications via Microsoft Teams.

**Capacity**: F2+ (Trial capacity may work)

## API Endpoints

```
POST   {fabricApiBase}/workspaces/{workspaceId}/OperationsAgents
PATCH  {fabricApiBase}/workspaces/{workspaceId}/OperationsAgents/{agentId}
POST   {fabricApiBase}/workspaces/{workspaceId}/items/{agentId}/updateDefinition
```

## Creation Flow

### Step 1: Create the Item
```powershell
$body = @{
    displayName = "Refinery_Operations_Monitor"
    description = "Monitors sensor anomalies and safety incidents"
} | ConvertTo-Json

$agent = Invoke-FabricApi -Method Post `
    -Uri "$FabricApiBase/workspaces/$WorkspaceId/OperationsAgents" `
    -Body $body -Token $fabricToken
$agentId = $agent.id
```

### Step 2: Push Definition (Configurations.json)
```powershell
$definition = @{
    definition = @{
        parts = @(
            @{
                path        = "Configurations.json"
                payload     = [Convert]::ToBase64String(
                    [System.Text.Encoding]::UTF8.GetBytes($configurationsJson))
                payloadType = "InlineBase64"
            }
        )
    }
}

Invoke-FabricApi -Method Post `
    -Uri "$FabricApiBase/workspaces/$WorkspaceId/items/$agentId/updateDefinition" `
    -Body ($definition | ConvertTo-Json -Depth 10) -Token $fabricToken
```

## Configurations.json Schema

```json
{
    "goals": "<goals_text>",
    "instructions": "<instructions_text>",
    "dataSources": [],
    "actions": [],
    "shouldRun": false
}
```

### Fields
| Field | Type | Description |
|-------|------|-------------|
| `goals` | string | What the agent should monitor (multi-line text) |
| `instructions` | string | How the agent should analyze data and format responses |
| `dataSources` | array | Usually empty — configured manually in UI |
| `actions` | array | Usually empty — Teams action configured in UI |
| `shouldRun` | boolean | Whether the agent schedule is active |

## Goals Template

Goals define WHAT the agent monitors. Write clear objectives:

```
Monitor the refinery for the following conditions:

1. SENSOR ANOMALIES: Detect sensors reporting anomalous readings (IsAnomaly = true).
   Report which equipment is affected and the severity.

2. EQUIPMENT STATUS: Track equipment that has changed to "Down" or "Warning" status.
   Flag any critical equipment failures.

3. SAFETY INCIDENTS: Monitor for new safety incidents, especially High severity.
   Identify the process unit and reporter.

4. MAINTENANCE OVERDUE: Identify maintenance tasks past their scheduled date
   that are still Pending or In Progress.

5. ENVIRONMENTAL COMPLIANCE: Check environmental readings exceeding regulatory limits.
   Flag any sensor readings above threshold.
```

## Instructions Template

Instructions define HOW the agent analyzes data and formats output:

```
You are a Refinery Operations Monitor. Use KQL to query the real-time database.

## Data Schema
Tables available:
- SensorReading (SensorId, Timestamp, ReadingValue, QualityFlag, IsAnomaly)
- Equipment (EquipmentId, EquipmentName, Status, EquipmentType)
- MaintenanceTask (TaskId, EquipmentId, TaskType, Status, Priority, ScheduledDate)
- SafetyIncident (IncidentId, ProcessUnitId, IncidentType, Severity, IncidentDate)
- EnvironmentalReading (ReadingId, SensorId, ReadingType, ReadingValue, Timestamp)

## Key Relationships
- SensorReading.SensorId → Sensor.SensorId → Equipment.EquipmentId
- MaintenanceTask.EquipmentId → Equipment.EquipmentId
- SafetyIncident.ProcessUnitId → ProcessUnit.ProcessUnitId

## Monitoring Rules
1. Check the last 15 minutes of data for anomalies
2. Compare reading values against sensor thresholds (MinThreshold, MaxThreshold)
3. Prioritize: Safety Incidents > Equipment Down > Anomalies > Overdue Maintenance

## Response Format
Always respond with:
- **Status**: 🟢 Normal / 🟡 Warning / 🔴 Critical
- **Summary**: One-line overview
- **Details**: Bullet points per issue found
- **Recommended Actions**: What operators should do next

## KQL Query Examples
```
SensorReading
| where Timestamp > ago(15m) and IsAnomaly == true
| join kind=inner Sensor on SensorId
| join kind=inner Equipment on EquipmentId
| summarize AnomalyCount=count(), LastReading=max(Timestamp) by EquipmentName, SensorName
| order by AnomalyCount desc
```
```

## Manual Steps After API Deployment

The following CANNOT be done via API and must be configured in the Fabric portal:

### 1. Add Knowledge Source (KQL Database)
1. Open the Operations Agent in Fabric portal
2. Go to **Knowledge Sources**
3. Click **Add** → Select the KQL Database
4. This gives the agent access to query the database

### 2. Configure Actions (Teams)
1. Go to **Actions** tab
2. Click **Add Action** → **Microsoft Teams**
3. Select the Teams channel for notifications
4. Configure message format

### 3. Set Schedule
1. Go to **Schedule** tab
2. Set frequency (e.g., every 15 minutes)
3. Enable the schedule (`shouldRun: true`)

### 4. Test
1. Use the **Try it** panel to ask a test question
2. Verify the agent queries the KQL database correctly
3. Verify Teams notifications are sent

## Python Equivalent

```python
import requests
import base64
import json

def create_operations_agent(token, workspace_id, agent_name, goals, instructions):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    api_base = "https://api.fabric.microsoft.com/v1"
    
    # Step 1: Create item
    create_body = {
        "displayName": agent_name,
        "description": "Operations monitoring agent"
    }
    resp = requests.post(
        f"{api_base}/workspaces/{workspace_id}/OperationsAgents",
        headers=headers, json=create_body
    )
    agent_id = resp.json()["id"]
    
    # Step 2: Push definition
    config = {
        "goals": goals,
        "instructions": instructions,
        "dataSources": [],
        "actions": [],
        "shouldRun": False
    }
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
    
    definition_body = {
        "definition": {
            "parts": [{
                "path": "Configurations.json",
                "payload": config_b64,
                "payloadType": "InlineBase64"
            }]
        }
    }
    requests.post(
        f"{api_base}/workspaces/{workspace_id}/items/{agent_id}/updateDefinition",
        headers=headers, json=definition_body
    )
    
    return agent_id
```

## Operations Agent vs Data Agent

| Aspect | Operations Agent | Data Agent |
|--------|-----------------|------------|
| Purpose | Proactive monitoring + alerting | User-driven Q&A |
| Trigger | Scheduled (cron-like) | User question |
| Output | Teams notification | Chat response |
| Data source | KQL Database (real-time) | Semantic Model or Ontology |
| Capacity | F2+ | F64+ |
| API endpoint | `/OperationsAgents` | `/dataAgents` |
| Definition | `Configurations.json` | `agent-definition.json` + parts |

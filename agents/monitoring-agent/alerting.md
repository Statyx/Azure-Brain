# Alerting, SLA Monitoring & Automated Remediation

## Purpose

Define alerting thresholds, SLA targets, monitoring dashboards, and automated remediation patterns for Microsoft Fabric workloads.

---

## SLA Targets by Workload

### Data Freshness SLAs

| Data Layer | Refresh Type | SLA Target | Alert After | Escalate After |
|-----------|-------------|-----------|------------|----------------|
| Bronze (raw) | Streaming / EventStream | ≤ 5 min latency | 10 min | 30 min |
| Bronze (raw) | Batch (pipeline) | Per schedule ± 15 min | Schedule + 30 min | Schedule + 2 h |
| Silver (curated) | Notebook / Spark | ≤ 1 h after bronze | Bronze + 2 h | Bronze + 4 h |
| Gold (aggregated) | Notebook / Spark | ≤ 2 h after silver | Silver + 3 h | Silver + 6 h |
| Semantic Model | Dataset refresh | ≤ 30 min after gold | Gold + 1 h | Gold + 2 h |
| Direct Lake | No refresh needed | Automatic | Fallback to DQ mode | Immediate |

### Pipeline Reliability SLAs

| Metric | Target | Alert Threshold | Critical Threshold |
|--------|--------|----------------|-------------------|
| Pipeline success rate | ≥ 99% (7-day rolling) | < 97% | < 95% |
| Notebook success rate | ≥ 98% (7-day rolling) | < 95% | < 90% |
| Data pipeline duration | Within 2× baseline | > 2× baseline | > 3× baseline |
| EventStream lag | ≤ 1000 events behind | > 5000 events | > 50000 events |
| Semantic Model refresh | ≤ 15 min | > 30 min | > 60 min |

### CU Consumption SLAs

| SKU | CU Budget/Month | Alert Threshold | Throttling Risk |
|-----|----------------|-----------------|----------------|
| F2 | 2 CU | > 70% utilization | > 85% |
| F4 | 4 CU | > 70% utilization | > 85% |
| F8 | 8 CU | > 70% utilization | > 85% |
| F16 | 16 CU | > 70% utilization | > 85% |
| F32 | 32 CU | > 70% utilization | > 85% |
| F64+ | 64+ CU | > 75% utilization | > 90% |

---

## KQL Monitoring Queries

### Query 1: Data Freshness Check

```kql
// Check when each table last received data
SensorReadings
| summarize LastEvent = max(Timestamp), EventCount = count() by bin(Timestamp, 1h)
| where LastEvent < ago(30m)
| project 
    Table = "SensorReadings",
    LastEvent,
    MinutesSinceLastEvent = datetime_diff('minute', now(), LastEvent),
    Status = iff(datetime_diff('minute', now(), LastEvent) > 60, "🔴 CRITICAL", "🟡 WARNING")
```

### Query 2: Pipeline Execution History

```kql
// Track pipeline run history and failure rate
.show commands
| where StartedOn > ago(7d)
| where CommandType has "DataPipeline" or CommandType has "Notebook"
| summarize 
    TotalRuns = count(),
    SuccessCount = countif(State == "Completed"),
    FailedCount = countif(State == "Failed"),
    AvgDuration = avg(Duration)
  by CommandType, bin(StartedOn, 1d)
| extend SuccessRate = round(100.0 * SuccessCount / TotalRuns, 2)
| order by StartedOn desc
```

### Query 3: CU Consumption Trend

```kql
// Monitor capacity utilization over time
.show capacity usage 
| where Timestamp > ago(24h)
| summarize 
    AvgCU = avg(CUConsumption),
    MaxCU = max(CUConsumption),
    P95CU = percentile(CUConsumption, 95)
  by bin(Timestamp, 1h)
| extend 
    Status = case(
        P95CU > CapacityLimit * 0.85, "🔴 THROTTLING RISK",
        P95CU > CapacityLimit * 0.70, "🟡 HIGH USAGE",
        "🟢 NORMAL"
    )
```

### Query 4: EventStream Lag Detection

```kql
// Detect EventStream consumer lag
EventHubMetrics
| where Timestamp > ago(1h)
| summarize 
    IncomingMessages = sum(IncomingMessages),
    OutgoingMessages = sum(OutgoingMessages)
  by bin(Timestamp, 5m)
| extend Lag = IncomingMessages - OutgoingMessages
| where Lag > 5000
| project Timestamp, IncomingMessages, OutgoingMessages, Lag,
    Status = iff(Lag > 50000, "🔴 CRITICAL", "🟡 WARNING")
```

### Query 5: Semantic Model Refresh Tracking

```kql
// Track semantic model refresh success/failure
FabricActivityLog
| where Timestamp > ago(7d)
| where Operation == "RefreshDataset"
| summarize 
    TotalRefreshes = count(),
    Succeeded = countif(Status == "Succeeded"),
    Failed = countif(Status == "Failed"),
    AvgDurationSec = avg(DurationMs) / 1000
  by DatasetName, bin(Timestamp, 1d)
| extend SuccessRate = round(100.0 * Succeeded / TotalRefreshes, 2)
| where SuccessRate < 100
```

---

## Alerting Configuration

### Pattern 1: Python-Based Monitoring Script

```python
"""
Fabric monitoring script — Run as a scheduled notebook or pipeline.
Checks SLA compliance and sends alerts via Teams webhook.
"""
import requests
import json
from datetime import datetime, timedelta

TEAMS_WEBHOOK_URL = "<TEAMS_WEBHOOK_URL>"  # Store in Key Vault in production

def send_teams_alert(title: str, severity: str, message: str, details: dict):
    """Send alert to Microsoft Teams channel via webhook."""
    color = {
        "CRITICAL": "FF0000",
        "WARNING": "FFA500",
        "INFO": "0078D4",
        "RESOLVED": "00FF00"
    }.get(severity, "808080")
    
    card = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "sections": [{
            "activityTitle": f"[{severity}] {title}",
            "activitySubtitle": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "facts": [{"name": k, "value": str(v)} for k, v in details.items()],
            "text": message,
            "markdown": True
        }]
    }
    
    requests.post(TEAMS_WEBHOOK_URL, json=card, timeout=10)


def check_data_freshness(table_name: str, max_age_minutes: int):
    """Check if a table's latest data is within SLA."""
    query = f"""
    SELECT MAX(Timestamp) as LastEvent
    FROM {table_name}
    """
    result = spark.sql(query).collect()[0]
    last_event = result["LastEvent"]
    
    if last_event is None:
        send_teams_alert(
            title=f"No data in {table_name}",
            severity="CRITICAL",
            message=f"Table {table_name} contains no data.",
            details={"Table": table_name, "Expected Freshness": f"{max_age_minutes} min"}
        )
        return False
    
    age_minutes = (datetime.utcnow() - last_event).total_seconds() / 60
    
    if age_minutes > max_age_minutes * 2:
        send_teams_alert(
            title=f"Data stale in {table_name}",
            severity="CRITICAL",
            message=f"Last event was {age_minutes:.0f} minutes ago (SLA: {max_age_minutes} min).",
            details={"Table": table_name, "Last Event": str(last_event), "Age (min)": f"{age_minutes:.0f}", "SLA (min)": str(max_age_minutes)}
        )
        return False
    elif age_minutes > max_age_minutes:
        send_teams_alert(
            title=f"Data freshness warning for {table_name}",
            severity="WARNING",
            message=f"Last event was {age_minutes:.0f} minutes ago (SLA: {max_age_minutes} min).",
            details={"Table": table_name, "Last Event": str(last_event), "Age (min)": f"{age_minutes:.0f}", "SLA (min)": str(max_age_minutes)}
        )
        return False
    
    return True


def check_pipeline_health(workspace_id: str, days: int = 7, min_success_rate: float = 0.97):
    """Check pipeline success rate over a rolling window."""
    # Use Fabric REST API to get pipeline run history
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items?type=DataPipeline",
        headers=headers
    )
    pipelines = resp.json().get("value", [])
    
    for pipeline in pipelines:
        # Get run history (pseudo-code, actual API may differ)
        runs_resp = requests.get(
            f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{pipeline['id']}/jobs",
            headers=headers
        )
        runs = runs_resp.json().get("value", [])
        
        total = len(runs)
        if total == 0:
            continue
        
        succeeded = sum(1 for r in runs if r.get("status") == "Completed")
        rate = succeeded / total
        
        if rate < min_success_rate:
            send_teams_alert(
                title=f"Pipeline failure rate high: {pipeline['displayName']}",
                severity="CRITICAL" if rate < 0.95 else "WARNING",
                message=f"Success rate: {rate*100:.1f}% over last {days} days (target: {min_success_rate*100:.0f}%).",
                details={
                    "Pipeline": pipeline["displayName"],
                    "Total Runs": total,
                    "Succeeded": succeeded,
                    "Failed": total - succeeded,
                    "Success Rate": f"{rate*100:.1f}%"
                }
            )
```

### Pattern 2: Data Activator (Reflex) Alert

Use Data Activator in Fabric for no-code alerting:

```
Setup Steps:
1. Create a Reflex item in the workspace
2. Connect to KQL database as source
3. Define trigger condition:
   - Measure: count() of SensorReadings in last 5 min
   - Condition: value < 10 (expected minimum is 100)
4. Set action: Send email / Teams message
5. Set frequency: Check every 5 minutes
```

---

## Automated Remediation

### Remediation 1: Auto-Retry Failed Pipeline

```python
import time

def retry_failed_pipeline(workspace_id: str, pipeline_id: str, max_retries: int = 3, backoff_seconds: int = 60):
    """Retry a failed pipeline with exponential backoff."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    for attempt in range(1, max_retries + 1):
        wait = backoff_seconds * (2 ** (attempt - 1))
        print(f"  Retry attempt {attempt}/{max_retries} (waiting {wait}s)...")
        time.sleep(wait)
        
        resp = requests.post(
            f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{pipeline_id}/jobs/instances?jobType=Pipeline",
            headers=headers
        )
        
        if resp.status_code == 202:
            # Poll for completion
            location = resp.headers.get("Location")
            while True:
                status_resp = requests.get(location, headers=headers)
                status = status_resp.json().get("status")
                if status == "Completed":
                    print(f"  ✅ Pipeline succeeded on attempt {attempt}")
                    return True
                elif status == "Failed":
                    break
                time.sleep(30)
    
    send_teams_alert(
        title="Pipeline auto-retry exhausted",
        severity="CRITICAL",
        message=f"Pipeline failed after {max_retries} retry attempts. Manual intervention required.",
        details={"Pipeline ID": pipeline_id, "Workspace ID": workspace_id, "Attempts": max_retries}
    )
    return False
```

### Remediation 2: Auto-Resume Paused Capacity

```python
def check_and_resume_capacity(subscription_id: str, resource_group: str, capacity_name: str):
    """Resume capacity if paused and workloads are scheduled."""
    import requests
    
    headers = {"Authorization": f"Bearer {azure_token}"}
    
    # Check capacity state
    resp = requests.get(
        f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Fabric/capacities/{capacity_name}?api-version=2023-11-01",
        headers=headers
    )
    state = resp.json().get("properties", {}).get("state")
    
    if state == "Paused":
        print("Capacity is paused. Resuming...")
        resume_resp = requests.post(
            f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Fabric/capacities/{capacity_name}/resume?api-version=2023-11-01",
            headers=headers
        )
        if resume_resp.status_code == 202:
            print("  ⏳ Resume initiated. Waiting for active state...")
            time.sleep(60)
            return True
        else:
            send_teams_alert(
                title="Failed to resume capacity",
                severity="CRITICAL",
                message=f"Auto-resume failed with status {resume_resp.status_code}.",
                details={"Capacity": capacity_name, "Status Code": resume_resp.status_code}
            )
            return False
    
    return True  # Already active
```

### Remediation 3: Auto-Scale Capacity on Throttling

```python
SCALE_MAP = {
    "F2": "F4",
    "F4": "F8",
    "F8": "F16",
    "F16": "F32",
    "F32": "F64",
    "F64": "F128"
}

def auto_scale_capacity(subscription_id: str, resource_group: str, capacity_name: str, current_sku: str):
    """Scale up capacity when sustained throttling is detected."""
    next_sku = SCALE_MAP.get(current_sku)
    
    if not next_sku:
        send_teams_alert(
            title="Cannot auto-scale: already at max SKU",
            severity="CRITICAL",
            message=f"Capacity {capacity_name} is at {current_sku} and cannot scale further.",
            details={"Capacity": capacity_name, "Current SKU": current_sku}
        )
        return False
    
    headers = {"Authorization": f"Bearer {azure_token}", "Content-Type": "application/json"}
    
    resp = requests.patch(
        f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Fabric/capacities/{capacity_name}?api-version=2023-11-01",
        headers=headers,
        json={"sku": {"name": next_sku, "tier": "Fabric"}}
    )
    
    if resp.status_code in (200, 202):
        send_teams_alert(
            title=f"Auto-scaled capacity: {current_sku} → {next_sku}",
            severity="INFO",
            message=f"Capacity {capacity_name} scaled from {current_sku} to {next_sku} due to throttling.",
            details={"Capacity": capacity_name, "From": current_sku, "To": next_sku}
        )
        return True
    
    return False
```

> **Warning**: Auto-scaling increases cost. Always set a maximum SKU limit and require approval for scaling beyond F32.

---

## Monitoring Dashboard Layout (KQL)

### Recommended Dashboard Panels

| Panel | KQL Query | Refresh | Visual |
|-------|-----------|---------|--------|
| Data freshness heatmap | Last event per table, color by age | 5 min | Heatmap tile |
| Pipeline success rate (7d) | Success/fail counts by pipeline | 1 h | Column chart |
| CU utilization trend | Hourly avg/max/P95 | 15 min | Area chart |
| EventStream lag | Incoming vs outgoing per 5 min | 5 min | Line chart |
| Active alerts | Open alerts by severity | 5 min | Table |
| Cost tracker | Daily CU spend, projected monthly | 1 h | Line chart + KPI |

---

## Cross-References

- [Workspace Admin CU Budgeting](../workspace-admin-agent/cu_budgeting.md) — CU benchmarks and cost optimization
- [Error Recovery Playbook](../../ERROR_RECOVERY.md) — General error recovery decision trees
- [RTI EventStream Agent](../rti-eventstream-agent/instructions.md) — EventStream-specific monitoring

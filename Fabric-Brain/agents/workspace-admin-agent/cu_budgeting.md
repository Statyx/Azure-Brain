# Capacity Unit (CU) Budgeting & Cost Optimization

## Fabric Capacity SKU Reference

| SKU | CU/s | CU Burst | Monthly Cost (approx.) | Use Case |
|-----|------|----------|----------------------|----------|
| **F2** | 2 | 4 | ~$260 | Dev/test, small demos |
| **F4** | 4 | 8 | ~$520 | Light BI workloads |
| **F8** | 8 | 16 | ~$1,040 | Small production |
| **F16** | 16 | 32 | ~$2,080 | Medium production, RTI |
| **F32** | 32 | 64 | ~$4,160 | Large production |
| **F64** | 64 | 128 | ~$8,320 | Enterprise, Data Agents with Ontology |
| **F128** | 128 | 256 | ~$16,640 | Large enterprise |
| **F256** | 256 | 512 | ~$33,280 | Very large enterprise |

> **Trial capacity** = F64 equivalent but with limitations (no SPN, limited features).
> **Data Agents with Ontology source** require F64 minimum.

---

## CU Consumption Benchmarks by Workload

### Spark / Notebook Operations

| Operation | CU/s Estimate | Duration | Total CU |
|-----------|--------------|----------|----------|
| Small Spark notebook (CSV → Delta, <10K rows) | 2–4 | 30–60s | 60–240 |
| Medium Spark notebook (transforms, 100K rows) | 4–8 | 60–120s | 240–960 |
| Large Spark session (1M+ rows, multiple transforms) | 8–16 | 120–300s | 960–4800 |
| Delta OPTIMIZE + V-ORDER | 4–8 | 30–60s | 120–480 |
| Delta VACUUM | 2–4 | 15–30s | 30–120 |

### Semantic Model Operations

| Operation | CU/s Estimate | Duration | Total CU |
|-----------|--------------|----------|----------|
| Direct Lake model load (first query) | 2–4 | 5–15s | 10–60 |
| DAX query (simple, <1M rows) | 1–2 | 1–5s | 1–10 |
| DAX query (complex, joins, 1M+ rows) | 4–8 | 5–30s | 20–240 |
| Model refresh | 2–8 | 10–120s | 20–960 |

### Report Operations

| Operation | CU/s Estimate | Duration | Total CU |
|-----------|--------------|----------|----------|
| Report page render (3–5 visuals) | 2–4 | 2–8s | 4–32 |
| Report page render (10+ visuals) | 4–8 | 5–15s | 20–120 |
| Slicer interaction | 1–2 | 1–3s | 1–6 |

### Real-Time Intelligence

| Operation | CU/s Estimate | Duration | Total CU |
|-----------|--------------|----------|----------|
| EventStream ingestion (idle) | 0.5–1 | continuous | 1,800/hr |
| EventStream ingestion (100 events/s) | 2–4 | continuous | 7,200/hr |
| KQL query (simple) | 1–2 | 1–5s | 1–10 |
| KQL query (aggregation, 1M+ rows) | 4–8 | 5–30s | 20–240 |

---

## Right-Sizing Decision Tree

```
Q: What is the primary workload?
├── Demo / POC (low concurrency, batch only)
│   └── F2 ($260/mo) — Sufficient for 1-2 users, small data
│
├── Standard BI (reports + semantic models, <10 concurrent users)
│   ├── Small data (<1M rows) → F4 ($520/mo)
│   └── Medium data (1M–10M rows) → F8 ($1,040/mo)
│
├── BI + RTI (streaming + reports)
│   ├── Light streaming (<100 events/s) → F8 ($1,040/mo)
│   └── Heavy streaming (>100 events/s) → F16 ($2,080/mo)
│
├── Full platform (BI + RTI + Ontology + Data Agent)
│   └── F64 minimum ($8,320/mo) — required for Ontology Data Agent
│
└── Enterprise (50+ users, heavy Spark, multiple domains)
    └── F128+ ($16,640+/mo) — consider multiple capacities
```

---

## Cost Optimization Strategies

### 1. Capacity Pause/Resume Scheduling

**The single highest-impact optimization.** Fabric charges by the hour when capacity is running.

```powershell
# Pause capacity (stops billing for CU)
$uri = "https://management.azure.com/subscriptions/{subId}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{name}/suspend?api-version=2023-11-01"
Invoke-RestMethod -Method POST -Uri $uri -Headers @{Authorization = "Bearer $armToken"}

# Resume capacity
$uri = "https://management.azure.com/subscriptions/{subId}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{name}/resume?api-version=2023-11-01"
Invoke-RestMethod -Method POST -Uri $uri -Headers @{Authorization = "Bearer $armToken"}
```

**Scheduling patterns**:

| Pattern | Hours ON | Monthly Savings vs 24/7 |
|---------|---------|------------------------|
| Business hours only (8am–8pm weekdays) | 260h/mo | **63% savings** |
| Business hours + Saturday | 312h/mo | **57% savings** |
| Demo-only (pause between demos) | 40–80h/mo | **89–94% savings** |
| 24/7 (no scheduling) | 730h/mo | 0% (baseline) |

> **F16 example**: 24/7 = ~$2,080/mo → Business hours only = ~$770/mo → **Saves $1,310/mo**

### 2. Azure Automation Runbook for Scheduling

```python
# Azure Automation runbook pattern (from environment.md)
# Schedule: Mon-Fri 8:00 AM CET → Start-FabricCapacity.ps1
# Schedule: Mon-Fri 8:00 PM CET → Stop-FabricCapacity.ps1

# Python equivalent for manual scheduling
import requests, subprocess

def resume_capacity(sub_id, rg, cap_name):
    token = subprocess.check_output(
        'az account get-access-token --resource "https://management.azure.com" --query accessToken -o tsv',
        shell=True
    ).decode().strip()
    
    url = f"https://management.azure.com/subscriptions/{sub_id}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{cap_name}/resume?api-version=2023-11-01"
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}"})
    print(f"Resume: {resp.status_code}")
```

### 3. Stagger Heavy Workloads

Avoid running multiple Spark notebooks simultaneously. Stagger to stay within CU burst limits:

```python
# BAD: All notebooks at once — may exceed CU limit
for nb in notebooks:
    start_notebook(nb)  # All run concurrently

# GOOD: Sequential with small gap
for nb in notebooks:
    run_notebook_sync(nb)  # Wait for completion
    time.sleep(5)          # Brief cooldown
```

### 4. Optimize Delta Tables

V-ORDER and Z-ORDER dramatically reduce query CU consumption:

```sql
-- After initial data load
OPTIMIZE fact_sales VORDER;
OPTIMIZE fact_sales ZORDER BY (date_key, product_id);

-- Schedule weekly VACUUM to reclaim storage
VACUUM fact_sales RETAIN 168 HOURS;
```

### 5. Direct Lake Instead of Import

Direct Lake mode for semantic models avoids costly data refresh cycles. Data stays in Delta format and is read directly — no duplicate copy.

| Mode | CU Cost (Refresh) | CU Cost (Query) | Total |
|------|-------------------|-----------------|-------|
| Import | High (full copy) | Low | High |
| Direct Lake | None (no refresh) | Medium | **Lower overall** |
| DirectQuery | None | High (every query) | Highest for frequent queries |

---

## ROI Calculator Template

```
Inputs:
  SKU:                    F16
  Monthly cost:           $2,080
  Scheduling:             Business hours (63% savings) = $770/mo
  Users:                  10 analysts
  Reports replaced:       15 Excel reports → 3 Power BI reports
  Time saved/analyst/week: 4 hours (manual Excel work eliminated)

Calculations:
  Annual capacity cost:   $770 × 12 = $9,240
  Annual time saved:      10 analysts × 4 hrs × 48 weeks = 1,920 hours
  Analyst hourly cost:    $75 (fully loaded)
  Annual value created:   1,920 × $75 = $144,000
  
  ROI = ($144,000 - $9,240) / $9,240 = 14.6x
  Payback period: < 1 month
```

---

## Monitoring Capacity Usage

### KQL Query for CU Consumption

```kql
// Track CU consumption over time (requires Monitoring workspace enabled)
FabricEvents
| where EventType == "CapacityMetrics"
| summarize AvgCU = avg(CUUsage), MaxCU = max(CUUsage) by bin(Timestamp, 1h)
| order by Timestamp desc
| take 24
```

### Alerting Thresholds

| Metric | Yellow (Warning) | Red (Action Required) |
|--------|-----------------|----------------------|
| CU utilization sustained | >70% for 1 hr | >90% for 30 min |
| CU burst utilization | >50% for 15 min | >80% for 15 min |
| Throttled operations | >5/hour | >20/hour |
| Queue depth | >10 items | >50 items |

> When CU is consistently >80%: scale up SKU OR stagger workloads OR optimize queries.

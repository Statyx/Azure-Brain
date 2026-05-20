# Latency Analysis — Where Time Is Actually Spent

How to measure, attribute, and optimize end-to-end response time of a Fabric Data Agent.
Most diagnostics tools display **wall-clock** durations from `run_steps[].created_at/completed_at`,
which **include queue time** and are misleading. The diagnostic JSON contains a separate
top-level `latency` section with **true tool execution times** — this is the only signal
you can trust for performance analysis.

---

## The Two Time Sources

| Source | What it measures | Accuracy | Field |
|--------|------------------|----------|-------|
| Wall-clock | `completed_at − created_at` on each `run_step` | ❌ Includes queue/scheduling | `thread.run_steps[]` |
| True latency | Duration measured by the agent runtime around the tool call | ✅ Tool execution only | `latency.tool_calls[]` |

**Always prefer `latency.tool_calls[]` when present.** Fall back to wall-clock only if absent.

### Shape of `latency.tool_calls[]`

```json
{
  "latency": {
    "tool_calls": [
      { "step_id": "step_fab_abc...", "duration_seconds": 12.47 },
      { "step_id": "step_fab_def...", "duration_seconds": 0.32 },
      { "step_id": "step_fab_ghi...", "duration_seconds": 2.10 }
    ]
  }
}
```

Some exports also nest the section under `thread.latency` — check both locations.

Join on `step_id` to attach a true duration to each parsed step.

---

## The Three Components of a Turn

```
Total turn duration  =  Tool execution  +  Orchestrator overhead
(runs[].created_at →    (Σ tool_calls)    (queue + LLM planning +
 runs[].completed_at)                       serialization + waits)
```

- **Tool execution** = sum of `latency.tool_calls[].duration_seconds`
- **Orchestrator overhead** = `run_total − tool_total` (always ≥ 0)
- **Orchestrator %** = `overhead / total × 100`

Why this matters: if a turn takes 45s but only 12s were spent in DAX/KQL, the other 33s
were not the model's fault — it was queue, cold start, or LLM planning latency.

---

## Anomaly Thresholds (proven defaults)

| Signal | Threshold | Severity | Likely cause |
|--------|-----------|----------|--------------|
| Single tool execution | ≥ **10s** | Warning | Slow DAX/SQL/KQL, large schema, missing aggregations |
| Total turn duration | ≥ **30s** | Warning | Compound slowness — user-perceived bad UX |
| Orchestrator overhead | ≥ **30%** of total | Info | Cold start, LLM contention, or chain of cheap tool calls |
| Tool retried with identical args | **3+** consecutive | Warning | Retry loop — agent is stuck, add a fewshot |
| `getschema` / `EVALUATE TOPN(1, X)` called | **≥ 2×** in same run | Info | Schema re-discovery — cache the schema in instructions |
| Thread messages | **≥ 50** | Warning | Thread pollution — delete and recreate the thread |

These are encoded in [`analyzer/diagnose.py`](../../../The_AI_Skill_Analyzer/analyzer/diagnose.py)
(`_compute_latency_breakdown`, `_detect_anomalies`).

---

## Cached Response Detection

A cached response returns instantly with no tool execution. Detection rules (any one matches):

1. An assistant message exists but **no `run_id`** is attached
2. A run exists but has **no tool_calls** AND total < **3s**
3. `latency.tool_calls` is empty for that run

Flag these as **info** (not an issue). They distort all averages — exclude them from
"avg response time" computations or label them separately.

---

## Standard Breakdown Report

```
LATENCY BREAKDOWN
  Total run        : 45.0s
  Tool execution   : 14.9s (33%)
  Orchestrator     : 30.1s (67%)  [queue + LLM + serialization]
  ----
  NL → DAX Generation   12.5s  28%  ######
  DAX Execution          2.1s   5%  #
  Fewshot Loading        0.3s   1%  #
  (µ = measured by latency.tool_calls, otherwise wall-clock)
```

A `µ` marker next to a step duration in pipeline traces denotes a true latency
measurement vs a wall-clock fallback.

---

## Recommendations by Pattern

| Observed pattern | Action |
|------------------|--------|
| Slow `nl2code` (>10s) | Trim schema (deselect unused tables/columns); shorten `additionalInstructions`; add focused fewshots for the failing intent |
| Slow `execute` on semantic model | Materialize hot measures, add aggregation tables, verify Direct Lake isn't falling back to DirectQuery |
| Slow `execute` on KQL | Materialize hot aggregations, add update policies, check function complexity |
| Slow `execute` on Lakehouse/Warehouse | Add `OPTION (RECOMPILE)` hint, check statistics, partition large fact tables |
| Orchestrator % > 50% with fast tools | Likely cold start — accept on first turn, monitor subsequent turns |
| Orchestrator % > 50% with many tool calls | Chain of fewshot + nl2code + execute is normal; ignore if total < 15s |
| Schema re-discovery (`getschema` ×N) | Cache schema (function signatures + key tables/columns) inside `additionalInstructions` |
| Retry loop (same tool + args ×3) | Add a fewshot covering this exact intent; clarify expected output in instructions |
| Thread pollution (≥50 msgs) | DELETE the thread before each question (see `fabric-essentials.md` user memory) |

---

## Cross-Turn Analysis (multi-turn diagnostics)

For diagnostics with multiple turns:

- **Avg response time** — exclude cached turns
- **Max response time** — flag the worst turn for investigation
- **Slowest tools across all turns** — top 3 by total accumulated time
- **Failed-turn rate** — `count(status != "completed") / count(turns)`
- **Cache hit rate** — `count(is_cached) / count(turns)`

Visualization-wise (out of scope for the CLI analyzer but useful in dashboards): a per-turn
bar chart colored by status (completed / failed / cached) plus a Gantt timeline of tool calls
chained from `runs[].created_at`.

---

## Reference Tools

- **CLI**: [`The_AI_Skill_Analyzer/analyzer/diagnose.py`](../../../The_AI_Skill_Analyzer/analyzer/diagnose.py) — `analyze_diagnostic()` returns a structured `latency` dict; `format_report()` prints the breakdown section above; `diff_diagnostics()` compares before/after.
- **Streamlit UI**: [pawarbi/data-agent-inspector](https://github.com/pawarbi/data-agent-inspector) — interactive visual inspector with Gantt timelines, per-turn drill-down, ERD view for semantic models. Same underlying logic; useful when sharing findings with non-technical stakeholders.

---

## Quick Parsing Recipe (Python)

```python
def attach_latency(steps, raw_json):
    """Mutate steps in place with true latency from latency.tool_calls."""
    lat_map = {}
    for src in (raw_json.get("latency") or {}, (raw_json.get("thread") or {}).get("latency") or {}):
        for tc in (src.get("tool_calls") or []):
            sid, dur = tc.get("step_id"), tc.get("duration_seconds")
            if sid and dur is not None:
                lat_map[sid] = float(dur)
    for s in steps:
        if s.get("id") in lat_map:
            s["latency_duration_s"] = lat_map[s["id"]]
    return steps


def compute_overhead(steps, runs):
    tool_total = sum((s.get("latency_duration_s") or s.get("duration_s") or 0) for s in steps)
    run_total = sum((r.get("completed_at", 0) - r.get("created_at", 0)) for r in runs if r.get("completed_at") and r.get("created_at"))
    overhead = max(0.0, run_total - tool_total)
    return {
        "tool_total_s": round(tool_total, 2),
        "run_total_s": round(run_total, 2),
        "orchestrator_overhead_s": round(overhead, 2),
        "orchestrator_pct": round(overhead / run_total * 100, 1) if run_total else None,
    }
```

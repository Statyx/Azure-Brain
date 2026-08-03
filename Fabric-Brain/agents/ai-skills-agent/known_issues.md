# Known Issues — Data Agent Gotchas & Workarounds

---

## Data Source Binding

| Issue | Symptom | Workaround |
|-------|---------|------------|
| Data source not attached after API creation | Agent says "I don't have access to any data" | Add datasource.json via `updateDefinition` or attach manually in portal |
| Wrong artifactId | Agent can't find tables | Verify ID with `GET /v1/workspaces/{wsId}/items?type=SemanticModel` |
| Elements array ignored | Agent sees all tables despite selection | Element selection may be advisory; agent can still discover full schema |
| Lakehouse type confusion | `lakehouse` vs `lakehouse-tables` | Use `lakehouse-tables` for table-only access (most common) |

## Instructions

| Issue | Symptom | Workaround |
|-------|---------|------------|
| **Missing "always query" rule** | Agent answers some questions from general knowledge with hallucinated data (no DAX query generated) | Add mandatory first instruction: `"ALWAYS query the semantic model using DAX. NEVER answer from general knowledge."` See instruction_writing_guide.md |
| Instructions too long | Agent ignores later sections | Keep under 5,000 chars; move data descriptions to datasource.json |
| Instructions in wrong language | Agent responds in unexpected language | Write instructions in the primary response language |
| Contradictory instructions | Agent behaves inconsistently | Review for conflicts; test each rule independently |
| Instructions not updating | Old behavior persists after update | Ensure you updated the correct stage (draft vs published); clear browser cache |
| No measures list | Agent writes raw aggregations (AVERAGE, SUM) instead of using DAX measures | List key measures in aiInstructions so the orchestrator references them in question reformulation |
| **Low description coverage** | Agent picks wrong columns or tables for queries (wrong measure, wrong join) | Add descriptions to ALL columns and measures in Prep for AI. Models with <50% coverage show significantly worse DAX accuracy. See `ai-skills-analysis-agent/dax_quality_analysis.md` |
| **Descriptions not in diagnostic export** | Prep for AI configs NOT visible in diagnostic JSON — can't audit via API | Check descriptions separately in Power BI Desktop or via MCP `manage_semantic` tool. Diagnostics only show `description: null` for schema elements |

## Few-Shot Examples

| Issue | Symptom | Workaround |
|-------|---------|------------|
| DAX query errors in examples | Agent produces similar broken queries | Validate every query in DAX query view before deploying |
| Measure name mismatch | "Cannot find measure [Revenue]" | Cross-check names exactly against model.bim |
| Too few examples | Agent guesses wrong query patterns | Add at least 8-10 examples covering different patterns |
| Examples don't cover user's questions | Agent falls back to generic queries | Add examples matching real user question patterns |

## Publishing

| Issue | Symptom | Workaround |
|-------|---------|------------|
| Draft works, published doesn't | Published agent gives errors | Ensure published/ folder has same parts as draft/ |
| Missing publish_info.json | Publish state unclear | Add `publish_info.json` with schema 1.0.0 and description |
| Published version out of date | Users see old behavior | Re-run updateDefinition with both draft/ and published/ parts |

## API Issues

| Issue | Symptom | Workaround |
|-------|---------|------------|
| **Thread pollution (context overflow)** | After ~50 accumulated messages, runs fail with `BadRequest: OpenAI request to 'openai/threads/{id}/runs' failed`. Agent only returns `fewshots.loading` step, skips DAX entirely, answers from stale cached context | **DELETE the thread before each question** using `DELETE /threads/{id}` with `api-version` param only (no `stage`). Then `POST /threads` to get a fresh one. See `../../fabric_api.md` Thread Management section |
| **Thread DELETE rejects `stage` param** | `400 BAD_REQUEST: Query parameter 'stage=sandbox' is not supported` | Use only `api-version=2024-02-15-preview` on DELETE calls. All other endpoints require `stage` |
| **Run shows `completed` but no DAX** | Agent answers correctly-sounding but stale data (e.g., 112 rows when model has 104K) | Thread pollution — agent uses prior Q&A context instead of querying the model. Verify by checking run_steps: if only 1 step (`fewshots.loading`) instead of 6, the thread is polluted |
| 202 with no body | Seems like nothing happened | This is normal — poll `x-ms-operation-id` until Succeeded |
| `/operations/{id}/result` endpoint hangs | SSL read timeout on `api.fabric.microsoft.com` | Use the `Location` header redirect URL instead (e.g., `wabi-west-us3-a-primary-redirect.analysis.windows.net`). For `updateDefinition`, skip result fetch entirely — just poll status |
| Location header URL also hangs for updates | SSL timeout on result fetch | For `updateDefinition` operations, don't fetch the result — just confirm status is "Succeeded" |
| "CorruptedPayload" error | 400 Bad Request | Validate JSON before base64-encoding; check for unicode issues |
| "ItemDisplayNameAlreadyInUse" | Cannot create agent | Delete existing agent first or use a different name |
| Rate limiting (429) | Too many requests | Respect `Retry-After` header; add delays between API calls |
| getDefinition returns encrypted | Can't read definition | Report has sensitivity label with encryption; cannot retrieve via API |

## Publishing & M365 Copilot

| Issue | Symptom | Workaround |
|-------|---------|------------|
| **Draft-only agent not visible** | Agent exists in workspace but can't be opened/tested in portal | **CRITICAL**: You MUST publish. Add `published/` parts + `publish_info.json`. Draft-only agents are invisible in the portal UI |
| No public API for M365 Copilot toggle | Cannot enable "Share with M365 Copilot" via REST | Portal-only: Data Agent → Settings → M365 Copilot toggle. No REST API as of 2025-06 |
| Publish via API | Need to publish agent programmatically | Include `publish_info.json` + duplicate draft parts into `published/` folder. Use `updateDefinition` with all 8 parts |
| Published version out of date | Users see old behavior | Re-run updateDefinition with both draft/ and published/ parts |
| Draft works, published doesn't | Published agent gives errors | Ensure published/ folder has same parts as draft/ |
| Missing publish_info.json | Publish state unclear | Add `publish_info.json` with schema 1.0.0 and description |

## Portal vs API Differences

| Feature | Portal | REST API |
|---------|--------|----------|
| Create agent | ✅ UI wizard | ✅ POST /items |
| Set instructions | ✅ Text editor | ✅ stage_config.json |
| Add data source | ✅ Browse & select | ⚠️ Must know artifactId/workspaceId |
| Add few-shots | ✅ Interactive Q&A | ✅ fewshots.json |
| Publish | ✅ One-click | ✅ Add published/ parts + publish_info.json |
| Test agent | ✅ Chat interface | ❌ No API chat endpoint yet |
| Select elements | ✅ Checkbox tree | ✅ elements array in datasource.json |

**Key insight**: The portal is better for testing and element selection. The API is better for automation and version control. Use both.

---

## Debugging Checklist

When a Data Agent doesn't work as expected:

1. **Check thread pollution**: Are run_steps showing only 1 step (`fewshots.loading`)? → Delete the thread and retry
2. **Check data source**: Is the correct semantic model/lakehouse attached?
3. **Check instructions**: Are they in the right stage (draft vs published)?
4. **Check few-shots**: Do all queries execute correctly in DAX query view?
5. **Check names**: Do measure/column names match the model exactly (case-sensitive)?
6. **Check permissions**: Does the agent's identity have read access to the data source?
7. **Check capacity**: Is the workspace on a Fabric capacity that supports Data Agents?
8. **Try in portal**: Open the agent in Fabric portal and test interactively
9. **getDefinition round-trip**: Retrieve the definition and verify all parts are present

## Pipeline Trace (run_steps) — What a Healthy Run Looks Like

A healthy Data Agent run produces **6 tool_calls steps**:

```
1. analyze.database.fewshots.loading   → Loads few-shot examples
2. analyze.database.fewshots.matching  → Matches question to examples  
3. analyze.database.nl2code            → Generates DAX query (output: ```dax ... ```)
4. trace.analyze_semantic_model        → Executes query against model
5. analyze.database.execute            → Returns query results (markdown table)
6. generate.filename                   → Names output file
```

**Red flags:**
- Only 1 step (`fewshots.loading`) → Thread pollution or agent error
- `nl2code` output empty → Question too ambiguous or no matching fewshots
- `execute` output has error → DAX syntax error (check `==` vs `=`, measure names)
- Run status `failed` with `server_error` → Thread has too many messages

---

## The run lock is per AGENT, not per thread (3 Aug 2026)

**Context:** Fabric Data Agent, `POST /threads/{id}/runs`, api-version `2024-05-01-preview`.

**Symptom:** A run is created and immediately fails with
`{"code":"invalid_prompt","message":"Status code BadRequest: A run is already in progress
for this thread. Please wait for it to complete before starting a new one."}`
— **on a thread that was just created and has never had a run**.

**Root cause:** the agent serialises runs across the whole item. The message names the
thread, which is misleading: creating a fresh thread does not obtain a fresh lock.

**Fix:** wait and re-run. Do **not** purge the thread — the block is not on it, and
`DELETE /threads/{id}` can kill a run another caller is mid-way through. Budget the wait
from measurement, not from the message: 6 attempts × 25 s covered the case below.

**Evidence:** same question, same agent, three consecutive attempts —
`t+0s` refused (thread A), `t+45s` refused on **thread B, brand new**, `t+150s` answered
normally. Deleting threads in between changed nothing.

**Correction to the "Red flags" entry above (`server_error` → thread has too many
messages):** that is one cause, not the only one, and the two need opposite cures. A run
that holds this lock makes *every* subsequent question fail with no answer, which looks
identical to thread pollution from the outside. They are separable only by reading
`last_error` on the run:

| `last_error` contains | Cause | Cure |
|---|---|---|
| `already in progress` | per-agent run lock | **wait**, same thread |
| `server_error` / empty | polluted sticky thread | `DELETE /threads/{id}`, retry once |

Polling only `status` collapses both into "failed, no answer" and the wait can never be
chosen. Fetch `last_error` in the same poll.

**Cost of not knowing this:** a cascade of failures across every question was diagnosed as
a *damaged agent item*, on the strength of a control that seemed decisive — a throwaway
agent built from the **same definition** answered in 2 s. It answered because it had no run
in flight, not because the production item was broken. A delete-and-recreate of a healthy
item was attempted on that basis. **Before concluding an item is damaged, confirm no run
is in flight on it.**

## The agent invents enum values it reads in the question (3 Aug 2026)

**Context:** Data Agent over an Ontology (GQL) and a semantic model (DAX). Applies to both.

**Symptom:** a valid query returns zero rows and the agent reports it as a finding —
*"no customer is at risk"*, *"no support interaction was recorded"*. Nothing in the run
looks wrong: routing is correct, traversal is correct, status is `completed`.

**Root cause:** the generated filter uses a literal **borrowed from the question**, not one
that exists in the data. Observed twice in one session:
`LOWER(lifecycle_stage) = LOWER("at risk")` where the stored value is `at_risk`, and
`interaction_type = "support"` where the column only holds call/email/chat/ticket/meeting —
"support" appeared in the user's phrasing and was treated as data.

**Fix:** state the domain of every enumerated column in `aiInstructions` — the exact
values, and explicitly **deny** the plausible-but-absent ones by name. Also resolve
homonyms: "customers at risk" matched both a lifecycle state and a segment *named* "At
Risk", and the agent silently answered on the segment for one question and the state for
another. Add: if a filter on an enumeration returns zero rows, re-run once without the
filter before reporting an absence. Generate the value lists from the source of truth
(config / generator) so the instructions cannot drift from the data.

**Evidence:** the exact failing question ("quels comptes B2B concentrent le plus
d'interactions **support** négatives") returned "aucune interaction de ce type" before the
rule and a ranked list of accounts after it, definition re-read from Fabric to confirm the
rule shipped (13 parts, 83 802 chars).

**Why this one is dangerous:** an empty result is indistinguishable from a real answer. It
does not fail, it does not warn, and it is most likely to hit precisely the domain terms a
demo is built around.

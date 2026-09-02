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
| **Missing "always query" rule** | Agent answers some questions from general knowledge with hallucinated data (no query generated) | Add a mandatory first instruction naming **the source's own query language** — DAX for `semantic_model`, SQL for `lakehouse-tables`, T-SQL for `data_warehouse`, KQL for `kusto`, GQL for `ontology`. Naming DAX on a non-semantic-model source does not work. Table in instruction_writing_guide.md |
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
### Two questions asked at once come back with each other's answers

**Context:** Fabric Data Agent, OpenAI-compatible assistants API
(`/v1/workspaces/{ws}/dataAgents/{id}/aiassistant/openai`), 3 Aug 2026. A portal with four
personas, all backed by ONE data agent.

**Symptom:** two questions posted 0.4s apart both return **HTTP 200**, both complete, and
**both answers are about the second question**. Nothing reports an error. The first
question, asked on its own, answers correctly.

**Root cause:** `POST /threads` is **sticky** - it hands back the same thread id to every
caller until that thread is DELETEd. Both user messages therefore land in the same thread
*before* either run starts, and each run answers the newest message it finds there. The
run then also picks its datasource for that other question: a counting question that
answers from the semantic model when asked alone was routed to the ontology when it
overlapped a graph question.

**Fix:** serialise. Admit one question at a time per agent, with a lock held across the
whole exchange (post message -> create run -> poll -> read messages). This costs nothing
real: the service already refuses concurrent runs on one agent
("A run is already in progress for this thread"), so the wait happens either way.

**Does NOT fix it:** matching the assistant reply by `run_id`. That correctly attributes
the reply to your run - but your run was fed the wrong prompt, so the attribution is right
and the answer is wrong. Per-caller threads do not help either while `POST /threads` stays
sticky.

**Evidence:** both calls HTTP 200 at 54.6s with answers about question 2; question 1 alone
-> "Il y a 825 clients a risque de churn." Server log shows the overlapping run using
`trace.analyze_ontology` where the solo run used `trace.analyze_semantic_model`. After
serialising, same input: Q1 correct at 12.8s, Q2 queues and answers its own question at
48.9s.

**Why this one is dangerous:** it is not an outage. The caller gets a confident,
well-formed, plausible answer to a question nobody asked, and every status code says
success. On stage it is indistinguishable from a correct answer.

## An ambiguous question makes the agent pick a different column each run (5 Aug 2026)

**Context:** Fabric Data Agent over a semantic model, driven repeatedly from a Foundry
supervisor over MCP. Nothing about the defect is Foundry-specific — supervision is only what
made it **visible**.

**Symptom:** the same question, asked four times in a row, with no change to the agent, the
model or the data:

| Run | Answer |
|---|---|
| 1 | **825** |
| 2 | **593** |
| 3 | **825** |
| 4 | **825** |

Every run is `completed`. Every run generates valid DAX. Every run returns a non-empty,
plausible, correctly-formatted business number.

**Root cause:** the question ("*combien de clients à risque ?*") is satisfied by **two
different legitimate columns**, and nothing in it chooses between them:

| Reading | Filter | Rows |
|---|---|---|
| the **score band** | `risk_band` ∈ {High, Critical}, i.e. score ≥ 65 | **825** |
| the **lifecycle state** | `lifecycle_stage = 'at_risk'` | **593** |

Both columns exist. Both are populated. Both answers are *correct* for their reading. The
agent re-decides which one it means on every run, and never says which it chose.

For reference, the bands in that model: Prospect · Low 0–39 · Medium 40–64 · High 65–84 ·
Critical 85–100.

**This is NOT the "invents enum values" entry above.** They look similar and need different
cures:

| | Invented enum (3 Aug) | Ambiguous column (5 Aug) |
|---|---|---|
| Filter value | **does not exist** in the data | exists, twice over |
| Result | **0 rows** | two different non-empty results |
| Deterministic? | yes — always wrong the same way | **no** — flips between runs |
| How you notice | an absence that contradicts the demo | **you don't**, unless you ask twice |
| Cure | declare the domain, deny absent values | **declare the default reading** |

**Fix — in the agent, not in the question.** Telling the presenter to phrase it better does not
survive a live demo:

1. In `aiInstructions`, pin the **default reading** for every business term that maps to more
   than one column. Literally: *"« client à risque » means `risk_band` ∈ {High, Critical}. It
   does NOT mean `lifecycle_stage = 'at_risk'`, which is a separate lifecycle concept — use it
   only when the user says «  cycle de vie » or « lifecycle »."*
2. State the **band boundaries** in the same place, so the score threshold can't drift either.
3. Add a few-shot example for each reading, so both paths are demonstrated rather than inferred.
4. Require the agent to **name the column it filtered on** in its answer. A number with its
   definition attached is auditable; a bare number is not.

**Detection — cheap, and nobody does it:** ask every demo question **three times** and diff the
answers. That is the whole test. This defect was found for free because a supervisor asked the
same downstream question on every run; a human asks once and believes the number.

**Evidence:** four consecutive runs returning 825 / 593 / 825 / 825 on an unchanged agent. The
answer becomes **stable immediately** once the question names the band explicitly — which
confirms ambiguity as the cause rather than caching, thread pollution or a flaky model.

**Why this one is dangerous:** there is no error, no empty result and no warning — the two
answers differ by 232 customers on the same question, and **both are defensible**. Ambiguity in
a business term is not a phrasing problem, it is missing metadata; the agent will resolve it
silently and differently every time until someone writes the default down.


---

## A run reports its own pipeline steps, not the data sources it read (2 Sep 2026)

**Context:** Fabric Data Agent over a Lakehouse + Eventhouse, `POST /threads/{id}/runs` then
`GET /runs/{id}/steps`, api-version `2024-05-01-preview`. Six real captures, Sep 2026.

**Symptom:** a UI that shows the room *which data was consulted* renders the agent's internals:

```
Read from  generate.filename · analyze.database.execute · analyze.database.fewshots.matching
           · trace.analyze_ontology · analyze.database.nl2code · trace.analyze_semantic_model
```

**Root cause — two mistakes, and the second is the dangerous one.**

1. The step names are the ones already documented under *Pipeline Trace* above. What is easy to
   assume, and wrong, is that a run *also* reports `itemReference.itemType` (`Lakehouse`,
   `KQLDatabase`, `SemanticModel`…). It does not. Across **six captures on two agents, zero runs
   returned a single `itemReference`.** A label map keyed on item types therefore never matches
   and every name falls through raw.

2. **Four of the six steps read nothing.** `generate.filename`, `analyze.database.nl2code`,
   `fewshots.loading` and `fewshots.matching` are the agent *preparing* to look — naming a file
   and turning a question into a query. Only these three touch data:

   | Step | What it actually read |
   |---|---|
   | `analyze.database.execute` | ran the generated query against the bound source |
   | `trace.analyze_ontology` | consulted the ontology / graph |
   | `trace.analyze_semantic_model` | consulted the semantic model |

   So `len(toolsFired)` is **not** a source count. An answer that never reached `execute` still
   fires 3–4 steps, and a UI counting them will tell the room it read from four places when it
   read from none. That is the exact failure a "what was consulted" badge exists to prevent, and
   counting steps *inverts* it.

**Fix:**

1. Classify every step name explicitly — a data-reading step gets an operator-facing label, a
   scaffolding step is dropped. Keep pass-through for genuinely unknown names (a true name beats
   an invented one), but **assert in a test that nothing in your recorded runs is unclassified**,
   or pass-through silently becomes the default path.
2. Filter scaffolding **before** the "nothing was consulted" check, so an answer that only
   prepared correctly falls through to the warning instead of claiming sources.
3. Do not translate `trace.analyze_semantic_model` etc. by hand into demo prose — see the
   vocabulary note below.

**Evidence:** six captured runs, `toolsFired` per run — 4, 4, 4, 6, 6, 7 steps; `itemReference`
absent from all six. Runs that fired 4 steps and runs that fired 7 both reached `execute` exactly
once.

---

## The agent narrates its own plumbing, and you cannot edit the answer (2 Sep 2026)

**Context:** same six captures. Answers frozen ahead of a demo and replayed verbatim.

**Symptom:** a recorded answer reads *"no further non-zero pause entries appear in the slice
returned by the **semantic model**"*. The sentence ships to the screen naming the storage layer,
in a console whose whole premise is operator language.

**Root cause:** the prompt named tables and columns (correctly — that is how you stop the agent
guessing) but said nothing about the **register of the write-up**, so the agent narrated its
retrieval as part of the story.

**Fix — change the question, never the answer.** A frozen answer that is hand-edited is no longer
evidence, and hardcoded prose is worse than no grounding because it still looks sourced. Append a
register instruction to the prompt and re-capture:

> *"Report it the way a duty manager briefs the operations room: name devices, sites, cells and
> customers rather than tables, models or systems."*

**Watch the phrasing of that instruction.** The first attempt — *"never name the storage, the
model or the tooling that produced the answer"* — was read by the agent as a constraint on its
**behaviour**: it returned in 29.5 s having consulted **nothing**. Reworded to describe the
*write-up* rather than forbid the *tooling*, the same question ran 139.4 s and fired 7 steps.
Phrase the constraint as a reporting style, never as a prohibition that mentions tools.

**Evidence:** same opener, three consecutive captures — original prompt 177.2 s / 7 steps /
leaked "semantic model"; "never name the tooling" 29.5 s / **0 steps** / refused as unsourced;
"report it the way a duty manager briefs the room" 139.4 s / 7 steps / clean.

---

## A non-merging capture script silently deletes a good recording (2 Sep 2026)

**Context:** a script that pre-records demo answers, refusing any run that consulted nothing.

**Symptom:** an answer captured successfully in 67.8 s with 4 steps was **gone** after the next
run. No error; the run that replaced it was correctly refused.

**Root cause:** two safe-looking decisions that are lethal together.

- The agent is **non-deterministic** — the same question returned 4 steps in 67.8 s, then 0 steps
  in 11.6 s minutes later, unchanged.
- The script started from an **empty map** each invocation and rewrote the whole file. So refusing
  the bad run also discarded the good recording already on disk, and `--only <id>` wiped every
  answer it was not asked to refresh.

The refusal rule was working perfectly. It is the *write* that lost the data.

**Fix:** load the existing file and merge, so a run can only **add** an answer or **replace one
with a newer sourced answer**. Losing a recording must take deleting the file on purpose.

**But merge alone strands entries.** The bank is keyed by the prompt text, so editing a prompt —
exactly what the vocabulary fix above requires — does not update its entry, it orphans the old one
under the old key. A stranded answer can never be served (the key no longer exists) yet still
ships in the bundle and still reads as demo copy. So prune against the **whole** question
registry, never the `--only` subset, or refreshing one question evicts the rest.

**Evidence:** `rca-culprit` — 67.8 s / 4 steps, then 11.6 s / 0 steps on an unchanged agent. After
the merge fix, a single-question re-capture left the other five answers byte-identical and dropped
one stranded key, logged explicitly.

**Generalises beyond capture scripts:** any cache in front of a non-deterministic producer, where
the writer validates before persisting, has this shape. Validation decides what to *keep*; it must
never decide what to *erase*.

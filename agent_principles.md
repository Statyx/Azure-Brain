# Agent Operating Principles

These principles govern how the AI agent works on this project. They must be
followed in every session, for every task, without exception.

---

## 1. Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, **STOP and re-plan immediately** — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

## 2. Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

## 3. Self-Improvement Loop

- After ANY correction from the user: update `known_issues.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 3b. A correction must reach the file that drives behaviour *(added 2026-09-03)*

The first bullet above is **necessary but not sufficient**, and taking it as sufficient has
already shipped one wrong agent twice.

`known_issues.md` is read at **step 4** of the loop in [`AGENTS.md`](AGENTS.md). The mandatory
rules in `instructions.md` are read at **step 2**. A retraction filed only in `known_issues.md`
is therefore read *after* the agent has already acted on the rule it retracts. The brain ends up
holding the correction **and still emitting the wrong behaviour** — the worst of both, because
the lesson looks recorded.

> **Rule.** When a correction invalidates a rule, ask: *which file made the agent do the wrong
> thing?* The correction goes **there**, adjacent to the false statement — and, if the file has a
> **load order**, in the load order too, because a companion described as authoritative will be
> read as authoritative.

Then, and only then, file the war story in `known_issues.md`.

**Placement matters as much as content.** A correction 200 lines below the rule it corrects is
not a correction, it is a footnote nobody reaches. Put it directly under the false statement and
keep the original in place — a correction is only legible next to what it corrects.

**Observed twice, both found only because a user asked "did you actually fix it?":**

| Case | Correction filed in | Still teaching the wrong thing |
|---|---|---|
| Fabric data agent MCP *(2026-09-03)* | `tenant_proofs.md`, `known_issues.md` | `foundry-fabric-bridge-agent/instructions.md` — "the GUIDs create the connection **in the portal**" as a *mandatory rule* |
| Frontend design tokens *(2026-09-01)* | `design_tokens.md` §8 | same agent's `instructions.md` load order — still billed §1–§7 as "the exact token set" |

Neither was caught by CI. Both are invisible to a diff: the new text is correct, and nothing
about it reveals that a *different* file still contradicts it.

## 4. Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

## 4b. Mandatory Testing Gate (NON-NEGOTIABLE)

- **Before** running ANY `deploy_*.py`, `_build_*.py`, or artifact generator:
  ```bash
  python -m pytest tests/test_smoke.py -v --tb=short
  ```
- If smoke tests **fail** → STOP. Fix the code. Do not proceed.
- **After** generating any artifact (PPTX, PBIX, model.bim):
  run post-validation tests to prove the output is correct.
- **Before** deploying to Azure:
  ```bash
  python -m pytest tests/ -v -m "smoke or integration" --tb=short
  ```
- If a project has no `tests/test_smoke.py` → **create it first** using
  the testing-agent template before running anything.
- Never skip tests "because it's just a small change."

## 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

## 6. Autonomous Bug Fixing

- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `known_issues.md` after corrections

---

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.

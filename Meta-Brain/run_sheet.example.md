# Run sheet — {Demo name}

> Copy this file into the **demo repository** as `RUN.md` and fill it in as you go.
> It is the journal of *one* demo. The model it came from lives in
> [`SCENARIOS.md`](https://github.com/Statyx/Azure-Brain/blob/main/Meta-Brain/SCENARIOS.md).
> At the end, walk §5 and push what you learned back into the brain — that is what makes the
> next demo cheaper.

| | |
| --- | --- |
| **Date** | YYYY-MM-DD |
| **Audience / story** | e.g. "operations manager, Zava plant 3" |
| **Preset** | `digital-twin` — or `custom` |
| **Formula** | `B1 + B2 + M-ONTO + M-DL + M-AGENT` |
| **Brain commit** | `git rev-parse --short HEAD` in Azure-Brain |

---

## 1. Axes

| Axis | Value | Why |
| --- | --- | --- |
| industry | manufacturing | |
| storyline | single culprit — *gate 7 saturates conveyor B, blocks orders X and Y* | the whole demo points at this |
| volume | demo | |
| capacity | F2 | |
| report format | PBIR | |
| identity | interactive | |
| naming | proposed-and-confirmed | names agreed before the first item was created |

## 2. Environment

Resource IDs are **not** written here — they live in the gitignored
`Fabric-Brain/resource_ids.md`. Record only what identifies the run:

| | |
| --- | --- |
| Workspace name | `{Project}-Demo` |
| Capacity SKU | F2 |
| Region | |

**Names confirmed with the caller** *(fill in at the naming gate, before the first item is
created — a late rename is the expensive kind, see `naming_conventions.md` § Rule 0)*:

| What | Proposed | Confirmed / overridden |
| --- | --- | --- |
| Workspace | | |
| Company / project token | | |
| Reports | | |
| Data agent(s) | | |

## 3. Progress

Tick as the gate passes, not as the step starts.

### Base

- [ ] B_ step 1 — gate:
- [ ] B_ step 2 — gate:
- [ ] …

### Modules

- [ ] `M-____` — gate:
- [ ] `M-____` — gate:

## 4. Deviations

One line per thing that did not go as the model says. This is the only section that matters
afterwards — be specific enough that someone else could reproduce the fix.

| # | Step | What the model says | What I actually did | Type |
| --- | --- | --- | --- | --- |
| 1 | | | | `fix` / `better-every-time` / `customer-only` / `new capability` |

**Types** — they decide where the line goes in §5:

- `fix` — a step failed and you found the workaround
- `better-every-time` — you changed a step and it should become the norm
- `customer-only` — a one-off for this audience
- `new capability` — you ran something the model does not describe at all

## 5. Promotion — push it back into the brain

Do this **before** you forget, ideally the same day.

| Deviation type | Destination | Done |
| --- | --- | --- |
| `fix` | the agent's `known_issues.md` | ☐ |
| `better-every-time` | edit the step in `SCENARIOS.md` (base or module) | ☐ |
| `customer-only` | stays here — nothing to do | ☑ |
| `new capability` | new module in `SCENARIOS.md` §2.3, or a new preset line in §1 | ☐ |
| The combination worked well and has no name | new preset line in `SCENARIOS.md` §1 | ☐ |

Then run the gate in the brain:

```bash
cd Meta-Brain
python -m pytest tests/ -v --tb=short
python tools/scan_public_safety.py ..
```

## 6. Retrospective

- **What landed** (the moment the room reacted):
- **What fell flat**:
- **Total time vs the estimate**:
- **Would I run this preset again as-is?**

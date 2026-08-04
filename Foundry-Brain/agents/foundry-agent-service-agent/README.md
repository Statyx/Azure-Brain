# foundry-agent-service-agent

**Authoring and operating individual Microsoft Foundry agents** — instructions, tools, versions,
and the contract each agent exposes to the rest of the system.

Start here when you need to *write an agent*. Go to `foundry-orchestration-agent` when you need
to *connect several*.

## Files

| File | What it is |
|---|---|
| [`instructions.md`](instructions.md) | The agent. Rules, the five roles, decision trees, the agent object as observed, error recovery. |
| [`prompt_templates.md`](prompt_templates.md) | **Copy-paste skeletons** for all five roles + a workflow wiring skeleton + a review checklist. |
| [`known_issues.md`](known_issues.md) | Traps, and what has actually been observed vs. read. |

## The three things people get wrong

**1. Writing the prompt before choosing the model.**
The model *gates which tools exist*. `Code interpreter` sits greyed out with *"This tool doesn't
work with the model you selected"* — a constraint found in no documentation. Design tools first
and you can end up with an agent that cannot be built.

**2. Treating the output format as style.**
In an observed system, routing is a literal string equality in YAML:
`=Last(Local.Var3365).Text = "Inventory-Agent"`. That is why the router's prompt insists on *"no
quotes, no extra whitespace, no newline"* — it is a **type contract**. Reword it politely and
routing fails silently, with no error and no log line.

**3. Believing the prompt enforces anything.**
*"Execute only if explicitly authorized"* is a **default**, not a control. Real enforcement is
the tool set you attach plus the platform's **tool-approval gate**, which pauses the run and
shows a human the concrete call — `GetDirectReportsDetails({"userId": "…", "select": "…"})` —
with `Approve once` / `Always approve this tool` / `Always approve all tools` / `Deny`.

## The five roles, in one table

| Role | Tools | Output | Read by |
|---|---|---|---|
| Router | none | one bare agent name | a string equality |
| Wrapper | exactly one | rigid `label : value` | another agent |
| Action | 1–3, scoped | one-line confirmations | another agent |
| Synthesizer | **none** | prose + one follow-up | **the human** |
| Resolver | one, identity-scoped | JSON | another agent, by contract |

**The through-line: output shape follows the consumer.** Machine reads it → rigid. Human reads
it → prose. Everything else in a prompt serves that decision.

See a complete seven-agent system using all five:
[`../../reference_workflow.md`](../../reference_workflow.md).

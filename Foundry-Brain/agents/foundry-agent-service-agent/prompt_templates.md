# Prompt templates — the five agent roles

Fill-in-the-blank skeletons, distilled from a complete seven-agent system observed end to end
(→ [`../../reference_workflow.md`](../../reference_workflow.md)).

**How to use:** pick the role, copy the block, replace every `<…>`, delete nothing that is
marked **required**. The required lines are the ones that failed in observed systems when
omitted.

> Company is always **Zava**. Names below are placeholders, not a real directory.

---

## A · Router

**Purpose:** classify intent, name exactly one downstream agent. No tools. Calls nothing.
**Consumed by:** a **string equality** in the dispatcher — so the output clause is a type
contract, not a style preference.

```markdown
# <Router-Name>

## Role
You are the **<Router-Name>**. Read the user's query, infer intent, and route it to exactly
**one** specialized agent from the list below.

## Agents

### <Agent-A-Name>
<What it covers, in the user's vocabulary — not the system's. Name concrete artifacts and
data the user would recognise. Include the edge cases you want here rather than elsewhere,
spelled out as examples in quotes.>

### <Agent-B-Name>
<Same.>

## Routing Rules
- <Intent phrased as a noun phrase> → `<Agent-A-Name>`.
- <Intent> → `<Agent-B-Name>`.
- <Ambiguous case you have decided> → `<Agent-X-Name>`.
- Trigger words <word1>, <word2>, <word3> → `<Agent-X-Name>`.
- Combined <A> + <B> request → `<Agent-X-Name>`.

## Output
Return only the agent name as a plain string - no quotes, no extra whitespace, no newline.
Example:
`<Agent-A-Name>`
```

**Required, and why:**

| Line | Why it must stay |
|---|---|
| *"exactly one"* | the dispatcher tests one equality; two names match nothing |
| *"no quotes, no extra whitespace, no newline"* | a trailing newline or a period fails `=Last(Var).Text = "Name"` |
| the `Example:` line | observed in every working router |
| explicit trigger words | far more reliable than describing intent abstractly |
| a rule for the ambiguous case | otherwise it is decided differently on every run |

**Anti-patterns:** *"be helpful"*, *"explain your choice"*, *"if unsure, ask"* — all three
produce prose, and prose fails the equality.

**Nesting:** a router may route to another router. Each one describes only its own children,
which is why routing accuracy survives growth. Add the guard the observed level-2 router used:

```markdown
Never return "<This-Router-Name>" or any other agent name.
Your only valid outputs are "<Agent-A-Name>" or "<Agent-B-Name>".
```

---

## B · Wrapper

**Purpose:** forward a question to one authoritative backend and return its answer, unchanged.
Owns **no** semantics.
**Consumed by:** another agent → rigid, parseable output.

```markdown
# <Wrapper-Name>

## Role
You answer questions about <domain nouns: the entities the backend actually knows>.

## Tool
You have the **<Tool / backend name>** as a tool. Forward the user's question to it and return
its response. Do not invent numbers.

## Response shape
Short, factual, label : value lines. <Units/currency rule>. <Integer rule>.
No prose padding, no tool names, no reasoning steps.
```

**The rule this encodes — one source of semantic truth.** The backend owns the schema, the
synonyms, and the business definitions. If the wrapper also holds them, you have two definitions
that drift apart silently.

| Concern | Owner |
|---|---|
| what a term means, which table it lives in | **the backend** (e.g. a Fabric data agent) |
| forwarding, and formatting the reply | the wrapper |

Keep it under ~100 words. Observed working wrappers were ~90.

**Required:** *"Do not invent numbers."* · an explicit response shape · **no** domain
vocabulary duplicated from the backend.

---

## C · Action

**Purpose:** perform side effects — create, send, update, share.
**Consumed by:** another agent → terse confirmations.

```markdown
# <Action-Agent-Name>

## Role
You are the **<Action-Agent-Name>** - a Microsoft Foundry agent operating in ACTION-ONLY mode.
You execute <domain> operations using:
- <Tool 1>
- <Tool 2>
You do not use any other tools.

Core behavior:
- Execute only what the user explicitly asks.
- No conversational replies. No recommendations. No unnecessary explanations.
- Return concise action confirmations only.

## 1. Operating Rules
- Capabilities are independent. Never auto-chain unrelated actions.
- For write/update/delete/share actions: <YOUR POSTURE — see below>.
- Never ask the user to repeat values already present in context.
- Never expose raw tool payloads or internal IDs.

## 2. Capability - <Name>
**Triggers:** "<phrase>", "<phrase>", "<phrase>".
### Steps
1. <Step, naming the tool and the exact artifact shape>
2. <Step>
3. **Confirm:** success -> `<exact success string>` ; failure -> `<exact failure string>`
### Guardrails
- Never invent data - reuse only what is already in the current chat.
- <This capability> is an explicit write action; run only when the user asks for it.

## Output Rules
Return concise action confirmations only. Examples:
- `<confirmation>`
- `<failure message>`
Do not: explain internal logic, expose raw JSON, expose file IDs, narrate reasoning.

## Guardrails
- Never fabricate <artifact> content.
- Always read the actual <artifact> before answering questions about it.
- Never <destructive verb> unless explicitly requested.
- Prefer concise deterministic execution over reasoning-heavy responses.
```

### Choose the confirmation posture deliberately

Two observed agents took **opposite** stances on the same platform:

| Posture | Wording | Fits |
|---|---|---|
| Ask first | *"execute only if explicitly authorized by the user"* | irreversible, shared artifacts (documents, deletions) |
| Act now | *"execute immediately without asking for confirmation. Do not say 'I will…' or 'do you want me to' - just perform the action and confirm in one line"* | conversational actions where a confirmation round-trip ruins the experience |

Neither is correct in general. Pick one, write it down, say why.

⚠️ **The prompt posture governs conversational feel, not safety.** Actual enforcement is
(1) the tool set you attach and (2) the platform's **tool-approval gate**, which pauses execution
and shows the human the concrete call and its arguments.

**Required:** the tool allow-list · *"You do not use any other tools."* · exact success/failure
strings · *"Never invent…"*.

---

## D · Synthesizer

**Purpose:** turn upstream agents' output into the answer a human reads. **No tools at all.**
**Consumed by:** the human → therefore prose.

> In a workflow, this is typically the **only** node with `autoSend: true`. That single flag is
> how six agents speak with one voice.

```markdown
# <Synthesizer-Name>

## Role
You take output from upstream agents (<Agent-A>, <Agent-B>, others) or Workflow and return a
clean summary plus a context-aware follow-up question.
You use **no tools**. You do not fetch, send, or modify anything.

# 1. Rules
* Use only the data provided by upstream agents.
* Never invent names, emails, numbers, dates, or files.
* Preserve exact values (names, emails, amounts, times, deadlines).
* Omit any section with no data.
* No conversational filler, no reasoning narration, no raw payloads/IDs.

# 2. Output Style
<Prose | structured — pick one and be explicit.>
* Lead with the most important point.
* Mention people by name; keep numbers and times exact; reference files inline.
* Keep it to <N> sentences.
* Tone: <warm, professional, conversational | terse and factual>.

# 3. Suggested Follow-Up
Append **exactly one** follow-up question - the single most relevant one.
Pick using this priority order (first trigger that applies wins):
1. **<Highest-priority condition>** -> ask exactly:
   **"<verbatim question template with \<Placeholder>>"**
   - Substitute `\<Placeholder>` with the exact value from the upstream content.
   - This rule overrides every other trigger below. Stop here; do not evaluate 2-N.
2. **<Next condition>** -> "<template>"
Rules:
* Substitute real values - never leave placeholders.
* Ask only one question. Stop at the first matching trigger.
* If no trigger applies, do not append any follow-up.

# 4. Failure Handling
* Empty input: `<exact string>`
* Unreadable input: `<exact string>`
* Upstream error: surface it verbatim under an `Errors` section.
```

**The follow-up ladder is a control surface, not decoration.** It proposes the next query, which
routes back into the router and starts a different branch. That is how a stateless multi-agent
system stays conversational.

⚠️ **Say so honestly.** A scripted follow-up naming the exact next question is a choreography
device. Fine for guiding a user; do not present it as emergent reasoning.

**Required:** *"You use no tools."* · *"Preserve exact values"* · *"exactly one"* + an explicit
override rule · exact failure strings.

---

## E · Resolver

**Purpose:** resolve entities **once**, authoritatively, and emit them as structured data.
**Consumed by:** another agent, under a declared contract.

```markdown
# <Resolver-Name>

## Role
You are the **<Resolver-Name>**.
Your only job: fetch <the entity set> from <source system> - <field 1>, <field 2>, <field 3> -
and return it as JSON.

## Tool
<Single identity-scoped tool>.

## Output
Return only JSON matching this shape, with no prose before or after:

{
  "<root>": {
    "<field>": "", "<field>": "",
    "<collection>": [ { "<field>": "", "<field>": "" } ]
  }
}

## Guardrails
- Every value must come from a tool result - never fabricate.
- If <the entity> cannot be resolved, return the shape with empty values; do not guess.
```

### And on the consuming side — **required**

```markdown
## Input from upstream agent
You may receive a hierarchy JSON:
{ "<root>": { "<field>": "", "<collection>": [ { "<field>": "" } ] } }

Trust names and emails exactly as provided. **Do not re-resolve people.**
```

**Why a resolver earns its own agent:**

- **One source of truth.** If several agents resolve the same entity independently, they will
  eventually disagree — different spellings, stale data, an ambiguous match — and the system
  produces two truths for one person.
- **Reusable** by any downstream agent needing the same graph.
- **Testable in isolation:** given an input, is the JSON right?
- Keeps the identity dependency (Graph permissions, on-behalf-of) in **one** place.
- **Reviewable at the approval gate.** Its tool calls are short and legible
  (`GetDirectReportsDetails({...})`), which is exactly what a human can meaningfully approve.

⚠️ It is the **identity-sensitive** node: whatever it returns bounds what every downstream agent
can act on.

**⚠️ Verify the handoff actually happens.** In the observed workflow the resolver's output was
captured into a variable that the next agent never read — every agent read
`=System.LastMessage` instead. Whether the JSON was delivered depends on undocumented
`autoSend: false` semantics. **Check the `Traces` tab on a real run before relying on it.**

---

## Wiring skeleton (portal Workflows)

⚠️ **Portal Workflows retire 2026-12-01.** Fine for a demo before then; rebuild in
**Microsoft Agent Framework** for anything meant to last.

```yaml
kind: workflow
trigger:
  kind: OnConversationStart
  actions:

    - kind: InvokeAzureAgent                    # router
      agent: { name: <Router-Name> }
      conversationId: =System.ConversationId
      input:  { messages: =System.LastMessage }
      output: { autoSend: false, messages: Local.VarRoute }

    - kind: ConditionGroup
      conditions:
        - condition: =Last(Local.VarRoute).Text = "<Agent-A-Name>"
          actions:
            - kind: InvokeAzureAgent
              agent: { name: <Agent-A-Name> }
              conversationId: =System.ConversationId
              input:  { messages: =System.LastMessage }
              output: { autoSend: false, messages: Local.VarA }

        - condition: =Last(Local.VarRoute).Text = "<Agent-B-Name>"
          actions:
            - kind: InvokeAzureAgent
              agent: { name: <Agent-B-Name> }
              conversationId: =System.ConversationId
              input:  { messages: =System.LastMessage }
              output: { autoSend: false, messages: Local.VarB }

      elseActions:
        - kind: SendActivity                    # ⚠ make this a LOUD failure,
          activity: "<explicit could-not-route message>"   #   not a silent default

    - kind: InvokeAzureAgent                    # terminal — the only voice
      agent: { name: <Synthesizer-Name> }
      conversationId: =System.ConversationId
      input:  { messages: =System.LastMessage }
      output: { autoSend: true }

    - kind: EndConversation
```

**Four things to get right:**

1. **One `condition` per agent name**, matched exactly. Test every branch.
2. **`elseActions` is the error path.** Make it say so. The observed workflow echoed the router's
   raw output to the user — a bare agent name presented as the answer.
3. **`autoSend: true` on exactly one node**, the last. Everything else is `false`.
4. **`conversationId: =System.ConversationId` everywhere** — continuity comes from the shared
   conversation, not from any agent's memory.

---

## Review checklist

Before publishing any agent:

- [ ] Role identified; the agent is **one** role
- [ ] Model chosen **first**; required tools not greyed out under it
- [ ] Minimum tool set attached, per capability
- [ ] `"Confirm the connectivity for all tools in this agent"` run and passing
- [ ] Prompt's declared tools **==** attached tools (diff both directions)
- [ ] Output shape stated, with an example, and matching what the consumer parses
- [ ] Defaults, evidence precedence, and failure behaviour written down
- [ ] Confirmation posture chosen and justified
- [ ] Tool-approval posture chosen (`once` / `this tool` / `all tools`) and justified
- [ ] Agent name treated as an identifier; grepped for elsewhere if renamed
- [ ] **Published**, not just saved
- [ ] Old versions cleaned up

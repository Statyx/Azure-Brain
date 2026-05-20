# Instruction Writing Guide — How to Write Great Data Agent Instructions

This is the **most important file** for Data Agent quality. The `aiInstructions` field in `stage_config.json` is the system prompt that shapes every response the agent produces.

---

## Why Instructions Matter

- A Data Agent without instructions is a general-purpose LLM pointing at your data — it has **no business context**
- Good instructions = accurate answers, correct terminology, proper formatting
- Bad instructions = hallucinated metrics, wrong joins, confused users
- **Without the mandatory "always query" rule**, the orchestrator may skip the DAX tool entirely and answer questions from general knowledge with fabricated data

---

## Mandatory Instructions (Include in EVERY Agent)

Before writing domain-specific content, every Data Agent instruction **MUST** include these rules:

```markdown
CRITICAL RULES:
1. ALWAYS query the semantic model using DAX to answer questions. NEVER answer from general knowledge or generate fictional numbers.
2. If you cannot find the data in the model, say so. Do not invent results.
3. Use existing DAX measures whenever possible instead of raw column calculations.
```

**Why this is mandatory**: The orchestrator LLM decides whether to call the DAX tool or answer from its own knowledge. Without rule #1, questions like "top 5 campaigns by revenue" may be answered with hallucinated campaign names and figures that look plausible but are completely fabricated — with no DAX query executed at all.

**Real-world evidence** (Marketing360 Agent, March 2026):

| Without these rules | With these rules |
| ------------------- | ---------------- |
| Q5 "top 5 campaigns by revenue": No DAX query. Hallucinated 5 campaign names with fake revenue figures. | Q5: 39-line DAX using SUMMARIZECOLUMNS + TOPN + [Total Revenue] measure. Real data from model. |

### Available Measures List

After the critical rules, **list all key DAX measures** available in the model. This helps the orchestrator reference them when reformulating questions:

```markdown
AVAILABLE MEASURES (use these, do not recalculate):
- Revenue: [Total Revenue], [Avg Order Value], [Revenue YTD]
- Orders: [Total Orders], [Orders per Customer]
- Customers: [Active Customers], [Churn Rate %]
```

The orchestrator reformulates user questions before sending them to the DAX tool. When it knows about `[Total Revenue]`, it can reformulate "what's our revenue?" into "Calculate [Total Revenue] for 2025" — which helps the DAX tool select the right measure.

---

## The 7-Section Framework

Every Data Agent instruction should follow this structure:

### Section 1: Role & Persona

Define WHO the agent is and what it does. This anchors the LLM's behavior.

```markdown
## Role
You are a **Finance Controller** expert, assistant to the CFO.
You help with P&L analysis, budget vs actual comparisons, variance explanations,
cash flow monitoring, and performance drivers identification.
```

**Best Practices:**

- Be specific: "Finance Controller" > "data analyst" > "helpful assistant"
- State the audience: "assistant to the CFO" sets the expertise level
- List the domains: helps the LLM scope its answers

### Section 2: Available Data

Describe the tables, their purpose, and approximate scale. The agent can discover schema, but descriptions help it choose the RIGHT tables.

```markdown
## Available Data

### Finance Tables
- `chart_of_accounts` — Chart of accounts (150 accounts)
- `general_ledger` — General ledger entries (~50,000 entries)
- `cost_centers` — Cost centers (13 CCs)
- `budgets` — Monthly budgets (~2,000 rows)

### Business Tables
- `customers` — Customer master (500 customers)
- `products` — Product catalog (50 products)
- `invoices` — Invoice headers (8,000 invoices)
- `invoice_lines` — Invoice line items (~20,000 lines)
```

**Best Practices:**

- Include row counts — helps the LLM understand data scale
- Group tables by domain — makes it easier to find the right source
- Describe relationships implicitly: "Invoice headers" and "Invoice line items" suggests a parent-child join
- Don't list every column — the agent can discover schema; focus on purpose

### Section 3: Key Metrics & Calculations

This is **critical**. Define how to calculate every important metric. Without this, the agent will guess — and guess wrong.

```markdown
## Key Metrics

### Revenue & Profitability
- **Total Revenue**: SUM(invoice_lines[line_total_eur])
- **Gross Margin %**: (Revenue - COGS) / Revenue × 100
- **EBITDA**: Revenue - COGS - Operating Expenses
- **Net Profit %**: Net Profit / Revenue × 100

### Budget Analysis
- **Budget Variance**: (Actual - Budget) / Budget × 100
- **Favorable Variance**: Actual < Budget (for expenses)
- **Unfavorable Variance**: Actual > Budget (for expenses)

### Cash Metrics
- **DSO**: (Accounts Receivable / Revenue) × 365
```

**Best Practices:**

- Use exact column/measure names from the semantic model
- Specify direction: "Favorable = Actual < Budget **for expenses**" (revenue is opposite)
- Include the formula, not just the name
- Cover edge cases: "If Revenue = 0, return N/A for margin"

### Section 4: Response Format Rules

Control HOW the agent presents data. Consistency builds user trust.

```markdown
## Response Format

### For KPIs:
Metric: Value
Example: Revenue: 31.2M€
         Gross Margin: 71.5%

### For Comparisons:
Budget vs Actual:
- Budget: X€
- Actual: Y€
- Variance: Z% (Favorable/Unfavorable)

### For Rankings:
Top 3 [element] by [criterion]:
1. Name: Value
2. Name: Value
3. Name: Value
```

**Best Practices:**

- Define templates for each answer type (KPI, comparison, ranking, trend)
- Specify currency format (€, $, M/K suffixes)
- Specify percentage precision (1 decimal: 71.5%, not 71.4832%)
- Tell the agent when to use tables vs bullet lists

### Section 5: Terminology Standards

Ensure consistent language across all responses.

```markdown
## Terminology

Use these terms consistently:
- **Revenue** (not "sales", "CA", or "turnover")
- **COGS** (Cost of Goods Sold)
- **Opex** (Operating Expenses)
- **EBITDA** (Earnings Before Interest, Taxes, Depreciation, Amortization)
- **DSO** (Days Sales Outstanding)
- **AR** (Accounts Receivable)
- **Favorable** / **Unfavorable** (not "positive"/"negative" for variances)
```

**Best Practices:**

- Define the canonical term for each concept
- List what NOT to use (eliminates ambiguity)
- Match the terminology to the audience (CFO-level = finance jargon OK)

### Section 6: Drill-Down Patterns

Tell the agent HOW to analyze "why" questions — this prevents shallow answers.

```markdown
## Drill-Down Analysis

When asked "why" something changed, analyze by:
1. **Product** (category, sub-category)
2. **Customer** (segment, individual)
3. **Region** (cost center region)
4. **Period** (month, quarter)
5. **Cost Center** (department)

Always provide:
- The magnitude of the change
- The top 2-3 contributing factors
- A comparison to the prior period
```

**Best Practices:**

- Define the drill-down dimensions relevant to your domain
- Specify the depth of analysis expected
- Tell the agent to quantify contributions (not just "marketing increased")

### Section 7: Scenario-Specific Guidance (Optional but Powerful)

Pre-program responses for known business scenarios. This is what differentiates a good agent from a great one.

```markdown
## Known Scenarios

### Scenario: Margin Decline
When gross margin drops > 3 points quarter-over-quarter:
- Check discount rates (discount_pct column)
- Check product mix (more services vs licenses?)
- Check average unit price trends
- Report the delta and top 3 contributing factors

### Scenario: Budget Overrun
When actual > budget by > 15%:
- Identify the cost center(s) driving the overrun
- Break down by account category
- Highlight one-time vs recurring costs
```

---

## Instruction Length Guidelines

| Agent Complexity | Target Length | Sections |
| --------------- | ------------ | -------- |
| Simple (1 data source, basic queries) | 500–1,000 chars | 1, 2, 3, 4 |
| Medium (multiple tables, calculations) | 1,500–3,000 chars | 1–6 |
| Complex (multi-domain, scenarios) | 3,000–6,000 chars | All 7 |

**Warning**: Instructions beyond ~8,000 characters may be truncated or lose effectiveness. If you need more, focus on:

- Move table schemas to the `datasource.json` descriptions instead
- Move Q&A examples to `fewshots.json` instead
- Keep instructions about BEHAVIOR, not DATA STRUCTURE

---

## Anti-Patterns (What NOT to Do)

| Don't | Why | Do Instead |
| ----- | --- | ---------- |
| Copy-paste the entire schema | Too long, dilutes behavioral instructions | Describe tables briefly, let discovery handle columns |
| Use vague roles ("you are helpful") | LLM defaults to generic behavior | Be specific: "Finance Controller, CFO assistant" |
| Omit calculation definitions | Agent will guess formulas | Define every metric explicitly |
| Write novel-length instructions | Context window saturation | Keep under 5,000 chars, use few-shots for examples |
| Forget negative instructions | Agent does unwanted things | Add "Do NOT..." rules for known failure modes |
| Mix languages inconsistently | Confuses the agent | Pick one primary language for instructions |
| Skip formatting rules | Inconsistent response quality | Define templates for each answer type |

---

## Testing Your Instructions

After deploying, test with these categories:

1. **Simple fact retrieval** — "What is the total revenue?"
2. **Calculation** — "What is the gross margin percentage?"
3. **Comparison** — "Compare Q1 and Q2 revenue"
4. **Ranking** — "Top 5 customers by revenue"
5. **Why analysis** — "Why did margin decrease this quarter?"
6. **Edge case** — "What is the revenue for a product that doesn't exist?"
7. **Ambiguity** — "How are we doing?" (should ask for clarification or give overview)

If any category fails, iterate on the relevant instruction section.

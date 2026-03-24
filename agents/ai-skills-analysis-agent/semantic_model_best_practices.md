# Semantic Model Best Practices for Data Agent

> **Source**: [Semantic model best practices for data agent](https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices)  
> **Tools**: [fabric-toolbox checklist & notebooks](https://github.com/microsoft/fabric-toolbox/tree/main/samples/data_agent_checklist_notebooks)

---

## Critical Insight: Where Instructions Actually Land

```
⚠️  THE #1 MISUNDERSTANDING WITH DATA AGENTS  ⚠️

The DAX generation tool IGNORES Data Agent-level instructions.
It ONLY uses Prep for AI configurations from the semantic model itself.

Data Agent "additionalInstructions" → influence the ORCHESTRATOR (query reformulation + answer formatting)
Prep for AI "AI Instructions"       → influence the DAX GENERATION TOOL (query accuracy)

These are TWO DIFFERENT systems. Both matter, but for different reasons.
```

### What goes WHERE

| Configuration | Set In | Used By | Controls |
|---------------|--------|---------|----------|
| **AI Instructions** | Prep for AI (semantic model) | DAX generation tool | Query accuracy, business terminology, metric preferences |
| **AI Data Schema** | Prep for AI (semantic model) | DAX generation tool | Which tables/columns/measures the AI can use |
| **Verified Answers** | Prep for AI (semantic model) | DAX generation tool | Pre-approved responses to common questions |
| **Data Agent Instructions** | Data Agent config | Orchestrator LLM | Response formatting, cross-source routing, tone, disclaimers |
| **Per-datasource instructions** | Data Agent datasource config | Orchestrator LLM | NOT supported for semantic models |
| **Few-shot examples** | Data Agent config | Orchestrator LLM | Example Q&A pairs for the orchestrator |

### Diagnostic Evidence

In a diagnostic JSON, you can see this split:
- `runs[].instructions` → contains the Data Agent `additionalInstructions` (orchestrator-level)
- `diagnostic_details.nl2sa_request` → the NL2SA request sent to the DAX tool does **NOT** contain those instructions
- The DAX tool uses Prep for AI configs that are **not visible** in the diagnostic export

---

## How the Data Agent Processes a Question (4 Stages)

```
User Question
    │
    ▼
┌─────────────────────────────────┐
│ 1. QUESTION PARSING             │  Azure OpenAI, security, permissions
│    (Orchestrator)               │  Uses: Data Agent instructions
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 2. DATA SOURCE SELECTION        │  Evaluates question vs available sources
│    (Orchestrator)               │  Uses: schema info, AI instructions
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 3. DAX QUERY GENERATION         │  Generates DAX from natural language
│    (DAX Generation Tool)        │  Uses: Prep for AI ONLY
│                                 │  (schema, AI instructions, verified
│                                 │   answers, synonyms, min/max values,
│                                 │   report visual metadata)
│                                 │  ⚠️ IGNORES Data Agent instructions
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 4. RESPONSE FORMATTING          │  Formats results into human text
│    (Orchestrator)               │  Uses: Data Agent instructions
└─────────────────────────────────┘
```

---

## Prep for AI: Three Configuration Components

### 1. AI Data Schema

**What**: Define a focused subset of your model for AI prioritization.  
**Where**: Power BI Desktop or Power BI Service → Home ribbon → Prep data for AI → Simplify data schema

**Rules**:
- Select only tables/columns/measures relevant to the agent's scope
- Must match the tables selected in the Data Agent data source configuration
- Include dependent objects (if a measure references other measures/columns, include them all)
- Use `get_measure_dependencies()` from [Semantic Link Labs](https://github.com/microsoft/semantic-link-labs) to identify dependencies

**Naming Best Practices**:
- Use clear, business-friendly names: `Total Revenue` not `TR_AMT`, `Sales Region` not `DIM_GEO_01`
- For large models, use the [Power BI Modeling MCP server](https://github.com/microsoft/powerbi-modeling-mcp) to auto-generate friendly names

**Example — Resolving Ambiguity**:

| Before | After |
|--------|-------|
| User asks "What were our sales last quarter?" → Model has Total Revenue, Gross Sales, Net Sales, Sales After Returns → AI picks Gross Sales (wrong) | Configure AI data schema to include only Net Sales, exclude the others → same question now correctly returns Net Sales |

---

### 2. Verified Answers

**What**: User-approved visual responses triggered by specific questions. Stored at the **semantic model level** (not report level), so they work across any data agent using the same model.  
**Where**: Power BI Desktop or Power BI Service → Prep data for AI → Verified answers

**How they work with Data Agent**:
- The system does NOT return the Power BI visual itself
- Instead, it uses the visual's properties (columns, measures, filters) to **guide DAX generation**
- When a user asks a question, the system checks for exact or semantically similar matches first

**Configuration Tips**:
- Use **5-7 trigger questions** per verified answer to cover natural variations
- Include both formal and conversational phrasings
- Configure up to **3 filters** for flexible slicing
- If you rename any referenced objects, update and re-save the verified answer
- Hidden columns referenced by verified answers will break them

**Example — Handling Terminology**:

| Before | After |
|--------|-------|
| User asks "Show me performance by territory" → AI interprets "territory" as product category (wrong column) | Create verified answer using regional sales visual with triggers: "sales performance by territory", "sales by territory", "sales across regions" → now consistently returns regional data |

---

### 3. AI Instructions (in Prep for AI)

**What**: Unstructured text guidance that provides business context to the DAX generation tool.  
**Where**: Power BI Desktop or Power BI Service → Prep data for AI → Add AI instructions

**Key Rule**: These are the ONLY instructions the DAX generation tool reads. Data Agent-level instructions are **ignored** for DAX generation.

**Effective Patterns**:

| Pattern Type | Example |
|-------------|---------|
| Time period definitions | "Peak season runs from November through January. Off-season is February through April." |
| Metric preferences | "When users ask about profitability, use the Contribution_Margin measure, not Gross_Profit." |
| Data source routing | "For inventory questions, prioritize the Warehouse_Inventory table over Sales_Orders." |
| Default groupings | "Unless specified otherwise, analyze revenue by fiscal quarter rather than calendar month." |
| Business terminology | "A top performer is a sales rep with Quota_Attainment >= 1.1. Use Rep_Performance table." |

**Limitations**: AI instructions are interpreted by the LLM but **not guaranteed** to be followed. Clear, specific instructions work better than complex or conflicting ones.

---

## Recommended Implementation Workflow (10 Steps)

| Step | Action | Details |
|------|--------|---------|
| **1** | Optimize the semantic model | Star schema, efficient DAX, remove unnecessary columns. Use Best Practice Analyzer and Memory Analyzer notebooks. Add descriptions to tables/columns/measures. |
| **2** | Define AI Data Schema | In Prep for AI → Simplify data schema. Select only relevant objects. |
| **3** | Create Verified Answers | Identify common questions. Use complete trigger phrases (not partial). 5-7 triggers per answer. |
| **4** | Add semantic model to Data Agent | Select same tables as AI Data Schema. |
| **5** | Add AI Instructions | In Prep for AI → Add AI instructions. Business terminology, metric preferences, date defaults. |
| **6** | Prepare report visuals | Descriptive titles. Visual metadata (title, columns, measures, filters) improves AI grounding. |
| **7** | Verify and test DAX | Review generated DAX in each response. If wrong, trace back to which config needs adjustment. |
| **8** | Configure Data Agent instructions | ONLY cross-source guidance: formatting, routing, tone, disclaimers. NOT semantic model-specific rules. |
| **9** | Validate & iterate | Use `fabric-data-agent-sdk` for automated evaluation. Involve stakeholders. |
| **10** | Source control & deployment | Git integration + deployment pipelines across dev/test/prod. |

---

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| **No star schema** | DAX is optimized for star schema. Flat/denormalized tables → inefficient queries | Unpivot wide tables, create fact + dimension tables |
| **Hidden fields in verified answers** | Verified answers referencing hidden columns silently fail | Unhide or restructure |
| **Unnecessary measures included** | Helper/intermediate measures create noise for DAX tool | Include only final business metrics in AI Data Schema |
| **Duplicate measures** | Total Sales, Sales Amount, Revenue → ambiguity | Consolidate or differentiate, exclude duplicates from schema |
| **Non-descriptive names** | `TR_AMT`, `F_SLS`, `DIM_GEO_01` → no context for AI | Use business-friendly names, or add descriptions + synonyms |
| **Implicit measures** | Unpredictable aggregations | Create explicit DAX measures, set correct default summarization |
| **Ambiguous dates** | Order Date, Ship Date, Due Date → AI guesses wrong | Use AI instructions + verified answers to specify defaults |
| **Conflicting instructions** | AI instructions vs verified answer configs → unpredictable behavior | Align all configurations |
| **Skipping schema refinement** | Large models with overlapping fields → low accuracy | Focus AI Data Schema on relevant subset |
| **Overly complex instructions** | LLM doesn't follow, adds latency | Keep instructions focused and specific |
| **SM instructions in Data Agent** | DAX tool ignores them → no impact on query accuracy | Move to Prep for AI. Agent-level = cross-source only. |

---

## Tools & Resources

| Tool | Purpose |
|------|---------|
| [Semantic Model Data Agent Checklist](https://github.com/microsoft/fabric-toolbox/blob/main/samples/data_agent_checklist_notebooks/Semantic%20Model%20Data%20Agent%20Checklist.md) | Step-by-step preparation checklist |
| [Data Agent Utilities Notebook](https://github.com/microsoft/fabric-toolbox/blob/main/samples/data_agent_checklist_notebooks/Data%20Agent%20Utilities.ipynb) | Helper functions for config and testing |
| [Power BI Modeling MCP Server](https://github.com/microsoft/powerbi-modeling-mcp) | Auto-generate business-friendly names |
| [Semantic Link Labs](https://github.com/microsoft/semantic-link-labs) | Programmatic model updates, dependency analysis |
| [Best Practice Analyzer](https://learn.microsoft.com/en-us/power-bi/transform-model/service-notebooks) | Identify data type, cardinality, DAX issues |
| [Prep for AI docs](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-prepare-data-ai) | Official configuration guide |

---

## Diagnostic Audit: Checking Prep for AI Readiness

When analyzing a diagnostic JSON, check these indicators:

| Check | What to Look For | Red Flag |
|-------|------------------|----------|
| **Description coverage** | `elements[].children[].description` | All `null` → model has no descriptions |
| **Measure names** | `display_name` on measures | Cryptic names or typos (e.g., `Churn Rate pourcentage`) |
| **Schema size** | Count tables × columns | >200 elements without schema refinement |
| **is_selected** | Any `is_selected: false` elements | Excluded elements reduce scope but may be needed |
| **Relationship integrity** | `csdl_relationships` | Orphan tables, inactive relationships |
| **Few-shots loaded** | `fewshots.loading` step output | "Loaded 0 fewshots" |
| **Per-DS instructions** | `dataSourceInfo.additional_instructions` | `null` (expected for SM — not supported) |
| **user_description** | `dataSourceInfo.user_description` | `null` (expected for SM — not supported) |

**Important**: Prep for AI configurations (AI Data Schema, Verified Answers, AI Instructions) are **NOT included** in the diagnostic export. You must check them separately in Power BI Desktop or the Power BI Service.

---

## Model Annotations Reference (Programmatic Access)

When configuring Prep for AI programmatically (via MCP PowerBI Model tools or REST API), the key model annotations are:

| Annotation | Format | Purpose |
|-----------|--------|---------|
| `__PBI_VerifiedAnswers` | JSON array | Pre-built DAX queries triggered by matching questions |
| `__PBI_CopilotInstructions` | Plain text | Unstructured guidance for the DAX engine |
| `__PBI_LinguisticSchema` | JSON | Synonyms, entities, language settings |
| `__PBI_TimeIntelligenceEnabled` | `0` or `1` | Auto-scopes ALL questions to current year when `1` |

### Verified Answers Format

```json
[
  {
    "Question": "what is the email open rate",
    "Answer": "The Email Open Rate is a KPI...",
    "Query": "EVALUATE ROW(\"Open Rate\", [Open Rate %])",
    "Description": "Returns the open rate percentage"
  }
]
```

**Tips**:
- Use 5-15 verified answers for the most common/critical questions
- Include variations (e.g., "how many active customers" AND "total active customers")
- The `Query` field must contain valid DAX (EVALUATE statement)
- `Answer` provides the natural language framing around the result

### CopilotInstructions — Disambiguation Rules Pattern

When measures can be ambiguous, add explicit disambiguation rules:

```
CRITICAL DISAMBIGUATION RULES:
- [Active Customers]: NEVER filter by first_seen_at or any date column. This measure counts all currently active customers regardless of when they were acquired.
- Campaign revenue: Use TREATAS pattern to bridge marketing_campaigns to orders via marketing_sends and marketing_events.
- Always prefer using existing measures over writing raw DAX.
```

**Limitation**: CopilotInstructions help guide the DAX engine but do NOT override the orchestrator's time intelligence reformulation. If `__PBI_TimeIntelligenceEnabled=1`, the reformulated prompt may still add date filters before CopilotInstructions are consulted.

### Time Intelligence Trade-off

| Setting | Behavior | Best For |
|---------|----------|----------|
| `__PBI_TimeIntelligenceEnabled=1` | All questions auto-scoped to current year | Time-series heavy models (sales, finance) |
| `__PBI_TimeIntelligenceEnabled=0` | No auto-scoping, user must specify dates | Models with cumulative/all-time metrics |

**Recommendation**: If your model has a mix of time-scoped and all-time measures, consider disabling time intelligence and relying on Verified Answers + CopilotInstructions to handle date scoping explicitly.

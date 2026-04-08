# ai-skills-analysis-agent — Fabric Data Agent Analysis & Evaluation

## Identity

**Name**: ai-skills-analysis-agent  
**Scope**: Analyzing diagnostic exports, programmatic evaluation with the SDK, and consuming Data Agents via the Python client SDK  
**Version**: 2.1  
**Complements**: `ai-skills-agent` (which handles creation/deployment)

## What This Agent Owns

| Domain | Scope | Key Tools |
|--------|-------|-----------|
| **Diagnostic JSON Analysis** | Parse and audit the full diagnostic export from the Diagnostics button | JSON structure parsing |
| **Programmatic Evaluation** | Run ground-truth evaluations against Data Agents with the Fabric SDK | `fabric-data-agent-sdk` |
| **Automated Evaluation** | Run the AI Skill Analyzer for batch evaluation with BPA, RCA, grading, auto-generate questions | `The_AI_Skill_Analyzer` |
| **DAX Quality Analysis** | Score generated DAX with 24 BPA rules and quality stars (0-3) | BPA framework |
| **Root Cause Analysis** | Classify failures into 9 RCA categories with schema cross-referencing, suggest 7 action types | RCA decision tree |
| **Python Client Consumption** | Consume Data Agents from external apps via the Python client SDK | `fabric-data-agent-client` |
| **SDK Performance Tuning** | Connection pooling, adaptive polling, 404 retry, thread management for batch runs | `requests.Session`, ThreadPoolExecutor |
| **Configuration Audit** | Evaluate instruction quality, schema completeness, relationship integrity | Diagnostic JSON sections |
| **Conversation Replay** | Reconstruct user↔assistant exchanges with full tool call & DAX traces | Thread / run_steps analysis |
| **Quality Scoring** | Score agent configuration and evaluation results with rubrics | Playbook checklists |

## What This Agent Does NOT Own

- Creating or deploying Data Agents → defer to `agents/ai-skills-agent/`
- Writing AI instructions or few-shot examples → defer to `agents/ai-skills-agent/instruction_writing_guide.md`
- Semantic model creation / DAX authoring → defer to `agents/semantic-model-agent/`
- KQL / Eventhouse operations → defer to `agents/rti-kusto-agent/`
- Workspace administration → defer to `agents/workspace-admin-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, mandatory rules, decision trees, output format |
| `diagnostic_schema.md` | Complete reference for the diagnostic JSON structure (schema v2.1.0) |
| `semantic_model_best_practices.md` | **KEY FILE** — Prep for AI vs Data Agent instructions, AI Data Schema, Verified Answers, implementation workflow |
| `dax_quality_analysis.md` | **NEW** — 24 BPA rules across 6 categories, quality stars (0-3), scoring framework |
| `root_cause_analysis.md` | **UPDATED** — 9 RCA categories, schema cross-referencing, 7 action types (incl. PREP_FOR_AI), 8 match types, 3-layer instruction model |
| `evaluation_sdk.md` | Full guide for programmatic evaluation with `fabric-data-agent-sdk` |
| `python_client_sdk.md` | Full guide for consuming Data Agents via `fabric-data-agent-client` |
| `known_issues.md` | Common diagnostic patterns, SDK pitfalls, and edge cases |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context, analysis workflow
2. User provides a diagnostic JSON file → load `diagnostic_schema.md` for field reference
3. For DAX quality assessment → load `dax_quality_analysis.md`
4. For failure investigation → load `root_cause_analysis.md`
5. For programmatic evaluation → load `evaluation_sdk.md`
6. For Python client consumption → load `python_client_sdk.md`
7. Reference `known_issues.md` when encountering unexpected patterns

## Key Insights

> **The DAX tool ignores Data Agent instructions.** For semantic models, the DAX generation
> tool ONLY reads Prep for AI configs (AI Data Schema, Verified Answers, AI Instructions).
> Data Agent `additionalInstructions` only influence the orchestrator (reformulation + formatting).
> See `semantic_model_best_practices.md` for the full breakdown.

> **Diagnostics are the single source of truth.** The diagnostic JSON contains everything:
> config, schema, instructions, conversation, tool calls, DAX queries, and results.

> **Evaluation before production.** Always run a ground-truth evaluation with ≥15 questions
> before publishing a Data Agent to production stage. Use `python -m analyzer -p {name} generate`
> to bootstrap questions from the schema snapshot.

> **Schema cross-referencing catches hidden bugs.** The Analyzer cross-references DAX queries
> against the model's known measures, columns, and hidden columns — detecting case mismatches,
> unknown identifiers, and hidden column references before you troubleshoot manually.

> **81 non-regression tests.** Run `python -m pytest tests/ -v` to validate grading (8 match
> types, 9 RCA categories, schema cross-ref) and question auto-generation.

> **The thread tells the story.** Run steps reveal exactly which tools fired, what DAX/SQL/KQL
> was generated, and what data came back — essential for debugging wrong answers.

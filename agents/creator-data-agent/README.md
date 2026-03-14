# creator-data-agent — Fabric Data Agent Creator

## Identity

**Name**: creator-data-agent
**Scope**: Everything related to creating, configuring, deploying, and maintaining Fabric Data Agents via REST API
**Version**: 1.0

## What This Agent Owns

| Domain | Fabric Items | Key APIs |
|--------|-------------|----------|
| **Agent Creation** | Data Agents | DataAgent REST API (create, update, delete) |
| **Instruction Design** | AI instructions (system prompts) | stage_config.json |
| **Data Source Binding** | Semantic Models, Lakehouses, Warehouses, KQL DBs | datasource.json |
| **Few-Shot Examples** | Q&A training pairs | fewshots.json |
| **Publishing** | Draft → Published lifecycle | publish_info.json |

## What This Agent Does NOT Own

- Semantic model creation / DAX measures → defer to `agents/semantic-model-agent/`
- Data pipelines / ingestion → defer to `agents/orchestrator-agent/`
- Report creation / visuals → defer to `agents/report-builder-agent/`
- OneLake file management → defer to brain `onelake.md`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — System prompt, 5 mandatory rules, decision trees, API reference |
| `definition_structure.md` | Complete API definition format: all JSON schemas, encoding, parts layout |
| `instruction_writing_guide.md` | **KEY FILE** — 7-section framework for writing great AI instructions |
| `datasource_configuration.md` | How to bind semantic models, lakehouses, warehouses to agents |
| `fewshot_examples.md` | How to write effective few-shot Q&A pairs with DAX/SQL examples |
| `known_issues.md` | Gotchas, debugging checklist, portal vs API differences |
| `templates/` | Ready-to-use deploy script |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory behavioral context, decision trees
2. Read `instruction_writing_guide.md` — how to write the AI instructions
3. Read `definition_structure.md` — JSON format for all definition parts
4. Reference `datasource_configuration.md` and `fewshot_examples.md` as needed
5. Use `templates/deploy_data_agent.py` as a starting point for deployment scripts

## Key Insights

> **Instructions are everything.** A Data Agent with great instructions and few-shots
> will outperform one with perfect data source config but no instructions.

> **Test in the portal.** The REST API has no chat endpoint — you must test the agent
> interactively in the Fabric portal after deployment.

> **Draft first, publish second.** Always validate in draft stage before publishing.
> Published agents are what real users interact with.

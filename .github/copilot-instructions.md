# Copilot Instructions — Github_Brain

## Role

This repository is a knowledge base for building Microsoft Fabric solutions with GitHub Copilot.
It contains 25 agent definitions, knowledge files, and deployment templates.

## How to Use

1. Read `resource_ids.md` for your workspace and item IDs
2. Read the relevant `agents/*/instructions.md` for your task
3. Follow the agent's rules — they exist because of real failures

## Key Rules

- **Always use Legacy PBIX format** for reports (`report.json` with `sections[].visualContainers[]`). Never PBIR.
- **Read `resource_ids.md`** before any deployment — it has all your workspace/item IDs
- **Read `known_issues.md`** before debugging — most errors are already documented
- **Follow `agent_principles.md`** — config-driven, idempotent, async-first

## Setup for New Users

If `resource_ids.md` doesn't exist:
1. Copy `resource_ids.example.md` → `resource_ids.md`
2. Copy `environment.example.md` → `environment.md`
3. Fill in your Azure subscription, Fabric workspace, and item IDs
4. See `GETTING_STARTED.md` for the full setup guide

## Testing

When modifying agent instructions or shared patterns:
```bash
python -m pytest tests/ -v --tb=short
```

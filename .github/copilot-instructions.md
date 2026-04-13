# Copilot Instructions — Github_Brain

## Role

This repository is the shared knowledge base for all Fabric demo projects.
It contains agent definitions, testing infrastructure, and documentation.

## Mandatory Testing

When modifying any agent instructions, visual_validator.py, or shared patterns:
run the tests in ALL downstream projects to verify nothing breaks:
```bash
python run_all_tests.py
```

## Shared Test Infrastructure

- `agents/testing-agent/instructions.md` — Test patterns and taxonomy
- `agents/testing-agent/visual_validator.py` — Reusable report visual validator
- `run_all_tests.py` — Cross-project test runner

## Downstream Projects

- `Financial_Platform/` — 125 tests (smoke + dryrun + model + report visuals)
- `Fabric RTI Demo/` — 30 tests (smoke + report visuals)
- `The_AI_Skill_Analyzer/` — 81 tests (grading + generation)

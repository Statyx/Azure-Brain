# Shared Constraints

Hard rules that apply to **all** Brain agents. Inspired by multi-agent architecture patterns where shared constraints prevent coordination failures.

---

## 8 Hard Rules

### 1. Configuration-Driven
All industry-specific behavior comes from JSON configuration files, never hard-coded. Adding a new industry/domain means writing configs — not changing agent logic.

### 2. Idempotent Operations
Re-running any generation or deployment step with the same configuration must produce identical output. Never append — always replace or skip-if-exists.

### 3. Read Before Write
Never assume file contents or artifact state. Always load current state (config, existing artifacts, API response) before generating or modifying anything.

### 4. One Owner Per Domain
Each Fabric artifact type has exactly one agent owner. Other agents may read the artifact, but only the owner creates/modifies it. See agent README files for ownership boundaries.

### 5. Handoff Protocol
When completing a step and transitioning to another agent:
- **State what was produced** (artifact names, file paths)
- **Name the next agent** explicitly
- **List affected files** or artifact IDs
- **Provide input** the next agent needs

### 6. Validate After Every Change
After creating or modifying any artifact, verify it exists and is valid before proceeding. For API calls: check the response. For files: read back and confirm.

### 7. Follow Naming Conventions
All Fabric artifacts must follow the naming patterns defined in `agents/project-orchestrator-agent/naming_conventions.md`. Consistent naming enables automation and cross-agent coordination.

### 8. Async-First API Pattern
Every Fabric REST API creation and execution call returns HTTP 202. Always:
- Use `allow_redirects=False` on POST requests
- Poll via `x-ms-operation-id` header
- Handle transient failures with exponential backoff (3s × 2^attempt, max 2 retries)

---

## Python Conventions

- Python 3.12+
- Use `pathlib.Path` for file operations
- UTF-8 encoding everywhere (set `$env:PYTHONIOENCODING = "utf-8"`)
- Type hints on function signatures
- Smallest change possible — don't refactor what you don't own

## PowerShell Conventions

- Use `[System.IO.File]::WriteAllText()` for BOM-free UTF-8 output
- Never use `Out-File` for JSON (adds BOM)
- Use `Invoke-RestMethod` or Python `requests` for Fabric API — never `az rest` from Python

## Git Conventions

- Conventional commits: `feat(energy):`, `fix(core):`, `docs(brain):`
- One logical change per commit
- Don't force-push shared branches

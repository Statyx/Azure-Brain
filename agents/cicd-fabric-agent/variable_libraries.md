# Variable Libraries — Fabric CI/CD

## Overview

A Variable Library is a Fabric workspace item that holds configuration variables consumed by other items. Each variable can have multiple **value sets** — one per deployment stage — so the same notebook, pipeline, or lakehouse shortcut resolves environment-specific values automatically.

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Variable** | A named key with a type (string, integer, boolean, item reference) |
| **Value Set** | A named collection of values for all variables — one per environment (dev, test, prod) |
| **Active Value Set** | The value set currently in effect for the workspace — exactly one is active at a time |
| **Consumer** | A workspace item that reads variables at runtime (Pipeline, Notebook, Lakehouse shortcut, etc.) |

### Structure

```
Variable Library: "EnvConfig"
├── Variable: "lakehouse_id" (item reference)
│   ├── dev:  aaa-aaa-...
│   ├── test: bbb-bbb-...
│   └── prod: ccc-ccc-...
├── Variable: "batch_size" (integer)
│   ├── dev:  100
│   ├── test: 1000
│   └── prod: 50000
└── Variable: "enable_logging" (boolean)
    ├── dev:  true
    ├── test: true
    └── prod: false

Active value set: "dev" (in Dev workspace)
```

---

## Variable Types

| Type | Use Case | Example |
|------|----------|---------|
| **String** | Connection strings, URLs, file paths | `"Server=my-server.database.windows.net"` |
| **Integer** | Batch sizes, thresholds, retry counts | `5000` |
| **Boolean** | Feature flags, logging toggles | `true` |
| **Item Reference** | Lakehouse ID, Warehouse ID, Notebook ID | Points to a specific Fabric item (resolves per workspace) |

---

## Supported Consumer Items

| Item | How to Consume |
|------|---------------|
| **Pipeline** | Reference variables in pipeline expressions and activities |
| **Lakehouse (shortcuts)** | Assign variables to shortcut data sources |
| **Notebook** | `NotebookUtils.variable_library.get("lib_name", "var_name")` or `%%configure` magic |
| **Dataflow Gen 2** | Reference variables in Power Query M expressions |
| **Copy Job** | Use variables in Copy Job source/destination config |
| **User Data Functions** | `get_variables` API in Python programming model |

---

## REST API Operations

### Create Variable Library

```http
POST /v1/workspaces/{workspaceId}/variableLibraries
{
  "displayName": "EnvConfig",
  "description": "Environment-specific configuration"
}
```

### Add Variable

```http
POST /v1/workspaces/{workspaceId}/variableLibraries/{id}/variables
{
  "name": "lakehouse_id",
  "type": "ItemReference",
  "values": {
    "dev": { "itemId": "aaa-...", "workspaceId": "..." },
    "test": { "itemId": "bbb-...", "workspaceId": "..." },
    "prod": { "itemId": "ccc-...", "workspaceId": "..." }
  }
}
```

### Set Active Value Set

```http
PATCH /v1/workspaces/{workspaceId}/variableLibraries/{id}
{
  "activeValueSet": "prod"
}
```

---

## CI/CD Integration

### With Deployment Pipelines

1. Create variable library in Dev workspace with all value sets (dev, test, prod)
2. When pipeline deploys to Test stage → variable library is deployed
3. In Test workspace, set active value set to "test"
4. Deploy to Prod → set active value set to "prod"
5. Consumer items automatically resolve correct values

### With Git Integration

Variable libraries are supported in Git. The definition (names, types, value sets) is version-controlled. The active value set is workspace-specific and NOT stored in Git.

---

## Notebook Consumption Patterns

### Using NotebookUtils

```python
# Read a string variable
connection = notebookutils.variableLibrary.get("EnvConfig", "connection_string")

# Read an item reference
lakehouse_id = notebookutils.variableLibrary.get("EnvConfig", "lakehouse_ref")

# Read an integer
batch_size = notebookutils.variableLibrary.get("EnvConfig", "batch_size")
```

### Using %%configure

```python
%%configure
{
  "variableLibrary": {
    "name": "EnvConfig",
    "defaultLakehouse": "lakehouse_ref"
  }
}
```

---

## Naming Conventions

| Rule | Detail |
|------|--------|
| Library name starts with | Letter (a-z, A-Z) |
| Allowed characters | Letters, numbers, underscores, hyphens, spaces |
| Max length | 256 characters |
| Case sensitivity | Not case-sensitive |
| No duplicates | Variable names unique within a library |

---

## Limitations

| Limitation | Detail |
|------------|--------|
| Max variables per library | 1,000 |
| Max value sets per library | 1,000 |
| Total cells (variables × value sets) | < 10,000 |
| Max library item size | 1 MB |
| Note / description field | Max 2,048 characters |
| Active value set | Exactly one per workspace (can't delete active set) |
| Value set order | Cannot reorder in UI (edit JSON directly) |
| Cross-workspace | Consumer must be in same workspace as variable library |

---

## Cross-References

- Environment promotion: `environment_promotion.md`
- Deployment pipelines: `deployment_pipelines.md`
- Lakehouse shortcuts: `../lakehouse-agent/instructions.md`

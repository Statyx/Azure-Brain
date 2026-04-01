# Source Code Formats — Fabric CI/CD

## Overview

When a Fabric workspace is connected to Git, each item is stored in its own directory with a specific format. Understanding these formats is essential for manual editing, PR reviews, and CI/CD automation.

---

## Directory Naming

Pattern: `{display_name}.{item_type}`

```
repo/
├── Sales.Notebook/
│   ├── .platform
│   └── notebook-content.py
├── Revenue.SemanticModel/
│   ├── .platform
│   └── definition/
│       ├── model.tmdl
│       ├── tables/
│       └── ...
├── Dashboard.Report/
│   ├── .platform
│   ├── definition.pbir
│   └── report.json
└── ETL.DataPipeline/
    ├── .platform
    └── pipeline-content.json
```

### Naming Rules

| Rule | Detail |
|------|--------|
| Pattern | `{displayName}.{PublicFacingType}` |
| Invalid characters | Replaced with HTML number codes |
| Leading space | Replaced with HTML number code |
| Trailing space or dot | Replaced with HTML number code |
| Fallback name | `{logicalId_GUID}.{Type}` if display name is unavailable |
| **Once created, directory name never changes** | Even if you rename the item |
| Dependency awareness | If you manually rename a directory, update all references |

---

## The .platform File (v2)

Every item directory contains a `.platform` file — the system metadata file.

```json
{
  "version": "2.0",
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/platform/platformProperties.json",
  "config": {
    "logicalId": "e553e3b0-0260-4141-a42a-70a24872f88d"
  },
  "metadata": {
    "type": "Report",
    "displayName": "Sales Dashboard",
    "description": "Monthly sales overview"
  }
}
```

### Fields

| Field | Purpose | Rules |
|-------|---------|-------|
| `version` | Platform file version | Always `"2.0"` for current format |
| `config.logicalId` | Cross-workspace item identifier | **NEVER change this** — breaks pairing |
| `metadata.type` | Item type | Case-sensitive — don't modify |
| `metadata.displayName` | Item display name | Can be changed → item gets renamed on sync |
| `metadata.description` | Optional description | Free text |

### Critical Rules

1. **logicalId is sacred** — it connects items across workspaces/branches. Changing it breaks deployment pipeline pairing.
2. **type is case-sensitive** — the exact casing from auto-generation must be preserved.
3. **When duplicating an item** in Git, you MUST change logicalId and displayName to unique values.
4. **Version 1 → 2 migration**: When you commit in v1 format, files auto-upgrade to v2 (`.platform` replaces `item.metadata.json` + `item.config.json`).

---

## Item Definition Files by Type

### Notebook (.Notebook/)

```
MyNotebook.Notebook/
├── .platform
└── notebook-content.py    # Python source code
```

### Semantic Model (.SemanticModel/)

```
Revenue.SemanticModel/
├── .platform
├── definition.pbism
└── definition/
    ├── model.tmdl           # TMDL format
    ├── tables/
    │   ├── Sales.tmdl
    │   └── Calendar.tmdl
    ├── relationships.tmdl
    └── expressions.tmdl
```

> Semantic models use TMDL (Tabular Model Definition Language) in Git, not model.bim.

### Report (.Report/)

```
Dashboard.Report/
├── .platform
├── definition.pbir          # Report identity reference
└── report.json              # Full report definition (legacy format)
```

> Reports in Git use PBIR format by default. For legacy PBIX rendering, see `report_format.md`.

### Pipeline (.DataPipeline/)

```
ETL.DataPipeline/
├── .platform
└── pipeline-content.json    # Activity definitions
```

### Lakehouse (.Lakehouse/)

```
Staging.Lakehouse/
├── .platform
└── lakehouse.json           # Schema definition (tables, shortcuts)
```

### Environment (.Environment/)

```
SparkEnv.Environment/
├── .platform
└── environment-content.json  # Spark config, libraries
```

### Paginated Report (.PaginatedReport/)

```
MonthlyReport.PaginatedReport/
├── .platform
└── definition.rdl           # RDL (Report Definition Language) XML
```

### User Data Functions (.UserDataFunction/)

```
ProcessData.UserDataFunction/
├── .platform
├── function-app.py          # Python function code
├── definitions.json         # Connections and library refs
└── resources/
    └── functions.json       # Metadata (don't edit manually)
```

---

## Folders and Subfolders

Workspace folders are preserved in Git:

```
repo/
├── Finance/
│   ├── Revenue.SemanticModel/
│   └── Dashboard.Report/
├── Operations/
│   ├── ETL.DataPipeline/
│   └── Notebook.Notebook/
```

- Max directory depth: 10 levels
- Folder structure syncs bidirectionally (workspace ↔ Git)
- Deploying content with folders preserves the folder hierarchy

---

## Important Behaviors

| Behavior | Detail |
|----------|--------|
| **CRLF → LF** | All files committed from service use LF line endings |
| **Unrelated files** | Files not in an item folder are NOT deleted by Git integration |
| **Files inside item folder** | Non-definition files ARE deleted on commit |
| **Enhanced refresh API** | Causes Git diff after each refresh (semantic model) |
| **Renamed column** | Pushed to end of `columns` array in bim file (semantically insignificant) |
| **Max file size** | 25 MB per file |

---

## Cross-References

- Git integration: `git_integration.md`
- Semantic model TMDL: `../semantic-model-agent/model_deployment.md`
- Report format: `../../report_format.md`
- Pipeline definitions: `../orchestrator-agent/pipeline_definitions.md`

# Pipeline Definition Format — Complete Reference

## pipeline-content.json Schema

Every Fabric Data Pipeline definition is a single JSON file with this structure:

```json
{
    "properties": {
        "activities": [],
        "parameters": {},
        "variables": {},
        "annotations": []
    }
}
```

---

## Expression Language

Pipeline expressions use `@` prefix and support functions, variables, parameters, and activity outputs.

### Syntax
```
@pipeline().parameters.myParam          // Pipeline parameter
@variables('myVar')                      // Pipeline variable
@activity('MyActivity').output           // Activity output
@activity('Copy1').output.rowsCopied     // Specific output property
@item()                                  // Current item in ForEach
@concat('prefix_', pipeline().parameters.name)  // String concat
@utcNow()                               // Current UTC time
@formatDateTime(utcNow(), 'yyyy-MM-dd') // Formatted date
```

### Common Functions

| Category | Function | Example |
|----------|----------|---------|
| **String** | `@concat(a, b)` | `@concat('LH_', pipeline().parameters.domain)` |
| **String** | `@replace(str, old, new)` | `@replace(item().name, ' ', '_')` |
| **String** | `@toLower(str)` | `@toLower(pipeline().parameters.table)` |
| **String** | `@substring(str, start, len)` | `@substring(item().name, 0, 3)` |
| **Date** | `@utcNow()` | Current UTC timestamp |
| **Date** | `@addDays(date, n)` | `@addDays(utcNow(), -7)` |
| **Date** | `@formatDateTime(date, fmt)` | `@formatDateTime(utcNow(), 'yyyyMMdd')` |
| **Logic** | `@if(cond, true, false)` | `@if(greater(activity('X').output.rowsCopied, 0), 'OK', 'EMPTY')` |
| **Logic** | `@equals(a, b)` | `@equals(pipeline().parameters.mode, 'full')` |
| **Logic** | `@greater(a, b)` | `@greater(activity('Copy1').output.rowsCopied, 0)` |
| **Logic** | `@and(a, b)`, `@or(a, b)` | `@and(equals(item().type, 'csv'), greater(item().size, 0))` |
| **Collection** | `@length(arr)` | `@length(pipeline().parameters.tables)` |
| **Collection** | `@first(arr)`, `@last(arr)` | `@first(pipeline().parameters.tables)` |
| **JSON** | `@json(str)` | `@json(activity('Web1').output.Response)` |
| **System** | `@pipeline().Pipeline` | Pipeline name |
| **System** | `@pipeline().RunId` | Current run GUID |
| **System** | `@pipeline().GroupId` | Workspace ID |

### Expression in Activity Properties
```json
{
    "typeProperties": {
        "url": "@concat('https://api.example.com/data/', pipeline().parameters.endpoint)",
        "body": {
            "date": "@formatDateTime(utcNow(), 'yyyy-MM-dd')",
            "table": "@pipeline().parameters.table_name"
        }
    }
}
```

---

## Complete Activity Type Reference

### Copy Activity
```json
{
    "name": "Copy_From_Blob",
    "type": "Copy",
    "dependsOn": [],
    "policy": {"timeout": "0.12:00:00", "retry": 2, "retryIntervalInSeconds": 30},
    "typeProperties": {
        "source": {
            "type": "BinarySource",
            "storeSettings": {
                "type": "AzureBlobFSReadSettings",
                "recursive": true
            }
        },
        "sink": {
            "type": "LakehouseSink",
            "tableActionOption": "Overwrite"
        },
        "enableStaging": false
    }
}
```

### SparkNotebook Activity
```json
{
    "name": "Run_NB01_Bronze",
    "type": "SparkNotebook",
    "dependsOn": [{"activity": "Copy_Raw", "dependencyConditions": ["Succeeded"]}],
    "policy": {"timeout": "0.04:00:00", "retry": 1, "retryIntervalInSeconds": 60},
    "typeProperties": {
        "notebookId": "{notebook-guid}",
        "parameters": {
            "source_path": {"value": "Files/raw/sales", "type": "string"},
            "target_table": {"value": "fact_sales", "type": "string"}
        },
        "sparkPool": ""
    }
}
```

### TridentNotebook Activity (Fabric Notebook)
```json
{
    "name": "Run_Fabric_Notebook",
    "type": "TridentNotebook",
    "typeProperties": {
        "notebookId": "{notebook-guid}",
        "workspaceId": "{workspace-guid}"
    }
}
```

### ForEach Activity
```json
{
    "name": "Process_Each_Table",
    "type": "ForEach",
    "typeProperties": {
        "isSequential": false,
        "batchCount": 5,
        "items": {"value": "@pipeline().parameters.tables", "type": "Expression"},
        "activities": [
            {
                "name": "Load_Table",
                "type": "SparkNotebook",
                "typeProperties": {
                    "notebookId": "{nb-guid}",
                    "parameters": {
                        "table_name": {"value": "@item()", "type": "Expression"}
                    }
                }
            }
        ]
    }
}
```

### IfCondition Activity
```json
{
    "name": "Check_Has_Data",
    "type": "IfCondition",
    "typeProperties": {
        "expression": {"value": "@greater(activity('Copy1').output.rowsCopied, 0)", "type": "Expression"},
        "ifTrueActivities": [{"name": "Transform", "type": "SparkNotebook", "typeProperties": {...}}],
        "ifFalseActivities": [{"name": "Log_Empty", "type": "WebActivity", "typeProperties": {...}}]
    }
}
```

### Switch Activity
```json
{
    "name": "Route_By_Type",
    "type": "Switch",
    "typeProperties": {
        "on": {"value": "@pipeline().parameters.source_type", "type": "Expression"},
        "cases": [
            {"value": "csv", "activities": [...]},
            {"value": "parquet", "activities": [...]},
            {"value": "json", "activities": [...]}
        ],
        "defaultActivities": [{"name": "Fail_Unknown", "type": "Fail", "typeProperties": {"message": "Unknown source type", "errorCode": "400"}}]
    }
}
```

### SetVariable Activity
```json
{
    "name": "Set_Start_Time",
    "type": "SetVariable",
    "typeProperties": {
        "variableName": "start_time",
        "value": {"value": "@utcNow()", "type": "Expression"}
    }
}
```

### AppendVariable Activity
```json
{
    "name": "Append_Processed_Table",
    "type": "AppendVariable",
    "typeProperties": {
        "variableName": "processed_tables",
        "value": {"value": "@item().name", "type": "Expression"}
    }
}
```

### Until Activity
```json
{
    "name": "Poll_Until_Ready",
    "type": "Until",
    "typeProperties": {
        "expression": {"value": "@equals(activity('Check').output.status, 'Ready')", "type": "Expression"},
        "timeout": "0.01:00:00",
        "activities": [
            {"name": "Wait", "type": "Wait", "typeProperties": {"waitTimeInSeconds": 30}},
            {"name": "Check", "type": "WebActivity", "typeProperties": {"method": "GET", "url": "..."}}
        ]
    }
}
```

### ExecutePipeline Activity
```json
{
    "name": "Run_Child_Pipeline",
    "type": "ExecutePipeline",
    "typeProperties": {
        "pipeline": {"referenceName": "PL_Child_ETL", "type": "PipelineReference"},
        "waitOnCompletion": true,
        "parameters": {
            "source": {"value": "@pipeline().parameters.source", "type": "Expression"}
        }
    }
}
```

### Fail Activity
```json
{
    "name": "Fail_Pipeline",
    "type": "Fail",
    "typeProperties": {
        "message": {"value": "@concat('Validation failed: ', activity('Validate').output.error)", "type": "Expression"},
        "errorCode": "500"
    }
}
```

### WebActivity
```json
{
    "name": "Notify_Teams",
    "type": "WebActivity",
    "typeProperties": {
        "method": "POST",
        "url": "https://hooks.example.com/webhook",
        "headers": {"Content-Type": "application/json"},
        "body": {
            "text": "@concat('Pipeline ', pipeline().Pipeline, ' completed. Rows: ', string(activity('Copy1').output.rowsCopied))"
        }
    }
}
```

### Lookup Activity
```json
{
    "name": "Get_Config",
    "type": "Lookup",
    "typeProperties": {
        "source": {
            "type": "LakehouseSource",
            "sqlReaderQuery": "SELECT * FROM config_table WHERE is_active = 1"
        },
        "firstRowOnly": false
    }
}
```

### Script Activity
```json
{
    "name": "Run_SQL",
    "type": "Script",
    "typeProperties": {
        "scripts": [
            {
                "type": "Query",
                "text": "SELECT COUNT(*) AS cnt FROM dbo.fact_sales"
            }
        ]
    }
}
```

### DataflowGen2 Activity
```json
{
    "name": "Run_Dataflow",
    "type": "DataflowGen2",
    "typeProperties": {
        "dataflowId": "{dataflow-guid}",
        "workspaceId": "{workspace-guid}"
    }
}
```

---

## Variables

Pipeline variables are mutable state within a run:

```json
{
    "properties": {
        "variables": {
            "start_time": {"type": "String", "defaultValue": ""},
            "row_count": {"type": "String", "defaultValue": "0"},
            "processed_tables": {"type": "Array", "defaultValue": []},
            "is_incremental": {"type": "Boolean", "defaultValue": false}
        },
        "activities": [...]
    }
}
```

Variable types: `String`, `Boolean`, `Array`.

---

## Standard Orchestration Pipeline Template

```json
{
    "properties": {
        "parameters": {
            "workspace_id": {"type": "String"},
            "lakehouse_name": {"type": "String", "defaultValue": "LH_MyProject"}
        },
        "activities": [
            {
                "name": "Load_Bronze",
                "type": "SparkNotebook",
                "typeProperties": {"notebookId": "{nb01-guid}"},
                "dependsOn": []
            },
            {
                "name": "Transform_Silver",
                "type": "SparkNotebook",
                "typeProperties": {"notebookId": "{nb02-guid}"},
                "dependsOn": [{"activity": "Load_Bronze", "dependencyConditions": ["Succeeded"]}]
            },
            {
                "name": "Build_Gold",
                "type": "SparkNotebook",
                "typeProperties": {"notebookId": "{nb03-guid}"},
                "dependsOn": [{"activity": "Transform_Silver", "dependencyConditions": ["Succeeded"]}]
            },
            {
                "name": "Refresh_Model",
                "type": "WebActivity",
                "typeProperties": {
                    "method": "POST",
                    "url": "@concat('https://api.fabric.microsoft.com/v1/workspaces/', pipeline().parameters.workspace_id, '/semanticModels/{model-guid}/refresh')"
                },
                "dependsOn": [{"activity": "Build_Gold", "dependencyConditions": ["Succeeded"]}]
            }
        ]
    }
}
```

---

## Gotchas

1. **Expression `@` conflicts with JSON** — Pipeline expressions starting with `@` must be inside `{"value": "...", "type": "Expression"}` objects
2. **ForEach `batchCount` max is 50** — Default is 20
3. **ForEach `isSequential: true`** ignores `batchCount` — Runs one at a time
4. **`ExecutePipeline` with `waitOnCompletion: false`** — Fire-and-forget; parent doesn't track child status
5. **Pipeline parameters are immutable during run** — Use variables for mutable state
6. **`activity().output` is only available in direct dependents** — Not accessible across parallel branches
7. **Notebook parameters type must be `string`** — Even for numbers; cast in the notebook code
8. **`SparkNotebook` vs `TridentNotebook`** — Both work; `SparkNotebook` has more parameter options
9. **Pipeline timeout format** — `"0.12:00:00"` = 12 hours (days.hours:minutes:seconds)
10. **Cannot reference variables inside ForEach body** — Use `@item()` and parameters instead

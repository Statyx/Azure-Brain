# Model Deployment — model.bim, definition.pbism & REST API

## Overview

A Fabric Semantic Model is deployed as two parts via the REST API:
1. `definition.pbism` — Connection metadata (strict format)
2. `model.bim` — The TMSL model definition (tables, columns, relationships, measures, expressions)

---

## definition.pbism — STRICT FORMAT

**The ONLY accepted format:**
```json
{"version": "1.0"}
```

❌ `datasetReference` → rejected  
❌ `connectionString` → rejected  
❌ `connections` → rejected  
❌ Any additional property → "Property is not defined in the metadata"

---

## model.bim Structure (TMSL)

### Top-Level Skeleton
```json
{
  "compatibilityLevel": 1604,
  "model": {
    "name": "SM_Finance",
    "defaultMode": "directLake",
    "culture": "en-US",
    "tables": [],
    "relationships": [],
    "expressions": [],
    "roles": [],
    "annotations": []
  }
}
```

### Compatibility Levels
| Level | Use Case |
|-------|----------|
| 1604 | Fabric Direct Lake (recommended) |
| 1600 | Power BI Premium |
| 1550 | Azure Analysis Services |
| 1500 | SQL Server 2017+ |

### Model Modes
| Mode | Description |
|------|-------------|
| `directLake` | Reads Delta tables directly — no import, no refresh needed |
| `import` | Data copied into model — requires refresh |
| `directQuery` | Live queries to source — no caching |

**For Fabric Lakehouse: always use `directLake`.**

---

## Table Definition

### Dimension Table
```json
{
  "name": "dim_customers",
  "columns": [
    {
      "name": "customer_id",
      "dataType": "string",
      "sourceColumn": "customer_id",
      "annotations": [
        {"name": "SummarizationSetBy", "value": "Automatic"}
      ]
    },
    {
      "name": "customer_name",
      "dataType": "string",
      "sourceColumn": "customer_name",
      "annotations": [
        {"name": "SummarizationSetBy", "value": "Automatic"}
      ]
    },
    {
      "name": "country",
      "dataType": "string",
      "sourceColumn": "country",
      "annotations": [
        {"name": "SummarizationSetBy", "value": "Automatic"}
      ]
    }
  ],
  "partitions": [
    {
      "name": "dim_customers",
      "source": {
        "type": "entity",
        "expression": "DatabaseQuery",
        "entityName": "dim_customers",
        "schemaName": "dbo",
        "expressionSource": "DatabaseQuery"
      }
    }
  ]
}
```

### Fact Table (with measures)
```json
{
  "name": "fact_general_ledger",
  "columns": [
    {
      "name": "entry_id",
      "dataType": "string",
      "sourceColumn": "entry_id",
      "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    },
    {
      "name": "amount",
      "dataType": "decimal",
      "sourceColumn": "amount",
      "formatString": "#,0.00",
      "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    },
    {
      "name": "entry_date",
      "dataType": "dateTime",
      "sourceColumn": "entry_date",
      "formatString": "yyyy-MM-dd",
      "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    },
    {
      "name": "account_id",
      "dataType": "string",
      "sourceColumn": "account_id",
      "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    }
  ],
  "measures": [
    {
      "name": "Total Revenue",
      "expression": "CALCULATE(SUM(fact_general_ledger[amount]), dim_chart_of_accounts[account_type] = \"Revenue\")",
      "formatString": "#,0.00"
    }
  ],
  "partitions": [
    {
      "name": "fact_general_ledger",
      "source": {
        "type": "entity",
        "expression": "DatabaseQuery",
        "entityName": "fact_general_ledger",
        "schemaName": "dbo",
        "expressionSource": "DatabaseQuery"
      }
    }
  ]
}
```

### Column Data Types

| TMSL `dataType` | Source Types | Format Example |
|-----------------|-------------|----------------|
| `string` | varchar, text, nvarchar | — |
| `int64` | int, bigint | `#,0` |
| `decimal` | decimal, float, money | `#,0.00` |
| `double` | double, real | `#,0.00` |
| `dateTime` | date, datetime, timestamp | `yyyy-MM-dd` |
| `boolean` | bit, boolean | — |

### Column Annotations

Always include `SummarizationSetBy`:
```json
"annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
```

This lets Power BI decide the default aggregation (Sum for numeric, Count for string, etc.).

---

## Partition — Direct Lake Entity Source

For Direct Lake, every table needs one partition with `type: "entity"`:

```json
{
  "name": "table_name",
  "source": {
    "type": "entity",
    "expression": "DatabaseQuery",
    "entityName": "table_name",
    "schemaName": "dbo",
    "expressionSource": "DatabaseQuery"
  }
}
```

**Rules:**
- `entityName` must match the Delta table name in Lakehouse exactly
- `schemaName` is always `"dbo"` for Lakehouse Delta tables
- `expression` and `expressionSource` reference the M expression that connects to the Lakehouse
- Do NOT add `"mode"` property — Direct Lake doesn't use it

---

## M Expression (Data Source Connection)

```json
{
  "name": "DatabaseQuery",
  "kind": "m",
  "expression": [
    "let",
    "    database = Sql.Database(\"eenhbexk3uueboufjqpzd6vyqe-obwdyezgf2lu3kwbr3kchw57gq.datawarehouse.fabric.microsoft.com\", \"LH_Finance\")",
    "in",
    "    database"
  ]
}
```

The SQL endpoint comes from the Lakehouse SQL analytics endpoint.  
Format: `Sql.Database("<sql_endpoint>", "<lakehouse_name>")`

---

## REST API Deployment

### Create Semantic Model (Full)
```python
import base64, json, requests, time

API = "https://api.fabric.microsoft.com/v1"
WS_ID = "133c6c70-2e26-4d97-aac1-8ed423dbbf34"

def deploy_semantic_model(model_bim: dict, display_name: str, headers: dict) -> str:
    """Deploy a semantic model and return the item ID."""
    
    bim_b64 = base64.b64encode(json.dumps(model_bim).encode()).decode()
    pbism_b64 = base64.b64encode(b'{"version": "1.0"}').decode()
    
    body = {
        "displayName": display_name,
        "type": "SemanticModel",
        "definition": {
            "parts": [
                {"path": "definition.pbism", "payload": pbism_b64, "payloadType": "InlineBase64"},
                {"path": "model.bim", "payload": bim_b64, "payloadType": "InlineBase64"},
            ]
        }
    }
    
    resp = requests.post(f"{API}/workspaces/{WS_ID}/items", headers=headers, json=body)
    
    if resp.status_code == 201:
        return resp.json()["id"]
    
    if resp.status_code == 202:
        op_id = resp.headers["x-ms-operation-id"]
        for _ in range(60):
            time.sleep(5)
            op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
            if op["status"] == "Succeeded":
                result = requests.get(f"{API}/operations/{op_id}/result", headers=headers).json()
                return result.get("id", op_id)
            if op["status"] in ("Failed", "Cancelled"):
                raise RuntimeError(f"Deploy failed: {op.get('error', {})}")
        raise TimeoutError("Deploy did not complete in 5 minutes")
    
    raise RuntimeError(f"Unexpected status {resp.status_code}: {resp.text}")
```

### Update Existing Model Definition
```python
def update_semantic_model(model_id: str, model_bim: dict, headers: dict):
    """Update an existing semantic model's definition."""
    
    bim_b64 = base64.b64encode(json.dumps(model_bim).encode()).decode()
    pbism_b64 = base64.b64encode(b'{"version": "1.0"}').decode()
    
    body = {
        "definition": {
            "parts": [
                {"path": "definition.pbism", "payload": pbism_b64, "payloadType": "InlineBase64"},
                {"path": "model.bim", "payload": bim_b64, "payloadType": "InlineBase64"},
            ]
        }
    }
    
    resp = requests.post(
        f"{API}/workspaces/{WS_ID}/semanticModels/{model_id}/updateDefinition",
        headers=headers, json=body
    )
    
    if resp.status_code == 200:
        return True
    
    if resp.status_code == 202:
        op_id = resp.headers["x-ms-operation-id"]
        for _ in range(60):
            time.sleep(5)
            op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
            if op["status"] == "Succeeded":
                return True
            if op["status"] in ("Failed", "Cancelled"):
                raise RuntimeError(f"Update failed: {op.get('error', {})}")
    
    raise RuntimeError(f"Update failed: {resp.status_code} {resp.text}")
```

### Get and Decode Model Definition
```python
def get_model_definition(model_id: str, headers: dict) -> dict:
    """Retrieve and decode a semantic model's model.bim."""
    
    resp = requests.post(
        f"{API}/workspaces/{WS_ID}/semanticModels/{model_id}/getDefinition",
        headers=headers
    )
    
    if resp.status_code == 200:
        parts = resp.json()["definition"]["parts"]
    elif resp.status_code == 202:
        op_id = resp.headers["x-ms-operation-id"]
        for _ in range(60):
            time.sleep(5)
            op = requests.get(f"{API}/operations/{op_id}", headers=headers).json()
            if op["status"] == "Succeeded":
                result = requests.get(f"{API}/operations/{op_id}/result", headers=headers).json()
                parts = result["definition"]["parts"]
                break
            if op["status"] in ("Failed", "Cancelled"):
                raise RuntimeError(f"getDefinition failed: {op.get('error', {})}")
    else:
        raise RuntimeError(f"getDefinition failed: {resp.status_code}")
    
    for part in parts:
        if part["path"] == "model.bim":
            return json.loads(base64.b64decode(part["payload"]).decode())
    
    raise RuntimeError("model.bim not found in definition parts")
```

### Delete Semantic Model
```python
def delete_semantic_model(model_id: str, headers: dict):
    resp = requests.delete(f"{API}/workspaces/{WS_ID}/semanticModels/{model_id}", headers=headers)
    assert resp.status_code == 200, f"Delete failed: {resp.status_code}"
```

---

## Existing Model Reference

| Property | Value |
|----------|-------|
| Name | `SM_Finance` |
| ID | `236080b8-3bea-4c14-86df-d1f9a14ac7a8` |
| Mode | Direct Lake |
| Tables | 11 |
| Relationships | 11 |
| DAX Measures | 26 |
| Lakehouse | `LH_Finance` (`f2c42d3b-d402-43e7-b8fb-a9aa395c14e1`) |
| SQL Endpoint | `eenhbexk3uueboufjqpzd6vyqe-obwdyezgf2lu3kwbr3kchw57gq.datawarehouse.fabric.microsoft.com` |

# Prepare Data for AI — Semantic Model AI-Readiness

## Overview

A semantic model becomes AI-ready when it includes enough metadata for **Copilot**, **Data Agents**, and **Q&A** to understand business meaning, choose correct aggregations, and present results properly. All properties below live in `model.bim` (TMSL JSON) and can be deployed via the REST API `updateDefinition`.

---

## Priority Checklist

| Priority | Action | Property | Impact |
|----------|--------|----------|--------|
| **P0** | Add descriptions to ALL tables, columns, measures | `description` | Copilot & Data Agents need natural language context |
| **P0** | Set `summarizeBy: "none"` on ID/Year/Month columns | `summarizeBy` | Prevents AI from summing non-additive columns |
| **P0** | Use star schema with all relationships defined | `relationships[]` | AI can't join tables without relationships |
| **P1** | Add synonyms to tables, columns, measures | `annotations[].synonyms` | Users say "sales" but field is "Total Revenue" |
| **P1** | Set data categories for geography columns | `dataCategory` | Enables maps, correct "where" handling |
| **P1** | Hide technical columns (IDs, FKs, sort keys) | `isHidden: true` | Reduces noise, improves AI accuracy |
| **P1** | Set proper format strings | `formatString` | AI presents numbers/dates correctly |
| **P1** | Set SortByColumn for month/day names | `sortByColumn` | Correct ordering in AI-generated charts |
| **P2** | Organize measures in DisplayFolders | `displayFolder` | Discoverability for users |
| **P2** | Discourage implicit measures | `discourageImplicitMeasures` | Forces AI to use defined measures |
| **P2** | Add PBI_FormatHint annotations | `PBI_FormatHint` | Locale-aware currency/date display |

---

## 1. Descriptions (`description`)

The **most important** AI-readiness feature. Copilot and Data Agents read descriptions to understand what each field/measure represents.

### JSON Paths
- Table: `model.tables[].description`
- Column: `model.tables[].columns[].description`
- Measure: `model.tables[].measures[].description`

### Example
```json
{
  "name": "dim_customers",
  "description": "Customer master data including company info, segment, region, and payment terms. One row per customer.",
  "columns": [
    {
      "name": "company_name",
      "dataType": "string",
      "sourceColumn": "company_name",
      "description": "Legal company name as registered in the ERP system."
    },
    {
      "name": "credit_limit_eur",
      "dataType": "double",
      "sourceColumn": "credit_limit_eur",
      "description": "Maximum credit in EUR allowed before payment is required."
    }
  ],
  "measures": [
    {
      "name": "Total Revenue",
      "expression": "CALCULATE(SUM(fact_general_ledger[amount]), dim_chart_of_accounts[account_type] = \"Revenue\")",
      "description": "Total revenue from all Revenue-type accounts in the general ledger. Responds to date, customer, product, and cost center filters."
    }
  ]
}
```

### Description Writing Guidelines
- **Tables**: State what the table contains, one row = what?, key business context
- **Columns**: Explain business meaning, not just data type. "Payment terms in days" not "integer field"
- **Measures**: Explain what it calculates, which filters apply, business interpretation
- Keep descriptions concise (1-2 sentences)
- Write for a business user, not a developer

---

## 2. Synonyms (`annotations[].synonyms`)

Synonyms bridge the gap between user vocabulary and model field names.

### JSON Path
Stored as annotations on tables, columns, and measures:
```json
"annotations": [
  {
    "name": "synonyms",
    "value": "[\"revenue\",\"sales\",\"top line\",\"turnover\"]"
  }
]
```

> **Note**: The `value` is a **JSON string containing a JSON array** (double-encoded).

### Example — Table Synonyms
```json
{
  "name": "dim_customers",
  "annotations": [
    {"name": "synonyms", "value": "[\"clients\",\"buyers\",\"accounts\"]"}
  ]
}
```

### Example — Column Synonyms
```json
{
  "name": "company_name",
  "dataType": "string",
  "sourceColumn": "company_name",
  "annotations": [
    {"name": "SummarizationSetBy", "value": "Automatic"},
    {"name": "synonyms", "value": "[\"customer name\",\"client name\",\"account name\"]"}
  ]
}
```

### Example — Measure Synonyms
```json
{
  "name": "Total Revenue",
  "expression": "...",
  "annotations": [
    {"name": "synonyms", "value": "[\"revenue\",\"sales\",\"top line\",\"total sales\",\"turnover\"]"}
  ]
}
```

### Rules
- Avoid assigning the same synonym to multiple columns (creates ambiguity)
- Include common business abbreviations (e.g., "P&L", "COGS", "AR")
- Include both French and English terms if your users speak both languages

---

## 3. Summarization (`summarizeBy`)

Controls default aggregation behavior. **Critical** for preventing AI from summing non-additive columns.

### JSON Path
- `model.tables[].columns[].summarizeBy`

### Values
| Value | When to Use |
|-------|-------------|
| `"sum"` | Amount/currency columns |
| `"count"` | When counting makes sense |
| `"min"` | Date ranges, floor values |
| `"max"` | Peak values |
| `"average"` | Rates, averages |
| `"none"` | **IDs, keys, names, Year/Month/Day columns** |

### Common Mistakes
```
❌ fiscal_year with summarizeBy: "sum"  → AI sums 2024+2025=4049
❌ customer_id with summarizeBy: "sum"  → AI tries to sum text IDs
❌ month_number with default aggregation → AI sums 1+2+3+...+12=78
```

### Fix Pattern
```json
{
  "name": "fiscal_year",
  "dataType": "int64",
  "sourceColumn": "fiscal_year",
  "summarizeBy": "none",
  "annotations": [{"name": "SummarizationSetBy", "value": "User"}]
}
```

---

## 4. Data Categories (`dataCategory`)

Tells AI the semantic type of a column — especially important for geography and visualization.

### JSON Path
- `model.tables[].columns[].dataCategory`

### Values
| Category | Column Type | AI Behavior |
|----------|------------|-------------|
| `Country` | string | Map visual, "where" questions |
| `City` | string | City-level maps |
| `StateOrProvince` | string | State/province maps |
| `PostalCode` | string/int | Zip code |
| `Address` | string | Street address |
| `Latitude` | double | Map coordinate |
| `Longitude` | double | Map coordinate |
| `WebUrl` | string | Rendered as clickable link |
| `ImageUrl` | string | Rendered as image |
| `Barcode` | string | Mobile barcode scanning |

### Example
```json
{
  "name": "country",
  "dataType": "string",
  "sourceColumn": "country",
  "dataCategory": "Country",
  "summarizeBy": "none"
}
```

---

## 5. Hidden Columns & Tables (`isHidden`)

Hide technical columns from users and AI to reduce noise and improve accuracy.

### JSON Paths
- `model.tables[].isHidden`
- `model.tables[].columns[].isHidden`
- `model.tables[].measures[].isHidden`

### What to Hide
- Primary key / foreign key columns (e.g., `customer_id`, `account_id`)
- Sort key columns (e.g., `month_number` when `month_name` is the display column)
- Bridge/junction tables
- Internal calculation helper measures

### Example
```json
{
  "name": "customer_id",
  "dataType": "string",
  "sourceColumn": "customer_id",
  "isHidden": true,
  "summarizeBy": "none"
}
```

For columns that should also be excluded from Excel PivotTables:
```json
{
  "name": "internal_sort_key",
  "dataType": "int64",
  "sourceColumn": "internal_sort_key",
  "isHidden": true,
  "isAvailableInMDX": false,
  "summarizeBy": "none"
}
```

---

## 6. Sort By Column (`sortByColumn`)

Ensures text columns sort in the correct order (e.g., months: Jan → Dec instead of Apr → Aug → Dec).

### JSON Path
- `model.tables[].columns[].sortByColumn`

### Example
```json
{
  "name": "month_name",
  "dataType": "string",
  "sourceColumn": "month_name",
  "sortByColumn": "month_number",
  "summarizeBy": "none"
},
{
  "name": "month_number",
  "dataType": "int64",
  "sourceColumn": "month_number",
  "isHidden": true,
  "summarizeBy": "none"
}
```

### Pattern
The sort-key column should be `isHidden: true` — users see the name, the engine uses the number.

---

## 7. Display Folders (`displayFolder`)

Organize measures and columns into logical business categories.

### JSON Paths
- `model.tables[].measures[].displayFolder`
- `model.tables[].columns[].displayFolder`

### Example
```json
{
  "name": "Total Revenue",
  "expression": "...",
  "displayFolder": "P&L"
},
{
  "name": "Gross Profit",
  "expression": "...",
  "displayFolder": "P&L"
},
{
  "name": "Budget Amount",
  "expression": "...",
  "displayFolder": "Budget"
},
{
  "name": "DSO",
  "expression": "...",
  "displayFolder": "AR & Collections"
}
```

Nested folders use backslash: `"Financial\\P&L\\Revenue Measures"`

---

## 8. Format Strings & PBI_FormatHint

### Common Formats
| Type | `formatString` | Output |
|------|---------------|--------|
| Currency (2 dec) | `#,##0.00` | 1,234,567.89 |
| Currency (no dec) | `#,##0` | 1,234,568 |
| Percentage | `0.00%` | 45.30% |
| Percentage (1 dec) | `0.0%` | 45.3% |
| Integer | `#,##0` | 1,234 |
| Date | `yyyy-MM-dd` | 2025-03-15 |

### PBI_FormatHint Annotation
```json
"annotations": [
  {"name": "PBI_FormatHint", "value": "{\"currencyCulture\":\"en-US\"}"}
]
```

| Purpose | Value |
|---------|-------|
| Currency culture | `{"currencyCulture":"en-US"}` or `{"currencyCulture":"fr-FR"}` |
| General number | `{"isGeneralNumber":true}` |
| Custom date | `{"isDateTimeCustom":true}` |

---

## 9. Model-Level AI Settings

### Discourage Implicit Measures
```json
{
  "model": {
    "discourageImplicitMeasures": true
  }
}
```
Forces Copilot to use **defined DAX measures** instead of auto-generating SUM/COUNT. This ensures consistent, validated calculations.

### Time Intelligence
```json
{
  "model": {
    "annotations": [
      {"name": "__PBI_TimeIntelligenceEnabled", "value": "1"}
    ]
  }
}
```

---

## Python: Add AI Metadata to Existing model.bim

```python
import json, copy

def prepare_model_for_ai(model_bim: dict, metadata: dict) -> dict:
    """
    Enrich a model.bim with AI-readiness metadata.
    
    metadata format:
    {
        "table_name": {
            "description": "...",
            "synonyms": ["...", "..."],
            "columns": {
                "col_name": {
                    "description": "...",
                    "synonyms": ["..."],
                    "dataCategory": "Country",  # optional
                    "isHidden": true,           # optional
                    "summarizeBy": "none",      # optional
                    "sortByColumn": "col_x"     # optional
                }
            },
            "measures": {
                "measure_name": {
                    "description": "...",
                    "synonyms": ["..."],
                    "displayFolder": "P&L"      # optional
                }
            }
        }
    }
    """
    model = copy.deepcopy(model_bim)
    
    for table in model["model"]["tables"]:
        tname = table["name"]
        if tname not in metadata:
            continue
        tmeta = metadata[tname]
        
        # Table description
        if "description" in tmeta:
            table["description"] = tmeta["description"]
        
        # Table synonyms
        if "synonyms" in tmeta:
            _set_annotation(table, "synonyms", json.dumps(tmeta["synonyms"]))
        
        # Column metadata
        col_meta = tmeta.get("columns", {})
        for col in table.get("columns", []):
            if col["name"] not in col_meta:
                continue
            cm = col_meta[col["name"]]
            if "description" in cm:
                col["description"] = cm["description"]
            if "synonyms" in cm:
                _set_annotation(col, "synonyms", json.dumps(cm["synonyms"]))
            if "dataCategory" in cm:
                col["dataCategory"] = cm["dataCategory"]
            if "isHidden" in cm:
                col["isHidden"] = cm["isHidden"]
            if "summarizeBy" in cm:
                col["summarizeBy"] = cm["summarizeBy"]
            if "sortByColumn" in cm:
                col["sortByColumn"] = cm["sortByColumn"]
        
        # Measure metadata
        msr_meta = tmeta.get("measures", {})
        for msr in table.get("measures", []):
            if msr["name"] not in msr_meta:
                continue
            mm = msr_meta[msr["name"]]
            if "description" in mm:
                msr["description"] = mm["description"]
            if "synonyms" in mm:
                _set_annotation(msr, "synonyms", json.dumps(mm["synonyms"]))
            if "displayFolder" in mm:
                msr["displayFolder"] = mm["displayFolder"]
    
    # Model-level: discourage implicit measures
    model["model"]["discourageImplicitMeasures"] = True
    
    return model


def _set_annotation(obj: dict, name: str, value: str):
    """Set or update an annotation on a TMSL object."""
    if "annotations" not in obj:
        obj["annotations"] = []
    for ann in obj["annotations"]:
        if ann["name"] == name:
            ann["value"] = value
            return
    obj["annotations"].append({"name": name, "value": value})
```

### Usage
```python
# Load model
with open("model.bim") as f:
    model_bim = json.load(f)

# Define AI metadata
metadata = {
    "dim_customers": {
        "description": "Customer master data. One row per customer.",
        "synonyms": ["clients", "buyers", "accounts"],
        "columns": {
            "customer_id": {"isHidden": True, "summarizeBy": "none", "description": "Unique customer identifier (PK)."},
            "company_name": {"description": "Legal company name.", "synonyms": ["customer name", "client name"]},
            "country": {"description": "Customer country.", "dataCategory": "Country", "synonyms": ["nation", "region"]},
            "segment": {"description": "Market segment: Enterprise, SMB, or Startup.", "synonyms": ["market segment", "customer type"]}
        }
    },
    "fact_general_ledger": {
        "description": "General ledger entries (journal lines). One row per accounting entry.",
        "measures": {
            "Total Revenue": {
                "description": "Sum of amounts from Revenue-type accounts. Responds to date, customer, product, and cost center filters.",
                "synonyms": ["revenue", "sales", "top line", "turnover"],
                "displayFolder": "P&L"
            },
            "Gross Profit": {
                "description": "Total Revenue minus Total COGS.",
                "synonyms": ["gross margin amount"],
                "displayFolder": "P&L"
            }
        }
    }
}

# Enrich and save
enriched = prepare_model_for_ai(model_bim, metadata)
with open("model.bim", "w") as f:
    json.dump(enriched, f, indent=2)
```

---

## Deploy AI-Enriched Model via API

The enriched model.bim deploys exactly the same way as a standard model:

```python
# getDefinition → enrich → updateDefinition
model_bim = get_model_definition(model_id, headers)
enriched = prepare_model_for_ai(model_bim, metadata)
update_semantic_model(model_id, enriched, headers)
```

No special API or feature flag is needed. All AI metadata is standard TMSL that Fabric accepts in `updateDefinition`.

---

## Validation: Check AI-Readiness

```python
def audit_ai_readiness(model_bim: dict) -> dict:
    """Audit a model.bim for AI-readiness and return issues."""
    issues = {"p0": [], "p1": [], "p2": []}
    
    for table in model_bim["model"]["tables"]:
        tname = table["name"]
        
        # P0: Table description
        if not table.get("description"):
            issues["p0"].append(f"Table '{tname}' has no description")
        
        for col in table.get("columns", []):
            cname = col["name"]
            
            # P0: Column description
            if not col.get("description"):
                issues["p0"].append(f"Column '{tname}.{cname}' has no description")
            
            # P0: ID/Year/Month without summarizeBy=none
            if any(kw in cname.lower() for kw in ["_id", "year", "month", "period"]):
                if col.get("summarizeBy", "sum") != "none":
                    issues["p0"].append(f"Column '{tname}.{cname}' looks like an ID/date-part but summarizeBy != 'none'")
            
            # P1: Geography without dataCategory
            if any(kw in cname.lower() for kw in ["country", "city", "state", "region", "postal"]):
                if not col.get("dataCategory"):
                    issues["p1"].append(f"Column '{tname}.{cname}' looks geographic but has no dataCategory")
            
            # P1: ID column not hidden
            if cname.endswith("_id") and not col.get("isHidden"):
                issues["p1"].append(f"Column '{tname}.{cname}' is an ID but not hidden")
        
        for msr in table.get("measures", []):
            mname = msr["name"]
            
            # P0: Measure description
            if not msr.get("description"):
                issues["p0"].append(f"Measure '{mname}' has no description")
            
            # P2: Measure without displayFolder
            if not msr.get("displayFolder"):
                issues["p2"].append(f"Measure '{mname}' has no displayFolder")
    
    # Model-level
    if not model_bim["model"].get("discourageImplicitMeasures"):
        issues["p2"].append("Model does not set discourageImplicitMeasures=true")
    
    return issues
```

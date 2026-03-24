# Power Query M Expression Library

## Purpose

Reusable M expressions for common data transformations in Dataflow Gen2.
Copy-paste these patterns into mashup documents or the Power Query editor.

---

## Source Connections

### Lakehouse Table Source

```m
let
    Source = Lakehouse.Contents(null){[workspaceId = "<workspace_id>"]}[Data],
    #"Navigation" = Source{[Id = "<lakehouse_id>", ItemKind = "Lakehouse"]}[Data],
    #"Table" = #"Navigation"{[Id = "dim_customers", ItemKind = "Table"]}[Data]
in
    #"Table"
```

### SQL Endpoint Source

```m
let
    Source = Sql.Database("<sql_endpoint>.datawarehouse.fabric.microsoft.com", "<lakehouse_name>"),
    #"Table" = Source{[Schema = "dbo", Item = "dim_customers"]}[Data]
in
    #"Table"
```

### CSV from OneLake Files

```m
let
    Source = Csv.Document(
        Web.Contents("https://onelake.dfs.fabric.microsoft.com/<workspace_id>/<lakehouse_id>/Files/raw/data.csv"),
        [Delimiter = ",", Columns = 5, Encoding = 65001, QuoteStyle = QuoteStyle.None]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
in
    #"Promoted Headers"
```

### REST API Source

```m
let
    Source = Json.Document(
        Web.Contents("https://api.example.com/data", [
            Headers = [#"Authorization" = "Bearer " & Token, #"Content-Type" = "application/json"]
        ])
    ),
    #"Converted to Table" = Table.FromList(Source, Splitter.SplitByNothing(), null, null, ExtraValues.Error)
in
    #"Converted to Table"
```

---

## Column Transformations

### Rename Multiple Columns

```m
let
    #"Renamed" = Table.RenameColumns(Source, {
        {"CustID", "customer_id"},
        {"CustName", "customer_name"},
        {"Rgn", "region"},
        {"Seg", "segment"}
    })
in
    #"Renamed"
```

### Change Column Types (Batch)

```m
let
    #"Changed Types" = Table.TransformColumnTypes(Source, {
        {"customer_id", Int64.Type},
        {"customer_name", type text},
        {"amount", type number},
        {"order_date", type date},
        {"is_active", type logical}
    })
in
    #"Changed Types"
```

### Add Calculated Column

```m
let
    #"Added Margin" = Table.AddColumn(Source, "profit_margin", 
        each [revenue] - [cost], type number),
    #"Added Year" = Table.AddColumn(#"Added Margin", "year", 
        each Date.Year([order_date]), Int64.Type),
    #"Added Month" = Table.AddColumn(#"Added Year", "month_name", 
        each Date.MonthName([order_date]), type text)
in
    #"Added Month"
```

### Conditional Column (If/Then)

```m
let
    #"Added Category" = Table.AddColumn(Source, "size_category", each
        if [revenue] > 1000000 then "Enterprise"
        else if [revenue] > 100000 then "Mid-Market"
        else if [revenue] > 10000 then "SMB"
        else "Micro",
        type text)
in
    #"Added Category"
```

---

## Row Operations

### Filter Rows

```m
let
    // Keep only active customers
    #"Filtered Active" = Table.SelectRows(Source, each [is_active] = true),
    
    // Remove nulls in key column
    #"Removed Nulls" = Table.SelectRows(#"Filtered Active", each [customer_id] <> null),
    
    // Date range filter
    #"Date Filter" = Table.SelectRows(#"Removed Nulls", each 
        [order_date] >= #date(2024, 1, 1) and [order_date] <= #date(2024, 12, 31))
in
    #"Date Filter"
```

### Remove Duplicates

```m
let
    // Remove exact duplicates on key columns
    #"Removed Duplicates" = Table.Distinct(Source, {"customer_id"}),
    
    // Keep first occurrence based on sort order
    #"Sorted" = Table.Sort(Source, {{"order_date", Order.Descending}}),
    #"Kept First" = Table.Distinct(#"Sorted", {"customer_id"})
in
    #"Kept First"
```

### Sort Rows

```m
let
    #"Sorted" = Table.Sort(Source, {
        {"region", Order.Ascending},
        {"revenue", Order.Descending}
    })
in
    #"Sorted"
```

---

## Table Operations

### Merge (Join) Tables

```m
let
    // Inner join
    #"Merged" = Table.NestedJoin(
        FactTable, {"customer_id"},
        DimCustomers, {"customer_id"},
        "Customers", JoinKind.Inner
    ),
    #"Expanded" = Table.ExpandTableColumn(#"Merged", "Customers", 
        {"customer_name", "region"}, {"customer_name", "region"})
in
    #"Expanded"
```

### Append (Union) Tables

```m
let
    #"Combined" = Table.Combine({Table_Jan, Table_Feb, Table_Mar})
in
    #"Combined"
```

### Unpivot Columns

```m
let
    // Turn Jan, Feb, Mar columns into Month + Value rows
    #"Unpivoted" = Table.UnpivotOtherColumns(Source, 
        {"product_id", "product_name"},  // Keep these columns
        "month", "sales_amount"          // New column names
    )
in
    #"Unpivoted"
```

### Pivot Column

```m
let
    // Turn row values into columns
    #"Pivoted" = Table.Pivot(Source, 
        List.Distinct(Source[region]),  // Column values
        "region",                       // Column to pivot
        "revenue",                      // Values column
        List.Sum                        // Aggregation
    )
in
    #"Pivoted"
```

### Group By (Aggregation)

```m
let
    #"Grouped" = Table.Group(Source, {"region", "year"}, {
        {"total_revenue", each List.Sum([revenue]), type number},
        {"avg_order", each List.Average([order_amount]), type number},
        {"order_count", each Table.RowCount(_), Int64.Type},
        {"max_date", each List.Max([order_date]), type date}
    })
in
    #"Grouped"
```

---

## Text Transformations

### Clean/Trim Text

```m
let
    #"Trimmed" = Table.TransformColumns(Source, {
        {"customer_name", Text.Trim, type text},
        {"email", Text.Lower, type text},
        {"product_code", Text.Upper, type text}
    })
in
    #"Trimmed"
```

### Split Column

```m
let
    // Split by delimiter
    #"Split Name" = Table.SplitColumn(Source, "full_name",
        Splitter.SplitTextByDelimiter(" ", QuoteStyle.None),
        {"first_name", "last_name"}
    ),
    
    // Split by position
    #"Split Code" = Table.SplitColumn(#"Split Name", "product_code",
        Splitter.SplitTextByPositions({0, 3}),
        {"category_code", "item_code"}
    )
in
    #"Split Code"
```

### Extract Patterns

```m
let
    // Extract year from date string
    #"Year" = Table.AddColumn(Source, "year", each 
        Text.Start([date_string], 4), type text),
    
    // Extract domain from email
    #"Domain" = Table.AddColumn(#"Year", "email_domain", each
        Text.AfterDelimiter([email], "@"), type text),
    
    // Replace text
    #"Cleaned" = Table.ReplaceValue(#"Domain", "N/A", null, Replacer.ReplaceValue, {"region"})
in
    #"Cleaned"
```

---

## Date/Time Functions

### Date Functions Reference

| Need | M Expression |
|------|-------------|
| Current date | `DateTime.LocalNow()` |
| Year | `Date.Year([date_col])` |
| Month number | `Date.Month([date_col])` |
| Month name | `Date.MonthName([date_col])` |
| Quarter | `Date.QuarterOfYear([date_col])` |
| Day of week | `Date.DayOfWeek([date_col])` |
| Week number | `Date.WeekOfYear([date_col])` |
| Start of month | `Date.StartOfMonth([date_col])` |
| End of month | `Date.EndOfMonth([date_col])` |
| Add days | `Date.AddDays([date_col], 30)` |
| Add months | `Date.AddMonths([date_col], 1)` |
| Days between | `Duration.Days([end_date] - [start_date])` |

### Generate Date Dimension Table

```m
let
    StartDate = #date(2020, 1, 1),
    EndDate = #date(2026, 12, 31),
    DayCount = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, DayCount, #duration(1, 0, 0, 0)),
    #"To Table" = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    #"Changed Type" = Table.TransformColumnTypes(#"To Table", {{"Date", type date}}),
    #"Added Year" = Table.AddColumn(#"Changed Type", "Year", each Date.Year([Date]), Int64.Type),
    #"Added Month" = Table.AddColumn(#"Added Year", "Month", each Date.Month([Date]), Int64.Type),
    #"Added MonthName" = Table.AddColumn(#"Added Month", "MonthName", each Date.MonthName([Date]), type text),
    #"Added Quarter" = Table.AddColumn(#"Added MonthName", "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    #"Added DayOfWeek" = Table.AddColumn(#"Added Quarter", "DayOfWeek", each Date.DayOfWeekName([Date]), type text),
    #"Added DateKey" = Table.AddColumn(#"Added DayOfWeek", "DateKey", each 
        Date.Year([Date]) * 10000 + Date.Month([Date]) * 100 + Date.Day([Date]), Int64.Type),
    #"Added IsWeekend" = Table.AddColumn(#"Added DateKey", "IsWeekend", each 
        Date.DayOfWeek([Date]) >= 5, type logical)
in
    #"Added IsWeekend"
```

---

## Error Handling Patterns

### Replace Errors in Column

```m
let
    #"Replaced Errors" = Table.ReplaceErrorValues(Source, {
        {"amount", 0},
        {"date", null},
        {"name", "Unknown"}
    })
in
    #"Replaced Errors"
```

### Try/Otherwise Pattern

```m
let
    #"Safe Convert" = Table.AddColumn(Source, "parsed_amount", each
        try Number.From([amount_text]) otherwise null, type number)
in
    #"Safe Convert"
```

### Remove Error Rows

```m
let
    #"Removed Errors" = Table.RemoveRowsWithErrors(Source, {"amount", "date"})
in
    #"Removed Errors"
```

---

## Mashup Document Template

Complete mashup document structure for Dataflow Gen2 API deployment:

```json
{
    "version": "1.0",
    "queriesMetadata": {
        "dim_customers": {
            "queryId": "00000000-0000-0000-0000-000000000001",
            "queryName": "dim_customers",
            "loadEnabled": true
        }
    },
    "queries": {
        "dim_customers": "let\n    Source = Csv.Document(Web.Contents(\"...\"), ...),\n    #\"Promoted Headers\" = Table.PromoteHeaders(Source)\nin\n    #\"Promoted Headers\""
    },
    "document": {
        "version": "1.0",
        "culture": "en-US",
        "modifiedTime": "2025-01-01T00:00:00.000Z"
    }
}
```

> **Reminder**: The mashup content must be base64-encoded when included in the Dataflow definition parts.

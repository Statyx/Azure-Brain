# Power Query M Patterns — Common Transformation Recipes

## M Language Fundamentals

### Basic Query Structure
```m
let
    // Step 1: Connect to source
    Source = Sql.Database("server.database.windows.net", "mydb"),
    
    // Step 2: Navigate to table
    SalesTable = Source{[Schema="dbo", Item="Sales"]}[Data],
    
    // Step 3: Transform
    FilteredRows = Table.SelectRows(SalesTable, each [Amount] > 0),
    RenamedColumns = Table.RenameColumns(FilteredRows, {{"OldName", "NewName"}}),
    TypeChanged = Table.TransformColumnTypes(RenamedColumns, {
        {"Amount", type number},
        {"SaleDate", type date}
    })
in
    TypeChanged
```

### Key Syntax
- `let ... in` — Define steps and return the final step
- `each [Column]` — Row-level function accessing column values
- `#"Step Name"` — Reference a named step (with special characters)
- `Table.*` — All table transformation functions
- `type text`, `type number`, `type date` — Type annotations
- `null` — Null value

---

## Source Connection Patterns

### SQL Server / Azure SQL
```m
let
    Source = Sql.Database("myserver.database.windows.net", "mydb"),
    dbo_Customers = Source{[Schema="dbo", Item="Customers"]}[Data]
in
    dbo_Customers
```

### SQL with Custom Query (Folding-Friendly)
```m
let
    Source = Sql.Database("myserver.database.windows.net", "mydb", [
        Query="SELECT * FROM dbo.Sales WHERE SaleDate >= '2024-01-01'"
    ])
in
    Source
```

### CSV File
```m
let
    Source = Csv.Document(
        File.Contents("C:\data\sales.csv"),
        [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        {"transaction_id", type text},
        {"amount", type number},
        {"sale_date", type date}
    })
in
    TypedColumns
```

### Web API / REST
```m
let
    Source = Json.Document(
        Web.Contents("https://api.example.com/data", [
            Headers = [#"Content-Type" = "application/json"]
        ])
    ),
    ConvertedToTable = Table.FromRecords(Source[results])
in
    ConvertedToTable
```

### Excel File
```m
let
    Source = Excel.Workbook(File.Contents("C:\data\report.xlsx"), null, true),
    Sheet1 = Source{[Item="Sheet1", Kind="Sheet"]}[Data],
    PromotedHeaders = Table.PromoteHeaders(Sheet1, [PromoteAllScalars=true])
in
    PromotedHeaders
```

### OData Feed
```m
let
    Source = OData.Feed("https://services.odata.org/V4/Northwind/Northwind.svc/"),
    Customers = Source{[Name="Customers", Signature="table"]}[Data]
in
    Customers
```

### SharePoint List
```m
let
    Source = SharePoint.Tables("https://contoso.sharepoint.com/sites/mysite", [ApiVersion=15]),
    MyList = Source{[Title="My List"]}[Items]
in
    MyList
```

### Lakehouse Files (Fabric Native)
```m
let
    Source = Lakehouse.Contents(null){[workspaceId="<ws-guid>"]}[Data]{[lakehouseId="<lh-guid>"]}[Data],
    Files = Source{[Id="Files"]}[Data],
    RawFolder = Files{[Name="raw"]}[Content],
    CsvFile = Csv.Document(RawFolder{[Name="data.csv"]}[Content], [Delimiter=","])
in
    CsvFile
```

---

## Transformation Recipes

### Filter Rows
```m
// Filter by value
Table.SelectRows(Source, each [Status] = "Active")

// Filter by date
Table.SelectRows(Source, each [OrderDate] >= #date(2024, 1, 1))

// Filter nulls
Table.SelectRows(Source, each [Email] <> null and [Email] <> "")

// Multiple conditions
Table.SelectRows(Source, each [Amount] > 100 and [Region] = "North")
```

### Select / Remove Columns
```m
// Keep only specific columns
Table.SelectColumns(Source, {"customer_id", "customer_name", "email"})

// Remove columns
Table.RemoveColumns(Source, {"internal_id", "temp_field"})
```

### Rename Columns
```m
Table.RenameColumns(Source, {
    {"CustomerID", "customer_id"},
    {"CustomerName", "customer_name"},
    {"EmailAddress", "email"}
})
```

### Change Column Types
```m
Table.TransformColumnTypes(Source, {
    {"amount", type number},
    {"sale_date", type date},
    {"quantity", Int64.Type},
    {"is_active", type logical},
    {"customer_id", type text}
})
```

### Add Calculated Column
```m
// Simple calculation
Table.AddColumn(Source, "total", each [quantity] * [unit_price], type number)

// Conditional column
Table.AddColumn(Source, "segment", each 
    if [amount] > 1000 then "High"
    else if [amount] > 100 then "Medium"
    else "Low",
    type text
)

// Date extraction
Table.AddColumn(Source, "year", each Date.Year([sale_date]), Int64.Type)
Table.AddColumn(Source, "month", each Date.Month([sale_date]), Int64.Type)
Table.AddColumn(Source, "quarter", each Date.QuarterOfYear([sale_date]), Int64.Type)
```

### Group By / Aggregate
```m
Table.Group(Source, {"region", "product_category"}, {
    {"total_revenue", each List.Sum([amount]), type number},
    {"transaction_count", each Table.RowCount(_), Int64.Type},
    {"avg_amount", each List.Average([amount]), type number},
    {"min_date", each List.Min([sale_date]), type date},
    {"max_date", each List.Max([sale_date]), type date}
})
```

### Merge Tables (Join)
```m
// Left join
let
    Sales = ...,
    Customers = ...,
    Merged = Table.NestedJoin(Sales, "customer_id", Customers, "customer_id", "CustomerDetails", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "CustomerDetails", {"customer_name", "segment"})
in
    Expanded
```

### Append Tables (Union)
```m
// Stack tables vertically
Table.Combine({Table1, Table2, Table3})
```

### Pivot / Unpivot
```m
// Unpivot: columns to rows (normalize)
Table.UnpivotOtherColumns(Source, {"site_id", "date"}, "Metric", "Value")

// Pivot: rows to columns (denormalize)
Table.Pivot(Source, List.Distinct(Source[Metric]), "Metric", "Value", List.Sum)
```

### Remove Duplicates
```m
Table.Distinct(Source, {"customer_id"})
```

### Replace Values
```m
// Replace specific value
Table.ReplaceValue(Source, "Old Value", "New Value", Replacer.ReplaceText, {"column_name"})

// Replace nulls
Table.ReplaceValue(Source, null, 0, Replacer.ReplaceValue, {"amount"})
Table.ReplaceValue(Source, null, "Unknown", Replacer.ReplaceValue, {"category"})
```

### Sort
```m
Table.Sort(Source, {{"sale_date", Order.Descending}, {"amount", Order.Descending}})
```

### Split Column
```m
// Split by delimiter
Table.SplitColumn(Source, "full_name", Splitter.SplitTextByDelimiter(" ", QuoteStyle.None), {"first_name", "last_name"})
```

### Trim and Clean Text
```m
// Trim whitespace
Table.TransformColumns(Source, {{"customer_name", Text.Trim, type text}})

// Clean (remove non-printable characters)
Table.TransformColumns(Source, {{"notes", Text.Clean, type text}})

// Uppercase
Table.TransformColumns(Source, {{"country_code", Text.Upper, type text}})
```

---

## Advanced Patterns

### Dynamic Date Filter (Relative)
```m
let
    Today = DateTime.LocalNow(),
    StartOfMonth = Date.StartOfMonth(DateTime.Date(Today)),
    Source = Sql.Database("server", "db"),
    Sales = Source{[Schema="dbo", Item="Sales"]}[Data],
    Filtered = Table.SelectRows(Sales, each [OrderDate] >= StartOfMonth)
in
    Filtered
```

### Error Handling
```m
// Replace errors in a column
Table.ReplaceErrorValues(Source, {{"amount", 0}, {"date", null}})

// Try/otherwise for a step
let
    Result = try SomeRiskyOperation() otherwise DefaultValue
in
    Result
```

### Parameters
```m
// Define a parameter (in the mashup metadata)
// Then use it in queries:
let
    Source = Sql.Database(ServerParam, DatabaseParam),
    FilteredByDate = Table.SelectRows(Source, each [Date] >= StartDateParam)
in
    FilteredByDate
```

---

## Query Folding

**Query folding** means the M engine pushes transformations back to the data source (e.g., SQL). This is critical for performance.

### Operations That Fold (SQL sources)
- `Table.SelectRows` → `WHERE`
- `Table.SelectColumns` → `SELECT`
- `Table.Sort` → `ORDER BY`
- `Table.Group` → `GROUP BY`
- `Table.NestedJoin` → `JOIN`
- `Table.FirstN` → `TOP`

### Operations That Break Folding
- `Table.AddColumn` with complex M functions
- `Text.From()`, `Number.From()` in filters
- Referencing other queries in calculations
- Custom functions (non-standard M)

### Check Folding
In Power Query Editor: Right-click a step → "View Native Query". If it shows SQL, folding is working.

---

## Best Practices

1. **Push filters early** — Filter rows before transformations for query folding
2. **Remove unnecessary columns** — Less data = faster processing
3. **Use explicit types** — Always set column types; don't rely on auto-detection
4. **Name steps clearly** — Step names become documentation
5. **Enable staging** — For any Dataflow processing > 100K rows
6. **Test M in Power Query Editor** — Write and test in the Fabric portal before pushing via API
7. **Avoid row-by-row operations** — Use column transformations instead of loops

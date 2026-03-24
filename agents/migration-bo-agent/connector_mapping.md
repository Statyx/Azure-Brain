# BO Data Connector → Power Query M Mapping

Mapping of BO/Crystal data connection types to Power BI connection modes and Power Query M patterns. Inspired by [cyphou/Tableau-To-PowerBI](https://github.com/cyphou/Tableau-To-PowerBI) (42 connector mappings) and [cyphou/Qlik-To-PowerBI](https://github.com/cyphou/Qlik-To-PowerBI) (25 connectors + 40 M transform generators).

---

## Connection Types

### Relational Databases

| # | BO Connection | Power BI Connector | M Function | Gateway Required | Notes |
|---|--------------|-------------------|------------|-----------------|-------|
| 1 | JDBC to SQL Server | SQL Server | `Sql.Database()` | Yes (on-prem) | Native connector, best performance |
| 2 | ODBC to SQL Server | SQL Server | `Sql.Database()` | Yes (on-prem) | Prefer native over ODBC |
| 3 | JDBC to Oracle | Oracle Database | `Oracle.Database()` | Yes | Requires Oracle client on gateway |
| 4 | ODBC to Oracle | Oracle Database | `Oracle.Database()` | Yes | Prefer native connector |
| 5 | JDBC to SAP HANA | SAP HANA | `SapHana.Database()` | Yes | DirectQuery supported |
| 6 | SAP BW (BICS) | SAP BW via MDX | `SapBusinessWarehouse.Cubes()` | Yes | MDX mode; also supports SAP BW Message Server |
| 7 | JDBC to PostgreSQL | PostgreSQL | `PostgreSQL.Database()` | Yes | Native connector available |
| 8 | JDBC to MySQL | MySQL | `MySQL.Database()` | Yes | Native connector |
| 9 | JDBC to DB2 | IBM DB2 | `DB2.Database()` | Yes | Requires IBM driver on gateway |
| 10 | JDBC to Teradata | Teradata | `Teradata.Database()` | Yes | Requires Teradata .NET provider |
| 11 | JDBC to Sybase ASE | Sybase Database | `Sybase.Database()` | Yes | Limited; consider ODBC fallback |
| 12 | JDBC to Informix | ODBC | `Odbc.DataSource()` | Yes | No native connector — use ODBC |
| 13 | JDBC to Netezza | ODBC | `Odbc.DataSource()` | Yes | No native connector — use ODBC |
| 14 | JDBC to Snowflake | Snowflake | `Snowflake.Databases()` | No (cloud) | Native connector, DirectQuery supported |
| 15 | Azure SQL | Azure SQL Database | `AzureSQL.Database()` | No | Cloud-native, no gateway |
| 16 | JDBC to Redshift | Amazon Redshift | `AmazonRedshift.Database()` | No | Native connector |
| 17 | JDBC to Google BigQuery | Google BigQuery | `GoogleBigQuery.Database()` | No | OAuth authentication |

### SAP-Specific Connections

| # | BO Connection | Power BI Connector | M Function | Notes |
|---|--------------|-------------------|------------|-------|
| 1 | SAP BW (BICS connector) | SAP BW | `SapBusinessWarehouse.Cubes()` | MDX-based queries |
| 2 | SAP BW via OLAP BICS | SAP BW Message Server | `SapBusinessWarehouseExecutionMode.SapBusinessExplorer` | BEx queries |
| 3 | SAP HANA (Information Views) | SAP HANA | `SapHana.Database()` | Calculation/Analytic views — DirectQuery recommended |
| 4 | SAP ERP (via Universe) | SAP HANA (if replicated) or Dataflow | Custom M | Migrate via SAP HANA SLT or ABAP CDS; no direct ERP connector in PBI |
| 5 | SAP BPC | SAP BW | Same BW connector | BPC models accessed through BW |

### File-Based Sources

| # | BO Connection | Power BI Connector | M Function | Notes |
|---|--------------|-------------------|------------|-------|
| 1 | CSV file (local/UNC) | Text/CSV | `Csv.Document(File.Contents())` | Schedule refresh via gateway |
| 2 | Excel file (local/UNC) | Excel Workbook | `Excel.Workbook(File.Contents())` | Gateway for on-prem files |
| 3 | Excel file (SharePoint) | Excel Workbook | `Excel.Workbook(Web.Contents())` | Cloud refresh, no gateway |
| 4 | XML file | XML | `Xml.Document(File.Contents())` | |
| 5 | CSV on FTP/SFTP | Custom M via Web.Contents | `Csv.Document(Web.Contents())` | May need custom function; evaluate Dataflow Gen2 |

### Web & Cloud Sources

| # | BO Connection | Power BI Connector | M Function | Notes |
|---|--------------|-------------------|------------|-------|
| 1 | Web service (REST) | Web | `Web.Contents()` | JSON/XML parsing in M |
| 2 | OData feed | OData Feed | `OData.Feed()` | Native support |
| 3 | SharePoint List | SharePoint Online List | `SharePoint.Tables()` | |
| 4 | Salesforce | Salesforce Objects | `Salesforce.Data()` | Cloud-native |

### BO-Specific Connection Patterns

| # | BO Pattern | Fabric/PBI Equivalent | Notes |
|---|-----------|----------------------|-------|
| 1 | Universe (UNX) single-source | Semantic Model (Import/DQ) | Universe → Semantic Model is the core migration |
| 2 | Universe (UNX) multi-source | Composite Model or Dataflow Gen2 | Each source becomes a connection; Dataflow Gen2 for staging |
| 3 | Universe derived table | Power Query M step | Convert derived table SQL to M query |
| 4 | Universe @Variable (security) | RLS DAX filter + `USERPRINCIPALNAME()` | See RLS migration section |
| 5 | Universe LOV (List of Values) | DirectQuery or Import for slicer | Pre-populate slicer via relationship |
| 6 | JNDI connection pool | Gateway connection pool | Gateway manages connections centrally |
| 7 | Crystal Report Command Object | Direct SQL in Power Query | `Value.NativeQuery()` — use sparingly |
| 8 | Crystal Report stored procedure | Stored Procedure connector | `Sql.Database(server, db, [Query=...])` |
| 9 | Crystal Report linked subreport | Drill-through or nested query | Subreport data source must be unified |
| 10 | BO Publication dynamic recipient | Paginated subscription | Map publication personalization to subscription parameters |

---

## Migration by Architecture Pattern

### Pattern A: Direct Import (< 1GB)

```
BO Universe (JDBC/ODBC) → Power Query M → Import Semantic Model → Power BI Report

M Template:
  let
      Source = Sql.Database("server", "database"),
      Table = Source{[Schema="dbo", Item="TableName"]}[Data],
      -- Apply universe-equivalent filters here
      Filtered = Table.SelectRows(Table, each [Active] = true)
  in
      Filtered
```

### Pattern B: DirectQuery (> 1GB, near-real-time)

```
BO Universe (JDBC) → DirectQuery Semantic Model → Power BI Report

M Template:
  let
      Source = Sql.Database("server", "database", [EnableFolding=true]),
      -- CRITICAL: ensure all steps fold to SQL for performance
      Table = Source{[Schema="dbo", Item="ViewName"]}[Data]
  in
      Table
```

### Pattern C: Direct Lake via Fabric Lakehouse

```
BO Universe → Dataflow Gen2 / Pipeline → Lakehouse → Direct Lake Semantic Model → Power BI Report

Steps:
  1. Create Lakehouse in Fabric workspace
  2. Ingest data via Dataflow Gen2 (equivalent to universe query)
  3. Create Direct Lake semantic model on Lakehouse tables
  4. Build Power BI report on semantic model
```

### Pattern D: Hybrid / Composite Model

```
BO Multi-Source Universe → Composite Model:
  - Large fact table: DirectQuery to Lakehouse
  - Small dimensions: Import mode
  - External data: Dataflow Gen2
```

---

## Power Query M Transform Patterns

Common BO universe object conversions to M:

| # | BO Universe Object | Power Query M Equivalent |
|---|-------------------|------------------------|
| 1 | Dimension object | Column reference (no transform) |
| 2 | Measure object (SUM) | `Table.Group(..., {{"Total", each List.Sum([Amount])}})` or DAX `SUM()` |
| 3 | Derived table (SQL subquery) | Nested `let...in` or `Table.SelectRows()` + `Table.Group()` |
| 4 | Pre-filter (WHERE clause) | `Table.SelectRows(table, each [col] = value)` |
| 5 | Join (multi-table) | `Table.NestedJoin()` + `Table.ExpandTableColumn()` |
| 6 | Alias / renamed column | `Table.RenameColumns(table, {{"OldName", "NewName"}})` |
| 7 | Concatenated dimension | `Table.AddColumn(table, "Full", each [First] & " " & [Last])` |
| 8 | Date extraction (Year) | `Table.AddColumn(table, "Year", each Date.Year([DateCol]))` |
| 9 | Custom SQL (free-hand) | `Value.NativeQuery(source, "SELECT ...")` |
| 10 | Prompted filter (@Prompt) | Report Parameter → `filterValue` in M query |

---

## Gateway Planning

| Scenario | Gateway Type | Notes |
|----------|-------------|-------|
| All data in cloud (Azure SQL, Snowflake, etc.) | No gateway needed | Direct cloud connection |
| On-prem SQL Server, Oracle | On-premises Data Gateway (standard) | Install on dedicated server near data source |
| Mixed cloud + on-prem | On-premises Data Gateway | Gateway handles on-prem; cloud connections are direct |
| Personal development/testing | Personal Gateway | Single user, cannot share |
| SAP HANA, SAP BW | On-premises Data Gateway + SAP drivers | Install SAP HANA ODBC + SAP BW MDX provider |
| File-based sources (CSV, Excel on UNC) | On-premises Data Gateway | Gateway accesses file share |

> **Rule of thumb**: If the BO server could reach the database, the gateway machine must also be able to reach it with the same network path and credentials.

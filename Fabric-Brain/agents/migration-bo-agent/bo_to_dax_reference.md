# BusinessObjects Formula → DAX Complete Reference

Complete mapping of **every BO formula/function** to its DAX (Power BI) equivalent.

> **Legend**
> ✅ Automatic — direct DAX equivalent exists
> ⚠️ Approximate — requires DAX rewrite, close equivalent
> 🔧 Manual — no direct equivalent, requires architecture redesign
> ❌ No equivalent — no DAX counterpart exists

> **Inspired by**: [cyphou/Tableau-To-PowerBI](https://github.com/cyphou/Tableau-To-PowerBI), [cyphou/MicroStrategyToPowerBI](https://github.com/cyphou/MicroStrategyToPowerBI), [cyphou/Qlik-To-PowerBI](https://github.com/cyphou/Qlik-To-PowerBI) — migration tools with 100-180+ function conversion tables.

---

## 1. Aggregation Functions

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=Sum([Column])` | `SUM(Table[Column])` | ✅ | |
| 2 | `=Avg([Column])` | `AVERAGE(Table[Column])` | ✅ | |
| 3 | `=Count([Column])` | `COUNT(Table[Column])` | ✅ | BO Count = non-null count |
| 4 | `=Count([Column]; Distinct)` | `DISTINCTCOUNT(Table[Column])` | ✅ | |
| 5 | `=Min([Column])` | `MIN(Table[Column])` | ✅ | |
| 6 | `=Max([Column])` | `MAX(Table[Column])` | ✅ | |
| 7 | `=Median([Column])` | `MEDIAN(Table[Column])` | ✅ | |
| 8 | `=StdDev([Column])` | `STDEV.S(Table[Column])` | ✅ | Sample std dev |
| 9 | `=Variance([Column])` | `VAR.S(Table[Column])` | ✅ | |
| 10 | `=Percentile([Column]; 0.9)` | `PERCENTILEX.INC(Table, Table[Column], 0.9)` | ✅ | |
| 11 | `=Product([Column])` | `PRODUCTX(Table, Table[Column])` | ✅ | |
| 12 | `=Mode([Column])` | `TOPN(1, SUMMARIZE(Table, Table[Column], "Cnt", COUNT(Table[Column])), [Cnt], DESC)` | ⚠️ | No native MODE in DAX |

### Automatic AGGX Promotion
When an aggregate wraps an expression (not a single column), promote to iterator:

| Pattern | DAX Conversion |
|---------|---------------|
| `=Sum([Qty] * [Price])` | `SUMX(Table, Table[Qty] * Table[Price])` |
| `=Avg(If(...)` | `AVERAGEX(Table, IF(...))` |
| `=Min(expression)` | `MINX(Table, expression)` |
| `=Max(expression)` | `MAXX(Table, expression)` |

---

## 2. Context Operators (BO-Specific — Critical)

> **These are the hardest BO formulas to translate.** They control the aggregation grain, similar to MicroStrategy Level Metrics and Tableau LOD expressions.

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=Sum([Revenue]) In [Region]` | `CALCULATE(SUM(Sales[Revenue]), ALLEXCEPT(Sales, Geo[Region]))` | ⚠️ | Forces calculation at Region grain |
| 2 | `=Sum([Revenue]) In ([Year];[Region])` | `CALCULATE(SUM(Sales[Revenue]), ALLEXCEPT(Sales, Calendar[Year], Geo[Region]))` | ⚠️ | Multi-dimension context |
| 3 | `=Sum([Revenue]) ForEach [Product]` | `CALCULATE(SUM(Sales[Revenue]), VALUES(Products[Product]))` | ⚠️ | Add Product to context; similar to INCLUDE LOD |
| 4 | `=Sum([Revenue]) ForAll [Region]` | `CALCULATE(SUM(Sales[Revenue]), REMOVEFILTERS(Geo[Region]))` | ⚠️ | Remove Region from context; similar to EXCLUDE LOD |
| 5 | `=Sum([Revenue]) In Report` | `CALCULATE(SUM(Sales[Revenue]), ALL(Sales))` | ⚠️ | Grand total — like MSTR `{^}` |
| 6 | `=Sum([Revenue]) In Block` | Context depends on visual grouping | 🔧 | Block context is report-layout-dependent — manual analysis required |
| 7 | `=Sum([Revenue]) In Section` | Section = drill-through page context | 🔧 | Depends on how sections are migrated |

### Cross-Platform Comparison
| Concept | BO | Tableau | MicroStrategy | Qlik | DAX |
|---------|-------------|-----------------|---------------------|------|------|
| Fixed grain | `In [Dim]` | `{FIXED [Dim]: ...}` | `{~+, Dim}` | `Aggr()` | `CALCULATE(..., ALLEXCEPT(...))` |
| Add dimension | `ForEach [Dim]` | `{INCLUDE [Dim]: ...}` | N/A | N/A | `CALCULATE(..., VALUES(...))` |
| Remove dimension | `ForAll [Dim]` | `{EXCLUDE [Dim]: ...}` | `{!Dim}` | N/A | `CALCULATE(..., REMOVEFILTERS(...))` |
| Grand total | `In Report` | `{: ...}` | `{^}` | `Total` | `CALCULATE(..., ALL(...))` |
| Percent of total | `Revenue / Sum(Revenue) In Report` | `SUM(Revenue) / TOTAL(SUM(Revenue))` | `Revenue / Sum(Revenue) {^}` | `Sum(Revenue) / Sum(Total Revenue)` | `DIVIDE([Rev], CALCULATE([Rev], ALL(...)))` |

---

## 3. Running / Window Functions

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=RunningSum([Revenue])` | `CALCULATE(SUM(Sales[Revenue]), FILTER(ALL(Calendar), Calendar[Date] <= MAX(Calendar[Date])))` | ⚠️ | Window pattern with date dimension |
| 2 | `=RunningAvg([Revenue])` | `CALCULATE(AVERAGE(Sales[Revenue]), FILTER(ALL(Calendar), Calendar[Date] <= MAX(Calendar[Date])))` | ⚠️ | |
| 3 | `=RunningCount([Revenue])` | `CALCULATE(COUNT(Sales[Revenue]), FILTER(ALL(Calendar), Calendar[Date] <= MAX(Calendar[Date])))` | ⚠️ | |
| 4 | `=RunningMax([Revenue])` | `CALCULATE(MAX(Sales[Revenue]), FILTER(ALL(Calendar), Calendar[Date] <= MAX(Calendar[Date])))` | ⚠️ | |
| 5 | `=RunningMin([Revenue])` | `CALCULATE(MIN(Sales[Revenue]), FILTER(ALL(Calendar), Calendar[Date] <= MAX(Calendar[Date])))` | ⚠️ | |
| 6 | `=Previous([Revenue])` | `CALCULATE([Revenue], DATEADD(Calendar[Date], -1, MONTH))` | ⚠️ | Time intelligence — period depends on report context |
| 7 | `=Previous([Revenue]; 2)` | `CALCULATE([Revenue], DATEADD(Calendar[Date], -2, MONTH))` | ⚠️ | Offset parameter |
| 8 | `=Rank([Revenue])` | `RANKX(ALL(Table), [Revenue])` | ✅ | Dense rank by default |
| 9 | `=Percentage([Revenue])` | `DIVIDE(SUM(Sales[Revenue]), CALCULATE(SUM(Sales[Revenue]), ALL(Sales)))` | ✅ | Percent of total |
| 10 | `=CumulativePercentage([Revenue])` | Running percentage pattern | ⚠️ | Combine RunningSum + percent of total |
| 11 | `=MovingAverage([Revenue]; 3)` | `AVERAGEX(TOPN(3, ALL(Calendar[Month]), Calendar[Month], DESC), [Revenue])` | ⚠️ | N-period moving average |

> **Note**: DAX WINDOW and OFFSET functions (2023+) simplify many running patterns. Use when targeting modern DAX.

---

## 4. String Functions

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=Left([Name]; 5)` | `LEFT(Table[Name], 5)` | ✅ | |
| 2 | `=Right([Name]; 3)` | `RIGHT(Table[Name], 3)` | ✅ | |
| 3 | `=Substr([Name]; 2; 4)` | `MID(Table[Name], 2, 4)` | ✅ | |
| 4 | `=Length([Name])` | `LEN(Table[Name])` | ✅ | |
| 5 | `=Upper([Name])` | `UPPER(Table[Name])` | ✅ | |
| 6 | `=Lower([Name])` | `LOWER(Table[Name])` | ✅ | |
| 7 | `=Trim([Name])` | `TRIM(Table[Name])` | ✅ | |
| 8 | `=LTrim([Name])` | `MID(Table[Name], ...)` | ⚠️ | No native LTRIM in DAX |
| 9 | `=RTrim([Name])` | `LEFT(Table[Name], ...)` | ⚠️ | No native RTRIM in DAX |
| 10 | `=Pos([Name]; "abc")` | `SEARCH("abc", Table[Name])` | ✅ | 1-based position; arg order swapped |
| 11 | `=Replace([Name]; "old"; "new")` | `SUBSTITUTE(Table[Name], "old", "new")` | ✅ | |
| 12 | `=Concatenation([First]; " "; [Last])` | `Table[First] & " " & Table[Last]` | ✅ | Or `CONCATENATE()` |
| 13 | `=Fill([Code]; 6; "0")` | `RIGHT(REPT("0", 6) & Table[Code], 6)` | ✅ | Left-pad |
| 14 | `=Asc([Char])` | `UNICODE(Table[Char])` | ✅ | |
| 15 | `=Chr(65)` | `UNICHAR(65)` | ✅ | |
| 16 | `=Match([Name]; "pattern")` | `CONTAINSSTRING(Table[Name], "pattern")` | ⚠️ | No full regex in DAX |
| 17 | `=WordCap([Name])` | `UPPER(LEFT(Table[Name],1)) & LOWER(MID(Table[Name],2,LEN(Table[Name])))` | ⚠️ | First word only — multi-word needs Power Query |
| 18 | `=HTMLEncode([Text])` | No equivalent | 🔧 | Handle in Power Query M or data layer |
| 19 | `=URLEncode([Text])` | No equivalent | 🔧 | Handle in Power Query M or data layer |

---

## 5. Date Functions

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=CurrentDate()` | `TODAY()` | ✅ | |
| 2 | `=CurrentTime()` | `NOW()` | ✅ | |
| 3 | `=Year([Date])` | `YEAR(Table[Date])` | ✅ | |
| 4 | `=Quarter([Date])` | `QUARTER(Table[Date])` | ✅ | |
| 5 | `=Month([Date])` | `MONTH(Table[Date])` | ✅ | |
| 6 | `=MonthNumberOfYear([Date])` | `MONTH(Table[Date])` | ✅ | |
| 7 | `=DayNumberOfMonth([Date])` | `DAY(Table[Date])` | ✅ | |
| 8 | `=DayNumberOfWeek([Date])` | `WEEKDAY(Table[Date])` | ✅ | |
| 9 | `=DayNumberOfYear([Date])` | `DATEDIFF(DATE(YEAR(Table[Date]),1,1), Table[Date], DAY) + 1` | ✅ | |
| 10 | `=Week([Date])` | `WEEKNUM(Table[Date])` | ✅ | |
| 11 | `=DayName([Date])` | `FORMAT(Table[Date], "DDDD")` | ✅ | |
| 12 | `=MonthName([Date])` | `FORMAT(Table[Date], "MMMM")` | ✅ | |
| 13 | `=DatesBetween([Start]; [End])` | `DATEDIFF(Table[Start], Table[End], DAY)` | ✅ | |
| 14 | `=RelativeDate([Date]; -30)` | `Table[Date] + (-30)` or `DATEADD(Table[Date], -30, DAY)` | ✅ | |
| 15 | `=LastDayOfMonth([Date])` | `ENDOFMONTH(Table[Date])` | ✅ | Time intelligence |
| 16 | `=LastDayOfWeek([Date])` | `Table[Date] + (7 - WEEKDAY(Table[Date]))` | ✅ | |
| 17 | `=ToDate("2024-01-15"; "yyyy-MM-dd")` | `DATE(2024, 1, 15)` | ✅ | Format arg not needed |
| 18 | `=FormatDate([Date]; "dd/MM/yyyy")` | `FORMAT(Table[Date], "dd/MM/yyyy")` | ✅ | |

---

## 6. Logical / Conditional Functions

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=If [Revenue] > 1000 Then "High" Else "Low"` | `IF(Table[Revenue] > 1000, "High", "Low")` | ✅ | |
| 2 | `=If ... ElseIf ... Else` | Nested `IF()` or `SWITCH(TRUE(), ...)` | ✅ | SWITCH preferred for readability |
| 3 | `=IsNull([Value])` | `ISBLANK(Table[Value])` | ✅ | |
| 4 | `=IfNull([Value]; 0)` | `IF(ISBLANK(Table[Value]), 0, Table[Value])` or `COALESCE(Table[Value], 0)` | ✅ | |
| 5 | `=Even([Number])` | `IF(MOD(Table[Number], 2) = 0, TRUE(), FALSE())` | ✅ | |
| 6 | `=Odd([Number])` | `IF(MOD(Table[Number], 2) <> 0, TRUE(), FALSE())` | ✅ | |
| 7 | `=Between([Value]; 10; 100)` | `Table[Value] >= 10 && Table[Value] <= 100` | ✅ | |
| 8 | `=InList([Status]; "A"; "B"; "C")` | `Table[Status] IN {"A", "B", "C"}` | ✅ | |
| 9 | `=Not [Condition]` | `NOT(condition)` | ✅ | |
| 10 | `=And([A]; [B])` | `[A] && [B]` | ✅ | |
| 11 | `=Or([A]; [B])` | `[A] \|\| [B]` | ✅ | |

---

## 7. Math Functions

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=Abs([Value])` | `ABS(Table[Value])` | ✅ | |
| 2 | `=Ceil([Value])` | `CEILING(Table[Value], 1)` | ✅ | DAX needs significance arg |
| 3 | `=Floor([Value])` | `FLOOR(Table[Value], 1)` | ✅ | |
| 4 | `=Round([Value]; 2)` | `ROUND(Table[Value], 2)` | ✅ | |
| 5 | `=Truncate([Value]; 2)` | `TRUNC(Table[Value], 2)` | ✅ | |
| 6 | `=Sign([Value])` | `SIGN(Table[Value])` | ✅ | |
| 7 | `=Power([Value]; 3)` | `POWER(Table[Value], 3)` | ✅ | |
| 8 | `=Sqrt([Value])` | `SQRT(Table[Value])` | ✅ | |
| 9 | `=Exp([Value])` | `EXP(Table[Value])` | ✅ | |
| 10 | `=Ln([Value])` | `LN(Table[Value])` | ✅ | |
| 11 | `=Log([Value])` | `LOG(Table[Value], 10)` | ✅ | Base 10 |
| 12 | `=Mod([A]; [B])` | `MOD(Table[A], Table[B])` | ✅ | |
| 13 | `=Interpolation(...)` | No direct equivalent | 🔧 | Build custom DAX or handle in data layer |
| 14 | `=Sin / Cos / Tan / etc.` | `SIN() / COS() / TAN() / etc.` | ✅ | All trig functions have DAX equivalents |

---

## 8. Document / Metadata Functions (BO-Specific)

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=DocumentName()` | No equivalent | 🔧 | Report name is metadata — not available in DAX |
| 2 | `=DocumentAuthor()` | No equivalent | 🔧 | |
| 3 | `=DocumentDate()` | `NOW()` | ⚠️ | Report refresh date ≈ last refresh timestamp |
| 4 | `=LastExecutionDate()` | Use Power Automate / Pipeline metadata | 🔧 | No direct DAX access to refresh metadata |
| 5 | `=ReportName()` | No equivalent | 🔧 | |
| 6 | `=CurrentUser()` | `USERPRINCIPALNAME()` | ✅ | Returns email (UPN) not BO username |
| 7 | `=UserResponse([Prompt])` | Slicer selection via `SELECTEDVALUE()` | ⚠️ | @Prompt → Slicer / parameter |
| 8 | `=NumberOfPages()` | No equivalent | ❌ | PBI reports are not page-counted the same way |
| 9 | `=Page()` | No equivalent | ❌ | PBI reports are not page-numbered |
| 10 | `=RowIndex()` | `RANKX(Table, Table[SortColumn])` | ⚠️ | Row numbering in visuals |
| 11 | `=NumberOfRows()` | `COUNTROWS(Table)` | ✅ | |
| 12 | `=DrillFilters()` | No equivalent | 🔧 | Drill context is implicit in PBI visuals |

---

## 9. @Prompt Conversions (BO-Specific)

| # | BO @Prompt Type | Fabric Equivalent | Status | Notes |
|---|----------------|-------------------|--------|-------|
| 1 | `@Prompt('Region', 'A', 'Geo\Region', mono, constrained)` | Slicer (single-select, constrained to dimension) | ✅ | |
| 2 | `@Prompt('Region', 'A', 'Geo\Region', multi, constrained)` | Slicer (multi-select) | ✅ | |
| 3 | `@Prompt('Start Date', 'D', , mono, free)` | Date slicer or date parameter | ✅ | |
| 4 | `@Prompt('Search', 'A', , mono, free)` | Text input (Power Apps visual) or What-If parameter | ⚠️ | PBI slicers don't support free text entry natively |
| 5 | Cascading @Prompts (Region → City) | Cascading slicers via relationships | ⚠️ | Relies on data model relationships; not identical to BO cascading LOVs |
| 6 | Optional @Prompts | Slicer with "Select All" default | ✅ | |
| 7 | @Prompt with default value | Slicer with default filter or bookmark | ✅ | |
| 8 | @Prompt in universe WHERE clause | RLS role DAX filter | ⚠️ | Security prompts → RLS |
| 9 | @Variable (session variables) | `USERPRINCIPALNAME()` + security table | ⚠️ | Session context → Entra ID identity |

---

## 10. Formatting & Display Functions

| # | BO Formula | DAX Equivalent | Status | Notes |
|---|-----------|----------------|--------|-------|
| 1 | `=FormatNumber([Value]; "#,##0.00")` | `FORMAT(Table[Value], "#,##0.00")` | ✅ | |
| 2 | `=FormatDate([Date]; "dd/MM/yyyy")` | `FORMAT(Table[Date], "dd/MM/yyyy")` | ✅ | |
| 3 | `=FormatCurrency([Value]; "€")` | `FORMAT(Table[Value], "€#,##0.00")` | ✅ | |
| 4 | Alerters (color by condition) | Conditional formatting rules in visual | ✅ | Configure in visual properties, not DAX |
| 5 | Hyperlink formulas | `[URL]` column + visual hyperlink setting | ✅ | |
| 6 | Image URL embedding | Image URL column + Image visual type | ✅ | |

---

## Summary Statistics

| Category | Total | ✅ Auto | ⚠️ Approx | 🔧 Manual | ❌ None |
|----------|-------|---------|-----------|-----------|---------|
| Aggregation | 12 | 11 | 1 | 0 | 0 |
| Context Operators | 7 | 0 | 5 | 2 | 0 |
| Running / Window | 11 | 2 | 9 | 0 | 0 |
| String | 19 | 14 | 3 | 2 | 0 |
| Date | 18 | 18 | 0 | 0 | 0 |
| Logical | 11 | 11 | 0 | 0 | 0 |
| Math | 14 | 13 | 0 | 1 | 0 |
| Document / Metadata | 12 | 2 | 3 | 5 | 2 |
| @Prompt | 9 | 4 | 5 | 0 | 0 |
| Formatting | 6 | 6 | 0 | 0 | 0 |
| **TOTAL** | **119** | **81** | **26** | **10** | **2** |

**Coverage: 81/119 (68%) fully automatic, 107/119 (90%) automatic+approximate**

> **Key insight**: The hardest BO formulas to migrate are **context operators** (In, ForEach, ForAll) and **running functions** (RunningSum, Previous). These require deep DAX expertise. Budget extra time for reports containing these.

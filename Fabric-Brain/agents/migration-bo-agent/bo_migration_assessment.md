# BO Migration Assessment & Readiness Scoring

Pre-migration readiness assessment with automated scoring inspired by [cyphou/MicroStrategyToPowerBI](https://github.com/cyphou/MicroStrategyToPowerBI) (14-category GREEN/YELLOW/RED system) and [cyphou/Tableau-To-PowerBI](https://github.com/cyphou/Tableau-To-PowerBI) (fidelity scoring framework).

---

## Assessment Categories

Score each category per report/document: **GREEN** (auto-migratable), **YELLOW** (requires adaptation), **RED** (manual rewrite).

### Category 1: Data Sources & Connectivity
| Criterion | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| Connection type | JDBC/ODBC to SQL Server, Oracle, SAP HANA | ODBC to DB2, Teradata, other RDBMS | JNDI, BICS, custom middleware |
| Authentication | SQL auth, Kerberos | SSO via BO Enterprise | Custom security plugin, BO token passthrough |
| Connection count | ≤ 3 data sources | 4–8 data sources | > 8 data sources or linked universes |
| Universe complexity | Single-source universe | Multi-source universe (single DB) | Multi-source universe (cross-DB federation) |

### Category 2: Formulas & Expressions
| Criterion | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| Basic aggregations | Sum, Count, Avg, Min, Max | CountDistinct, Percentage | Weighted aggregations, custom AGGX |
| Context operators | None used | `In` with simple dims | `ForEach`, `ForAll`, `In` nested combos |
| Running/Window functions | None | RunningSum, Rank | Previous, MovingAverage(N), Interpolation |
| @Prompt functions | None | Mono-value, dropdown | Cascading, multi-value, free-text, @Variable |
| Variable references | Simple variables | Variables referencing other variables | Circular references, pass-through SQL in variable |

### Category 3: Visual Types
| Criterion | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| Charts | Bar, Line, Pie, Donut, Area, Scatter | Combined charts, Waterfall, TreeMap | Radar, 3D charts, Box plot |
| Tables | Simple table | Cross-tab with subtotals | Cross-tab with nested breaks + alerters |
| Interactive controls | None | Dropdown slicers | Text-entry controls, cascading input controls |
| Map visuals | None | Geo map (lat/long) | Custom SVG map |

### Category 4: Report Structure
| Criterion | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| Pages/tabs | 1–5 tabs | 6–15 tabs | > 15 tabs or deeply nested sections |
| Sections/groups | None | Section with group break | Multi-level nested sections with breaks |
| Sub-reports | None | 1–2 linked reports | > 2, or cross-document OpenDocument links |
| Drill paths | Simple drill in same report | Drill-through to other report | Multi-hop drill chain across 3+ reports |

### Category 5: Security & RLS
| Criterion | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| Row-level security | None | Static RLS (mapped to users) | Dynamic RLS based on universe @Variable |
| BO security profile | Basic access rights | Folder-level restrictions | Object-level security on individual dimensions |
| Data-level security | None | Connection-level filtering | Universe-level restrictions + row restriction |
| Publication recipients | ≤ 10 | 11–50 | > 50 or dynamic distribution list |

### Category 6: Scheduling & Distribution
| Criterion | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| Schedule type | None or simple daily | Weekly/monthly recurrence | Event-based, dependency chain |
| Output format | Web viewer | PDF, Excel export | Burst to individual files per recipient |
| Destination | BI Launchpad / inbox | Email with attachment | FTP, SFTP, custom folder, printer |
| Publication personalization | None | Filter-based personalization | Profile-based burst with different data per user |

### Category 7: Crystal Reports Specifics
| Criterion | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| Report type | Simple list | Group/summary with subtotals | Cross-tab with complex formulas |
| Data source | Single stored procedure or table | Multiple tables with joins | Command object with raw SQL |
| Special features | None | Subreports, running totals | Custom DLL, `WhilePrintingRecords`, repository |
| Barcode/label | None | Standard barcode font | Custom barcode DLL, label layout |
| Page layout | Portrait/Landscape simple | Multi-column layout | Pixel-perfect placement dependent on printer DPI |

### Category 8: Advanced / SDK
| Criterion | GREEN | YELLOW | RED |
|-----------|-------|--------|-----|
| SDK integration | None | OpenDocument URL | Custom BO SDK application |
| Xcelsius/Design Studio | None | Simple gauge dashboard | Complex Flash-based interactivity |
| Live Office | None | Simple Excel embed | Complex multi-query Live Office workbook |
| BO Explorer usage | None | Light usage | Heavy ad-hoc analysis dependency |

---

## Scoring Methodology

### Per-Report Score

```
For each category:
  GREEN = 3 points
  YELLOW = 2 points
  RED = 1 point

Category Score = Average of all criteria within category
Report Score = Average of all applicable category scores (skip N/A categories)

Interpretation:
  2.5 – 3.0  → Low complexity   (auto-migratable, minimal manual work)
  2.0 – 2.4  → Medium complexity (mostly automated, some adaptation needed)
  1.5 – 1.9  → High complexity   (significant manual work required)
  1.0 – 1.4  → Very High         (manual rewrite, consider redesign)
```

### Portfolio-Level Aggregation

```
Total Reports: N
├── Low Complexity:     n₁ (score 2.5-3.0)   → Auto-migrate first (Wave 1)
├── Medium Complexity:  n₂ (score 2.0-2.4)   → Adapt and migrate (Wave 2)
├── High Complexity:    n₃ (score 1.5-1.9)   → Redesign and migrate (Wave 3)
└── Very High:          n₄ (score 1.0-1.4)   → Evaluate: migrate vs. retire vs. rewrite

Migration Readiness Index = (3*n₁ + 2*n₂ + 1*n₃ + 0*n₄) / (3*N) × 100%
```

---

## Fidelity Classification

After migration, classify each object's output quality:

| Classification | Symbol | Meaning | Action |
|---------------|--------|---------|--------|
| **Fully Migrated** | ✅ | Output matches original within tolerance | Sign off |
| **Approximated** | ⚠️ | Functionally equivalent, minor visual/behavior difference | Document delta, get stakeholder acceptance |
| **Manual Review** | 🔧 | Partial conversion, needs manual completion | Estimate manual effort, assign to developer |
| **Unsupported** | ❌ | Cannot be represented in Power BI | Evaluate alternatives: redesign, retire, or custom visual |

### Expected Distribution (typical BO portfolio)

```
Fully Migrated:  45-55%   (simple reports, standard charts/tables)
Approximated:    25-35%   (context operators, cross-tabs, alerters)
Manual Review:   10-15%   (complex Crystal, @Prompt, nested sections)
Unsupported:      2-5%    (custom DLLs, Flash, repository objects)
```

---

## Strategy Advisor Matrix

Based on assessment scores, recommend the target architecture:

| Source | Complexity | Data Volume | Target | Reasoning |
|--------|-----------|-------------|--------|-----------|
| Webi (simple) | Low | < 1M rows | Power BI Import | Fastest, full DAX, scheduled refresh |
| Webi (complex) | Medium | 1M–100M rows | Power BI Direct Lake | Lakehouse + Semantic Model, near-real-time |
| Webi (enterprise) | High | > 100M rows | Power BI DirectQuery to Lakehouse | Large scale, live queries |
| Crystal (standard) | Low–Medium | Any | Paginated Report (Power BI) | Maintained pixel-perfect layout |
| Crystal (complex) | High | Any | Paginated + Power BI companion | Paginated for print, PBI for interactive |
| Xcelsius | Any | < 10M rows | Power BI Dashboard | Full upgrade — Flash obsolete |
| BO Explorer / ad-hoc | Any | Any | Power BI Q&A + Self-service | Natural language → ad-hoc analysis |
| Publication (burst) | Medium | Any | Paginated data-driven subscription | Closest equivalent for burst distribution |
| SDK custom app | High | Any | Power BI Embedded | Complete rewrite of integration layer |

---

## Sample Assessment Output

```
╔══════════════════════════════════════════════════╗
║          BO Migration Assessment Report          ║
╠══════════════════════════════════════════════════╣
║ Report: Monthly Sales Dashboard (Webi)           ║
║ Universe: Sales_Universe_v3                      ║
╠══════════════════════════════════════════════════╣
║ Category                        │ Score │ Status ║
║─────────────────────────────────┼───────┼────────║
║ 1. Data Sources & Connectivity  │  2.75 │ 🟢    ║
║ 2. Formulas & Expressions       │  2.00 │ 🟡    ║
║ 3. Visual Types                 │  2.75 │ 🟢    ║
║ 4. Report Structure             │  2.25 │ 🟡    ║
║ 5. Security & RLS               │  2.50 │ 🟢    ║
║ 6. Scheduling & Distribution    │  2.50 │ 🟢    ║
║ 7. Crystal Reports              │  N/A  │  —     ║
║ 8. Advanced / SDK               │  3.00 │ 🟢    ║
╠══════════════════════════════════════════════════╣
║ Overall Score: 2.54 → Low Complexity             ║
║ Recommended: Wave 1 (Auto-migrate)               ║
║ Target: Power BI Import mode                     ║
║ Est. Effort: 2-3 days                            ║
║ Key Risks:                                       ║
║  - ForEach context operator in 3 formulas        ║
║  - Nested section with group break on Region     ║
╚══════════════════════════════════════════════════╝
```

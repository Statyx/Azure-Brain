# BO Migration — Discovery Questionnaire

Use this questionnaire during the first engagement meeting with the customer.

---

## 1. Current BO Environment

### Infrastructure
- [ ] SAP BO version: _____ (XI 3.1 / BI 4.1 / BI 4.2 / BI 4.3)
- [ ] Deployment: On-prem / SAP Cloud / Hybrid
- [ ] OS: Windows / Linux
- [ ] BO Servers: Number of CMS, processing, web, job servers: _____
- [ ] Clustering: Yes / No
- [ ] Current BO license type: Named / Concurrent — Count: _____
- [ ] License renewal / expiry date: _____

### Data Sources
- [ ] Primary databases: _____  (Oracle / SQL Server / SAP HANA / DB2 / Teradata / MySQL / Other)
- [ ] Number of distinct data connections in CMC: _____
- [ ] Connection types: JDBC / ODBC / JNDI / BICS / OLAP
- [ ] Any SAP BW/BEx queries? Yes / No — Count: _____
- [ ] Any stored procedures called from universes? Yes / No

### Volumes
| Asset | Count | Active (used last 6 months) |
|-------|-------|-----------------------------|
| Universes (.unx / .unv) | | |
| Webi Reports | | |
| Crystal Reports | | |
| Lumira / Explorer documents | | |
| Xcelsius / Design Studio | | |
| Publications | | |
| Scheduled instances (total) | | |
| Analysis for OLAP workbooks | | |
| Live Office documents | | |
| BO SDK custom applications | | |
| Registered users | | |
| Active users (last 30 days) | | |
| Concurrent users (peak) | | |

---

## 2. Universe Complexity Assessment

For each universe (or top 10 by usage):

| Universe Name | Tables/Joins | Derived Tables | Contexts | LOVs | Row Restrictions | Aggregate Awareness | Linked? |
|---------------|:------------:|:--------------:|:--------:|:----:|:----------------:|:-------------------:|:-------:|
| | | | | | | | |

### Key questions:
- Do universes use **@Prompt** with cascading LOVs? How many?
- Are there **derived tables** with complex SQL (subqueries, CTEs, window functions)?
- Do universes use **aggregate awareness**?
- Are universes **linked** (@BusinessFilter, linked universes)?
- Are there **multi-source universes** (federation across different databases)?

---

## 3. Report Complexity Assessment

### Webi Reports — Sample top 20 by usage:

| Report Name | Universe(s) | Prompts | Variables/Formulas | Cross-tabs | Sections | Alerters | Drill | Complexity (1-5) |
|-------------|-------------|:-------:|:-----------------:|:----------:|:--------:|:--------:|:-----:|:----------------:|
| | | | | | | | | |

### Crystal Reports — Sample top 10:

| Report Name | Data Source | Parameters | Subreports | Formulas | Cross-Tab | Barcode/Image | Complexity (1-5) |
|-------------|------------|:----------:|:----------:|:--------:|:---------:|:-------------:|:----------------:|
| | | | | | | | |

### Key questions:
- Which reports use **BO context operators** (In, ForEach, ForAll)? → These need DAX rewrite
- Are there reports with **Previous()** or **RunningSum()**? → Time intelligence rewrite
- Any reports with **embedded JavaScript** or **VBA macros**?
- Do reports use **tracking** (data changes between refreshes)?
- Do reports **export to specific formats** (PDF, Excel, CSV) for downstream systems?

---

## 4. Security Model

### CMC Structure
- [ ] Number of top-level folders: _____
- [ ] Number of user groups: _____
- [ ] Security model: Folder-based / Group-based / Hybrid
- [ ] Row-level security in universes: Yes / No — Which ones?
- [ ] Profile-based security (BO security profiles): Yes / No
- [ ] Connection-level restrictions: Yes / No

### Identity
- [ ] User source: Enterprise (AD synced) / LDAP / SAP / Local CMC
- [ ] Already using Entra ID (Azure AD)? Yes / No
- [ ] Already using Microsoft 365? Yes / No
- [ ] SSO configured? Type: _____

---

## 5. Scheduling & Distribution

- [ ] Number of scheduled reports: _____
- [ ] Scheduling frequency: Mostly daily / Weekly / Mixed
- [ ] Publication (bursting): Yes / No — Count: _____
  - Burst by: Parameter / Group / Profile
  - Delivery: Email / BO Inbox / File system / FTP
- [ ] Event-based triggers: Yes / No — Describe: _____
- [ ] Report dependencies (A must finish before B starts): Yes / No
- [ ] Alerting on schedule failures: Yes / No — How?

---

## 6. Integration Points

- [ ] **Live Office**: Excel integration with BO? Count of documents: _____
- [ ] **BO SDK apps**: Custom .NET / Java / REST applications? Describe: _____
- [ ] **RESTful Web Services**: Reports consumed via BO REST API?
- [ ] **Embedded**: BO reports embedded in portals / SharePoint / custom apps?
- [ ] **File exports**: Automated exports to file shares / FTP / SharePoint?
- [ ] **ETL dependency**: Do ETL jobs trigger BO refreshes or vice versa?

---

## 7. Pain Points & Expectations

### Current pain points with BO:
- [ ] Performance (slow reports)
- [ ] Licensing costs
- [ ] Complex administration
- [ ] Lack of self-service
- [ ] Poor mobile experience
- [ ] Outdated technology (Flash dependencies)
- [ ] Hard to find reports (BI Launchpad navigation)
- [ ] Other: _____

### Expectations from Fabric migration:
- [ ] Cost reduction
- [ ] Modern self-service BI
- [ ] Real-time data access
- [ ] AI / Copilot capabilities
- [ ] Consolidation (single platform)
- [ ] Mobile access
- [ ] Better governance
- [ ] Cloud-first strategy
- [ ] Other: _____

---

## 8. Constraints & Dependencies

- [ ] **Timeline**: Hard deadline? BO license expiry?
- [ ] **Budget**: Capex / Opex constraints?
- [ ] **Team**: Who does the migration? Internal / SI / Mixed?
- [ ] **Fabric already in use?** Yes / No — What for?
- [ ] **Power BI already in use?** Yes / No — Extent?
- [ ] **Change management**: User readiness assessment done?
- [ ] **Compliance**: GDPR, SOX, HIPAA, industry-specific?
- [ ] **Data residency**: Must data stay in specific region?
- [ ] **Parallel run requirement**: How long? Business sign-off process?

---

## 9. Governance & Organization Readiness

### COE & Champion Network
- [ ] Existing Center of Excellence (COE) for BI? Yes / No
- [ ] Existing Power BI or Fabric community/champions? Yes / No — Size: _____
- [ ] Identified power users per department who can become champions? List: _____
- [ ] Internal training capability (can you train end-users)? Yes / No
- [ ] Who will own content post-migration? Centralized COE / Departments / Hybrid

### Governance Maturity
- [ ] Naming conventions for reports/workspaces defined? Yes / No
- [ ] Content ownership model defined (every report has an owner)? Yes / No
- [ ] Certification/endorsement process for shared data? Yes / No
- [ ] Data quality processes in place for source systems? Yes / No
- [ ] Change management plan for BO → Fabric transition? Yes / No

### Success Criteria (define at project start)
- [ ] What defines "migration success" for the executive sponsor? _____
- [ ] Target: % of users actively using Fabric after migration: _____
- [ ] Target: Legacy BO decommission date: _____
- [ ] Acceptable parallel run duration: _____ weeks
- [ ] Performance target: Report page load < _____ seconds
- [ ] How will adoption be measured? (Activity logs / surveys / other): _____

---

## 10. Data Reusability Assessment

> This section identifies opportunities to build shared semantic models (replacing BO universes) that can serve multiple reports.

- [ ] Which BO universes are shared across multiple reports? List:
  - Universe: _____ → Used by _____ reports
  - Universe: _____ → Used by _____ reports
- [ ] Are there duplicate/overlapping universes (same data, different structure)? Yes / No
- [ ] Can universes be **consolidated** into fewer, broader semantic models? (target: >3 reports per model)
- [ ] Are there "personal" universes that should not become shared models?
- [ ] Which universes have the most complex business logic (measures, derived tables, contexts)?
  - These become migration-critical semantic models — assign senior DAX developer
- [ ] Data layer consolidation: Can multiple database connections be replaced by a single Lakehouse? Yes / No — Candidates: _____

---

## 11. Quick Wins Identification

After filling this questionnaire, identify:
1. **Top 10 most-used reports** → Migrate first (highest visibility)
2. **Simple reports (complexity 1-2)** → Quick automation candidates
3. **Dormant reports (>6 months unused)** → Retire, don't migrate
4. **Crystal Reports with simple layouts** → Paginated report conversion
5. **Dashboards / Xcelsius** → Power BI dashboard replacement (Flash EOL)

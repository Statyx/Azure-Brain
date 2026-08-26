# Advanced Test Patterns

Companion to [`instructions.md`](instructions.md) — load it before writing tests
for a Fabric project. The spine file defines *when* tests run and what gates on
them; this file defines *what the tests look like*.

Distilled from a 3 760-test, 140-file Fabric migration framework (OACToFabric).
Use them as templates rather than copying blindly: the assertions are the point,
the file names are not.

---

### Pattern A — Model / TMDL Structural Validation
Validate model artifacts **before** deployment, not after.

```python
@pytest.mark.smoke
class TestModelStructure:
    """Validate model.bim / TMDL integrity offline."""

    def test_model_bim_builds(self):
        """build_model_bim() returns valid JSON with required structure."""
        from deploy_semantic_model import build_model_bim
        import yaml, json
        cfg = yaml.safe_load(Path("src/config.yaml").read_text())
        state = json.loads(Path("src/state.json").read_text())
        bim = build_model_bim(cfg, state)
        assert "model" in bim
        assert bim["model"].get("defaultPowerBIDataSourceVersion") == "PowerBI_V3"

    def test_tables_have_lineage_tags(self):
        bim = _load_model()
        for tbl in bim["model"]["tables"]:
            assert "lineageTag" in tbl, f'Table {tbl["name"]} missing lineageTag'

    def test_relationships_reference_valid_tables(self):
        bim = _load_model()
        table_names = {t["name"] for t in bim["model"]["tables"]}
        for rel in bim["model"].get("relationships", []):
            assert rel["fromTable"] in table_names, f'Bad rel: {rel["fromTable"]}'
            assert rel["toTable"] in table_names, f'Bad rel: {rel["toTable"]}'

    def test_measures_dax_balanced_parens(self):
        bim = _load_model()
        for tbl in bim["model"]["tables"]:
            for m in tbl.get("measures", []):
                expr = "".join(m["expression"]) if isinstance(m["expression"], list) else m["expression"]
                assert expr.count("(") == expr.count(")"), \
                    f'Measure {m["name"]}: unbalanced parens'
```

Key checks per OACToFabric `test_tmdl_validator.py`:
- `model.tmdl` or `model.bim` exists
- `.platform` JSON valid (if TMDL folder mode)
- `tables/` directory present (if TMDL folder mode)
- Every table has `lineageTag` (UUID)
- Every measure's DAX has balanced parentheses
- Relationships reference existing tables only
- `defaultPowerBIDataSourceVersion` = `"PowerBI_V3"`
- No `isKey` on Direct Lake tables (engine manages keys)

### Pattern B — Deployment Dry-Run
Pre-validate a deployment manifest **without hitting Azure**.

```python
@pytest.mark.smoke
class TestDeploymentDryRun:
    """Pre-deploy validation — catches naming, ordering, missing deps."""

    def test_fabric_item_names_valid(self):
        """Fabric names: 1-256 chars, no leading/trailing spaces."""
        import yaml
        cfg = yaml.safe_load(Path("src/config.yaml").read_text())
        for key in ["workspace_name", "lakehouse_name", "semantic_model_name"]:
            name = cfg.get(key, "")
            assert 1 <= len(name.strip()) <= 256, f"{key}='{name}' invalid length"
            assert name == name.strip(), f"{key} has leading/trailing spaces"

    def test_deployment_order_respected(self):
        """deploy_all.py must call steps in dependency order."""
        src = Path("src/deploy_all.py").read_text()
        steps = re.findall(r'(deploy_\w+)', src)
        REQUIRED_ORDER = ["deploy_workspace", "deploy_lakehouse",
                          "deploy_setup_notebook", "deploy_semantic_model",
                          "deploy_report"]
        indices = []
        for step in REQUIRED_ORDER:
            matches = [i for i, s in enumerate(steps) if step in s]
            if matches:
                indices.append(matches[0])
        assert indices == sorted(indices), \
            f"Deployment order broken: {list(zip(REQUIRED_ORDER, indices))}"

    def test_no_duplicate_item_names(self):
        """All deployed item names must be unique within the workspace."""
        import yaml
        cfg = yaml.safe_load(Path("src/config.yaml").read_text())
        names = [v for k, v in cfg.items() if k.endswith("_name") and isinstance(v, str)]
        assert len(names) == len(set(names)), f"Duplicate names: {names}"
```

Key checks per OACToFabric `test_tools.py::TestFabricDeploymentDryRun`:
- All Fabric item names are 1-256 chars, no leading/trailing whitespace
- No duplicate item names within a workspace
- Deployment order respects dependencies (Lakehouse → Notebook → Model → Report)
- All referenced capacity IDs are valid UUID format
- State file not stale (workspace_id present if items already deployed)
- Blockers vs warnings: blockers = fatal, warnings = informational

### Pattern C — VCR Cassettes (Record/Replay API Calls)
Test Fabric API interactions offline using recorded HTTP exchanges.

```python
import json, tempfile

class Cassette:
    """Record or replay Fabric API calls."""
    def __init__(self, path: Path):
        self.path = path
        self.calls = json.loads(path.read_text()) if path.exists() else []
        self._idx = 0

    def record(self, method, url, status, body):
        self.calls.append({"method": method, "url": url,
                           "status": status, "body": body})
        self.path.write_text(json.dumps(self.calls, indent=2))

    def replay(self):
        if self._idx >= len(self.calls):
            raise IndexError("No more recorded calls")
        call = self.calls[self._idx]
        self._idx += 1
        return call


@pytest.fixture
def cassette(tmp_path):
    return Cassette(tmp_path / "cassette.json")
```

Usage: record real API calls once → replay in CI without credentials.
Per OACToFabric: `RequestRecorder`, `PlaybackEngine`, `MockOACServer`.

### Pattern D — Data Reconciliation
Compare expected vs actual data with tolerance.

```python
@pytest.mark.smoke
class TestDataReconciliation:
    """Row counts, column stats, null checks."""

    def test_csv_row_counts(self):
        """Each CSV must have the expected minimum rows."""
        EXPECTATIONS = {
            "dim_countries.csv": 5,
            "dim_disciplines.csv": 3,
            "fact_benchmarks.csv": 100,
        }
        for name, min_rows in EXPECTATIONS.items():
            p = Path("data/raw") / name
            if p.exists():
                lines = p.read_text().strip().split("\n")
                assert len(lines) - 1 >= min_rows, \
                    f"{name}: {len(lines)-1} rows < {min_rows}"

    def test_no_empty_columns(self):
        """No CSV should have entirely-null columns."""
        import csv
        for p in Path("data/raw").glob("*.csv"):
            with open(p, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            if not rows:
                continue
            for col in rows[0].keys():
                vals = [r[col].strip() for r in rows if r[col].strip()]
                assert len(vals) > 0, f"{p.name}: column '{col}' is entirely empty"

    def test_numeric_values_in_range(self):
        """Fact numeric columns must be non-negative."""
        import csv
        p = Path("data/raw/fact_benchmarks.csv")
        if not p.exists():
            pytest.skip()
        with open(p, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for row in rows[:50]:  # sample first 50
            for key, val in row.items():
                try:
                    v = float(val)
                    assert v >= 0, f"Negative value in {key}: {v}"
                except ValueError:
                    pass  # skip non-numeric
```

Per OACToFabric `test_data_reconciliation.py`:
- Row count queries (expected ± tolerance)
- Null count per column
- Distinct count per column
- Numeric aggregates (min/max/sum/avg)
- Tolerance-based comparison (`abs(a-b)/max(abs(a),1e-9) < tolerance`)
- Offline snapshot comparison (no live DB needed)

### Pattern E — DAX Validation
Catch DAX syntax issues before executeQueries.

```python
@pytest.mark.smoke
class TestDAXValidation:
    """Validate DAX expressions in model measures."""

    def test_balanced_parentheses(self, measures):
        for m in measures:
            assert m["dax"].count("(") == m["dax"].count(")"), \
                f'{m["name"]}: unbalanced parens'

    def test_var_has_return(self, measures):
        """Every VAR block must have a matching RETURN."""
        for m in measures:
            dax = m["dax"].upper()
            if "VAR " in dax:
                assert "RETURN" in dax, f'{m["name"]}: VAR without RETURN'

    def test_no_unknown_functions(self, measures):
        """Flag functions not in the standard DAX library."""
        KNOWN = {"SUM", "CALCULATE", "FILTER", "ALL", "VALUES",
                 "SUMX", "AVERAGEX", "COUNTROWS", "DIVIDE",
                 "RELATED", "SELECTEDVALUE", "IF", "SWITCH",
                 "BLANK", "ISBLANK", "MAX", "MIN", "AVERAGE",
                 "DISTINCTCOUNT", "CONCATENATE", "FORMAT",
                 "DATESYTD", "TOTALYTD", "SAMEPERIODLASTYEAR",
                 "DATEADD", "PREVIOUSMONTH", "PREVIOUSYEAR",
                 "HASONEVALUE", "KEEPFILTERS", "REMOVEFILTERS",
                 "UNION", "EXCEPT", "INTERSECT", "TREATAS",
                 "GENERATESERIES", "ADDCOLUMNS", "SELECTCOLUMNS",
                 "FIRSTDATE", "LASTDATE", "EARLIER", "RANKX",
                 "TOPN", "MAXX", "MINX", "CONCATENATEX",
                 "CONTAINSSTRING", "ISINSCOPE", "USERELATIONSHIP",
                 "CROSSJOIN", "NATURALLEFTOUTERJOIN",
                 "NOT", "AND", "OR", "TRUE", "FALSE", "IN",
                 "PATHITEM", "PATHLENGTH", "PATH",
                 "COALESCE", "COMBINEVALUES", "DATATABLE",
                 "ERROR", "LOOKUPVALUE", "SUMMARIZECOLUMNS",
                 "CALENDAR", "CALENDARAUTO", "DATE", "YEAR",
                 "MONTH", "DAY", "NOW", "TODAY", "EOMONTH",
                 "NETWORKDAYS", "ROUND", "ROUNDUP", "ROUNDDOWN",
                 "INT", "ABS", "POWER", "SQRT", "LN", "LOG",
                 "FIXED", "LEFT", "RIGHT", "MID", "LEN",
                 "TRIM", "UPPER", "LOWER", "SUBSTITUTE",
                 "FIND", "SEARCH", "REPT", "UNICHAR", "VALUE"}
        import re as _re
        for m in measures:
            funcs = set(_re.findall(r'\b([A-Z][A-Z0-9_]+)\s*\(', m["dax"].upper()))
            unknown = funcs - KNOWN
            if unknown:
                # warn, don't fail — custom functions are possible
                import warnings
                warnings.warn(f'{m["name"]}: unknown DAX functions: {unknown}')
```

Per OACToFabric `test_tools.py::TestDAXDeepValidator`:
14 error codes — DAX001 unbalanced parens, DAX003 unknown function,
DAX006 VAR without RETURN, etc.

### Pattern F — Report Visual Feedback Loop (MANDATORY)
**This is the #1 source of bugs** — blank visuals, overlaps, out-of-bounds.
Use `visual_validator.py` (in `Azure-Brain/Meta-Brain/agents/testing-agent/`) to validate
`build_report()` output BEFORE deployment.

The validator catches these recurring pitfalls:
1. **Missing prototypeQuery** → visual renders completely BLANK (no error shown)
2. **Config/filters not stringified** → API accepts but renders blank
3. **Visual overlaps** → content visuals (z>0) stacked on top of each other
4. **Out-of-bounds** → visuals outside 1280×720 canvas get clipped
5. **Alias mismatches** → Select references alias not in From → blank visual
6. **Unknown visual types** → typos in visualType go undetected
7. **Card minimum height** → h<100px clips callout text

```python
# In tests/test_report_visuals.py — call build_report() offline, then validate
from visual_validator import ReportValidator

@pytest.fixture(scope="module")
def report():
    from deploy_report import build_report  # or build_report_json
    return build_report(stub_state, config)[0]

@pytest.mark.smoke
class TestReportVisualFeedback:
    def test_no_errors(self, report):
        v = ReportValidator(report)
        v.validate_all()
        errs = v.errors()
        assert not errs, v.summary()
```

**Rule**: Every project with a `deploy_report.py` MUST have `test_report_visuals.py`.
Run it BEFORE every report deployment.

"""
Scaffold test infrastructure for a new Fabric demo project.

Usage:
    python scaffold_tests.py <project_path>

Creates:
    tests/conftest.py
    tests/test_smoke.py
    tests/test_report_visuals.py  (if deploy_report.py exists)
    pytest.ini
"""
import sys
import textwrap
from pathlib import Path


def scaffold(project_path: Path):
    tests_dir = project_path / "tests"
    tests_dir.mkdir(exist_ok=True)

    src_dir = project_path / "src"
    has_report = (src_dir / "deploy_report.py").exists()
    py_files = list(src_dir.glob("*.py")) if src_dir.exists() else []
    deploy_scripts = [f.stem for f in py_files if f.stem.startswith("deploy_")]

    # --- pytest.ini ---
    pytest_ini = project_path / "pytest.ini"
    if not pytest_ini.exists():
        pytest_ini.write_text(textwrap.dedent("""\
            [pytest]
            testpaths = tests
            markers =
                smoke: fast offline tests
                integration: require Azure credentials
                regression: domain-specific tests
        """), encoding="utf-8")
        print(f"  Created {pytest_ini}")

    # --- conftest.py ---
    conftest = tests_dir / "conftest.py"
    if not conftest.exists():
        conftest.write_text(textwrap.dedent("""\
            import sys
            from pathlib import Path

            ROOT = Path(__file__).resolve().parent.parent
            SRC = ROOT / "src"
            sys.path.insert(0, str(SRC))

            import pytest

            @pytest.fixture
            def src_dir():
                return SRC

            @pytest.fixture
            def project_root():
                return ROOT
        """), encoding="utf-8")
        print(f"  Created {conftest}")

    # --- test_smoke.py ---
    smoke = tests_dir / "test_smoke.py"
    if not smoke.exists():
        # Build file list for parametrize
        file_names = [f.name for f in py_files]
        smoke_content = textwrap.dedent(f"""\
            import pytest
            import py_compile
            import json
            from pathlib import Path

            SRC = Path(__file__).resolve().parent.parent / "src"

            @pytest.mark.smoke
            class TestSyntax:
                @pytest.fixture(params={file_names!r})
                def pyfile(self, request):
                    return SRC / request.param

                def test_compiles(self, pyfile):
                    py_compile.compile(str(pyfile), doraise=True)

            @pytest.mark.smoke
            class TestConfig:
                def test_config_exists(self):
                    assert (SRC / "config.yaml").exists()

                def test_config_keys(self):
                    import yaml
                    cfg = yaml.safe_load((SRC / "config.yaml").read_text(encoding="utf-8"))
                    for key in ["workspace_name", "capacity_id"]:
                        assert key in cfg, f"Missing config key: {{key}}"

                def test_config_values_nonempty(self):
                    import yaml
                    cfg = yaml.safe_load((SRC / "config.yaml").read_text(encoding="utf-8"))
                    for key in ["workspace_name"]:
                        assert cfg.get(key), f"Empty config key: {{key}}"
        """)
        smoke.write_text(smoke_content, encoding="utf-8")
        print(f"  Created {smoke} ({len(file_names)} .py files parametrized)")

    # --- test_report_visuals.py (only if deploy_report.py exists) ---
    if has_report:
        visuals_test = tests_dir / "test_report_visuals.py"
        if not visuals_test.exists():
            visuals_test.write_text(textwrap.dedent("""\
                import pytest
                import sys
                from pathlib import Path

                SRC = Path(__file__).resolve().parent.parent / "src"
                BRAIN = Path(__file__).resolve().parent.parent.parent / "Github_Brain"
                sys.path.insert(0, str(SRC))
                sys.path.insert(0, str(BRAIN / "agents" / "testing-agent"))

                from visual_validator import ReportValidator

                @pytest.fixture(scope="module")
                def report_data():
                    # Import your project's build_report function and call it
                    # Return the report dict for validation
                    raise NotImplementedError(
                        "Edit this fixture to call your build_report() function"
                    )

                @pytest.mark.smoke
                class TestReportVisualFeedback:
                    def test_no_errors(self, report_data):
                        v = ReportValidator(report_data)
                        v.validate_all()
                        assert not v.errors(), v.errors()

                    def test_warnings_count(self, report_data):
                        v = ReportValidator(report_data)
                        v.validate_all()
                        # Warn but don't fail
                        for w in v.warnings():
                            print(f"WARNING: {w}")
            """), encoding="utf-8")
            print(f"  Created {visuals_test} (requires editing the fixture)")

    print(f"\nDone! Scaffolded tests for {project_path.name}")
    print(f"Run: python -m pytest tests/ -v --tb=short")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scaffold_tests.py <project_path>")
        sys.exit(1)
    scaffold(Path(sys.argv[1]).resolve())

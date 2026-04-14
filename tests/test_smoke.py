"""Smoke tests for Github_Brain knowledge base.

Validates structural integrity: all Python compiles, YAML parses,
agent catalog matches disk, and files are non-empty.
"""
import ast
import json
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
CATALOG_PATH = AGENTS_DIR / "_catalog.yaml"


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def catalog():
    """Parsed _catalog.yaml."""
    return yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def catalog_agent_names(catalog):
    """Set of agent names declared in _catalog.yaml."""
    names = set()
    for domain in catalog.get("domains", {}).values():
        for agent in domain.get("agents", []):
            names.add(agent["name"])
    return names


@pytest.fixture(scope="session")
def agent_folders():
    """Set of agent folder names on disk (excluding _ prefixed files)."""
    return {d.name for d in AGENTS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_")}


# ── Catalog tests ───────────────────────────────────────────────


class TestCatalog:
    """Validate _catalog.yaml structure."""

    def test_catalog_exists(self):
        assert CATALOG_PATH.exists(), "_catalog.yaml missing"

    def test_catalog_parses(self, catalog):
        assert "domains" in catalog

    def test_catalog_has_domains(self, catalog):
        assert len(catalog["domains"]) >= 7

    def test_every_agent_has_name_and_purpose(self, catalog):
        for domain_key, domain in catalog["domains"].items():
            for agent in domain.get("agents", []):
                assert "name" in agent, f"Agent in {domain_key} missing 'name'"
                assert "purpose" in agent, f"{agent['name']} missing 'purpose'"

    def test_no_duplicate_agent_names(self, catalog):
        names = []
        for domain in catalog["domains"].values():
            for agent in domain.get("agents", []):
                names.append(agent["name"])
        assert len(names) == len(set(names)), f"Duplicate agent names: {[n for n in names if names.count(n) > 1]}"


# ── Folder ↔ Catalog sync ──────────────────────────────────────


class TestCatalogSync:
    """Catalog and disk folders must match."""

    def test_every_folder_in_catalog(self, agent_folders, catalog_agent_names):
        orphans = agent_folders - catalog_agent_names
        assert not orphans, f"Folders on disk not in catalog: {orphans}"

    def test_every_catalog_entry_on_disk(self, agent_folders, catalog_agent_names):
        missing = catalog_agent_names - agent_folders
        assert not missing, f"Catalog entries with no folder: {missing}"


# ── Agent structure ─────────────────────────────────────────────


def _all_agent_dirs():
    return sorted(d for d in AGENTS_DIR.iterdir()
                  if d.is_dir() and not d.name.startswith("_"))


@pytest.fixture(scope="session")
def all_agent_dirs():
    return _all_agent_dirs()


class TestAgentStructure:
    """Every agent folder must contain instructions.md."""

    @pytest.fixture(params=[d.name for d in _all_agent_dirs()],
                    ids=[d.name for d in _all_agent_dirs()])
    def agent_dir(self, request):
        return AGENTS_DIR / request.param

    def test_has_instructions(self, agent_dir):
        assert (agent_dir / "instructions.md").exists(), \
            f"{agent_dir.name}/ missing instructions.md"

    def test_instructions_not_empty(self, agent_dir):
        path = agent_dir / "instructions.md"
        if path.exists():
            assert path.stat().st_size > 50, \
                f"{agent_dir.name}/instructions.md is suspiciously small"


# ── Python compilation ──────────────────────────────────────────


EXCLUDED_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", "node_modules"}


def _should_skip(path: pathlib.Path) -> bool:
    """Return True if path is inside an excluded directory."""
    return any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)


def _all_python_files():
    return sorted(
        p for p in ROOT.rglob("*.py")
        if not _should_skip(p)
    )


def _py_ids():
    return [str(p.relative_to(ROOT)) for p in _all_python_files()]


class TestPythonCompiles:
    """All .py files in the repo must compile without syntax errors."""

    @pytest.fixture(params=_all_python_files(), ids=_py_ids())
    def py_file(self, request):
        return request.param

    def test_compiles(self, py_file):
        source = py_file.read_text(encoding="utf-8", errors="replace")
        try:
            ast.parse(source, filename=str(py_file))
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {py_file.relative_to(ROOT)}: {e}")

    def test_no_hardcoded_secrets(self, py_file):
        # Skip test files (they contain the patterns as literals)
        if py_file.parent.name == "tests":
            pytest.skip("test file")
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in ["AKIA", "ghp_", "gho_"]:
            assert pattern not in content, \
                f"Potential secret ({pattern}...) in {py_file.relative_to(ROOT)}"


# ── Markdown non-empty ──────────────────────────────────────────


def _root_md_files():
    return sorted(ROOT.glob("*.md"))


class TestRootMarkdown:
    """Root-level .md files should be non-trivial."""

    @pytest.fixture(params=_root_md_files(),
                    ids=[f.name for f in _root_md_files()])
    def md_file(self, request):
        return request.param

    def test_not_empty(self, md_file):
        assert md_file.stat().st_size > 30, \
            f"{md_file.name} is suspiciously small"


# ── JSON templates ──────────────────────────────────────────────


def _all_json_files():
    return sorted(
        p for p in ROOT.rglob("*.json")
        if not _should_skip(p)
    )


class TestJsonTemplates:
    """All JSON files must be valid."""

    @pytest.fixture(params=_all_json_files(),
                    ids=[str(f.relative_to(ROOT)) for f in _all_json_files()])
    def json_file(self, request):
        return request.param

    def test_valid_json(self, json_file):
        content = json_file.read_text(encoding="utf-8")
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {json_file.relative_to(ROOT)}: {e}")

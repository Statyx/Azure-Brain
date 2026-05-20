"""Smoke tests for Azure-Brain knowledge base (Fabric-Brain + Meta-Brain).

Validates structural integrity: catalogs parse, agent folders match catalogs,
instructions.md exists per agent, Python files compile, JSON parses.
"""
import ast
import json
import pathlib

import pytest
import yaml

# ROOT = Azure-Brain umbrella (parent of Fabric-Brain and Meta-Brain)
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BRAINS = ["Fabric-Brain", "Meta-Brain"]


def _agents_dir(brain_name: str) -> pathlib.Path:
    return ROOT / brain_name / "agents"


def _catalog_path(brain_name: str) -> pathlib.Path:
    return _agents_dir(brain_name) / "_catalog.yaml"


def _load_catalog(brain_name: str) -> dict:
    return yaml.safe_load(_catalog_path(brain_name).read_text(encoding="utf-8"))


def _catalog_agent_names(brain_name: str) -> set[str]:
    cat = _load_catalog(brain_name)
    names = set()
    for domain in cat.get("domains", {}).values():
        for agent in domain.get("agents", []):
            names.add(agent["name"])
    return names


def _folder_agent_names(brain_name: str) -> set[str]:
    ad = _agents_dir(brain_name)
    if not ad.exists():
        return set()
    return {d.name for d in ad.iterdir()
            if d.is_dir() and not d.name.startswith("_")}


def _all_agent_dirs() -> list[pathlib.Path]:
    out = []
    for b in BRAINS:
        ad = _agents_dir(b)
        if ad.exists():
            out.extend(sorted(d for d in ad.iterdir()
                              if d.is_dir() and not d.name.startswith("_")))
    return out


# ── Catalog tests (one per brain) ───────────────────────────────


@pytest.mark.parametrize("brain", BRAINS)
class TestCatalog:
    def test_catalog_exists(self, brain):
        assert _catalog_path(brain).exists(), f"{brain}/agents/_catalog.yaml missing"

    def test_catalog_parses(self, brain):
        assert "domains" in _load_catalog(brain)

    def test_catalog_has_domains(self, brain):
        assert len(_load_catalog(brain)["domains"]) >= 1

    def test_every_agent_has_name_and_purpose(self, brain):
        for domain_key, domain in _load_catalog(brain)["domains"].items():
            for agent in domain.get("agents", []):
                assert "name" in agent, f"{brain}/{domain_key} agent missing 'name'"
                assert "purpose" in agent, f"{brain}/{agent.get('name')} missing 'purpose'"

    def test_no_duplicate_agent_names(self, brain):
        names = []
        for domain in _load_catalog(brain)["domains"].values():
            for agent in domain.get("agents", []):
                names.append(agent["name"])
        dups = [n for n in names if names.count(n) > 1]
        assert not dups, f"{brain} duplicate agent names: {dups}"


# ── Folder ↔ Catalog sync ──────────────────────────────────────


@pytest.mark.parametrize("brain", BRAINS)
class TestCatalogSync:
    def test_every_folder_in_catalog(self, brain):
        orphans = _folder_agent_names(brain) - _catalog_agent_names(brain)
        assert not orphans, f"{brain} folders not in catalog: {orphans}"

    def test_every_catalog_entry_on_disk(self, brain):
        missing = _catalog_agent_names(brain) - _folder_agent_names(brain)
        assert not missing, f"{brain} catalog entries with no folder: {missing}"


# ── Agent structure ─────────────────────────────────────────────


class TestAgentStructure:
    """Every agent folder (across both brains) must contain instructions.md."""

    @pytest.fixture(params=_all_agent_dirs(),
                    ids=[f"{d.parent.parent.name}/{d.name}" for d in _all_agent_dirs()])
    def agent_dir(self, request):
        return request.param

    def test_has_instructions(self, agent_dir):
        assert (agent_dir / "instructions.md").exists(), \
            f"{agent_dir}/instructions.md missing"

    def test_instructions_not_empty(self, agent_dir):
        path = agent_dir / "instructions.md"
        if path.exists():
            assert path.stat().st_size > 50, \
                f"{path} is suspiciously small"


# ── Python compilation ──────────────────────────────────────────


EXCLUDED_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", "node_modules"}


def _should_skip(path: pathlib.Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)


def _all_python_files():
    return sorted(p for p in ROOT.rglob("*.py") if not _should_skip(p))


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
        if py_file.parent.name == "tests":
            pytest.skip("test file")
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in ["AKIA", "ghp_", "gho_"]:
            assert pattern not in content, \
                f"Potential secret ({pattern}...) in {py_file.relative_to(ROOT)}"


# ── Markdown non-empty ──────────────────────────────────────────


def _root_md_files():
    """Markdown files at Azure-Brain umbrella root + each brain root."""
    out = sorted(ROOT.glob("*.md"))
    for b in BRAINS:
        bp = ROOT / b
        if bp.exists():
            out.extend(sorted(bp.glob("*.md")))
    return out


class TestRootMarkdown:
    @pytest.fixture(params=_root_md_files(),
                    ids=[str(f.relative_to(ROOT)) for f in _root_md_files()])
    def md_file(self, request):
        return request.param

    def test_not_empty(self, md_file):
        assert md_file.stat().st_size > 30, \
            f"{md_file.relative_to(ROOT)} is suspiciously small"


# ── JSON templates ──────────────────────────────────────────────


def _all_json_files():
    return sorted(p for p in ROOT.rglob("*.json") if not _should_skip(p))


class TestJsonTemplates:
    """All JSON files must be valid."""

    @pytest.fixture(params=_all_json_files(),
                    ids=[str(f.relative_to(ROOT)) for f in _all_json_files()])
    def json_file(self, request):
        return request.param

    def test_parses(self, json_file):
        try:
            json.loads(json_file.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError as e:
            pytest.fail(f"{json_file.relative_to(ROOT)}: {e}")

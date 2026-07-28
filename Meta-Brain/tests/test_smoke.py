"""Smoke tests for the Azure-Brain knowledge base (every brain in `conftest.BRAINS`).

Validates structural integrity: catalogs parse, agent folders match catalogs,
instructions.md exists per agent, Python files compile, JSON parses.

Brain list and agent discovery live in `conftest.py` (single source of truth,
depth-aware so both flat and domain-nested brains are covered).
"""
import ast
import json
import pathlib

import pytest

from conftest import (
    ROOT,
    BRAINS,
    agent_id,
    all_agent_dirs,
    catalog_agent_names,
    catalog_entries,
    catalog_path,
    folder_agent_names,
    load_catalog,
)

_ALL_AGENT_DIRS = all_agent_dirs()


# ── Catalog tests (one per brain) ───────────────────────────────


@pytest.mark.parametrize("brain", BRAINS)
class TestCatalog:
    def test_catalog_exists(self, brain):
        assert catalog_path(brain).exists(), f"{brain}/agents/_catalog.yaml missing"

    def test_catalog_parses(self, brain):
        assert "domains" in load_catalog(brain)

    def test_catalog_has_domains(self, brain):
        assert len(load_catalog(brain)["domains"]) >= 1

    def test_every_agent_has_name_and_purpose(self, brain):
        for domain_key, domain in load_catalog(brain)["domains"].items():
            for agent in domain.get("agents", []):
                assert "name" in agent, f"{brain}/{domain_key} agent missing 'name'"
                assert "purpose" in agent, f"{brain}/{agent.get('name')} missing 'purpose'"

    def test_no_duplicate_agent_names(self, brain):
        names = [a["name"] for a in catalog_entries(brain)]
        dups = [n for n in names if names.count(n) > 1]
        assert not dups, f"{brain} duplicate agent names: {dups}"

    def test_status_values_are_known(self, brain):
        allowed = {"active", "planned", "deprecated"}
        for agent in catalog_entries(brain):
            status = agent.get("status")
            assert status is None or status in allowed, \
                f"{brain}/{agent['name']} has unknown status '{status}'"


# ── Folder ↔ Catalog sync ──────────────────────────────────────


@pytest.mark.parametrize("brain", BRAINS)
class TestCatalogSync:
    def test_every_folder_in_catalog(self, brain):
        orphans = folder_agent_names(brain) - catalog_agent_names(brain, implemented_only=False)
        assert not orphans, f"{brain} folders not in catalog: {orphans}"

    def test_every_implemented_catalog_entry_on_disk(self, brain):
        missing = catalog_agent_names(brain) - folder_agent_names(brain)
        assert not missing, \
            f"{brain} catalog entries marked implemented but with no folder: {missing}"


# ── Agent structure ─────────────────────────────────────────────


class TestAgentStructure:
    """Every agent folder (across every brain) must contain instructions.md."""

    @pytest.fixture(params=_ALL_AGENT_DIRS,
                    ids=[agent_id(d) for d in _ALL_AGENT_DIRS])
    def agent_dir(self, request):
        return request.param

    def test_has_instructions(self, agent_dir):
        assert (agent_dir / "instructions.md").exists(), \
            f"{agent_id(agent_dir)}/instructions.md missing"

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
            # utf-8-sig tolerates a leading BOM (CLI oracle dumps carry one)
            json.loads(json_file.read_text(encoding="utf-8-sig", errors="replace"))
        except json.JSONDecodeError as e:
            pytest.fail(f"{json_file.relative_to(ROOT)}: {e}")

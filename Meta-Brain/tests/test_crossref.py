"""Cross-reference tests for Azure-Brain (Fabric-Brain + Meta-Brain).

Validates that internal links between agent instructions and root docs
resolve correctly, and that catalogs are consistent with disk.
"""
import pathlib
import re

import pytest
import yaml

# ROOT = Azure-Brain umbrella
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BRAINS = ["Fabric-Brain", "Meta-Brain"]


def _agents_dir(brain_name: str) -> pathlib.Path:
    return ROOT / brain_name / "agents"


def _catalog_path(brain_name: str) -> pathlib.Path:
    return _agents_dir(brain_name) / "_catalog.yaml"


def _load_catalog(brain_name: str) -> dict:
    return yaml.safe_load(_catalog_path(brain_name).read_text(encoding="utf-8"))


# ── Internal link resolution ────────────────────────────────────

# Matches markdown links like [text](../fabric_api.md)
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+\.md)\)')


def _all_instruction_files():
    out = []
    for b in BRAINS:
        ad = _agents_dir(b)
        if ad.exists():
            out.extend(sorted(ad.rglob("instructions.md")))
    return out


class TestInternalLinks:
    """All relative markdown links in instructions.md must resolve."""

    @pytest.fixture(params=_all_instruction_files(),
                    ids=[f"{f.parent.parent.parent.name}/{f.parent.name}"
                         for f in _all_instruction_files()])
    def instruction_file(self, request):
        return request.param

    def test_links_resolve(self, instruction_file):
        content = instruction_file.read_text(encoding="utf-8", errors="ignore")
        broken = []
        for match in LINK_RE.finditer(content):
            link_text, link_target = match.groups()
            if link_target.startswith(("http://", "https://", "#")):
                continue
            target_path = link_target.split("#")[0]
            resolved = (instruction_file.parent / target_path).resolve()
            if not resolved.exists():
                broken.append(f"  [{link_text}]({link_target}) → {resolved}")
        if broken:
            pytest.fail(
                f"{instruction_file.parent.name}/instructions.md broken links:\n"
                + "\n".join(broken)
            )


# ── Catalog domain descriptions ─────────────────────────────────


@pytest.mark.parametrize("brain", BRAINS)
class TestCatalogDomains:
    def test_domain_descriptions(self, brain):
        for key, domain in _load_catalog(brain)["domains"].items():
            assert "description" in domain, f"{brain}/{key} missing description"
            assert len(domain["description"]) > 5, f"{brain}/{key} trivial description"

    def test_agent_count_matches_folders(self, brain):
        catalog_count = sum(
            len(d.get("agents", []))
            for d in _load_catalog(brain)["domains"].values()
        )
        ad = _agents_dir(brain)
        folder_count = len([
            d for d in ad.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ])
        assert catalog_count == folder_count, \
            f"{brain} catalog has {catalog_count} agents, disk has {folder_count}"


# ── Known issues files ──────────────────────────────────────────

def _agent_known_issues():
    out = []
    for b in BRAINS:
        ad = _agents_dir(b)
        if ad.exists():
            out.extend(sorted(ad.rglob("known_issues.md")))
    return out


class TestKnownIssues:
    """known_issues.md files should have real content."""

    @pytest.fixture(params=_agent_known_issues(),
                    ids=[f"{f.parent.parent.parent.name}/{f.parent.name}"
                         for f in _agent_known_issues()])
    def ki_file(self, request):
        return request.param

    def test_not_empty(self, ki_file):
        assert ki_file.stat().st_size > 20, \
            f"{ki_file} appears empty"

"""Cross-reference tests for Github_Brain.

Validates that internal links between agent instructions and root docs
resolve correctly, and that the catalog is consistent with reality.
"""
import pathlib
import re

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
CATALOG_PATH = AGENTS_DIR / "_catalog.yaml"


@pytest.fixture(scope="session")
def catalog():
    return yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))


# ── Internal link resolution ────────────────────────────────────

# Matches markdown links like [text](../../fabric_api.md) or [text](../shared_constraints.md)
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+\.md)\)')


def _all_instruction_files():
    return sorted(AGENTS_DIR.rglob("instructions.md"))


class TestInternalLinks:
    """All relative markdown links in instructions.md must resolve."""

    @pytest.fixture(params=_all_instruction_files(),
                    ids=[str(f.parent.name) for f in _all_instruction_files()])
    def instruction_file(self, request):
        return request.param

    def test_links_resolve(self, instruction_file):
        content = instruction_file.read_text(encoding="utf-8", errors="ignore")
        broken = []
        for match in LINK_RE.finditer(content):
            link_text, link_target = match.groups()
            # Skip external URLs and anchors
            if link_target.startswith(("http://", "https://", "#")):
                continue
            # Strip anchors from path
            target_path = link_target.split("#")[0]
            resolved = (instruction_file.parent / target_path).resolve()
            if not resolved.exists():
                broken.append(f"  [{link_text}]({link_target}) → {resolved}")
        if broken:
            pytest.fail(
                f"{instruction_file.parent.name}/instructions.md has broken links:\n"
                + "\n".join(broken)
            )


# ── Catalog domain descriptions ─────────────────────────────────


class TestCatalogDomains:
    """Every domain must have a description."""

    def test_domain_descriptions(self, catalog):
        for key, domain in catalog["domains"].items():
            assert "description" in domain, f"Domain {key} missing description"
            assert len(domain["description"]) > 5, f"Domain {key} has trivial description"

    def test_agent_count_matches_folders(self, catalog):
        catalog_count = sum(
            len(d.get("agents", []))
            for d in catalog["domains"].values()
        )
        folder_count = len([
            d for d in AGENTS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ])
        assert catalog_count == folder_count, \
            f"Catalog has {catalog_count} agents, disk has {folder_count} folders"


# ── Known issues files ──────────────────────────────────────────

def _agent_known_issues():
    return sorted(AGENTS_DIR.rglob("known_issues.md"))


class TestKnownIssues:
    """known_issues.md files should have real content."""

    @pytest.fixture(params=_agent_known_issues(),
                    ids=[str(f.parent.name) for f in _agent_known_issues()])
    def ki_file(self, request):
        return request.param

    def test_not_empty(self, ki_file):
        assert ki_file.stat().st_size > 20, \
            f"{ki_file.parent.name}/known_issues.md appears empty"

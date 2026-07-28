"""Cross-reference tests for Azure-Brain (every brain in `conftest.BRAINS`).

Validates that internal links between agent instructions and root docs
resolve correctly, and that catalogs are consistent with disk.
"""
import re

import pytest

from conftest import (
    BRAINS,
    agent_dirs,
    agent_id,
    catalog_agent_names,
    folder_agent_names,
    load_catalog,
)


# ── Internal link resolution ────────────────────────────────────

# Matches markdown links like [text](../fabric_api.md)
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+\.md)\)')


def _all_instruction_files():
    out = []
    for brain in BRAINS:
        for d in agent_dirs(brain):
            f = d / "instructions.md"
            if f.exists():
                out.append(f)
    return out


_INSTRUCTION_FILES = _all_instruction_files()


class TestInternalLinks:
    """All relative markdown links in instructions.md must resolve."""

    @pytest.fixture(params=_INSTRUCTION_FILES,
                    ids=[agent_id(f.parent) for f in _INSTRUCTION_FILES])
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
                f"{agent_id(instruction_file.parent)}/instructions.md broken links:\n"
                + "\n".join(broken)
            )


# ── Catalog domain descriptions ─────────────────────────────────


@pytest.mark.parametrize("brain", BRAINS)
class TestCatalogDomains:
    def test_domain_descriptions(self, brain):
        for key, domain in load_catalog(brain)["domains"].items():
            assert "description" in domain, f"{brain}/{key} missing description"
            assert len(domain["description"]) > 5, f"{brain}/{key} trivial description"

    def test_implemented_agent_count_matches_folders(self, brain):
        catalog_count = len(catalog_agent_names(brain))
        folder_count = len(folder_agent_names(brain))
        assert catalog_count == folder_count, \
            (f"{brain} catalog lists {catalog_count} implemented agents, "
             f"disk has {folder_count}")


# ── Known issues files ──────────────────────────────────────────

def _agent_known_issues():
    out = []
    for brain in BRAINS:
        for d in agent_dirs(brain):
            f = d / "known_issues.md"
            if f.exists():
                out.append(f)
    return out


_KNOWN_ISSUES = _agent_known_issues()


class TestKnownIssues:
    """known_issues.md files should have real content."""

    @pytest.fixture(params=_KNOWN_ISSUES,
                    ids=[agent_id(f.parent) for f in _KNOWN_ISSUES])
    def ki_file(self, request):
        return request.param

    def test_not_empty(self, ki_file):
        assert ki_file.stat().st_size > 20, \
            f"{ki_file} appears empty"

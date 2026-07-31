"""Cross-reference tests for Azure-Brain (every brain in `conftest.BRAINS`).

Validates that internal links between agent instructions and root docs
resolve correctly, and that catalogs are consistent with disk.
"""
import re

import pytest

from conftest import (
    BRAINS,
    ROOT,
    agent_dirs,
    agent_id,
    catalog_agent_names,
    folder_agent_names,
    load_catalog,
)


# ── Internal link resolution ────────────────────────────────────

# Matches markdown links like [text](../fabric_api.md)
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+\.md)\)')


def _gitignored_basenames():
    """Bare filenames .gitignore keeps local — absent from a fresh clone.

    Only plain `name.md` entries count. Anything with a path separator or a
    glob is left out rather than half-interpreted: a wrong exemption is worse
    than a missing one, because it hides a genuinely broken link.
    """
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        return frozenset()
    names = set()
    for raw in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if line.endswith(".md") and not any(c in line for c in "/*?[]"):
            names.add(line)
    return frozenset(names)


_GITIGNORED = _gitignored_basenames()


def _is_local_only_target(resolved):
    """True for a link to a file the repo deliberately never ships.

    `resource_ids.md` holds tenant / subscription / workspace GUIDs, so it is
    gitignored and shipped as `resource_ids.example.md` for the user to copy
    (see AGENTS.md § Setup). A fresh clone therefore has the link target
    missing *by design*, and failing on it makes the whole suite permanently
    red — which destroys the signal the suite exists to give.

    Both conditions are required. A file that is merely missing, or one that
    is gitignored without a committed template, is still a broken link.
    """
    if resolved.name not in _GITIGNORED:
        return False
    return resolved.with_name(f"{resolved.stem}.example{resolved.suffix}").exists()


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
            if resolved.exists() or _is_local_only_target(resolved):
                continue
            broken.append(f"  [{link_text}]({link_target}) → {resolved}")
        if broken:
            pytest.fail(
                f"{agent_id(instruction_file.parent)}/instructions.md broken links:\n"
                + "\n".join(broken)
            )


class TestLocalOnlyLinkExemption:
    """The exemption above must stay narrow, or it becomes a blanket pass."""

    def test_the_real_case_is_exempt(self):
        target = ROOT / "Fabric-Brain" / "resource_ids.md"
        assert target.name in _GITIGNORED, ".gitignore no longer hides it"
        assert (ROOT / "Fabric-Brain" / "resource_ids.example.md").exists(), \
            "the committed template is what makes the absence intentional"
        assert _is_local_only_target(target)

    def test_both_conditions_are_required(self, tmp_path):
        # gitignored, but no committed template -> still a broken link
        assert not _is_local_only_target(tmp_path / "resource_ids.md")

        # a template exists, but the name is not gitignored -> still broken
        (tmp_path / "invented.example.md").write_text("x", encoding="utf-8")
        assert not _is_local_only_target(tmp_path / "invented.md")

    def test_an_ordinary_missing_link_still_fails(self, tmp_path):
        assert not _is_local_only_target(tmp_path / "no_such_file.md")

    def test_gitignore_globs_are_not_interpreted(self):
        assert not any(
            any(c in name for c in "/*?[]") for name in _GITIGNORED), \
            "only bare filenames may exempt a link; a glob would over-exempt"


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

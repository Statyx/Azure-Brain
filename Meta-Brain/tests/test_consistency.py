"""Doctrinal consistency tests for Azure-Brain.

The rest of the suite validates **form**: links resolve, files are non-empty,
JSON parses, Python compiles. None of it can catch the failure mode that actually
hurts a knowledge base — two files giving an agent contradictory orders.

That is not hypothetical. On 2026-07-31 an audit found the report format rule
stated in *both* directions across eleven files in three brains:

  * `report-builder-agent/instructions.md` (declared authoritative by AGENTS.md)
    had moved to PBIR folder format in v2.0.
  * Eleven other files still said "NEVER PBIR", "PBIR renders blank",
    "Always use the Legacy PBIX format" — in the imperative.

The prohibition was real once. PBIR reports did render blank, and the workaround
was to fall back to Legacy PBIX. But the root cause was diagnosed and fixed on
2026-06-13 (`report-builder-agent/known_issues.md` issue 19: `version.json` must
be 2.0.0, `report.json` needs reportSource+settings+objects, `baseTheme` must be
a real built-in, `visualContainer` schema 2.10.0). The workaround outlived the
bug and hardened into doctrine — which is the specific way knowledge bases rot.

These tests exist so it cannot happen silently again.
"""
import re

import pytest

from conftest import ROOT

# Files that legitimately describe the superseded format. They document Legacy
# PBIX for maintaining reports already shipped in it, so "use Legacy" is correct
# *there* and nowhere else.
_LEGACY_SUFFIX = ".legacy.md"
_LEGACY_SPEC = ROOT / "Fabric-Brain" / "report_format.md"

# Phrases that forbid PBIR or assert it cannot render. Each is a rule an agent
# would obey, not prose. Kept narrow on purpose: this test must fail on real
# instructions, not on a sentence merely mentioning the words.
_STALE_RULES = [
    re.compile(r"never\s+use\s+PBIR", re.I),
    re.compile(r"\(\s*NEVER\s+PBIR\s*\)", re.I),
    re.compile(r"\.\s*Never\s+PBIR\b", re.I),
    re.compile(r"always\s+use\s+(the\s+)?legacy\s+pbix", re.I),
    re.compile(r"use\s+\*{0,2}legacy\s+pbix\s+format\*{0,2}\s+exclusively", re.I),
    re.compile(r"PBIR[^.\n]{0,40}\brenders\s+blank", re.I),
    re.compile(r"PBIR[^.\n]{0,40}\bnever\s+renders", re.I),
    re.compile(r"rebuild\s+in\s+legacy\s+pbix", re.I),
]


def _markdown_files():
    for path in ROOT.rglob("*.md"):
        if any(part.startswith((".", "_")) for part in path.relative_to(ROOT).parts):
            continue
        if path.name.endswith(_LEGACY_SUFFIX) or path == _LEGACY_SPEC:
            continue
        yield path


_MD_FILES = sorted(_markdown_files())


def _offending_lines(path):
    """Lines asserting the superseded rule, ignoring explicitly historical ones."""
    hits = []
    for n, line in enumerate(
            path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        # A file may quote the old rule to explain that it was retired.
        # NB: `solved` is safe to exempt, `fix` is not — "**Fix**: use Legacy
        # PBIX EXCLUSIVELY" is exactly the kind of line this test must catch.
        if re.search(r"historical|used to (say|read)|outlived|no longer"
                     r"|superseded|stale|\bsolved\b",
                     line, re.I):
            continue
        for rx in _STALE_RULES:
            if rx.search(line):
                hits.append(f"  L{n}: {line.strip()}")
                break
    return hits


class TestReportFormatDoctrine:
    """No file may order agents away from PBIR — the owning agent mandates it."""

    @pytest.mark.parametrize(
        "md", _MD_FILES,
        ids=[str(p.relative_to(ROOT)).replace("\\", "/") for p in _MD_FILES])
    def test_no_stale_pbir_prohibition(self, md):
        hits = _offending_lines(md)
        if hits:
            pytest.fail(
                f"{md.relative_to(ROOT)} still forbids PBIR:\n" + "\n".join(hits)
                + "\n\nPBIR is the default for new reports "
                  "(Fabric-Brain/agents/report-builder-agent/instructions.md). "
                  "It renders once the v2.0 rules are applied — known_issues.md #19. "
                  "Legacy PBIX stays valid ONLY for maintaining reports already "
                  "shipped in it; say so explicitly, or move the text to a "
                  "*.legacy.md file."
            )

    def test_owning_agent_still_mandates_pbir(self):
        """If the owner ever reverts, these tests must be revisited, not deleted."""
        owner = (ROOT / "Fabric-Brain" / "agents" / "report-builder-agent"
                 / "instructions.md").read_text(encoding="utf-8", errors="ignore")
        assert re.search(r"PBIR folder format", owner, re.I), \
            ("report-builder-agent no longer mandates PBIR. This test file encodes "
             "that decision — update both together, deliberately.")

    def test_detector_catches_the_original_wording(self, tmp_path):
        """Guard the guard: the exact phrasings found in the 2026-07-31 audit."""
        for original in [
            "> Always use the **Legacy PBIX format** (`report.json`). Never PBIR.",
            "- Generate report using **Legacy PBIX format** (NEVER PBIR)",
            "> Always use PBIR-Legacy. PBIR folder format is accepted but renders blank.",
            "| Blank visuals | PBIR format used | ... | Rebuild in Legacy PBIX format |",
            "- **Fix**: Use **Legacy PBIX format** EXCLUSIVELY.",
        ]:
            probe = tmp_path / "probe.md"
            probe.write_text(original, encoding="utf-8")
            assert _offending_lines(probe), f"detector missed: {original}"

    def test_detector_allows_legitimate_mentions(self, tmp_path):
        """It must not fire on maintenance guidance or on retired-rule history."""
        for benign in [
            "Legacy PBIX remains valid for maintaining reports already shipped in it.",
            "This file used to say: always use the Legacy PBIX format. That is stale.",
            "Historical note: PBIR renders blank was true before the 2026-06-13 fix.",
            "### 10. PBIR Folder Format Renders Blank — **SOLVED 2026-06-13**",
            "New reports use the PBIR folder format.",
        ]:
            probe = tmp_path / "probe.md"
            probe.write_text(benign, encoding="utf-8")
            assert not _offending_lines(probe), f"false positive on: {benign}"

    def test_the_word_fix_does_not_grant_amnesty(self, tmp_path):
        """`fix` must NOT exempt a line — the worst offender was a **Fix**: line."""
        probe = tmp_path / "probe.md"
        probe.write_text("- **Fix**: Use **Legacy PBIX format** EXCLUSIVELY.",
                         encoding="utf-8")
        assert _offending_lines(probe), \
            "a remediation line ordering Legacy PBIX must still fail"


class TestAsyncPatternCompleteness:
    """Documenting the LRO poll without `allow_redirects=False` is a half-rule.

    The redirect the Fabric API returns on a 202 can hang indefinitely on SSL
    read. A file that teaches `x-ms-operation-id` but omits the guard sends the
    reader into that hang. The audit found 17 of 22 such files; this test stops
    the ratio getting worse by locking the ones that are complete.
    """

    def test_core_api_reference_carries_both(self):
        api = (ROOT / "Fabric-Brain" / "fabric_api.md").read_text(
            encoding="utf-8", errors="ignore")
        assert "x-ms-operation-id" in api, "fabric_api.md lost the LRO pattern"
        assert "allow_redirects" in api, (
            "fabric_api.md documents async polling without allow_redirects=False — "
            "that guard is what prevents the SSL-read hang")

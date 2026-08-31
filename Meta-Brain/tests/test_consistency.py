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

from conftest import ROOT, all_agent_dirs

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


# --------------------------------------------------------------------------
# Agent README summary counts
# --------------------------------------------------------------------------
# A README is a *summary* of the agent, and an agent reading only the summary
# must not get a smaller contract than the authoritative file gives.
#
# On 2026-08-31 `app-frontend-agent/README.md` announced "the 8 rules" in its
# file table and, twelve lines below, "## The seven rules, in one line each"
# followed by a list of seven — Rule 8 (the app shell blueprint) was invisible
# to anyone who trusted the summary. The same audit found
# `orchestrator-agent/README.md` claiming 10 documented issues against a
# known_issues.md holding 12.
#
# Neither is catchable by review: the number is right *somewhere else* in the
# same file, and nobody counts headings while reading a diff.
#
# LIMIT OF THIS GUARD, stated rather than implied: it can only verify a claim
# when the target file numbers its entries in headings. A file whose rules live
# in a plain numbered list is not covered — `test_the_guard_covers_the_known_cases`
# below fails if the currently-covered files ever drop out, so the loss of
# coverage is loud instead of silent.

_WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}

# Which file a counted noun refers to.
_CLAIM_TARGET = {
    "rule": "instructions.md",
    "rules": "instructions.md",
    "pitfall": "known_issues.md",
    "pitfalls": "known_issues.md",
    "issue": "known_issues.md",
    "issues": "known_issues.md",
    "entry": "known_issues.md",
    "entries": "known_issues.md",
}

_CLAIM_RX = re.compile(
    r"(?<![\w.])(\d{1,3}|" + "|".join(_WORD_NUMBERS) + r")\s+"
    r"(?:documented\s+)?"
    r"(rules?|pitfalls?|issues?|entries|entry)\b",
    re.I)

# `## Rule 8 — …`, `## Issue #12: …`, `### 20. …`
_NUMBERED_HEADING_RX = re.compile(
    r"^#{2,3}\s+(?:issue\s*#?\s*|rule\s+)?(\d{1,3})\s*[.:\u2014\u2013-]", re.I)


def _entry_count(path):
    """How many numbered entries a file actually holds, or None if unverifiable.

    Uses the highest index rather than the number of matches: a file that
    retires entry 7 but keeps 1-12 still documents twelve, and a README saying
    so is right.
    """
    if not path.exists():
        return None
    indices = [
        int(m.group(1))
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if (m := _NUMBERED_HEADING_RX.match(line))
    ]
    return max(indices) if indices else None


def _claims(readme):
    """(line no, claimed count, target filename, raw line) for verifiable claims.

    A bare number near a noun is not a claim about a file. It counts only when
    the line names the matching file — a table row like
    `| known_issues.md | 20 documented pitfalls |` — or when it is a heading,
    which is a section title *about* that set. That keeps prose such as
    "Top 3 issues by frequency:" out, since it names neither.
    """
    out = []
    for n, line in enumerate(
            readme.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        for m in _CLAIM_RX.finditer(line):
            raw, noun = m.group(1).lower(), m.group(2).lower()
            target = _CLAIM_TARGET[noun]
            if target not in line and not line.startswith("#"):
                continue
            count = _WORD_NUMBERS.get(raw) or int(raw)
            out.append((n, count, target, line.strip()))
    return out


_AGENT_READMES = sorted(
    d / "README.md" for d in all_agent_dirs() if (d / "README.md").exists())

# A file may also miscount *itself*: pptx-builder-agent's instructions.md carried
# `## 7 Mandatory Rules` above Rule 1 … Rule 9. Same defect, one file instead of two.
_SUMMARY_FILES = sorted(
    d / name
    for d in all_agent_dirs()
    for name in ("README.md", "instructions.md")
    if (d / name).exists())


class TestAgentSummaryCounts:
    """A stated count of rules or issues must match the file it summarises."""

    @pytest.mark.parametrize(
        "doc", _SUMMARY_FILES,
        ids=[str(p.relative_to(ROOT)).replace("\\", "/") for p in _SUMMARY_FILES])
    def test_counts_match_the_authoritative_file(self, doc):
        for lineno, claimed, target, line in _claims(doc):
            actual = _entry_count(doc.parent / target)
            if actual is None:
                continue          # target does not number its entries — see LIMIT above
            assert claimed == actual, (
                f"{doc.relative_to(ROOT)} L{lineno} claims {claimed} "
                f"but {target} documents {actual}:\n  {line}\n\n"
                "Update the summary — an agent that reads only the summary would "
                "act on the smaller contract. Do not renumber the source file to "
                "match the summary.")

    def test_the_guard_covers_the_known_cases(self):
        """Guard the guard: the two files audited on 2026-08-31 stay covered."""
        for rel, target in [
            ("Apps-Brain/agents/app-frontend-agent", "instructions.md"),
            ("Apps-Brain/agents/app-frontend-agent", "known_issues.md"),
            ("Fabric-Brain/agents/orchestrator-agent", "known_issues.md"),
        ]:
            agent = ROOT / rel
            assert _entry_count(agent / target) is not None, (
                f"{rel}/{target} no longer numbers its entries in headings, so "
                "the count guard silently stopped covering it. Restore the "
                "numbered headings or narrow this test deliberately.")
            claims = _claims(agent / "README.md")
            assert any(t == target for _, _, t, _ in claims), (
                f"{rel}/README.md no longer states a count for {target}. That is "
                "allowed, but remove it from this list so the guard stays honest.")

    def test_detector_catches_the_original_wording(self, tmp_path):
        """The exact two defects found in the audit, plus the spelled-out form."""
        (tmp_path / "instructions.md").write_text(
            "## Rule 1 — a\n## Rule 2 — b\n## Rule 3 — c\n", encoding="utf-8")
        (tmp_path / "known_issues.md").write_text(
            "## 1. a\n## 2. b\n", encoding="utf-8")
        assert _entry_count(tmp_path / "instructions.md") == 3
        assert _entry_count(tmp_path / "known_issues.md") == 2

        readme = tmp_path / "README.md"
        readme.write_text(
            "## The seven rules, in one line each\n"
            "| `known_issues.md` | 10 documented issues |\n", encoding="utf-8")
        found = {(c, t) for _, c, t, _ in _claims(readme)}
        assert (7, "instructions.md") in found, "missed a spelled-out heading claim"
        assert (10, "known_issues.md") in found, "missed a table-row claim"

    def test_detector_ignores_prose_that_names_no_file(self, tmp_path):
        """`Top 3 issues by frequency:` is a sample, not a total."""
        readme = tmp_path / "README.md"
        readme.write_text(
            "See `instructions.md` -> **Common pitfalls**. Top 3 issues by frequency:\n"
            "The agent applies 4 rules of thumb when sizing a visual.\n",
            encoding="utf-8")
        assert not _claims(readme), (
            "a count that names neither the file it counts nor a section title "
            "must not be read as a claim")

    def test_highest_index_wins_over_match_count(self, tmp_path):
        """A retired entry leaves a gap; the README may still say twelve."""
        (tmp_path / "known_issues.md").write_text(
            "## 1. a\n## 2. b\n## 12. l\n", encoding="utf-8")
        assert _entry_count(tmp_path / "known_issues.md") == 12


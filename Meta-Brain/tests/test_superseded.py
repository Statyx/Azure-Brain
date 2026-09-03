"""Registry-driven enforcement of retired rules — `superseded_rules.yaml`.

`agent_principles.md` §3b states the policy: a correction must sit adjacent to the false
statement it corrects, in the file that drives behaviour. The same section records why it was
written, and concedes the gap this module closes:

    "Neither was caught by CI. Both are invisible to a diff."

`test_consistency.py` does enforce one retired rule — the PBIR prohibition — but it does so by
hand: eight regexes and five bespoke tests, written for that doctrine alone. Retiring the next
rule meant writing all of that again, so nobody did, and the brain accumulated four competing
and mostly unenforced ways to mark a rule dead (`## Corrections` sections, `*.legacy.md`
suffixes, `status: deprecated` in catalogs, and hardcoded regexes here).

This module makes retirement declarative. A rule is retired by adding an entry to
`superseded_rules.yaml`; the entry is enforced from that moment, with no new Python.

Two failure modes are covered, because the brain has suffered both:

  * `superseded` — the rule is wrong and must never be applied again.
  * `conditional` — the rule is still valid, but only under a stated condition. Ignoring the
    condition is a real failure mode, not a theoretical one: known_issues.md #51 records a flat
    `src/` layout applied to a five-workload project because its "one workload only" condition
    was never read. A registry that only tracked dead rules would not have caught it.

The `authority_anchor` of every entry is checked against the live file, so the registry cannot
quietly describe a rule that has since been reworded or deleted.
"""
import re

import pytest
import yaml

from conftest import ROOT

REGISTRY = ROOT / "superseded_rules.yaml"

_KINDS = {"superseded", "conditional"}
_REQUIRED_KEYS = {
    "id", "kind", "recorded", "summary", "replaced_by",
    "authority", "authority_anchor", "evidence",
}
_ENFORCEMENTS = ("forbidden", "adjacency", "enforced_by")
_ADJACENCY_KEYS = {"file", "near", "must_contain", "within_lines"}

# A file may quote a dead rule in order to explain that it died. Same exemption as
# test_consistency.py, plus the dated `Correction YYYY-MM-DD` marker that §3b prescribes.
_HISTORICAL = re.compile(
    r"historical|used to (say|read)|outlived|no longer|superseded|stale|\bsolved\b"
    r"|correction \d{4}-\d{2}-\d{2}", re.I)


def _load_rules():
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and "rules" in data, \
        "superseded_rules.yaml must be a mapping with a top-level `rules:` list"
    return data["rules"]


_RULES = _load_rules()
_IDS = [r.get("id", f"<unnamed entry {i}>") for i, r in enumerate(_RULES)]


def _markdown_files():
    for path in ROOT.rglob("*.md"):
        if any(part.startswith((".", "_")) for part in path.relative_to(ROOT).parts):
            continue
        yield path


_MD_FILES = sorted(_markdown_files())


def _forbidden_hits(path, patterns, exempt_rel_paths):
    """Lines asserting a retired rule, ignoring explicitly historical ones."""
    try:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        rel = str(path)          # probe files live outside ROOT
    if rel in exempt_rel_paths:
        return []
    hits = []
    for n, line in enumerate(
            path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if _HISTORICAL.search(line):
            continue
        for pattern in patterns:
            if re.search(pattern, line, re.I):
                hits.append(f"  L{n}: {line.strip()}")
                break
    return hits


def _adjacency_violations(spec, base=ROOT):
    """§3b: 'a correction 200 lines below the rule it corrects is not a correction'."""
    path = base / spec["file"]
    if not path.exists():
        return [f"{spec['file']} does not exist"]
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    near = re.compile(spec["near"])
    must = re.compile(spec["must_contain"], re.I)
    within = int(spec["within_lines"])

    anchors = [i for i, line in enumerate(lines) if near.search(line)]
    if not anchors:
        return [f"the statement {spec['near']!r} was not found in {spec['file']} — "
                f"either it was removed (retire the registry entry deliberately) "
                f"or the `near` pattern has drifted"]
    out = []
    for i in anchors:
        if not any(must.search(line) for line in lines[i:i + within + 1]):
            out.append(f"L{i + 1}: {lines[i].strip()[:90]!r} — no correction matching "
                       f"{spec['must_contain']!r} within {within} lines below it")
    return out


class TestRegistryIntegrity:
    """The registry must stay well-formed, or it silently stops enforcing anything."""

    def test_registry_exists_and_is_non_empty(self):
        assert REGISTRY.exists(), f"{REGISTRY} is missing"
        assert _RULES, "superseded_rules.yaml lists no rules"

    def test_ids_are_unique(self):
        dupes = {i for i in _IDS if _IDS.count(i) > 1}
        assert not dupes, f"duplicate rule ids in the registry: {sorted(dupes)}"

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_required_keys_present(self, rule):
        missing = _REQUIRED_KEYS - set(rule)
        assert not missing, (
            f"registry entry {rule.get('id')!r} is missing {sorted(missing)}. "
            f"`evidence` is not optional — the brain's umbrella rule is that nothing is "
            f"'verified' without a trace that proves it.")

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_kind_is_known(self, rule):
        assert rule["kind"] in _KINDS, (
            f"{rule['id']}: kind {rule['kind']!r} not in {sorted(_KINDS)}")

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_conditional_entries_state_their_condition(self, rule):
        if rule["kind"] != "conditional":
            pytest.skip("not a conditional entry")
        assert rule.get("condition", "").strip(), (
            f"{rule['id']}: a conditional rule without a written condition is exactly the "
            f"failure it is meant to prevent (see known_issues.md #51)")

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_every_entry_is_actually_enforced(self, rule):
        present = [k for k in _ENFORCEMENTS if rule.get(k)]
        assert present, (
            f"{rule['id']} carries none of {_ENFORCEMENTS}. An unenforced entry is a note, "
            f"not a rule — and unenforced notes are how this problem started.")

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_adjacency_spec_is_complete(self, rule):
        spec = rule.get("adjacency")
        if not spec:
            pytest.skip("no adjacency spec")
        missing = _ADJACENCY_KEYS - set(spec)
        assert not missing, f"{rule['id']}: adjacency spec missing {sorted(missing)}"


class TestRegistryMatchesReality:
    """Anti-rot: the registry must keep describing files as they actually are."""

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_authority_file_exists(self, rule):
        path = ROOT / rule["authority"]
        assert path.exists(), (
            f"{rule['id']}: authority file {rule['authority']} does not exist")

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_authority_still_states_the_current_rule(self, rule):
        path = ROOT / rule["authority"]
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert re.search(rule["authority_anchor"], text, re.I), (
            f"{rule['id']}: {rule['authority']} no longer contains "
            f"{rule['authority_anchor']!r}.\n"
            f"The registry says the current rule is: {rule['replaced_by'].strip()}\n"
            f"Either the rule moved, or it was reverted. Update both together, "
            f"deliberately — do not delete this entry to make the test pass.")

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_enforced_by_file_exists(self, rule):
        target = rule.get("enforced_by")
        if not target:
            pytest.skip("no bespoke enforcement declared")
        assert (ROOT / target).exists(), (
            f"{rule['id']}: enforced_by points at {target}, which does not exist")

    @pytest.mark.parametrize("rule", _RULES, ids=_IDS)
    def test_correction_sits_next_to_the_statement_it_corrects(self, rule):
        spec = rule.get("adjacency")
        if not spec:
            pytest.skip("no adjacency spec")
        violations = _adjacency_violations(spec)
        if violations:
            pytest.fail(
                f"{rule['id']}: agent_principles.md §3b requires the correction to sit "
                f"adjacent to the statement it corrects.\n" + "\n".join(violations))


class TestForbiddenPhrasings:
    """Retired phrasings must not reappear anywhere as live instructions."""

    def test_no_markdown_file_asserts_a_retired_rule(self):
        scanned = [r for r in _RULES if r.get("forbidden")]
        if not scanned:
            pytest.skip("no registry entry declares `forbidden` patterns")
        failures = []
        for rule in scanned:
            exempt = set(rule.get("exempt_paths", []))
            for md in _MD_FILES:
                hits = _forbidden_hits(md, rule["forbidden"], exempt)
                if hits:
                    failures.append(
                        f"[{rule['id']}] {md.relative_to(ROOT)}\n" + "\n".join(hits))
        if failures:
            pytest.fail("retired rules still stated as live instructions:\n\n"
                        + "\n\n".join(failures))


class TestGuardTheGuard:
    """The detectors must be shown to work, or a green suite proves nothing."""

    def test_adjacency_detector_rejects_a_distant_correction(self, tmp_path):
        (tmp_path / "far.md").write_text(
            "| Fabric workload folder | `kebab-case` |\n"
            + "filler\n" * 40
            + "> Correction 2026-09-03 - must be `snake_case`.\n",
            encoding="utf-8")
        spec = {"file": "far.md", "near": r"\| Fabric workload folder \|",
                "must_contain": r"Correction \d{4}-\d{2}-\d{2}", "within_lines": 5}
        assert _adjacency_violations(spec, base=tmp_path), \
            "a correction 40 lines away must NOT count as adjacent"

    def test_adjacency_detector_accepts_a_close_correction(self, tmp_path):
        (tmp_path / "near.md").write_text(
            "| Fabric workload folder | `kebab-case` |\n"
            "\n"
            "> Correction 2026-09-03 - must be `snake_case`.\n",
            encoding="utf-8")
        spec = {"file": "near.md", "near": r"\| Fabric workload folder \|",
                "must_contain": r"Correction \d{4}-\d{2}-\d{2}", "within_lines": 5}
        assert not _adjacency_violations(spec, base=tmp_path), \
            "an adjacent correction must be recognised"

    def test_adjacency_detector_reports_a_vanished_statement(self, tmp_path):
        """If the corrected statement is deleted, the entry must be revisited, not ignored."""
        (tmp_path / "gone.md").write_text("nothing here\n", encoding="utf-8")
        spec = {"file": "gone.md", "near": r"\| Fabric workload folder \|",
                "must_contain": r"Correction", "within_lines": 5}
        assert _adjacency_violations(spec, base=tmp_path), \
            "a missing anchor must fail loudly rather than pass vacuously"

    def test_forbidden_detector_catches_an_imperative(self, tmp_path):
        probe = tmp_path / "probe.md"
        probe.write_text("- Always name workload folders `fabric/data-agent/`.",
                         encoding="utf-8")
        assert _forbidden_hits(probe, [r"fabric/data-agent/"], set()), \
            "detector missed a live imperative"

    def test_forbidden_detector_exempts_explicit_history(self, tmp_path):
        probe = tmp_path / "probe.md"
        probe.write_text(
            "> Correction 2026-09-03 — `fabric/data-agent/` is not importable in Python.",
            encoding="utf-8")
        assert not _forbidden_hits(probe, [r"fabric/data-agent/"], set()), \
            "a dated correction quoting the dead rule must not be flagged"


def test_forbidden_hits_is_relative_to_root_safely(tmp_path):
    """`_forbidden_hits` must not crash on files outside ROOT (used by the probes)."""
    probe = tmp_path / "outside.md"
    probe.write_text("nothing to see", encoding="utf-8")
    assert _forbidden_hits(probe, [r"zzz-no-match"], set()) == []

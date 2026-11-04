"""Expiry clocks — fail before a documented future date turns the brain wrong.

The brain states facts that are only true until a date: a retirement, an
end-of-support, a preview window. Written in the future tense, they turn false
overnight and nothing notices — markdown has no expiry.

`Meta-Brain/clocks.yaml` is the registry; this module is the alarm. A clock
fails once it is inside `warn_days`, giving a heads-up window rather than a
post-mortem. An evidenced acknowledgement can close that warning after review,
but the clock always fails again on and after the deadline.

The registry deliberately stores no file list. It would rot the moment someone
adds a mention. Instead the test scans the repo live, so the failure message
always names the files that actually need rewriting today.
"""
import datetime
import pathlib

import pytest
import yaml

from conftest import ROOT

CLOCKS_PATH = ROOT / "Meta-Brain" / "clocks.yaml"

EXCLUDED_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", "node_modules"}


def _load():
    return yaml.safe_load(CLOCKS_PATH.read_text(encoding="utf-8"))


_REGISTRY = _load()
_CLOCKS = _REGISTRY.get("clocks", [])
_WARN_DAYS = int(_REGISTRY.get("warn_days", 30))


def _clock_id(clock: dict) -> str:
    return f"{clock['date']} {clock['what']}"


def _scan(clock: dict) -> list[str]:
    """Repo-relative paths of every markdown file stating this clock's date."""
    needles = [str(clock["date"])] + list(clock.get("aliases") or [])
    hits = []
    for path in sorted(ROOT.rglob("*.md")):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(n in text for n in needles):
            hits.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return hits


def _validate_acknowledgement(clock: dict, today: datetime.date, warn_days: int,
                              root: pathlib.Path = ROOT) -> None:
    ack = clock.get("warning_acknowledged")
    if ack is None:
        return
    assert isinstance(ack, dict), "warning_acknowledged must be a mapping"
    reviewed = ack.get("date")
    assert isinstance(reviewed, datetime.date), "acknowledgement date must be an unquoted ISO date"
    assert reviewed <= today, "acknowledgement cannot be dated in the future"
    assert 0 < (clock["date"] - reviewed).days <= warn_days, \
        "acknowledgement must be made within the warning window, before the deadline"
    assert isinstance(ack.get("reason"), str) and ack["reason"].strip(), \
        "acknowledgement must explain the completed review"
    evidence = ack.get("evidence")
    assert isinstance(evidence, str) and evidence.strip(), \
        "acknowledgement must identify a repository evidence file"
    evidence_path = (root / evidence).resolve()
    try:
        evidence_path.relative_to(root.resolve())
    except ValueError:
        pytest.fail("acknowledgement evidence must stay inside the repository")
    assert evidence_path.is_file(), f"acknowledgement evidence not found: {evidence}"
    assert str(clock["date"]) in evidence_path.read_text(encoding="utf-8"), \
        "acknowledgement evidence must mention the clock's date"


def _is_due(clock: dict, today: datetime.date, warn_days: int,
            root: pathlib.Path = ROOT) -> bool:
    _validate_acknowledgement(clock, today, warn_days, root)
    days = (clock["date"] - today).days
    return days <= 0 or (days <= warn_days and clock.get("warning_acknowledged") is None)


class TestClockRegistry:
    """The registry itself must be well-formed."""

    def test_registry_exists(self):
        assert CLOCKS_PATH.exists(), "Meta-Brain/clocks.yaml missing"

    def test_has_clocks(self):
        assert _CLOCKS, "clocks.yaml declares no clocks — did a date get dropped?"

    @pytest.mark.parametrize("clock", _CLOCKS, ids=[_clock_id(c) for c in _CLOCKS])
    def test_fields_present(self, clock):
        for field in ("date", "what", "why_it_matters", "when_due"):
            assert clock.get(field), f"clock {clock.get('date')} missing '{field}'"
        assert isinstance(clock["date"], datetime.date), \
            f"clock {clock['date']!r} must be an unquoted ISO date (YYYY-MM-DD)"
        _validate_acknowledgement(clock, datetime.date.today(), _WARN_DAYS)


@pytest.mark.parametrize("clock", _CLOCKS, ids=[_clock_id(c) for c in _CLOCKS])
class TestClocksNotDue:
    def test_not_due(self, clock):
        today = datetime.date.today()
        days = (clock["date"] - today).days
        if not _is_due(clock, today, _WARN_DAYS):
            return
        where = _scan(clock)
        state = "has passed" if days < 0 else f"is due in {days} day(s)"
        pytest.fail(
            f"Clock {clock['date']} ({clock['what']}) {state}.\n"
            f"  Why it matters: {clock['why_it_matters'].strip()}\n"
            f"  What to do:     {clock['when_due'].strip()}\n"
            f"  Files stating this date ({len(where)}):\n    "
            + "\n    ".join(where or ["(none — the clock can be removed)"])
        )

    def test_still_referenced(self, clock):
        """A clock nobody states any more is registry drift — remove it."""
        assert _scan(clock), (
            f"Clock {clock['date']} ({clock['what']}) is in clocks.yaml but no "
            f"markdown file mentions it. Either the prose was rewritten and the "
            f"clock should be deleted, or a date was silently reworded."
        )


class TestAcknowledgedClock:
    def test_warning_and_deadline(self, tmp_path):
        deadline = datetime.date(2030, 7, 1)
        clock = {"date": deadline}
        assert not _is_due(clock, datetime.date(2030, 5, 31), 30, tmp_path)
        assert _is_due(clock, datetime.date(2030, 6, 1), 30, tmp_path)
        evidence = tmp_path / "review.md"
        evidence.write_text("Reviewed retirement on 2030-07-01.", encoding="utf-8")
        clock["warning_acknowledged"] = {
            "date": datetime.date(2030, 6, 2),
            "reason": "Reviewed and updated the guidance.",
            "evidence": "review.md",
        }
        assert not _is_due(clock, datetime.date(2030, 6, 2), 30, tmp_path)
        assert not _is_due(clock, datetime.date(2030, 6, 30), 30, tmp_path)
        assert _is_due(clock, deadline, 30, tmp_path)
        assert _is_due(clock, datetime.date(2030, 7, 2), 30, tmp_path)

    @pytest.mark.parametrize(
        "ack",
        [
            {},
            {"date": datetime.date(2030, 5, 31), "reason": "reviewed", "evidence": "review.md"},
            {"date": datetime.date(2030, 6, 3), "reason": "reviewed", "evidence": "review.md"},
            {"date": datetime.date(2030, 6, 2), "reason": "", "evidence": "review.md"},
            {"date": datetime.date(2030, 6, 2), "reason": "reviewed", "evidence": "../review.md"},
            {"date": datetime.date(2030, 6, 2), "reason": "reviewed", "evidence": "missing.md"},
        ],
    )
    def test_invalid_acknowledgement_does_not_silence_alarm(self, tmp_path, ack):
        clock = {"date": datetime.date(2030, 7, 1), "warning_acknowledged": ack}
        with pytest.raises((AssertionError, pytest.fail.Exception)):
            _is_due(clock, datetime.date(2030, 6, 2), 30, tmp_path)

    def test_evidence_must_mention_deadline(self, tmp_path):
        (tmp_path / "review.md").write_text("Unrelated review", encoding="utf-8")
        clock = {
            "date": datetime.date(2030, 7, 1),
            "warning_acknowledged": {
                "date": datetime.date(2030, 6, 2),
                "reason": "reviewed",
                "evidence": "review.md",
            },
        }
        with pytest.raises(AssertionError, match="mention the clock"):
            _is_due(clock, datetime.date(2030, 6, 2), 30, tmp_path)

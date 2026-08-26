"""Expiry clocks — fail before a documented future date turns the brain wrong.

The brain states facts that are only true until a date: a retirement, an
end-of-support, a preview window. Written in the future tense, they turn false
overnight and nothing notices — markdown has no expiry.

`Meta-Brain/clocks.yaml` is the registry; this module is the alarm. A clock
fails once it is inside `warn_days`, giving a heads-up window rather than a
post-mortem.

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


@pytest.mark.parametrize("clock", _CLOCKS, ids=[_clock_id(c) for c in _CLOCKS])
class TestClocksNotDue:
    def test_not_due(self, clock):
        days = (clock["date"] - datetime.date.today()).days
        if days > _WARN_DAYS:
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

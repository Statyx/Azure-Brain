"""The brain must stay publishable at all times.

Added 2026-07-31 alongside `PUBLIC_SAFETY.md` and
`Meta-Brain/tools/scan_public_safety.py`.

Rationale: this repo is public, and the projects built from it are shared on
GitHub. Anonymising *after the fact* does not work — it is tedious, it is done
under time pressure right before a demo, and it silently misses git history.
The only reliable approach is to never write the real value down, which means
the convention has to be machine-checked.

These tests are the ratchet: once the brain is clean, it cannot silently drift
back.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

from conftest import ROOT

TOOL = ROOT / "Meta-Brain" / "tools" / "scan_public_safety.py"


def _load_scanner():
    spec = importlib.util.spec_from_file_location("scan_public_safety", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules["scan_public_safety"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def scanner():
    assert TOOL.exists(), f"scanner is missing: {TOOL}"
    return _load_scanner()


@pytest.fixture(scope="module")
def findings(scanner):
    return scanner.scan(ROOT)


# ── The brain itself ────────────────────────────────────────────

def test_no_blocking_findings(findings):
    """Nothing in the tracked content may be a hard leak."""
    blocks = [f for f in findings if f["severity"] == "BLOCK"]
    detail = "\n".join(
        f"  {f['file']}:{f['line']}  [{f['rule']}]  {f['match']}"
        for f in blocks)
    assert not blocks, (
        f"{len(blocks)} value(s) must not be published:\n{detail}\n"
        "Redact them, or add them to .publicsafety-allow with a reason "
        "(see PUBLIC_SAFETY.md).")


def test_no_warning_findings(findings):
    """Real-looking GUIDs and home paths create re-anonymisation work."""
    warns = [f for f in findings if f["severity"] == "WARN"]
    detail = "\n".join(
        f"  {f['file']}:{f['line']}  [{f['rule']}]  {f['match']}"
        for f in warns)
    assert not warns, (
        f"{len(warns)} value(s) look tenant-specific:\n{detail}\n"
        "Use a placeholder GUID (a0000000-0000-4000-a000-00000000000a) "
        "or $PSScriptRoot / %USERPROFILE% for paths.")


# ── The scanner must actually work ──────────────────────────────
#
# A scanner that silently matches nothing would make the two tests above pass
# forever. These prove it still has teeth, and still has the exemptions that
# stop it crying wolf.

@pytest.mark.parametrize("line,rule", [
    ("client_secret = 'Xk9~ab_cdEF0123456789'", "azure-secret-assignment"),
    ("host = contoso-corp.onmicrosoft.com", "tenant-domain"),
    ("owner: someone@microsoft.com", "corporate-email"),
    ("url = https://x.blob.core.windows.net/c?sv=1&sig=abcdefghij0123456789ABCDEF",
     "sas-token"),
    ("workspace = 3f2a91cd-77bd-4e0a-9f31-2c5d8ab41e77", "real-guid"),
    (r'$root = "D:\Users\someone\repo"', "windows-user-path"),
])
def test_scanner_detects(scanner, tmp_path, line, rule):
    f = tmp_path / "sample.md"
    f.write_text(line, encoding="utf-8")
    hits = scanner.scan_file(f, tmp_path, scanner.load_allowlist(tmp_path))
    assert rule in {h["rule"] for h in hits}, (
        f"rule {rule!r} no longer fires on: {line!r}")


@pytest.mark.parametrize("line,why", [
    ('id = "a0000000-0000-4000-a000-00000000000a"', "canonical placeholder"),
    ('id = "00000000-0000-0000-0000-000000000000"', "empty GUID"),
    ('id = "12345678-1234-1234-1234-123456789abc"', "counting sequence"),
    ('roleId = "4633458b-17de-408a-b874-0445c86b69e6"',
     "Key Vault Secrets User built-in role — public constant"),
    ('appId = "2746ea77-4702-4b45-80ca-3c97e680e8b7"',
     "Azure Data Explorer first-party appId — public constant"),
    ('pwd = dbutils.secrets.get(scope="prod", key="db-password")',
     "reading a secret is the pattern we teach"),
    ('pwd = notebookutils.credentials.getSecret(url, "db-password")',
     "same, Fabric side"),
    ('Password=${DB_PASSWORD}', "environment expansion, not a literal"),
    ('tenant = "zava.onmicrosoft.com"', "the prescribed fictional tenant"),
    (r'$here = "C:\Users\<user>\repo"', "explicit placeholder"),
])
def test_scanner_stays_quiet(scanner, tmp_path, line, why):
    """Cry-wolf protection.

    An over-eager scanner gets disabled, and then it protects nothing. Each
    case here is something a correct file legitimately contains.
    """
    f = tmp_path / "sample.md"
    f.write_text(line, encoding="utf-8")
    hits = scanner.scan_file(f, tmp_path, scanner.load_allowlist(tmp_path))
    assert not hits, f"false positive ({why}): {hits}"


def test_repo_allowlist_entries_are_explained():
    """An unexplained allowlist entry is indistinguishable from a mistake."""
    f = ROOT / ".publicsafety-allow"
    if not f.exists():
        pytest.skip("no repo-level allowlist")
    lines = f.read_text(encoding="utf-8").splitlines()
    for i, raw in enumerate(lines):
        token = raw.split("#", 1)[0].strip()
        if not token:
            continue
        preceding = [ln for ln in lines[:i] if ln.strip().startswith("#")]
        assert preceding, (
            f".publicsafety-allow line {i + 1} ({token!r}) has no comment "
            "above it explaining why it is safe.")


# ── The conventions must be documented and reachable ────────────

def test_public_safety_doc_exists():
    doc = ROOT / "PUBLIC_SAFETY.md"
    assert doc.exists(), "PUBLIC_SAFETY.md is the contract; it must exist."
    assert len(doc.read_text(encoding="utf-8")) > 2000


@pytest.mark.parametrize("name", ["AGENTS.md", ".github/copilot-instructions.md"])
def test_entry_points_reference_public_safety(name):
    """An unreferenced doc is an unread doc."""
    text = (ROOT / name).read_text(encoding="utf-8")
    assert "PUBLIC_SAFETY.md" in text, (
        f"{name} must point at PUBLIC_SAFETY.md, or agents will never load it.")


def test_zava_is_the_documented_company():
    text = (ROOT / "PUBLIC_SAFETY.md").read_text(encoding="utf-8")
    assert "Zava" in text


@pytest.mark.parametrize("pattern", [
    "state.json",
    ".env",
    "*.local.*",
    "resource_ids.md",
    "environment.md",
])
def test_gitignore_covers_local_only_files(pattern):
    """These are how a real tenant ID actually reaches a public repo."""
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert pattern in text, f".gitignore no longer covers {pattern!r}"


def test_gitignore_has_no_bom():
    """A BOM becomes part of the first pattern, silently disabling it."""
    raw = (ROOT / ".gitignore").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), (
        ".gitignore starts with a UTF-8 BOM — the first rule will not match.")

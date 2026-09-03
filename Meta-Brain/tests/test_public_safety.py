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
import subprocess
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
    # ── the four classes the 2026-08-03 audit found and the scanner missed ──
    #
    # Every value below is FABRICATED. A detection test must exercise the
    # mechanism, never real data: writing a customer name here would leak it
    # into this public repo — which is the very thing the rule forbids.
    # Real terms reach the scanner through CLIENT_DENYLIST / .publicsafety-deny,
    # covered by test_denylist_adds_repo_specific_terms below.
    ("demos (the Live Event Center, Network Operations)", "client-name"),
    ("Proven on the LEC and Network Operations", "client-acronym"),
    ('  workspaceName: "ABC - Demo Marketing"', "personal-workspace-prefix"),
    ("### Pattern: Full Platform (as deployed in ABC - Financial Platform)",
     "personal-workspace-prefix"),
    ("- **ABC - Fabric RTI Demo** (IoT sensor monitoring)",
     "personal-workspace-prefix"),
    ('  workspace: "ABC \u2013 Financial Platform"',
     "personal-workspace-prefix"),   # en dash — how this one hid for 73 commits
    ('db = Sql.Database("abcdefghijklmnopqrstuvwxyz-0123456789abcdefghijklmno'
     '.datawarehouse.fabric.microsoft.com", "LH_Finance")',
     "fabric-sql-endpoint"),
    ('server = "abc123def456.datawarehouse.pbidedicated.windows.net"',
     "fabric-sql-endpoint"),
    # ── added 2026-08-31: an identifier with no GUID in it ──
    ('PROJECT_ENDPOINT = "https://mktg-fdry-prod.services.ai.azure.com/api/projects/p1"',
     "azure-resource-hostname"),
    ('"endpoint": "https://zv7k2contoso-openai.openai.azure.com/"',
     "azure-resource-hostname"),
    ('KV = "kv-prod-weu-7743.vault.azure.net"',
     "azure-resource-hostname"),
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
    # ── cry-wolf protection for the rules added 2026-08-03 ──
    ("| SQL Analytics Endpoint | `*.datawarehouse.fabric.microsoft.com` |",
     "the wildcard form is how the brain documents the host"),
    ('Source = Sql.Database("<sql_endpoint>.datawarehouse.fabric.microsoft.com", '
     '"<lakehouse_name>"),',
     "the placeholder form is the shape we teach"),
    ('workspaceName: "Zava - Retail Analytics"',
     "the prescribed workspace prefix is not all-caps initials"),
    ("SELECT COUNT(*) FROM fact_sales", "'SELECT' contains the letters l-e-c"),
    ("- **EBITDA**: Revenue - COGS - Operating Expenses",
     "a subtraction chain, not a workspace name"),
    ("FAB_W   = SLIDE_W - FAB_L - USR_W - GAP - M",
     "a formula, not a workspace name"),
    ("# Fabric API \u2014 REST Reference",
     "an em dash is this brain's title separator, not a workspace prefix"),
    ("## Ontology \u2014 Graph Model Deployment",
     "same, and 15 headings like it exist in the tree"),
    ("ACCENT3    = RGBColor(0xF7, 0x63, 0x0C)   # orange",
     "'orange' is a colour here, and colours are never a finding"),
    ("![build](https://img.shields.io/badge/status-beta-orange)",
     "shields.io colour token"),
    ("Proven on the Live Event Operations and Network Operations demos",
     "the sanitised label must not itself be a finding"),
    # ── cry-wolf protection for azure-resource-hostname (2026-08-31) ──
    ('endpoint = "https://<resource>.services.ai.azure.com/api/projects/<project>"',
     "the placeholder form is the shape this brain teaches"),
    ("`{account}.services.ai.azure.com` is the Foundry data-plane host",
     "the brace form, used in the same docs"),
    ('vaultUri: "https://myvault.vault.azure.net/"',
     "'my*' is the Azure docs' own example label"),
    ('url = f"https://{KV_NAME}.vault.azure.net"',
     "an f-string expansion is a read, not a literal"),
    ('abfss://files@storageaccount.dfs.core.windows.net/path',
     "a bare role word names a role, not an instance — 11 such lines exist"),
    ('wasbs://container@account.blob.core.windows.net/',
     "same, and it is how every ADLS example in this brain is written"),
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


def test_denylist_adds_repo_specific_terms(scanner, tmp_path, monkeypatch):
    """Real customer names reach the scanner WITHOUT being committed.

    Both sources are tested with a fabricated term. That is the point: the tool
    must never contain the names it forbids, so the rule is verified on its
    mechanism, not on real data (`known_issues.md` #47).
    """
    monkeypatch.delenv("CLIENT_DENYLIST", raising=False)
    f = tmp_path / "sample.md"
    f.write_text("Delivered for Acmecorp Utilities in Q3.", encoding="utf-8")
    allowed = scanner.load_allowlist(tmp_path)

    def hits():
        return scanner.scan_file(f, tmp_path, allowed,
                                 scanner.RULES + scanner.denylist_rules(tmp_path))

    # Nothing forbids it yet — so any finding below is the denylist's doing.
    assert not hits()

    # Source 1: the env var (a repository secret in CI).
    monkeypatch.setenv("CLIENT_DENYLIST", "acmecorp")
    assert {h["rule"] for h in hits()} == {"denylisted-term"}
    monkeypatch.delenv("CLIENT_DENYLIST")

    # Source 2: the gitignored file.
    deny = tmp_path / ".publicsafety-deny"
    deny.write_text("# the customer this repo was built for\nAcmecorp Utilities\n",
                    encoding="utf-8")
    assert {h["rule"] for h in hits()} == {"denylisted-term"}


def test_path_exclusion_is_scoped_to_the_file(scanner, tmp_path):
    """A repo may exempt its own leak-guard corpus — by path, never by value.

    Added 2026-09-03. `SELF` skips this tool's own fixtures, but the scanner is
    documented as usable on any project, and a responsible project has its own
    leak guard whose fixtures are full of the patterns by construction. Scanning
    a sibling demo repo returned 19 of 20 BLOCKs from its `test_leak_guard.py`,
    burying the one real finding — the noise failure PUBLIC_SAFETY.md forbids.

    The load-bearing property is the second half: excluding the fixture must NOT
    silence the same value in shipped code, which is what a value-level
    allowlist entry would have done.
    """
    secret = "x7qk3zv9m2rt6bd1ncf8.datawarehouse.fabric.microsoft.com"
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_leak_guard.py").write_text(
        f'BAD = "{secret}"\n', encoding="utf-8")
    shipped = tmp_path / "config.md"
    shipped.write_text(f"endpoint: {secret}\n", encoding="utf-8")

    # Without the exemption both files are reported.
    files = {f["file"] for f in scanner.scan(tmp_path)}
    assert files == {"tests/test_leak_guard.py", "config.md"}

    (tmp_path / ".publicsafety-allow").write_text(
        "# our own detection fixtures\npath:tests/test_leak_guard.py\n",
        encoding="utf-8")

    findings = scanner.scan(tmp_path)
    assert {f["file"] for f in findings} == {"config.md"}, (
        "a path: entry must exempt only that file — the same value in shipped "
        "code is still a leak.")


def test_path_exclusion_never_becomes_an_allowed_value(scanner, tmp_path):
    """`path:` lines are routed to the path list, not the value allowlist."""
    (tmp_path / ".publicsafety-allow").write_text(
        "# fixtures\npath:tests/*.py\n", encoding="utf-8")
    assert "path:tests/*.py" not in scanner.load_allowlist(tmp_path)
    assert scanner.load_path_exclusions(tmp_path) == ["tests/*.py"]


def test_tool_hardcodes_no_customer_name(scanner):
    """The scanner must not be the leak.

    A sibling repo shipped its entire client portfolio inside the very tool
    meant to catch it. `CLIENT_NAMES` may hold generic English phrases only;
    anything customer-specific goes through the denylist.
    """
    for pattern in scanner.CLIENT_NAMES:
        assert " " in pattern or pattern.islower(), pattern
        assert "live event cent" in pattern, (
            f"{pattern!r} looks like a customer name hardcoded into the tool — "
            "use CLIENT_DENYLIST or .publicsafety-deny instead.")


def test_no_powerpoint_is_tracked():
    """Ship the generator, never the binary.

    A `.pptx` round-tripped through a rights-protected tenant comes back as an
    OLE/MIP container whose *unencrypted* envelope still carries tenant GUIDs —
    the content is unreadable outside the tenant, the metadata is not.
    See `Fabric-Brain/agents/migration-bo-agent/README.md`.
    """
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "*.pptx", "*.ppt"],
                         capture_output=True, text=True)
    tracked = [line for line in out.stdout.splitlines() if line.strip()]
    assert not tracked, (
        "PowerPoint decks must not be committed:\n  " + "\n  ".join(tracked) +
        "\nRun `git rm --cached <file>` and regenerate them from their script.")


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

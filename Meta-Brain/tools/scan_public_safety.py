#!/usr/bin/env python
"""Public-safety scanner — find anything that must not be published.

Run it before making a repo public, before every demo hand-off, and in CI.
It is deliberately usable **outside** Azure-Brain: point it at any project.

    python scan_public_safety.py                 # scan the current repo
    python scan_public_safety.py ../My-Project   # scan another repo
    python scan_public_safety.py --json          # machine-readable
    python scan_public_safety.py --list-allowed  # show the built-in allowlist

Exit code is 1 when anything is found, 0 when clean — so it can gate a
publish step.

Design note — why an allowlist is mandatory, not optional
---------------------------------------------------------
Azure is full of GUIDs that are **public constants**: built-in role definition
IDs, first-party application IDs. A scanner that flags them produces findings
on a clean repo, and a scanner that is always red is one nobody reads. That is
the same failure the umbrella test suite already suffered from and fixed.

So: every allowlisted value carries a reason, and a repo can add its own in a
`.publicsafety-allow` file (one token per line, `#` comments allowed).

The mirror image exists too: `.publicsafety-deny` adds repo-specific forbidden
terms on top of the shared `CLIENT_NAMES` baseline.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

# ── What is safe, and why ───────────────────────────────────────

# Public Microsoft constants. Not secrets — publishing them reveals nothing.
PUBLIC_GUIDS: dict[str, str] = {
    "2746ea77-4702-4b45-80ca-3c97e680e8b7":
        "Azure Data Explorer first-party resource appId (documented)",
    "4633458b-17de-408a-b874-0445c86b69e6":
        "Key Vault Secrets User built-in role definition ID (documented)",
    "00000009-0000-0000-c000-000000000000":
        "Power BI Service first-party appId (documented)",
    "00000003-0000-0000-c000-000000000000":
        "Microsoft Graph first-party appId (documented)",
}

# A GUID shaped like a placeholder is intentional documentation, not a leak.
# Canonical shape for new examples: <N>0000000-0000-4000-a000-00000000000<M>
PLACEHOLDER_GUID = re.compile(
    r"""^(?:
          ([0-9a-f])\1{7}-.*                             # 8 identical chars
        | [0-9a-f]0{7}-0{4}-4000-a000-0{11}[0-9a-f]      # documented shape
        | 12345678-1234-1234-1234-.*                     # counting sequence
        | a1b2c3d4-e5f6-7890-abcd-ef1234567890
        | b2c3d4e5-f6a7-8901-bcde-f12345678901
        | deadbeef-.*
        )$""",
    re.I | re.X,
)

GUID_RE = (r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
           r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")

SCAN_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".ps1", ".bicep",
                 ".sh", ".txt", ".env", ".cfg", ".ini", ".tf", ".sql", ".js",
                 ".ts", ".html", ".xml", ".csv"}

# Never scan our own definitions — they contain every pattern by construction.
SELF = {"scan_public_safety.py", "PUBLIC_SAFETY.md", "test_public_safety.py",
        ".publicsafety-allow", ".publicsafety-deny"}

# ── Names that identify a real engagement ───────────────────────
#
# Added 2026-08-03 after an external audit found a customer name in three files
# that had survived 73 commits.
#
# THE LIST IS DELIBERATELY EMPTY HERE. Writing a customer name into a public
# repo to prove it must not appear in that repo is the leak it is meant to
# prevent — and a sibling repo shipped its whole client portfolio that way.
# Real terms are supplied at run time, never committed:
#
#   * `CLIENT_DENYLIST` env var, comma-separated  (CI: a repository secret)
#   * `.publicsafety-deny`, one term per line     (gitignored, local use)
#
# `live event cent(er|re)` stays hardcoded: it is a generic English phrase, not
# a customer name, and it is what the audited files actually contained.
CLIENT_NAMES = [r"live event cent(?:er|re)"]

# An acronym is a client name with the letters filed off. Case-SENSITIVE on
# purpose: a lowercase token in prose is noise, and an acronym only leaks when
# written in capitals. Supply real ones through the denylist too.
CLIENT_ACRONYMS: list[str] = [r"LEC"]

# Left-hand sides that mark a Fabric SQL endpoint as documentation, not a host.
_HOST_PLACEHOLDER_CHARS = set("<{$%*")
_HOST_PLACEHOLDER_WORDS = re.compile(
    r"^(?:your|my|xxx+|host|server|endpoint|sql[_-]?endpoint|placeholder|"
    r"workspace|lakehouse|warehouse)$", re.I)


class Rule:
    __slots__ = ("name", "rx", "severity", "hint")

    def __init__(self, name: str, pattern: str, severity: str, hint: str,
                 flags: int = re.I):
        self.name = name
        self.rx = re.compile(pattern, flags)
        self.severity = severity
        self.hint = hint


# `BLOCK` must never be published. `WARN` is usually fine but worth a look.
RULES: list[Rule] = [
    Rule("private-key",
         r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----",
         "BLOCK", "Remove the key and rotate it — assume it is compromised."),
    Rule("connection-string-secret",
         r"(?:AccountKey|SharedAccessKey|Password|Pwd)\s*=\s*[^\s;\"']{12,}",
         "BLOCK", "Move to a secret store; reference by name only."),
    Rule("sas-token",
         r"[?&]sig=[A-Za-z0-9%+/=]{20,}",
         "BLOCK", "SAS tokens grant access — revoke and regenerate."),
    Rule("bearer-token",
         r"\b(?:eyJ[A-Za-z0-9_-]{10,}\.){2}[A-Za-z0-9_-]{10,}",
         "BLOCK", "A JWT was pasted into the repo. Remove it."),
    Rule("azure-secret-assignment",
         r"(?:client_secret|clientSecret|api[_-]?key|apiKey|access[_-]?key)"
         r"\s*[:=]\s*[\"']?[A-Za-z0-9~._\-]{16,}",
         "BLOCK", "Replace with a placeholder and read from env/Key Vault."),
    Rule("tenant-domain",
         r"\b(?!zava\.|contoso\.|fabrikam\.|example\.|yourtenant\.|mytenant\.)"
         r"[A-Za-z0-9][A-Za-z0-9-]{1,60}\.onmicrosoft\.com\b",
         "BLOCK", "Identifies your tenant. Use zava.onmicrosoft.com."),
    Rule("corporate-email",
         r"\b[A-Za-z0-9._%+-]+@(?:microsoft|outlook|gmail|hotmail)\.com\b",
         "BLOCK", "Use first.last@zava.com or user@example.com."),
    Rule("windows-user-path",
         r"[A-Za-z]:\\Users\\(?!<|\{|%|USERNAME|Public\b)[A-Za-z0-9._-]+",
         "WARN", "Leaks your account name. Use %USERPROFILE% or <user>."),
    Rule("posix-home-path",
         r"/(?:home|Users)/(?!<|\{|runner\b|vsts\b)[a-z][a-z0-9._-]{2,}/",
         "WARN", "Leaks your account name. Use $HOME or <user>."),
    Rule("real-guid",
         GUID_RE,
         "WARN", "Tenant / subscription / workspace / item ID. Use a "
                 "placeholder GUID, or allowlist it if it is a public constant."),
    # ── added 2026-08-03 after the external audit ────────────────
    Rule("client-name",
         r"\b(?:" + "|".join(CLIENT_NAMES) + r")\b",
         "BLOCK", "Names a real engagement. Use Zava, or an undeducible "
                  "generic label ('a live-event control-room demo')."),
    Rule("client-acronym",
         r"\b(?:" + "|".join(CLIENT_ACRONYMS) + r")\b",
         "BLOCK", "An acronym is a client name with the letters filed off. "
                  "Remove it.", flags=0),
    # Hyphen and EN DASH only. The en dash is how one of the audited names hid
    # (`ABC – Financial Platform` does not match a plain `-` grep). The EM DASH
    # is deliberately excluded: this brain uses it as a title separator
    # (`# Fabric API — REST Reference`, `## Ontology — GQL`), so including it
    # produced 15 false positives on a clean tree — and a scanner that cries
    # wolf gets switched off.
    Rule("personal-workspace-prefix",
         r"(?<![A-Za-z0-9_])[A-Z]{2,4} [-\u2013] (?=[A-Z][a-z])",
         "BLOCK", "Initials in a workspace name publish their owner into every "
                  "screenshot and API response. Use the 'Zava - ' prefix "
                  "(PUBLIC_SAFETY.md).", flags=0),
    Rule("fabric-sql-endpoint",
         r"[A-Za-z0-9_<>{}$%*.\-]+\."
         r"(?:datawarehouse\.fabric\.microsoft\.com"
         r"|datawarehouse\.pbidedicated\.windows\.net)",
         "BLOCK", "A real SQL analytics endpoint identifies the workspace and "
                  "the tenant. Use <sql_endpoint>.datawarehouse.fabric.microsoft.com."),
    # ── added 2026-08-31: a resource hostname is an identifier with no GUID ──
    # `real-guid` cannot see this: there is no 8-4-4-4-12 run in
    # `myproject.services.ai.azure.com`, yet the label names a tenant resource
    # as precisely as a GUID does. Found in a downstream project, where a real
    # Foundry endpoint had been compiled into a bundle served *without*
    # authentication and no rule flagged it.
    Rule("azure-resource-hostname",
         r"[A-Za-z0-9_<>{}$%*.\-]+\."
         r"(?:services\.ai\.azure\.com"
         r"|openai\.azure\.com"
         r"|cognitiveservices\.azure\.com"
         r"|search\.windows\.net"
         r"|vault\.azure\.net"
         r"|servicebus\.windows\.net"
         r"|documents\.azure\.com"
         r"|blob\.core\.windows\.net"
         r"|dfs\.core\.windows\.net)",
         "BLOCK", "A resource hostname names your tenant's resource even though "
                  "it contains no GUID. Use a placeholder: "
                  "<resource>.services.ai.azure.com, or read it from env."),
]


# ── Scanning ────────────────────────────────────────────────────

def repo_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Files git would publish. Falls back to a plain walk outside git.

    Using `git ls-files` matters: it honours .gitignore, so a correctly
    ignored `resource_ids.md` is not reported. That is the whole point —
    keep the real values locally, publish only templates.
    """
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files"],
                             capture_output=True, text=True, timeout=60)
        if out.returncode == 0 and out.stdout.strip():
            return [root / line for line in out.stdout.splitlines() if line]
    except (OSError, subprocess.SubprocessError):
        pass
    return [p for p in root.rglob("*")
            if p.is_file() and ".git" not in p.parts]


def load_allowlist(root: pathlib.Path) -> dict[str, str]:
    """Values this repo has declared safe. Applies to *every* rule, not just GUIDs.

    A scanner without an escape hatch gets disabled the first time it is wrong.
    """
    allowed = {k.lower(): v for k, v in PUBLIC_GUIDS.items()}
    f = root / ".publicsafety-allow"
    if f.exists():
        for raw in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.split("#", 1)[0].strip()
            if line:
                allowed[line.lower()] = "allowlisted in .publicsafety-allow"
    return allowed


def load_denylist(root: pathlib.Path) -> list[str]:
    """Extra forbidden terms for this repo, supplied WITHOUT committing them.

    Two sources, both deliberately outside version control:

      * `CLIENT_DENYLIST` — comma-separated env var. In CI this is a repository
        secret, so the real customer names never appear in the repo, the logs
        or a pull request.
      * `.publicsafety-deny` — one term per line, `#` comments. Gitignored;
        for local runs.

    This indirection is the whole point. A scanner that hardcodes the names it
    forbids publishes them — see `known_issues.md` #47.
    """
    terms: list[str] = []

    env = os.environ.get("CLIENT_DENYLIST", "")
    terms += [t.strip() for t in env.split(",") if t.strip()]

    f = root / ".publicsafety-deny"
    if f.exists():
        for raw in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.split("#", 1)[0].strip()
            if line:
                terms.append(line)
    return terms


def denylist_rules(root: pathlib.Path) -> list[Rule]:
    terms = load_denylist(root)
    if not terms:
        return []
    return [Rule("denylisted-term",
                 r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")\b",
                 "BLOCK",
                 "Listed in this repo's denylist (CLIENT_DENYLIST or "
                 ".publicsafety-deny). Remove it.")]


# Rules whose match IS a client name. Reprinting it would republish the very
# thing this scanner exists to remove, into a public Actions log. GitHub secret
# masking does not cover it: these rules are case-insensitive and report the
# text as written in the file, not the secret's own spelling.
NAME_BASED_RULES = frozenset({"client-name", "client-acronym", "denylisted-term"})


def _is_secret_read(line: str, match: re.Match) -> bool:
    """True when the value is fetched at runtime rather than hardcoded.

    `pwd = dbutils.secrets.get(scope, key)` is the *correct* pattern — flagging
    it would train the reader to ignore this rule. A hardcoded literal never
    contains a call or an expansion.
    """
    value = match.group(0)
    return any(tok in value for tok in ("(", "${", "$(", "%(", "os.environ",
                                        "getenv", "<", "{{"))


def _is_arithmetic(line: str, match: re.Match) -> bool:
    """True when `ABC - ` is a subtraction, not a workspace prefix.

    `Revenue - COGS - Operating Expenses` and `SLIDE_W - FAB_L - GAP - M` are
    formulas that happen to spell capitals. A name never follows an operator.
    """
    before = line[:match.start()].rstrip()
    return before.endswith(("-", "\u2013", "\u2014", "+", "/", "="))


def _is_placeholder_host(match: re.Match) -> bool:
    """True when the SQL endpoint is documentation rather than a real host.

    `*.datawarehouse.fabric.microsoft.com` and
    `<sql_endpoint>.datawarehouse.fabric.microsoft.com` are the shapes the brain
    teaches; flagging them would make the rule unusable in the very files that
    explain the format.
    """
    value = match.group(0)
    left = value[:value.lower().index(".datawarehouse")]
    if any(c in _HOST_PLACEHOLDER_CHARS for c in left):
        return True
    return bool(_HOST_PLACEHOLDER_WORDS.match(left))


def _is_placeholder_resource_host(match: re.Match) -> bool:
    """True when an Azure resource hostname is documentation, not a real host.

    Sibling of `_is_placeholder_host`, kept separate because the suffix list
    differs and because that function hardcodes `.datawarehouse`. Same failure
    mode to avoid: the brain *teaches* these hostnames, so a rule that flags
    `<resource>.services.ai.azure.com` fires 20 times on a clean tree and gets
    switched off — which protects nothing.

    Also accepts `my*` / `your*` labels (`myvault.vault.azure.net`), which the
    Azure docs use as example names, and bare role words (`account`,
    `storageaccount`, `storage`) — a label that is only a common noun names a
    role, not an instance. Real resource names carry a discriminator: digits, a
    region or environment suffix, or a non-word run.
    """
    value = match.group(0)
    left = re.split(r"\.(?:services|openai|cognitiveservices|search|vault|"
                    r"servicebus|documents|blob|dfs)\.", value, maxsplit=1)[0]
    if any(c in _HOST_PLACEHOLDER_CHARS for c in left):
        return True
    if _HOST_PLACEHOLDER_WORDS.match(left):
        return True
    if re.match(r"^(?:my|your|example|sample|contoso|zava|fabrikam)"
                r"[a-z0-9-]*$", left, re.I):
        return True
    return bool(re.match(
        r"^(?:storage|storageaccount|account|container|resource|project|"
        r"foundry|namespace|vault|keyvault|kv|adls|datalake|onelake|"
        r"cosmos|search|openai|aiservices|blobstorage)$", left, re.I))


def scan_file(path: pathlib.Path, root: pathlib.Path,
              allowed: dict[str, str],
              rules: list[Rule] | None = None) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for rule in (rules or RULES):
            for m in rule.rx.finditer(line):
                value = m.group(0)
                if value.lower() in allowed:
                    continue
                if rule.name == "real-guid" and PLACEHOLDER_GUID.match(value):
                    continue
                if rule.name == "connection-string-secret" and _is_secret_read(line, m):
                    continue
                if rule.name == "personal-workspace-prefix" and _is_arithmetic(line, m):
                    continue
                if rule.name == "fabric-sql-endpoint" and _is_placeholder_host(m):
                    continue
                if (rule.name == "azure-resource-hostname"
                        and _is_placeholder_resource_host(m)):
                    continue
                findings.append({
                    "file": str(path.relative_to(root)).replace("\\", "/"),
                    "line": lineno,
                    "rule": rule.name,
                    "severity": rule.severity,
                    "match": ("[redacted]" if rule.name in NAME_BASED_RULES
                              else (value if len(value) <= 60
                                    else value[:57] + "...")),
                    "hint": rule.hint,
                })
    return findings


def scan(root: pathlib.Path) -> list[dict]:
    allowed = load_allowlist(root)
    rules = RULES + denylist_rules(root)
    out: list[dict] = []
    for path in repo_files(root):
        if not path.is_file() or path.name in SELF:
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        out.extend(scan_file(path, root, allowed, rules))
    return out


# ── CLI ─────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Find anything that must not be published.")
    ap.add_argument("path", nargs="?", default=".", help="repo to scan")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--warn-ok", action="store_true",
                    help="exit 0 when only WARN findings remain")
    ap.add_argument("--list-allowed", action="store_true")
    args = ap.parse_args()

    root = pathlib.Path(args.path).resolve()
    if args.list_allowed:
        for guid, why in sorted(PUBLIC_GUIDS.items()):
            print(f"{guid}  {why}")
        return 0

    findings = scan(root)

    if args.as_json:
        print(json.dumps(findings, indent=2))
    else:
        blocks = [f for f in findings if f["severity"] == "BLOCK"]
        warns = [f for f in findings if f["severity"] == "WARN"]
        if not findings:
            print(f"clean - nothing to redact in {root.name}")
        for group, label in ((blocks, "BLOCK"), (warns, "WARN")):
            if not group:
                continue
            print(f"\n{label} ({len(group)})")
            for f in group:
                print(f"  {f['file']}:{f['line']}  [{f['rule']}]  {f['match']}")
                print(f"      -> {f['hint']}")
        if findings:
            print(f"\n{len(blocks)} BLOCK, {len(warns)} WARN. "
                  f"See PUBLIC_SAFETY.md for the redaction conventions.")

    if not findings:
        return 0
    if args.warn_ok and not any(f["severity"] == "BLOCK" for f in findings):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

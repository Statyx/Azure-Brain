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
"""
from __future__ import annotations

import argparse
import json
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
        ".publicsafety-allow"}


class Rule:
    __slots__ = ("name", "rx", "severity", "hint")

    def __init__(self, name: str, pattern: str, severity: str, hint: str):
        self.name = name
        self.rx = re.compile(pattern, re.I)
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


def _is_secret_read(line: str, match: re.Match) -> bool:
    """True when the value is fetched at runtime rather than hardcoded.

    `pwd = dbutils.secrets.get(scope, key)` is the *correct* pattern — flagging
    it would train the reader to ignore this rule. A hardcoded literal never
    contains a call or an expansion.
    """
    value = match.group(0)
    return any(tok in value for tok in ("(", "${", "$(", "%(", "os.environ",
                                        "getenv", "<", "{{"))


def scan_file(path: pathlib.Path, root: pathlib.Path,
              allowed: dict[str, str]) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for rule in RULES:
            for m in rule.rx.finditer(line):
                value = m.group(0)
                if value.lower() in allowed:
                    continue
                if rule.name == "real-guid" and PLACEHOLDER_GUID.match(value):
                    continue
                if rule.name == "connection-string-secret" and _is_secret_read(line, m):
                    continue
                findings.append({
                    "file": str(path.relative_to(root)).replace("\\", "/"),
                    "line": lineno,
                    "rule": rule.name,
                    "severity": rule.severity,
                    "match": value if len(value) <= 60 else value[:57] + "...",
                    "hint": rule.hint,
                })
    return findings


def scan(root: pathlib.Path) -> list[dict]:
    allowed = load_allowlist(root)
    out: list[dict] = []
    for path in repo_files(root):
        if not path.is_file() or path.name in SELF:
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        out.extend(scan_file(path, root, allowed))
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

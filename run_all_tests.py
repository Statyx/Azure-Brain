"""
Cross-project test runner for all Fabric demo projects.

Usage:
    python run_all_tests.py          # Run all tests
    python run_all_tests.py --smoke  # Smoke tests only
    python run_all_tests.py -v       # Verbose output
"""
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent  # parent of Github_Brain

PROJECTS = [
    {"name": "Financial_Platform",    "path": BASE_DIR / "Financial_Platform",    "expected": 125},
    {"name": "Fabric RTI Demo",       "path": BASE_DIR / "Fabric RTI Demo",       "expected": 30},
    {"name": "The_AI_Skill_Analyzer", "path": BASE_DIR / "The_AI_Skill_Analyzer", "expected": 81},
]


def run_tests(project, extra_args=None):
    """Run pytest for a single project. Returns (name, returncode, output)."""
    test_dir = project["path"] / "tests"
    if not test_dir.exists():
        return project["name"], -1, "NO tests/ DIRECTORY FOUND"

    cmd = [sys.executable, "-m", "pytest", str(test_dir), "--tb=short", "-q"]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(
        cmd,
        cwd=str(project["path"]),
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        timeout=120,
    )
    output = result.stdout + result.stderr
    return project["name"], result.returncode, output


def main():
    extra = []
    if "--smoke" in sys.argv:
        extra.extend(["-m", "smoke"])
    if "-v" in sys.argv:
        extra.append("-v")
    if "--cov" in sys.argv:
        extra.extend(["--cov=src", "--cov-report=term-missing"])

    print("=" * 60)
    print("  CROSS-PROJECT TEST RUNNER")
    print("=" * 60)

    results = []
    total_passed = 0
    total_failed = 0

    for project in PROJECTS:
        if not project["path"].exists():
            print(f"\n--- {project['name']} --- SKIPPED (directory not found)")
            continue

        print(f"\n--- {project['name']} ---")
        name, rc, output = run_tests(project, extra)
        results.append((name, rc))

        # Parse passed/failed from pytest output
        for line in output.strip().split("\n"):
            if "passed" in line or "failed" in line or "error" in line:
                print(f"  {line.strip()}")

        if rc == 0:
            print(f"  PASS")
        elif rc == -1:
            print(f"  SKIP — {output}")
        else:
            print(f"  FAIL (exit code {rc})")
            # Show failures
            for line in output.strip().split("\n"):
                if line.startswith("FAILED") or "ERROR" in line:
                    print(f"    {line.strip()}")

        if rc == 0:
            total_passed += project["expected"]
        else:
            total_failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    all_pass = all(rc == 0 for _, rc in results if rc != -1)
    for name, rc in results:
        status = "PASS" if rc == 0 else ("SKIP" if rc == -1 else "FAIL")
        print(f"  {name:30s} {status}")

    total_expected = sum(p["expected"] for p in PROJECTS)
    print(f"\n  Expected: ~{total_expected} tests across {len(PROJECTS)} projects")
    print(f"  Result:   {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()

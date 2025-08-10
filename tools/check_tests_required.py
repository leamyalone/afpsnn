import os
import subprocess
import sys

BASE = os.environ.get("GITHUB_BASE_REF", "main")
try:
    subprocess.run(
        ["git", "fetch", "--depth=1", "origin", BASE],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
except Exception:
    pass

diff = subprocess.check_output(
    [
        "git",
        "diff",
        "--name-only",
        f"origin/{BASE}...HEAD",
    ],
    text=True,
)
files = [p.strip() for p in diff.splitlines() if p.strip()]
touches_code = any(p.startswith(("models/", "src/")) for p in files)
touches_tests = any(p.startswith("tests/") for p in files)

if touches_code and not touches_tests:
    print("[tests-required] PR touches code but not tests.")
    sys.exit(1)

print("[tests-required] OK")

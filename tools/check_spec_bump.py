import pathlib
import re
import subprocess
import sys

repo = pathlib.Path(__file__).resolve().parents[1]
base = "origin/main"

try:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}...HEAD"], text=True
    ).splitlines()
except subprocess.CalledProcessError:
    changed = []

api_touch = any(p.startswith(("API-INTERFACES.md", "src/")) for p in changed)

manifest_path = repo / "AFPSNN-MANIFEST.md"
if not manifest_path.exists():
    print("AFPSNN-MANIFEST.md not found")
    sys.exit(1)

manifest = manifest_path.read_text(encoding="utf-8", errors="ignore")

# The manifest line is formatted as "Spec version: **v0.3.5**" with markdown
# emphasis. Accept optional surrounding asterisks so the check works even if
# the version string is bolded.
m = re.search(r"Spec version:\s*\**v(\d+\.\d+\.\d+)\**", manifest)
if not m:
    print("Unable to read spec version from AFPSNN-MANIFEST.md")
    sys.exit(1)
version = m.group(1)

if api_touch and version == "0.3.5":
    print("API/kernels changed but MANIFEST still at v0.3.5 — require v0.3.6 + SPEC AMENDMENT in PR.")
    sys.exit(2)

print("Spec bump guard OK.")

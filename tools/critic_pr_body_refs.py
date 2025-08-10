import os, sys

body = (os.environ.get("PR_BODY") or "").lower()
ok = ("spec references" in body) and (
    "§11" in body or "section 11" in body or
    "§12" in body or "section 12" in body or
    "manifest" in body
)
if not ok:
    print("[spec-refs] PR body must include 'Spec references' citing MANIFEST sections (e.g., §11, §12).")
    sys.exit(1)

print("[spec-refs] OK")

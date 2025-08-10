import os
import sys

body = (os.environ.get("PR_BODY") or "").lower()

has_header = "spec references" in body
mentions_section = any(
    tok in body
    for tok in ("§11", "section 11", "§12", "section 12", "§4.6", "section 4.6")
)

if not (has_header and mentions_section):
    print(
        "[spec-refs] PR body must include a 'Spec references' section citing MANIFEST sections "
        "(e.g., §11, §12, §4.6)."
    )
    sys.exit(1)

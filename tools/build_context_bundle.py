#!/usr/bin/env python3
"""
Assemble a small context bundle for an AFPSNN task.
This script reads STATE.md and an optional impact JSON file and prints a
context snippet including the current task, manifest/API summaries, and
impact details. It helps downstream models operate on only the relevant
portion of the repository when the codebase grows.
"""
import argparse
import json
import pathlib

import yaml


def read_summary(summary_dir: pathlib.Path, name: str) -> str:
    """Return the contents of a summary file if it exists."""
    p = summary_dir / f"{name}.summary.md"
    if p.exists():
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a context bundle for the next AFPSNN task."
    )
    parser.add_argument(
        "--state", default="STATE.md", help="Path to STATE.md YAML file"
    )
    parser.add_argument(
        "--impact", help="Path to impact JSON file (from impact_map.py)"
    )
    args = parser.parse_args()

    state_path = pathlib.Path(args.state)
    if not state_path.exists():
        raise SystemExit(f"State file {args.state} not found")

    # Load state YAML
    with state_path.open("r", encoding="utf-8") as f:
        state = yaml.safe_load(f)
    next_steps = state.get("next_steps", [])
    current_task = next_steps[0] if next_steps else "No tasks"

    lines = []
    lines.append("## Current task\n")
    lines.append(current_task + "\n")

    # Append summaries
    summary_dir = pathlib.Path("docs") / "summaries"
    manifest_summary = read_summary(summary_dir, "AFPSNN-MANIFEST.md")
    if manifest_summary:
        lines.append("## Manifest summary\n")
        lines.append(manifest_summary + "\n")
    api_summary = read_summary(summary_dir, "API-INTERFACES.md")
    if api_summary:
        lines.append("## API summary\n")
        lines.append(api_summary + "\n")

    # Include impact details if provided
    if args.impact:
        impact_path = pathlib.Path(args.impact)
        if impact_path.exists():
            try:
                data = json.loads(impact_path.read_text(encoding="utf-8"))
                lines.append("## Impact\n")
                lines.append(json.dumps(data, indent=2) + "\n")
            except Exception:
                pass

    print("\n".join(lines))


if __name__ == "__main__":
    main()

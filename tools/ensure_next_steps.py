#!/usr/bin/env python3

import argparse
import yaml
import os
import datetime


def main():
    parser = argparse.ArgumentParser(description="Ensure next_steps list is not empty and replenish from backlog.")
    parser.add_argument("--ci", action="store_true", help="Validate only; fail if next_steps empty or invalid YAML.")
    parser.add_argument("--agent", action="store_true", help="Replenish next_steps from backlog until at least length 2.")
    args = parser.parse_args()

    # Determine path to STATE.md relative to this script
    # STATE.md resides two directories up from this file (project root)
    state_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "STATE.md")

    if not os.path.exists(state_path):
        raise SystemExit("STATE.md not found at expected location: {}".format(state_path))

    with open(state_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML portion by discarding markdown heading lines starting with '#'
    lines = content.splitlines()
    yaml_lines = [line for line in lines if not line.lstrip().startswith("#")]
    yaml_str = "\n".join(yaml_lines)

    try:
        data = yaml.safe_load(yaml_str) or {}
    except Exception as e:
        raise SystemExit(f"Failed to parse STATE.md: {e}")

    # Ensure dictionaries for keys
    if not isinstance(data.get("next_steps"), list):
        data["next_steps"] = data.get("next_steps", []) or []
    if not isinstance(data.get("backlog"), list):
        data["backlog"] = data.get("backlog", []) or []
    if not isinstance(data.get("done"), list):
        data["done"] = data.get("done", []) or []

    next_steps = data["next_steps"]
    backlog = data["backlog"]

    if args.ci:
        # Validation mode: ensure next_steps is non-empty
        if len(next_steps) == 0:
            raise SystemExit("STATE.md next_steps is empty; please add tasks before merging.")
        # Optionally check YAML version fields etc.
        return

    if args.agent:
        # Replenish next_steps from backlog until length >= 2
        changed = False
        while len(next_steps) < 2 and backlog:
            next_steps.append(backlog.pop(0))
            changed = True
        if changed:
            data["next_steps"] = next_steps
            data["backlog"] = backlog
            # Reconstruct file preserving header lines
            header_lines = [line for line in lines if line.lstrip().startswith("#")]
            # Dump YAML with keys kept in insertion order
            new_yaml = yaml.safe_dump(data, sort_keys=False)
            new_content = "\n".join(header_lines + [""] + new_yaml.splitlines())
            with open(state_path, "w", encoding="utf-8") as wf:
                wf.write(new_content)
        return


if __name__ == "__main__":
    main()

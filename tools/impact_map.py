# tools/impact_map.py
"""Static analysis tool to compute impacted files, symbols and manifest sections for a proposed task.

This tool is intentionally conservative.  Given a list of files and optionally symbols that a task will
modify or read, it walks the Python AST to gather import dependencies and scans C/CUDA source files
for simple #include statements.  The output is a JSON blob containing the original task description,
the transitive closure of files that may be impacted, the list of touched symbols, and an empty
placeholder for manifest sections (which can be filled manually).

Usage examples:

    # Analyse a scheduler update touching scheduler.py and kernels.cu
    python tools/impact_map.py --task "S01-T02 router buckets" \
        --files "models/core/scheduler.py,src/kernels.cu" \
        --symbols "router_schedule,combine_detect" \
        -o impact.json
"""

import argparse
import ast
import json
import os
import re
from typing import List, Set


def collect_imports_py(path: str) -> List[str]:
    """Return a list of top-level module names imported by a Python file."""
    imports: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(module)
    except Exception:
        # If parsing fails, ignore to keep analysis lightweight
        pass
    return imports


def collect_includes_cpp(path: str) -> List[str]:
    """Return a list of header paths included by a C/C++/CUDA source file."""
    includes: List[str] = []
    pattern = re.compile(r"#include\s*[<\"]([^>\"]+)[>\"]")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    includes.append(match.group(1))
    except Exception:
        # Best-effort only; ignore unreadable files
        pass
    return includes


def build_impact(task: str, files: List[str], symbols: List[str], repo_root: str) -> dict:
    """Compute a simple impact map for the given files and symbols."""
    impacted: Set[str] = set()
    for rel in files:
        # normalise and store touched file
        rel = rel.strip()
        if not rel:
            continue
        impacted.add(rel)
        path = os.path.join(repo_root, rel)
        if not os.path.exists(path):
            continue
        if rel.endswith(".py"):
            for mod in collect_imports_py(path):
                # Convert module name to a candidate file under models
                mod_path = mod.replace(".", "/") + ".py"
                candidate = os.path.join(repo_root, mod_path)
                # Also check under models/ for canonical project layout
                alt_candidate = os.path.join(repo_root, "models", mod_path)
                for cand in (candidate, alt_candidate):
                    if os.path.exists(cand):
                        rel_cand = os.path.relpath(cand, repo_root)
                        impacted.add(rel_cand)
        elif any(rel.endswith(ext) for ext in (".c", ".cpp", ".cu")):
            for inc in collect_includes_cpp(path):
                # Only consider includes under src/
                inc_candidate = os.path.join(repo_root, "src", inc)
                if os.path.exists(inc_candidate):
                    rel_inc = os.path.relpath(inc_candidate, repo_root)
                    impacted.add(rel_inc)
    return {
        "task": task,
        "files": sorted(impacted),
        "symbols": symbols,
        # Manifest sections can be filled by higher-level tools
        "manifest_sections": []
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute a simple impact map for a proposed task.")
    parser.add_argument("--task", type=str, default="", help="Task description")
    parser.add_argument("--files", type=str, help="Comma-separated list of touched files")
    parser.add_argument("--symbols", type=str, default="", help="Comma-separated list of touched symbols")
    parser.add_argument("--repo-root", type=str, default=".", help="Root of the repository")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output JSON file path")
    args = parser.parse_args()

    touched_files = [f.strip() for f in args.files.split(",")] if args.files else []
    touched_symbols = [s.strip() for s in args.symbols.split(",")] if args.symbols else []

    impact = build_impact(args.task, touched_files, touched_symbols, args.repo_root)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(impact, f, indent=2)
    else:
        print(json.dumps(impact, indent=2))


if __name__ == "__main__":
    main()

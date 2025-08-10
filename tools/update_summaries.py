#!/usr/bin/env python3
"""
Update summary files for AFPSNN documentation.
This script reads the first N lines of key markdown documents and writes them to
corresponding files under docs/summaries/.
"""
import argparse
import pathlib


def summarize_file(path: pathlib.Path, lines: int = 40) -> str:
    """Return the first `lines` lines of a text file."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.readlines()[:lines]
        return "".join(content)
    except Exception:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate summary snippets for AFPSNN docs."
    )
    parser.add_argument(
        "--lines", type=int, default=40, help="Number of lines to capture from each doc"
    )
    parser.add_argument(
        "--docs-dir", default=".", help="Root directory containing the docs"
    )
    parser.add_argument(
        "--output-dir",
        default="docs/summaries",
        help="Directory to write summary files",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.docs_dir)
    outdir = root / args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)

    # List of docs to summarise
    docs = [
        "AFPSNN-MANIFEST.md",
        "API-INTERFACES.md",
        "SPRINT-01.md",
        "README-SESSION-PRIMER.md",
        "README-BOOTSTRAP.md",
    ]
    for doc in docs:
        src = root / doc
        dst = outdir / f"{doc}.summary.md"
        if src.exists():
            snippet = summarize_file(src, lines=args.lines)
            with dst.open("w", encoding="utf-8") as out:
                out.write(f"# Summary of {doc}\n\n")
                out.write(snippet)


if __name__ == "__main__":
    main()

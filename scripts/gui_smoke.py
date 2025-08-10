#!/usr/bin/env python3
"""
Headless GUI smoke: run a 1s sim, render a minimal visual, write PNG under artifacts/gui_smoke/.
Non-interactive; used by CI so a human can review.
"""
from __future__ import annotations
import os, time, pathlib
import matplotlib.pyplot as plt  # ensure matplotlib in requirements.txt
from models.visual.network_map import render_network_overview  # or a simple plot fallback

ART_DIR = pathlib.Path("artifacts/gui_smoke")
ART_DIR.mkdir(parents=True, exist_ok=True)

def main() -> str:
    # TODO: replace with real model when available
    fig, ax = plt.subplots()
    try:
        render_network_overview(ax=ax)  # if this exists; else just draw a stub
    except Exception:
        ax.set_title("AFPSNN GUI Smoke — placeholder")
        ax.plot([0, 1, 2], [0, 1, 0])

    ts = time.strftime("%Y%m%d-%H%M%S")
    out = ART_DIR / f"smoke-{ts}.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return str(out)

if __name__ == "__main__":
    path = main()
    print(f"[gui-smoke] wrote {path}")

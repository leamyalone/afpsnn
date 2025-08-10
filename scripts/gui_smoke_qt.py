#!/usr/bin/env python3
from __future__ import annotations
import os, time, pathlib

# Headless/offscreen
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtWidgets
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter

ART_DIR = pathlib.Path("artifacts/gui_smoke")
ART_DIR.mkdir(parents=True, exist_ok=True)

def main() -> str:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    # Minimal, deterministic visual; replace with real scene later
    w = pg.PlotWidget(title="AFPSNN GUI Smoke — PyQtGraph")
    w.resize(800, 480)
    p = w.plot([0, 1, 2, 3], [0, 1, 0, 1], pen=pg.mkPen(width=2))
    w.setLabel("bottom", "t")
    w.setLabel("left", "a.u.")
    app.processEvents()

    ts = time.strftime("%Y%m%d-%H%M%S")
    out = ART_DIR / f"smoke-{ts}.png"

    # Export without needing a visible display
    exporter = ImageExporter(w.plotItem)
    exporter.parameters()["width"] = 800  # keep crisp
    exporter.export(str(out))

    w.close()
    app.quit()
    print(f"[gui-smoke] wrote {out}")
    return str(out)

if __name__ == "__main__":
    main()

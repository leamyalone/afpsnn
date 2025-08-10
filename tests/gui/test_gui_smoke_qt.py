from __future__ import annotations
from pathlib import Path
import importlib

def test_gui_smoke_qt_writes_png(tmp_path: Path):
    mod = importlib.import_module("scripts.gui_smoke_qt")
    out = Path(mod.main())
    assert out.exists(), "GUI smoke did not write an image"
    assert out.suffix.lower() == ".png"
    assert out.stat().st_size > 1024, "PNG too small—likely empty"

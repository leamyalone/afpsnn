from __future__ import annotations

import importlib
from pathlib import Path


def test_gui_smoke_writes_png(tmp_path: Path):
    # Run the smoke script and assert we got a PNG with bytes
    mod = importlib.import_module("scripts.gui_smoke")
    out_path = Path(mod.main())
    assert out_path.exists(), "GUI smoke did not write an image"
    assert out_path.suffix.lower() == ".png"
    assert out_path.stat().st_size > 1024, "PNG too small—likely empty"

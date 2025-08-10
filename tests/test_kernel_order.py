"""Kernel order tests based on MANIFEST §11."""

import re
from pathlib import Path


def _manifest_kernel_order():
    manifest = Path(__file__).resolve().parents[1] / "AFPSNN-MANIFEST.md"
    order = []
    in_section = False
    pattern = re.compile(r"\*\*(\w+)\*\*")
    for line in manifest.read_text().splitlines():
        if line.startswith("## 11"):
            in_section = True
            continue
        if in_section:
            if line.startswith("##"):
                break
            m = pattern.search(line)
            if m:
                order.append(m.group(1))
    return order


def test_kernel_order_matches_manifest():
    expected = [
        "router_drain_coalesce",
        "integrate_arrivals",
        "decay_spectra",
        "update_history",
        "pacer_update_scales",
        "combine_detect",
        "refractory_update",
        "schmitt_emit",
        "plasticity_update",
        "apply_residual",
        "router_schedule",
    ]
    assert _manifest_kernel_order() == expected

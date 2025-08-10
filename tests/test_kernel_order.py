"""Kernel order tests based on MANIFEST §11."""

from __future__ import annotations

import re
from pathlib import Path


def _manifest_kernel_order() -> list[str]:
    manifest = Path(__file__).resolve().parents[1] / "AFPSNN-MANIFEST.md"
    order: list[str] = []
    in_section = False
    # Support either **NAME** or `NAME`
    bold = re.compile(r"\*\*([A-Za-z0-9_]+)\*\*")
    code = re.compile(r"`([A-Za-z0-9_]+)`")

    for line in manifest.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("## 11") or re.search(r"(^|\s)(§?\s*11)(\D|$)", line):
            in_section = True
            continue
        if in_section:
            if line.startswith("##"):
                break
            m = bold.search(line) or code.search(line)
            if m:
                order.append(m.group(1))
    assert order, "Parsed empty kernel order from §11; check MANIFEST formatting."
    return order


def _runtime_kernel_order() -> list[str]:
    """Scheduler must expose KERNEL_ORDER or get_kernel_order()."""
    from models.core import scheduler  # type: ignore

    if hasattr(scheduler, "KERNEL_ORDER"):
        return list(getattr(scheduler, "KERNEL_ORDER"))
    if hasattr(scheduler, "get_kernel_order"):
        return list(scheduler.get_kernel_order())
    raise AssertionError(
        "Scheduler must expose KERNEL_ORDER or get_kernel_order() to enforce §11."
    )


def test_kernel_order_matches_manifest_and_runtime() -> None:
    # Your original expected list (kept)
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

    spec = _manifest_kernel_order()
    runtime = _runtime_kernel_order()

    assert spec == expected, f"Spec §11 changed? \nSpec: {spec}\nExpected: {expected}"
    assert (
        runtime == expected
    ), f"Runtime kernel order mismatch.\nRuntime: {runtime}\nExpected: {expected}"
    assert len(runtime) == len(set(runtime)), "Runtime kernel order has duplicates."

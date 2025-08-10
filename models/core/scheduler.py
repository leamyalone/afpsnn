# models/core/scheduler.py
"""
Runtime scheduler for AFPSNN kernel loop.

This module exposes the canonical kernel order from the spec and provides a
strict (or lenient) step executor that calls each stage in that order.

Stages (in order):
    1) router_drain_coalesce
    2) integrate_arrivals
    3) decay_spectra
    4) update_history
    5) pacer_update_scales
    6) combine_detect
    7) refractory_update
    8) schmitt_emit
    9) plasticity_update
    10) apply_residual
    11) router_schedule

Design notes:
- `get_kernel_order()` returns a plain list for tests and tooling.
- `Scheduler` accepts a mapping of {stage_name: callable(ctx)}.
- `allow_missing=True` lets you bring up the loop before all kernels exist.
  Set to False in CI or production to fail fast if any stage is absent.
- No global state: you can instantiate multiple schedulers with different
  kernel bindings (CPU reference vs. CUDA).
"""

from __future__ import annotations
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

# Canonical order from the spec (keep in lock-step with §11 and tests)
KERNEL_ORDER: Tuple[str, ...] = (
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
)

__all__ = [
    "KERNEL_ORDER",
    "get_kernel_order",
    "Scheduler",
    "validate_kernel_bindings",
]

def get_kernel_order() -> List[str]:
    """
    Returns the canonical kernel order as a list (stable, copy-safe).
    """
    return list(KERNEL_ORDER)


def validate_kernel_bindings(
    kernels: Mapping[str, Callable[..., None]],
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """
    Check provided kernel mapping against the required order.

    Returns:
        missing: tuple of stage names in KERNEL_ORDER that are not provided
        extras:  tuple of provided keys that are not in KERNEL_ORDER

    This does not mutate anything; it just reports. Useful for CI and logs.
    """
    required = set(KERNEL_ORDER)
    provided = set(kernels.keys())
    missing = tuple(name for name in KERNEL_ORDER if name not in provided)
    extras = tuple(sorted(provided - required))
    return missing, extras


class Scheduler:
    """
    Executes AFPSNN kernels in the canonical order.

    Args:
        kernels: mapping from stage name -> callable(ctx)
        allow_missing: if True, skip missing stages with a no-op; if False,
            raise NotImplementedError on the first missing stage.

    Methods:
        step_tick(ctx): run one ordered pass over the kernel loop.
    """

    def __init__(
        self,
        kernels: Optional[Mapping[str, Callable[..., None]]] = None,
        *,
        allow_missing: bool = True,
    ) -> None:
        self._kernels: Dict[str, Callable[..., None]] = dict(kernels or {})
        self._allow_missing = allow_missing

    @property
    def allow_missing(self) -> bool:
        return self._allow_missing

    def bind(self, name: str, fn: Callable[..., None]) -> None:
        """
        Bind or replace a kernel implementation at runtime.
        """
        if name not in KERNEL_ORDER:
            raise ValueError(f"Unknown kernel name '{name}'.")
        if not callable(fn):
            raise TypeError(f"Kernel '{name}' must be callable.")
        self._kernels[name] = fn

    def step_tick(self, ctx: object) -> None:
        """
        Execute one scheduler tick over KERNEL_ORDER.

        Behavior:
            - If a kernel is missing and allow_missing is False: raise.
            - If a kernel is missing and allow_missing is True: skip (no-op).
            - Any exception raised by a kernel bubbles up (fail fast).
        """
        for name in KERNEL_ORDER:
            fn = self._kernels.get(name)
            if fn is None:
                if self._allow_missing:
                    # Soft bring-up path; explicit no-op
                    continue
                raise NotImplementedError(
                    f"Kernel '{name}' is not bound. "
                    f"Provide an implementation or construct Scheduler(allow_missing=True)."
                )
            fn(ctx)

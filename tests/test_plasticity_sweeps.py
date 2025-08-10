"""Plasticity sweeps verifying phase relationships (§5.1–§5.2)."""

from __future__ import annotations

import math

import numpy as np


def _get_funcs():
    # Expect real implementations in models.adaptation.plasticity
    from models.adaptation import plasticity  # type: ignore

    delta_g = getattr(plasticity, "delta_g", None)
    delta_d = getattr(plasticity, "delta_d", None)
    assert callable(delta_g), "models.adaptation.plasticity.delta_g must exist"
    assert callable(delta_d), "models.adaptation.plasticity.delta_d must exist"
    return delta_g, delta_d


def test_plasticity_phase_signs() -> None:
    """In-phase potentiates; anti-phase depresses; lead/lag delay signs per §5.1–§5.2."""
    delta_g, delta_d = _get_funcs()
    phi_post = 0.0
    assert delta_g(0.0, phi_post) > 0  # in-phase potentiates (§5.1)
    assert delta_g(math.pi, phi_post) < 0  # anti-phase depresses (§5.1)
    assert delta_d(math.pi / 2, phi_post) < 0  # pre lags -> delay decreases (§5.2)
    assert delta_d(-math.pi / 2, phi_post) > 0  # pre leads -> delay increases (§5.2)


def test_plasticity_outputs_finite_and_bounded() -> None:
    """Basic sanity: Δg, Δd produce finite values in a reasonable range."""
    delta_g, delta_d = _get_funcs()
    xs = np.linspace(-math.pi, math.pi, 129)
    for f in (delta_g, delta_d):
        ys = [float(f(float(x), 0.0)) for x in xs]
        assert all(math.isfinite(y) for y in ys), "No NaN/inf in sweep"
        assert min(ys) >= -1.5 and max(ys) <= 1.5  # loose bound; tune if spec states exact limits

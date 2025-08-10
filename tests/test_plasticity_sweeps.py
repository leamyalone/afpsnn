"""Plasticity sweeps verifying phase relationships (§5.1–§5.2)."""

import numpy as np

# Phase-based plasticity sign checks (§5.1–§5.2)


def _delta_g(phi_pre, phi_post):
    return np.cos(phi_pre - phi_post)


def _delta_d(phi_pre, phi_post):
    return -np.sin(phi_pre - phi_post)


def test_plasticity_phase_signs():
    phi_post = 0.0
    assert _delta_g(0.0, phi_post) > 0  # in-phase potentiates (§5.1)
    assert _delta_g(np.pi, phi_post) < 0  # anti-phase depresses (§5.1)
    assert _delta_d(np.pi / 2, phi_post) < 0  # pre lags → delay decreases (§5.2)
    assert _delta_d(-np.pi / 2, phi_post) > 0  # pre leads → delay increases (§5.2)

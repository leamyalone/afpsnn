import numpy as np


def combine_detect_np(X_f, X_s, T_base, T_min, lambda_F, S_F, T_base_scale, lambda_scale, w_f, w_s, alpha_b=None):
    """
    Simplified CPU reference for combine and detect.
    X_f, X_s: np.ndarray of shape (B,) or (N,B).
    S_F: sensitivity array shape (B,) or (N,B,P). We'll use first P=0 index.
    T_base, T_min: scalar thresholds.
    T_base_scale, lambda_scale: per-neuron scaling, treat as scalars.
    Returns M, Phi, T_eff, spike_F, spike_P.
    """
    # Combine
    X = w_f * X_f + w_s * X_s
    M = np.abs(X)
    Phi = np.angle(X)
    # Sensitivity slice
    if hasattr(S_F, 'ndim') and S_F.ndim == 3:
        S = S_F[..., 0]
    else:
        S = S_F
    # Effective thresholds
    T_base_eff = T_base * T_base_scale
    lambda_eff = lambda_F * lambda_scale
    T_eff = np.maximum(T_min, T_base_eff * (1 - lambda_eff * S))
    # Spiking decisions
    spike_F = bool((M > T_eff).any())
    spike_P = False
    return M, Phi, T_eff, spike_F, spike_P


def router_sort_key(atom):
    """
    Return a tuple key for sorting router atoms deterministically.
    Accepts dict with keys: dst, bin, src, t_emit_s, type, toggle_dir, seq.
    """
    return (atom['dst'], atom['bin'], atom['src'], atom['t_emit_s'], atom['type'], atom['toggle_dir'], atom['seq'])

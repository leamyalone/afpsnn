import numpy as np

from tools.cpu_reference import combine_detect_np


def test_combine_detect_spike():
    X_f = np.array([[1.0 + 0.0j, 0.0 + 0.0j]], dtype=np.complex64)
    X_s = np.zeros_like(X_f)
    T_base = np.array([0.5], dtype=np.float32)
    T_min = np.array([0.1], dtype=np.float32)
    S_F = np.zeros((1, 2), dtype=np.float32)
    T_base_scale = np.array([1.0], dtype=np.float32)
    lambda_scale = np.array([1.0], dtype=np.float32)
    w_f = 1.0
    w_s = 0.0
    lambda_F = 0.0
    M, Phi, T_eff, spike_F, spike_P = combine_detect_np(
        X_f,
        X_s,
        T_base,
        T_min,
        lambda_F,
        S_F,
        T_base_scale,
        lambda_scale,
        w_f,
        w_s,
    )
    assert spike_F is True

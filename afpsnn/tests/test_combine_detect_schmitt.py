import numpy as np
from tools.cpu_reference import combine_detect_np


def test_combine_detect_spike():
    # Create simple pools for one neuron with two bins
    # X_f: fast pool complex values
    X_f = np.array([[1.0 + 0.0j, 0.0 + 0.0j]], dtype=np.complex64)
    # X_s: slow pool complex values (unused in this test)
    X_s = np.array([[0.0 + 0.0j, 0.0 + 0.0j]], dtype=np.complex64)
    # Base and minimum thresholds
    T_base = np.array([0.5], dtype=np.float32)
    T_min = np.array([0.1], dtype=np.float32)
    # Sensitivities disabled for this simple test
    S_F = None
    S_P = None
    alpha_b = None
    # Pacer scales and weights
    T_base_scale = np.array([1.0], dtype=np.float32)
    lambda_scale = np.array([1.0], dtype=np.float32)
    w_f_scale = np.array([1.0], dtype=np.float32)
    w_f = 1.0
    w_s = 0.0
    lambda_F = 0.0
    lambda_P = 0.0
    # Call CPU reference combine/detect
    result = combine_detect_np(
        X_f, X_s, T_base, T_min,
        S_F, S_P,
        T_base_scale, lambda_scale, w_f_scale,
        w_f, w_s,
        lambda_F, lambda_P,
        alpha_b,
    )
    # Expect spike for F path because amplitude 1 > threshold 0.5
    spike_F = result['spike_F']
    assert spike_F[0] is True

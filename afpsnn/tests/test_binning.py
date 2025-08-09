import numpy as np
import pytest

from afpsnn.models.core.signal import phase_bin, log_spaced_frequencies


def test_phase_bin_scalar_and_array():
    P = 4
    angles = np.array(
        [
            -np.pi,
            -np.pi / 2,
            0.0,
            np.pi / 2,
            np.pi - 1e-6,
            3 * np.pi / 2,
        ]
    )
    expected = np.array([0, 1, 2, 3, 3, 1])
    np.testing.assert_array_equal(phase_bin(angles, P), expected)
    assert phase_bin(-np.pi / 2, P) == 1


def test_phase_bin_invalid_bins():
    with pytest.raises(ValueError):
        phase_bin(0.0, 0)


def test_log_spaced_frequencies_values():
    freqs = log_spaced_frequencies(1.0, 1000.0, 4)
    expected = np.array([1.0, 10.0, 100.0, 1000.0])
    np.testing.assert_allclose(freqs, expected)


def test_log_spaced_frequencies_invalid_bins():
    with pytest.raises(ValueError):
        log_spaced_frequencies(1.0, 10.0, 1)

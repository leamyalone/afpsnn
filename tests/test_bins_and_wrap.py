import numpy as np

from models.core.signal import wrap_phase


def test_wrap_phase_idempotent():
    # Create a range of angles covering multiple periods
    angles = np.array(
        [
            -4 * np.pi,
            -3 * np.pi / 2,
            -np.pi,
            -np.pi / 2,
            0.0,
            np.pi / 2,
            np.pi,
            3 * np.pi / 2,
            4 * np.pi,
        ]
    )
    wrapped_once = wrap_phase(angles)
    wrapped_twice = wrap_phase(wrapped_once)
    # Idempotent: wrapping twice yields same result as once
    assert np.allclose(wrapped_once, wrapped_twice)
    # All wrapped phases should be within [-pi, pi)
    assert np.all((wrapped_once >= -np.pi) & (wrapped_once < np.pi))

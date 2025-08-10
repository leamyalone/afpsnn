import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))

from models.core.signal import wrap_phase


def test_wrap_phase_scalar_and_array():
    # Scalar value wraps from pi to -pi
    assert wrap_phase(np.pi) == -np.pi

    angles = np.array([0.0, np.pi, -np.pi, 3 * np.pi, -3 * np.pi, 10 * np.pi + 0.1])
    expected = np.array([0.0, -np.pi, -np.pi, -np.pi, -np.pi, 0.1])

    np.testing.assert_allclose(wrap_phase(angles), expected)

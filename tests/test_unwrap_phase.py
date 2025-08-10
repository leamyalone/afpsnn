import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))

from models.core.signal import unwrap_phase


def test_unwrap_phase_continuous():
    angles = np.array([0.0, np.pi - 0.1, -np.pi + 0.1, -np.pi + 0.2])
    expected = np.array([0.0, np.pi - 0.1, np.pi + 0.1, np.pi + 0.2])
    np.testing.assert_allclose(unwrap_phase(angles), expected)


def test_unwrap_phase_scalar():
    assert unwrap_phase(np.pi) == np.pi

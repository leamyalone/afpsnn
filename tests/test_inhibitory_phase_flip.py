import numpy as np
from models.core.signal import wrap_phase, effective_phase


def test_inhibitory_phase_flip_scalar():
    assert effective_phase(0.0, inhibitory=True) == -np.pi
    np.testing.assert_allclose(effective_phase(0.1, inhibitory=True),
                               wrap_phase(0.1 + np.pi))


def test_inhibitory_phase_flip_array_and_idempotence():
    phases = np.array([0.0, np.pi/2, -np.pi/2, np.pi - 1e-9, -np.pi + 1e-9])
    out_inh = effective_phase(phases, inhibitory=True)
    out_exc = effective_phase(phases, inhibitory=False)

    np.testing.assert_allclose(out_exc, wrap_phase(phases))
    np.testing.assert_allclose(out_inh, wrap_phase(phases + np.pi))

    # passing the already-flipped phases with inhibitory=False should be a no-op
    np.testing.assert_allclose(out_inh, effective_phase(out_inh, inhibitory=False))

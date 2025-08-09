"""Phase wrapping helpers."""

from __future__ import annotations

import numpy as np


def wrap_phase(x):
    """Wrap radians to the ``[-pi, pi)`` interval.

    Parameters
    ----------
    x : array_like
        Angle or array of angles in radians.

    Returns
    -------
    array_like
        Wrapped angle(s) in the range ``[-pi, pi)`` with the same shape as
        ``x``. If ``x`` is a scalar a scalar is returned.
    """

    arr = np.asarray(x)
    wrapped = (arr + np.pi) % (2 * np.pi) - np.pi
    # Preserve scalar input type for convenience
    return wrapped.item() if np.isscalar(x) else wrapped


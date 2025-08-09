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


def unwrap_phase(x, discont=np.pi):
    """Unwrap a sequence of angles to produce a continuous phase trace.

    Parameters
    ----------
    x : array_like
        Angle or array of angles in radians. For arrays, unwrapping is
        performed along the last axis.
    discont : float, optional
        Maximum discontinuity between values before wrapping is corrected.
        Defaults to ``np.pi`` which matches NumPy's behaviour.

    Returns
    -------
    array_like
        Unwrapped angle(s) with the same shape as ``x``. If ``x`` is a
        scalar a scalar is returned.

    Notes
    -----
    This is a thin wrapper around :func:`numpy.unwrap` that preserves the
    scalar input type for convenience.
    """

    arr = np.asarray(x)
    if arr.ndim == 0:
        return arr.item()
    unwrapped = np.unwrap(arr, discont=discont)
    # Preserve scalar input type for convenience
    return unwrapped.item() if np.isscalar(x) else unwrapped

"""Signal helpers for phase and frequency bins.

Utilities here implement binning rules defined by ``AFPSNN-MANIFEST v0.3.6``.
They provide deterministic mappings between continuous values and discrete
indices used throughout the simulator.
"""

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


def phase_bin(phi, num_bins):
    """Map phase angle(s) to phase-bin indices.

    Implements the lower-inclusive, upper-exclusive rule from
    ``AFPSNN-MANIFEST v0.3.6 §1.2``. Angles are wrapped to ``[-pi, pi)`` and
    then assigned to ``num_bins`` uniform bins over that interval.

    Parameters
    ----------
    phi : array_like
        Phase angle(s) in radians.
    num_bins : int
        Number of phase bins ``P``. Must be at least 1.

    Returns
    -------
    ndarray or int
        Bin index(es) in the range ``[0, P-1]``. Scalar inputs yield scalars.
    """
    if not isinstance(num_bins, (int, np.integer)):
        raise TypeError("num_bins must be an integer")
    if num_bins < 1:
        raise ValueError("num_bins must be >= 1")

    arr = np.asarray(phi)
    wrapped = wrap_phase(arr)
    t = (wrapped + np.pi) / (2 * np.pi)
    bins = np.floor(num_bins * t).astype(int)
    return bins.item() if np.isscalar(phi) else bins


def log_spaced_frequencies(f_min, f_max, bins):
    """Compute log-spaced frequency bin centres.

    Follows ``AFPSNN-MANIFEST v0.3.6 §1.1`` which defines centres ``f_b`` over
    ``[f_min, f_max]`` as::

        f_b = f_min * (f_max / f_min) ** (b / (B - 1))

    Parameters
    ----------
    f_min : float
        Lower frequency bound in Hertz.
    f_max : float
        Upper frequency bound in Hertz.
    bins : int
        Number of bins ``B``; must be at least 2.

    Returns
    -------
    ndarray
        Array of ``B`` log-spaced bin centres in Hertz.
    """

    if bins < 2:
        raise ValueError("bins must be >= 2")
    if f_min <= 0 or f_max <= 0:
        raise ValueError("frequencies must be positive")

    ratio = f_max / f_min
    exponents = np.arange(bins) / (bins - 1)
    return f_min * ratio**exponents


def effective_phase(phi, inhibitory: bool):
    """
    Return phase adjusted for inhibitory sources (π flip), wrapped to [-π, π).
    See MANIFEST §4.2 / §6.
    """
    if inhibitory:
        return wrap_phase(phi + np.pi)
    return wrap_phase(phi)

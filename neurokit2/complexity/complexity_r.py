# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt

from .complexity_delay import complexity_delay
from .complexity_dimension import complexity_dimension
from .entropy_approximate import entropy_approximate


def complexity_r(signal, delay=None, dimension=None, method="maxApEn", show=False):
    """Estimate optimal tolerance (similarity threshold)
    Parameters
    ----------
    signal : list, array or Series
        The signal (i.e., a time series) in the form of a vector of values.
    delay : int
        Time delay (often denoted 'Tau', sometimes referred to as 'lag'). In practice, it is common to have a fixed time lag (corresponding for instance to the sampling rate; Gautama, 2003), or to find a suitable value using some algorithmic heuristics (see ``delay_optimal()``).
    dimension : int
        Embedding dimension (often denoted 'm' or 'd', sometimes referred to as 'order'). Typically 2 or 3. It corresponds to the number of compared runs of lagged data. If 2, the embedding returns an array with two columns corresponding to the original signal and its delayed (by Tau) version.
    method : str
        If 'maxApEn', rmax where ApEn is max will be returned. If 'traditional', r = 0.2 * standard deviation of the signal will be returned.
    show : bool
        If true and method is 'maxApEn', will plot the ApEn values for each value of r.

    Returns
    ----------
    float
        The optimal r as float value.


    Examples
    ----------
    >>> import neurokit2 as nk
    >>>
    >>> signal = nk.signal_simulate(duration=2, frequency=5)
    >>> delay = nk.complexity_delay(signal)
    >>> dimension = nk.complexity_dimension(signal, delay=delay)
    >>> r = nk.complexity_r(signal, delay, dimension)
    >>> r
    0.010609254363011076

olerance (similarity threshold). It corresponds to the filtering level - max absolute difference between segments.

    References
    -----------
    - Lu, S., Chen, X., Kanters, J. K., Solomon, I. C., & Chon, K. H. (2008). Automatic selection of the threshold value r for approximate entropy. IEEE Transactions on Biomedical Engineering, 55(8), 1966-1972.
    """
    # Method
    method = method.lower()
    if method in ["traditional"]:
        r = 0.2 * np.std(signal, ddof=1)
    elif method in ["maxapen", 'optimize']:
        r = _optimize_r(signal, delay=delay, dimension=dimension, show=show)
    return r


# =============================================================================
# Internals
# =============================================================================
def _optimize_r(signal, delay=None, dimension=None, show=False):

    if not delay:
        delay = complexity_delay(signal, delay_max=100, method="fraser1986")
    if not dimension:
        dimension = complexity_dimension(signal, delay=delay, dimension_max=20, show=True)

    modulator = np.arange(0.02, 0.8, 0.02)
    r_range = modulator * np.std(signal, ddof=1)

    ApEn = np.zeros_like(r_range)

    for i, r in enumerate(r_range):
        ApEn[i] = entropy_approximate(signal, delay=delay, dimension=dimension, r=r_range[i])

    r = r_range[np.argmax(ApEn)]

    if show is True:
        plt.title(r'ApEn')
        plt.xlabel(r'r')
        plt.ylabel(r'Approximate Entropy $ApEn$')
        plt.plot(r_range, ApEn, 'bo-', label=r'$ApEn$')
        plt.legend()

    return r

# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt

from .density import density
from ..misc import findclosest


def hdi(x, ci=0.95, show=False, **kwargs):
    """Highest Density Interval (HDI)

    Compute the Highest Density Interval (HDI) of a distribution. All points within this interval have a higher probability density than points outside the interval. The HDI can be used in the context of uncertainty characterisation of posterior distributions (in the Bayesian farmework) as Credible Interval (CI). Unlike equal-tailed intervals that typically exclude 2.5% from each tail of the distribution and always include the median, the HDI is not equal-tailed and therefore always includes the mode(s) of posterior distributions.

    Parameters
    ----------
    x : list, array or Series
        A vector of values.
    ci : float
        Value of probability of the (credible) interval - CI (between 0 and 1) to be estimated. Default to .95 (95%).

    Returns
    ----------
    float, floats
        The HDI low and high limits.


    Examples
    ----------
    >>> import numpy as np
    >>> import neurokit2 as nk
    >>>
    >>> x = np.random.normal(loc=0, scale=1, size=100000)
    >>> ci_min, ci_high = nk.hdi(x, ci=0.95, show=True)
    """
    x_sorted = np.sort(x)
    window_size = np.ceil(ci * len(x_sorted)).astype('int')

    if window_size < 2:
        raise ValueError("NeuroKit error: hdi(): `ci` is too small or x does not contain enough data points.")

    nCIs = len(x_sorted) - window_size

    ciWidth = [0]*nCIs
    for i in np.arange(0, nCIs):
        ciWidth[i] = x_sorted[i + window_size] - x_sorted[i]
    hdi_low = x_sorted[ciWidth.index(np.min(ciWidth))]
    hdi_high = x_sorted[ciWidth.index(np.min(ciWidth))+window_size]

    if show is True:
        _hdi_plot(x, hdi_low, hdi_high, **kwargs)

    return hdi_low, hdi_high






def _hdi_plot(vals, hdi_low, hdi_high, ci=0.95, **kwargs):
    x, y = density(vals, show=False, **kwargs)

    where = np.full(len(x), False)
    where[0:findclosest(x, hdi_low, return_index=True)] = True
    where[findclosest(x, hdi_high, return_index=True)::] = True

    plt.plot(x, y, color="white")
    plt.fill_between(x, y, where=where, color='#E91E63', label="CI {:.0%} [{:.2f}, {:.2f}]".format(ci, hdi_low, hdi_high))
    plt.fill_between(x, y, where=~where, color='#2196F3')
    plt.legend(loc="upper right")

# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np





def rescale(data, to=[0, 1]):
    """Rescale data.

    Rescale a numeric variable to a new range.

    Parameters
    ----------
    data : list, array or Series
        Raw data.
    to : list
        New range of values of the data after rescaling.

    Returns
    ----------
    list, array or Series
        The rescaled values.


    Examples
    ----------
    >>> import neurokit2 as nk
    >>>
    >>> nk.rescale(data=[3, 1, 2, 4, 6], to=[0, 1])
    """

    # Return appropriate type
    if isinstance(data, list):
        data = list(_rescale(np.array(data), to=to))
    else:
        data = _rescale(data, to=to)

    return data







def _rescale(data, to=[0, 1]):
    y = (to[1] - to[0]) / (np.nanmax(data) - np.nanmin(data)) * (data - np.nanmin(data)) + to[0]
    return y

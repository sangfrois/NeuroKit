# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import scipy.signal
import matplotlib.pyplot as plt


from .signal_psd import signal_psd


def signal_power(signal, frequency_band, sampling_rate=1000, continuous=False, show=False, **kwargs):
    """Compute the power of a signal in a given frequency band.

    Parameters
    ----------
    signal : list, array or Series
        The signal (i.e., a time series) in the form of a vector of values.
    frequency_band :tuple or list
        Tuple or list of tuples indicating the range of frequencies to compute the power in.
    sampling_rate : int
        The sampling frequency of the signal (in Hz, i.e., samples/second).
    continuous : bool
        Compute instant frequency, or continuous power.
    show : bool
        If True, will return a Poincaré plot. Defaults to False.
    **kwargs
        Keyword arguments to be passed to `signal_psd()`.

    See Also
    --------
    signal_filter, signal_psd

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the Power Spectrum values and a plot if
        `show` is True.

    Examples
    --------
    >>> import neurokit2 as nk
    >>> import numpy as np
    >>>
    >>> # Instant power
    >>> signal = nk.signal_simulate(frequency=5) + 0.5*nk.signal_simulate(frequency=20)
    >>> nk.signal_power(signal, frequency_band=[(18, 22), (10, 14)], method="multitapers")
    >>>
    >>> # Continuous (simulated signal)
    >>> signal = np.concatenate((nk.ecg_simulate(duration=30, heart_rate=75),
                                 nk.ecg_simulate(duration=30, heart_rate=85)))
    >>> power = nk.signal_power(signal, frequency_band=[(72/60, 78/60), (82/60, 88/60)], continuous=True)
    >>> processed, _ = nk.ecg_process(signal)
    >>> power["ECG_Rate"] = processed["ECG_Rate"]
    >>> nk.signal_plot(power, standardize=True)
    >>>
    >>> # Continuous (real signal)
    >>> signal = nk.data("bio_eventrelated_100hz")["ECG"]
    >>> power = nk.signal_power(signal, sampling_rate=100, frequency_band=[(0.12, 0.15), (0.15, 0.4)], continuous=True)
    >>> processed, _ = nk.ecg_process(signal, sampling_rate=100)
    >>> power["ECG_Rate"] = processed["ECG_Rate"]
    >>> nk.signal_plot(power, standardize=True)
    """

    if continuous is False:
        out = _signal_power_instant(signal, frequency_band, sampling_rate=sampling_rate, show=show, **kwargs)
    else:
        out = _signal_power_continuous(signal, frequency_band, sampling_rate=sampling_rate)

    out = pd.DataFrame.from_dict(out, orient="index").T

    return out



# =============================================================================
# Instant
# =============================================================================

def _signal_power_instant(signal, frequency_band, sampling_rate=1000, show=False, **kwargs):
    psd = signal_psd(signal, sampling_rate=sampling_rate, show=False, **kwargs)

    out = {}
    if isinstance(frequency_band[0], list) or isinstance(frequency_band[0], tuple):
        for band in frequency_band:
            out.update(_signal_power_instant_get(psd, band))
    else:
        out.update(_signal_power_instant_get(psd, frequency_band))

    if show:
        _signal_power_instant_plot(psd, out, frequency_band)
    return out



def _signal_power_instant_get(psd, frequency_band):

    indices = np.logical_and(psd["Frequency"] >= frequency_band[0], psd["Frequency"] < frequency_band[1]).values

    out = {}
    out["{:.2f}-{:.2f}Hz".format(frequency_band[0], frequency_band[1])] = np.trapz(y=psd["Power"][indices], x=psd["Frequency"][indices])
    return out



def _signal_power_instant_plot(psd, out, frequency_band):

    # sanitize signal:
    if isinstance(frequency_band[0], int):
        if len(frequency_band) > 2:
            print("NeuroKit error: signal_power(): The `frequency_band` argument must be a list of tuples or a tuple of 2 integers")
        else:
            frequency_band = [tuple(i for i in frequency_band)]

    # Get indexes for different frequency band
    frequency_band_index = []
    for band in frequency_band:
        indexes = np.logical_and(psd["Frequency"] >= band[0], psd["Frequency"] < band[1])
        frequency_band_index.append(np.array(indexes))
    label_list = list(out.keys())

    # Plot
    ax = psd.plot(x="Frequency", y="Power", logy=False, title='Power Spectral Density (PSD)', color='lightgrey', linewidth=0.6)
    ax.fill_between(psd["Frequency"], 0, psd["Power"], color='lightgrey', label='Signal')

    for band_index, label in zip(frequency_band_index, label_list):
        ax.fill_between(psd["Frequency"][band_index], 0, psd["Power"][band_index], label=label)
    ax.legend()

    ax.set(xlabel="Frequency (Hz)", ylabel="Spectrum (ms2/Hz)")
    return ax

# =============================================================================
# Continuous
# =============================================================================

def _signal_power_continuous(signal, frequency_band, sampling_rate=1000):

    out = {}
    if isinstance(frequency_band[0], list) or isinstance(frequency_band[0], tuple):
        for band in frequency_band:
            out.update(_signal_power_continuous_get(signal, band, sampling_rate))
    else:
        out.update(_signal_power_continuous_get(signal, frequency_band, sampling_rate))
    return out



def _signal_power_continuous_get(signal, frequency_band, sampling_rate=1000, precision=20):

    try:
        import mne
    except ImportError:
        raise ImportError("NeuroKit warning: signal_power(): the 'mne'",
                          "module is required. ",
                          "Please install it first (`pip install mne`).")

    out = mne.time_frequency.tfr_array_morlet([[signal]],
                                              sfreq=sampling_rate,
                                              freqs=np.linspace(frequency_band[0], frequency_band[1], precision),
                                              output='power')
    power = np.mean(out[0][0], axis=0)

    out = {}
    out["{:.2f}-{:.2f}Hz".format(frequency_band[0], frequency_band[1])] = power
    return out

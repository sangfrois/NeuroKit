# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from ..signal import signal_filter
from ..signal import signal_resample


def ecg_rsa(signals, rpeaks=None, sampling_rate=1000):
    """
    Returns Respiratory Sinus Arrhythmia (RSA) features. The Peak-to-trough (P2T) algorithm are the Porges-Bohrer method are implemented.


    Parameters
    ----------
    signals : DataFrame
        DataFrame obtained from `bio_process()`.
    rpeaks : dict
        The samples at which the R-peaks of the ECG signal occur. Dict returned by
        `ecg_peaks()`, `ecg_process()`, or `bio_process()`. Defaults to None.
    sampling_rate : int
        The sampling frequency of signals (in Hz, i.e., samples/second).

    Returns
    ----------
    rsa : dict
        A dictionary containing the RSA features, which includes:
        - "*RSA_P2T_Values*": the estimate of RSA during each breath cycle, produced
        by subtracting the shortest heart period (or RR interval) from the longest
        heart period in ms.
        - "*RSA_P2T_Mean*": the mean peak-to-trough across all cycles in ms
        - "*RSA_P2T_Mean_log*": the logarithm of the mean of RSA estimates.
        - "*RSA_P2T_Variability*": the standard deviation of all RSA estimates.
        - "*RSA_P2T_NoRSA*": the number of breath cycles
        from which RSA could not be calculated.
        - "*RSA_PorgesBohrer*": the Porges-Bohrer estimate of RSA, optimal
        when the signal to noise ratio is low.

    Example
    ----------
    >>> import neurokit as nk
    >>>
    >>> data = pd.read_csv("https://raw.githubusercontent.com/neuropsychology/NeuroKit/master/data/example_bio_100hz.csv")
    >>>
    >>> # Process the data
    >>> signals, info = nk.bio_process(ecg=data["ECG"], rsp=data["RSP"], sampling_rate=100)
    >>> rsa = nk.ecg_rsa(signals, info)

    References
    ------------
    - Lewis, G. F., Furman, S. A., McCool, M. F., & Porges, S. W. (2012). Statistical strategies to quantify respiratory sinus arrhythmia: Are commonly used metrics equivalent?. Biological psychology, 89(2), 349-364.
    """
    # Sanity Checks
    if isinstance(signals, tuple):
        signals = signals[0]
        rpeaks = signals[1]["ECG_R_Peaks"]

    if isinstance(signals, pd.DataFrame):
        rsp_cols = [col for col in signals.columns if 'RSP_Phase' in col]
        if len(rsp_cols) != 2:
            raise ValueError("NeuroKit error: ecg_rsa(): we couldn't extract"
                             "respiratory phases and cycles.")
        ecg_cols = [col for col in signals.columns if 'ECG_Rate' in col]
        if len(ecg_cols) == 0:
            raise ValueError("NeuroKit error: ecg_rsa(): we couldn't extract"
                             "heart rate signal.")

    # Extract cycles
    rpeaks = rpeaks["ECG_R_Peaks"]
    rsp_cycles = _ecg_rsa_cycles(signals)
    rsp_onsets = rsp_cycles["RSP_Inspiration_Onsets"]
    rsp_cycle_center = rsp_cycles["RSP_Expiration_Onsets"]
    rsp_cycle_center = np.array(rsp_cycle_center)[rsp_cycle_center > rsp_onsets[0]]

    if len(rsp_cycle_center) - len(rsp_onsets) == 0:
        rsp_cycle_center = rsp_cycle_center[:-1]
    if len(rsp_cycle_center) - len(rsp_onsets) != -1:
        print("NeuroKit Error: ecg_rsp(): Couldn't find clean rsp cycles onsets and centers. Check your RSP signal.")

    rsa = {}

    # Peak-to-trough algorithm (P2T)
    # ===============================
    # Find all RSP cycles and the Rpeaks within
    cycles_rri = []
    for idx in range(len(rsp_onsets) - 1):
        cycle_init = rsp_onsets[idx]
        cycle_end = rsp_onsets[idx + 1]
        cycles_rri.append(rpeaks[np.logical_and(rpeaks >= cycle_init,
                                                rpeaks < cycle_end)])

    # Iterate over all cycles
    rsa["RSA_P2T_Values"] = []
    for cycle in cycles_rri:
        # Estimate of RSA during each breath
        RRis = np.diff(cycle) / sampling_rate
        if len(RRis) > 1:
            rsa["RSA_P2T_Values"].append(np.max(RRis) - np.min(RRis))
        else:
            rsa["RSA_P2T_Values"].append(np.nan)
    rsa["RSA_P2T_Mean"] = pd.Series(rsa["RSA_P2T_Values"]).mean()
    rsa["RSA_P2T_Mean_log"] = np.log(rsa["RSA_P2T_Mean"])
    rsa["RSA_P2T_Variability"] = pd.Series(rsa["RSA_P2T_Values"]).std()
    values = pd.Series(rsa["RSA_P2T_Values"])
    rsa["RSA_P2T_NoRSA"] = len(values.index[values.isnull()])

    # Porges-Bohrer method
    # ===============================
    heart_period = signals["ECG_Rate"]

    # Re-sample at 2 Hz
    resampled = signal_resample(heart_period, sampling_rate=100, desired_sampling_rate=2)

    # Fit 21-point cubic polynomial filter (zero mean, 3rd order) with a low-pass cutoff frequency of 0.095Hz
    trend = signal_filter(resampled, sampling_rate=2, lowcut=0.095, highcut=None, method="savgol", order=3, window_length=21)

    zero_mean = resampled - trend
    # Remove variance outside bandwidth of spontaneous respiration
    zero_mean_filtered = signal_filter(zero_mean, sampling_rate=2, lowcut=0.12, highcut=0.40)

    # Divide into 30-second epochs
    time = np.arange(0, len(zero_mean_filtered)) / 2
    time = pd.DataFrame({'Epoch Index': time // 30,
                         'Signal': zero_mean_filtered})
    time = time.set_index('Epoch Index')

    epochs = []
    for i in range(int(np.max(time.index.values))+1):
        epochs.append(time.loc[i])

    variance = []
    for epoch in epochs:
        variance.append(np.log(epoch.var(axis=0)))

    rsa["RSA_PorgesBohrer"] = pd.concat(variance).mean()

    return(rsa)


# =============================================================================
# Internals
# =============================================================================
def _ecg_rsa_cycles(signals):
    """
    Extract respiratory cycles.
    """
    inspiration_onsets = np.intersect1d(np.where(signals["RSP_Phase"] == 1)[0], np.where(signals["RSP_PhaseCompletion"] == 0)[0], assume_unique=True)

    expiration_onsets = np.intersect1d(np.where(signals["RSP_Phase"] == 0)[0], np.where(signals["RSP_PhaseCompletion"] == 0)[0], assume_unique=True)

    cycles_length = np.diff(inspiration_onsets)

    rsp_cycles = {"RSP_Inspiration_Onsets": inspiration_onsets,
                  "RSP_Expiration_Onsets": expiration_onsets,
                  "RSP_Cycles_Length": cycles_length}

    return(rsp_cycles)
# cdpem_core/fft_cycle.py

import numpy as np


def compute_fft_spectrum(series, dt: float = 1.0):
    """
    Compute single-sided FFT spectrum for a real-valued time series.

    Parameters
    ----------
    series : list or np.ndarray
        Time series data.
    dt : float
        Time step between observations (e.g., 1 for yearly, 0.25 for quarterly).

    Returns
    -------
    freqs : np.ndarray
        Frequencies (cycles per unit time).
    amps : np.ndarray
        Amplitudes of the spectrum.
    """
    x = np.asarray(series, dtype=float)
    n = len(x)
    if n == 0:
        return np.array([]), np.array([])

    x = x - np.mean(x)  # centre

    fft_vals = np.fft.rfft(x)
    amps = np.abs(fft_vals) / n
    freqs = np.fft.rfftfreq(n, d=dt)

    return freqs, amps

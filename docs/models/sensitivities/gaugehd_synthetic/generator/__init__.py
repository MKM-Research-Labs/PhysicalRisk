# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""GaugeHD Synthetic generator sensitivity analysis."""

import math

import numpy as np

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate GaugeHD synthetic sensitivity tables.

    The GaugeHD Synthetic model generates synthetic daily gauge readings
    with seasonal cycles, AR(1) autocorrelation, and tidal influence.
    """
    rng = np.random.default_rng(42)

    # Table 1: Sensitivity to AR(1) autocorrelation parameter
    ar1_values = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95]
    n_days = 365
    rows = []
    for phi in ar1_values:
        # Simulate AR(1): x_t = phi * x_{t-1} + epsilon
        series = np.zeros(n_days)
        for t in range(1, n_days):
            series[t] = phi * series[t - 1] + rng.normal(0, 1)
        # Unconditional variance = sigma^2 / (1 - phi^2) for |phi| < 1
        theoretical_var = 1.0 / (1.0 - phi**2) if abs(phi) < 1 else float('inf')
        rows.append([phi, round(np.std(series), 3),
                     round(theoretical_var, 2)])

    t1 = latex_table(
        'Synthetic series volatility by AR(1) parameter ($\\sigma_\\epsilon=1$).',
        'sens_ar1',
        [r'$\phi$ (AR1)', 'Sample std dev', r'Theoretical variance'],
        rows,
    )

    # Table 2: Sensitivity to seasonal amplitude
    amplitudes = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]
    mean_level = 2.0
    rows = []
    for amp in amplitudes:
        # Seasonal component: A * sin(2*pi*t/365)
        t = np.arange(n_days)
        seasonal = amp * np.sin(2 * math.pi * t / 365)
        series = mean_level + seasonal + rng.normal(0, 0.5, n_days)
        rows.append([amp, round(np.min(series), 2),
                     round(np.max(series), 2),
                     round(np.max(series) - np.min(series), 2)])

    t2 = latex_table(
        'Synthetic gauge range by seasonal amplitude (mean=2.0m, noise $\\sigma=0.5$).',
        'sens_seasonal',
        ['Amplitude (m)', 'Min (m)', 'Max (m)', 'Range (m)'],
        rows,
    )

    # Table 3: Sensitivity to tidal influence weight
    tidal_weights = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
    rows = []
    for tw in tidal_weights:
        # Tidal component: tw * sin(2*pi*t/0.5)  (semi-diurnal)
        t = np.arange(n_days * 24) / 24.0  # hourly resolution
        tidal = tw * np.sin(2 * math.pi * t / 0.5)
        daily_range = np.mean([
            np.max(tidal[d * 24:(d + 1) * 24]) - np.min(tidal[d * 24:(d + 1) * 24])
            for d in range(n_days)
        ])
        rows.append([tw, round(daily_range, 3)])

    t3 = latex_table(
        'Mean daily tidal range by tidal influence weight.',
        'sens_tidal',
        ['Tidal weight', 'Mean daily range (m)'],
        rows,
    )

    write_tables('gaugehd_synthetic', '\n\n'.join([t1, t2, t3]))

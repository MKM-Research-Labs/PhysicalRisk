# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Storm Sequence Generator (storm_multi) sensitivity analysis."""

import numpy as np

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate storm sequence sensitivity tables.

    The storm_multi model generates multi-event storm sequences.
    Sensitivity is measured by varying sequence parameters and observing
    the effect on aggregate severity metrics.
    """
    rng = np.random.default_rng(42)

    # Table 1: Sensitivity to mean inter-storm gap (days)
    # Simulate how sequence count changes with gap parameter
    simulation_days = 365
    mean_gaps = [3, 5, 7, 10, 14, 21, 30]
    rows = []
    for gap in mean_gaps:
        # Simple Poisson-process simulation
        n_events = rng.poisson(simulation_days / gap)
        avg_events = simulation_days / gap
        rows.append([gap, round(avg_events, 1), n_events])

    t1 = latex_table(
        'Expected storm events per year by mean inter-storm gap.',
        'sens_gap',
        ['Mean gap (days)', 'Expected events/yr', 'Simulated (seed=42)'],
        rows,
    )

    # Table 2: Sensitivity to sequence length (number of storms in a cluster)
    seq_lengths = [1, 2, 3, 5, 7, 10]
    base_intensity = 50.0  # mm/hr
    decay = 0.85  # intensity decay per subsequent storm
    rows = []
    for n in seq_lengths:
        intensities = [base_intensity * (decay ** i) for i in range(n)]
        total = sum(intensities)
        peak = max(intensities)
        rows.append([n, round(peak, 1), round(total, 1),
                     round(total / n, 1)])

    t2 = latex_table(
        'Aggregate severity by storm sequence length '
        '(base 50\\,mm/hr, decay 0.85).',
        'sens_seqlen',
        ['Storms in cluster', 'Peak (mm/hr)', 'Total (mm/hr)',
         'Mean (mm/hr)'],
        rows,
    )

    # Table 3: Sensitivity to intensity correlation between storms
    correlations = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    rows = []
    for rho in correlations:
        # Higher correlation means storms in a cluster have similar intensity
        # Model as: variance of cluster total = n * sigma^2 * (1 + (n-1)*rho)
        n = 3
        sigma = 15.0
        cluster_var = n * sigma**2 * (1 + (n - 1) * rho)
        cluster_std = cluster_var ** 0.5
        rows.append([rho, round(cluster_var, 1), round(cluster_std, 1)])

    t3 = latex_table(
        'Cluster total variance by intensity correlation ($n=3$, $\\sigma=15$).',
        'sens_corr',
        [r'Correlation $\rho$', 'Cluster variance', 'Cluster std dev'],
        rows,
    )

    write_tables('storm_multi', '\n\n'.join([t1, t2, t3]))

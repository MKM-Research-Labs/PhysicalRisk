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

"""Delta Engine sensitivity analysis."""

import math

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate delta engine sensitivity tables."""
    from models.hazard.prs_analytical import compute_prs_spread

    # The delta engine computes mark-to-market via spread changes.
    # Sensitivity is measured as spread delta per unit input change.
    notional = 1_000_000  # GBP 1M notional

    # Table 1: Delta sensitivity to hazard rate shock
    base_hazard = 0.01
    shocks = [-0.005, -0.002, -0.001, 0.0, 0.001, 0.002, 0.005, 0.01]
    rows = []
    base_spread = compute_prs_spread(base_hazard, tenor=5, recovery=0.0,
                                      risk_free_rate=0.03)
    for s in shocks:
        h = max(0.0001, base_hazard + s)
        spread = compute_prs_spread(h, tenor=5, recovery=0.0,
                                     risk_free_rate=0.03)
        delta_bp = spread - base_spread
        mtm = notional * delta_bp / 10000.0
        rows.append([f'{s:+.3f}', round(h, 4), round(spread, 1),
                     round(delta_bp, 1), round(mtm, 0)])

    t1 = latex_table(
        'Delta sensitivity to hazard rate shock ($T=5$yr, notional \\pounds1M).',
        'sens_delta_hazard',
        [r'Shock $\Delta\lambda$', r'$\lambda$', 'Spread (bp)',
         r'$\Delta$ Spread (bp)', 'MtM (\\pounds)'],
        rows,
    )

    # Table 2: Delta sensitivity to tenor
    tenors = [1, 2, 3, 5, 7, 10]
    rows = []
    for t in tenors:
        spread = compute_prs_spread(0.01, tenor=t, recovery=0.0,
                                     risk_free_rate=0.03)
        dv01 = notional * spread / 10000.0 * t / 365.0
        rows.append([t, round(spread, 1), round(dv01, 0)])

    t2 = latex_table(
        'Spread and approximate DV01 by tenor ($\\lambda=0.01$, notional \\pounds1M).',
        'sens_delta_tenor',
        ['Tenor (yr)', 'Spread (bp)', 'Approx DV01 (\\pounds)'],
        rows,
    )

    write_tables('delta_engine', '\n\n'.join([t1, t2]))

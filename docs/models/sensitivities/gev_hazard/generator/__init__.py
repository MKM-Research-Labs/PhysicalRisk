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

"""GEV Hazard sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate GEV hazard sensitivity tables."""
    from models.hazard.gev import GEVFitter, compute_term_structure

    fitter = GEVFitter()

    # Table 1: Shape parameter sensitivity
    shapes = [-0.2, -0.1, 0.0, 0.1, 0.2, 0.3]
    mu, sigma = 2.0, 0.5
    return_periods = [10, 50, 100]
    headers = [r'$\xi$', 'Tail Type'] + [f'{t}-yr RL (m)' for t in return_periods] + [r'$P(X > 3.0)$']
    rows = []
    tail_names = {-0.2: 'Weibull', -0.1: 'Weibull', 0.0: 'Gumbel',
                  0.1: r"Fr\'{e}chet", 0.2: r"Fr\'{e}chet", 0.3: r"Fr\'{e}chet"}
    for xi in shapes:
        rls = [round(fitter.return_level(rp, xi, mu, sigma), 3) for rp in return_periods]
        exc = fitter.exceedance_probability(3.0, xi, mu, sigma)
        rows.append([xi, tail_names[xi]] + rls + [round(exc, 6)])

    t1 = latex_table(
        r'GEV return levels and exceedance by shape parameter ($\mu=2.0$\,m, $\sigma=0.5$\,m).',
        'sens_shape', headers, rows,
        col_fmt='rl' + 'r' * (len(return_periods) + 1),
    )

    # Table 2: Scale parameter sensitivity
    scales = [0.2, 0.3, 0.5, 0.7, 1.0]
    headers = [r'$\sigma$'] + [f'{t}-yr RL (m)' for t in return_periods] + [r'$P(X > 3.0)$']
    rows = []
    for s in scales:
        rls = [round(fitter.return_level(rp, 0.0, mu, s), 3) for rp in return_periods]
        exc = fitter.exceedance_probability(3.0, 0.0, mu, s)
        rows.append([s] + rls + [round(exc, 6)])

    t2 = latex_table(
        r'GEV return levels by scale parameter ($\xi=0$, $\mu=2.0$\,m).',
        'sens_scale', headers, rows,
    )

    # Table 3: Term structure
    hazard_rates = [0.01, 0.02, 0.05, 0.10]
    headers = [r'$\lambda_{\text{annual}}$'] + [f'$P(\\leq {y}$yr$)$' for y in range(1, 6)]
    rows = []
    for h in hazard_rates:
        ts = compute_term_structure(h, max_years=5)
        cum_probs = [round(pt.cumulative_default_prob, 6) for pt in ts]
        rows.append([h] + cum_probs)

    t3 = latex_table(
        'Poisson term structure: cumulative flood probability by year.',
        'sens_term_structure', headers, rows,
    )

    write_tables('gev_hazard', '\n\n'.join([t1, t2, t3]))

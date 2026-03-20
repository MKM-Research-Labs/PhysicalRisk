# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""PRS Pricing sensitivity analysis."""

import math

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate PRS pricing sensitivity tables."""
    from models.hazard.prs_analytical import compute_prs_spread

    # Table 1: Hazard rate sensitivity
    hazard_rates = [0.001, 0.005, 0.01, 0.02, 0.05, 0.10]
    rows = []
    for h in hazard_rates:
        lam = -math.log(1 - h)
        spread = compute_prs_spread(h, tenor=5, recovery=0.0, risk_free_rate=0.03)
        rows.append([h, round(lam, 6), round(spread, 1)])

    t1 = latex_table(
        'PRS spread sensitivity to annual hazard rate ($T=5$yr, $R=0$, $r=0.03$).',
        'sens_hazard',
        [r'$\lambda_{\text{annual}}$', r'$\lambda$ (continuous)', 'Spread (bp)'],
        rows,
    )

    # Table 2: Risk-free rate sensitivity
    rfr_values = [0.00, 0.01, 0.03, 0.05, 0.10]
    rows = []
    for r in rfr_values:
        spread = compute_prs_spread(0.01, tenor=5, recovery=0.0, risk_free_rate=r)
        rows.append([r, round(spread, 1)])

    t2 = latex_table(
        r'PRS spread sensitivity to risk-free rate ($\lambda_{\text{annual}}=0.01$, $R=0$, $T=5$yr).',
        'sens_rfr',
        [r'$r$', 'Spread (bp)'],
        rows,
    )

    # Table 3: Tenor sensitivity
    tenors = [1, 2, 3, 5, 7, 10, 20, 30]
    rows = []
    for t in tenors:
        spread = compute_prs_spread(0.01, tenor=t, recovery=0.0, risk_free_rate=0.03)
        rows.append([t, round(spread, 1)])

    t3 = latex_table(
        r'PRS spread sensitivity to tenor ($\lambda_{\text{annual}}=0.01$, $R=0$, $r=0.03$).',
        'sens_tenor',
        ['Tenor (yr)', 'Spread (bp)'],
        rows,
    )

    write_tables('prs_pricing', '\n\n'.join([t1, t2, t3]))

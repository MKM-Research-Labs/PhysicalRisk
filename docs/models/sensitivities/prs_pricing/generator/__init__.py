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

"""PRS Pricing sensitivity analysis — v2.0.

Tables 1-3: core pricing sensitivities (hazard rate, risk-free rate, tenor).
Tables 4-6: basis sensitivities (distance, elevation, combined matrix).
"""

import math
from pathlib import Path

from config.models import EA_FLOOD_ZONE_RATES
from docs.models.sensitivities import latex_table, write_tables


# Elevation decay scale for sensitivity illustration (metres).
# At h = ELEV_SCALE the flood probability drops to 1/e of the gauge rate.
# Calibrated to Thames corridor typical flood depth distribution.
ELEV_SCALE_M = 2.0


def _find_gauge_rate_for_spread(target_bps, tenor=5, recovery=0.0,
                                 risk_free_rate=0.03):
    """Binary search for annual hazard rate producing target spread."""
    from models.hazard.prs_analytical import compute_prs_spread

    lo, hi = 0.0001, 0.50
    for _ in range(100):
        mid = (lo + hi) / 2
        spread = compute_prs_spread(mid, tenor=tenor, recovery=recovery,
                                     risk_free_rate=risk_free_rate)
        if spread < target_bps:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def generate():
    """Generate PRS pricing sensitivity tables."""
    from models.hazard.prs_analytical import compute_prs_spread
    from models.floodrisk.velocity import compute_retention

    # ----------------------------------------------------------------
    # Table 1: Hazard rate sensitivity
    # ----------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # Table 2: Risk-free rate sensitivity
    # ----------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # Table 3: Tenor sensitivity
    # ----------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # Table 4: Distance sensitivity (gauge at 300 bp)
    # ----------------------------------------------------------------
    gauge_rate = _find_gauge_rate_for_spread(300.0)
    gauge_spread = compute_prs_spread(gauge_rate, tenor=5, recovery=0.0,
                                       risk_free_rate=0.03)

    distances_m = [0, 200, 500, 1000, 2000, 3000, 5000, 8000, 12000]
    rows = []
    for d in distances_m:
        ret = compute_retention(d)
        prop_rate = gauge_rate * ret
        prop_spread = compute_prs_spread(prop_rate, tenor=5, recovery=0.0,
                                          risk_free_rate=0.03)
        basis = round(gauge_spread - prop_spread, 1)
        rows.append([d, round(ret, 4), round(prop_spread, 1), basis])

    t4 = latex_table(
        r'Property spread by distance from gauge (gauge spread $\approx 300$\,bp, '
        r'$T=5$yr, $R=0$, $r=0.03$, $L=3{,}000$\,m).',
        'sens_distance',
        ['Distance (m)', 'Retention', 'Property Spread (bp)', 'Basis (bp)'],
        rows,
    )

    # ----------------------------------------------------------------
    # Table 5: Elevation sensitivity (gauge at 300 bp, distance = 0)
    # ----------------------------------------------------------------
    elev_diffs = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 15.0]
    rows = []
    for h in elev_diffs:
        elev_factor = math.exp(-h / ELEV_SCALE_M)
        prop_rate = gauge_rate * elev_factor
        prop_spread = compute_prs_spread(prop_rate, tenor=5, recovery=0.0,
                                          risk_free_rate=0.03)
        basis = round(gauge_spread - prop_spread, 1)
        rows.append([h, round(prop_spread, 1), basis])

    t5 = latex_table(
        r'Property spread by elevation above gauge (gauge spread $\approx 300$\,bp, '
        r'$d=0$, $T=5$yr, $h_{\text{scale}}=2.0$\,m).',
        'sens_elevation',
        [r'$\Delta h$ (m)', 'Property Spread (bp)', 'Basis (bp)'],
        rows,
    )

    # ----------------------------------------------------------------
    # Table 6: Combined distance x elevation matrix (property spread bp)
    # ----------------------------------------------------------------
    mat_distances = [0, 500, 1000, 3000, 5000]
    mat_elevations = [0.0, 1.0, 2.0, 5.0, 10.0]

    # Build header row
    elev_headers = [r'$\Delta h = ' + (str(int(e)) if e == int(e) else f'{e:.1f}')
                    + r'$\,m' for e in mat_elevations]
    headers = ['Distance (m)'] + elev_headers

    rows = []
    for d in mat_distances:
        ret = compute_retention(d)
        row = [d]
        for h in mat_elevations:
            elev_factor = math.exp(-h / ELEV_SCALE_M)
            prop_rate = gauge_rate * ret * elev_factor
            prop_spread = compute_prs_spread(prop_rate, tenor=5, recovery=0.0,
                                              risk_free_rate=0.03)
            row.append(round(prop_spread, 1))
        rows.append(row)

    col_fmt = 'r' + 'r' * len(mat_elevations)
    t6 = latex_table(
        r'Property spread (bp) by distance and elevation '
        r'(gauge $\approx 300$\,bp, $T=5$yr, $R=0$, $r=0.03$).',
        'sens_combined',
        headers,
        rows,
        col_fmt=col_fmt,
    )

    # ----------------------------------------------------------------
    # Table 7: Terrain sensitivity — EA flood zone gauge spreads and
    # resulting property spreads at representative distance/elevation
    # ----------------------------------------------------------------
    # Representative annual hazard rates per EA flood zone (midpoint of
    # published EA probability ranges).
    terrain_zones = list(EA_FLOOD_ZONE_RATES.items())
    rep_dist = 500
    rep_ret = compute_retention(rep_dist)
    terrain_elevations = [0.5, 1.0, 1.5, 2.0, 2.5]

    terrain_tables = []
    for idx, elev in enumerate(terrain_elevations):
        elev_factor = math.exp(-elev / ELEV_SCALE_M)
        rows = []
        for zone_name, zone_rate in terrain_zones:
            g_spread = compute_prs_spread(zone_rate, tenor=5, recovery=0.0,
                                           risk_free_rate=0.03)
            prop_rate = zone_rate * rep_ret * elev_factor
            p_spread = compute_prs_spread(prop_rate, tenor=5, recovery=0.0,
                                           risk_free_rate=0.03)
            basis = round(g_spread - p_spread, 1)
            rows.append([zone_name, zone_rate, round(g_spread, 1),
                         round(p_spread, 1), basis])

        label_suffix = chr(ord('a') + idx)
        elev_str = f'{elev:.1f}'
        tt = latex_table(
            r'Gauge and property spreads by EA flood zone '
            r'($d=500$\,m, $\Delta h=' + elev_str + r'$\,m, $T=5$yr, $R=0$, $r=0.03$).',
            f'sens_terrain_{label_suffix}',
            ['EA Flood Zone', r'$\lambda_{\text{annual}}$', 'Gauge Spread (bp)',
             'Property Spread (bp)', 'Basis (bp)'],
            rows,
            col_fmt='lrrrr',
        )
        terrain_tables.append(tt)

    # ----------------------------------------------------------------
    # Tables 8a-8e: Terrain sensitivity by EA flood zone at five
    # distances (250m, 500m, 750m, 1000m, 1500m), elev = 1.0m
    # ----------------------------------------------------------------
    rep_elev_dist = 1.0
    elev_factor_dist = math.exp(-rep_elev_dist / ELEV_SCALE_M)
    terrain_distances = [250, 500, 750, 1000, 1500]

    distance_tables = []
    for idx, dist in enumerate(terrain_distances):
        ret = compute_retention(dist)
        rows = []
        for zone_name, zone_rate in terrain_zones:
            g_spread = compute_prs_spread(zone_rate, tenor=5, recovery=0.0,
                                           risk_free_rate=0.03)
            prop_rate = zone_rate * ret * elev_factor_dist
            p_spread = compute_prs_spread(prop_rate, tenor=5, recovery=0.0,
                                           risk_free_rate=0.03)
            basis = round(g_spread - p_spread, 1)
            rows.append([zone_name, zone_rate, round(g_spread, 1),
                         round(p_spread, 1), basis])

        label_suffix = chr(ord('a') + idx)
        tt = latex_table(
            r'Gauge and property spreads by EA flood zone '
            r'($d=' + str(dist) + r'$\,m, $\Delta h=1.0$\,m, $T=5$yr, $R=0$, $r=0.03$).',
            f'sens_terrain_dist_{label_suffix}',
            ['EA Flood Zone', r'$\lambda_{\text{annual}}$', 'Gauge Spread (bp)',
             'Property Spread (bp)', 'Basis (bp)'],
            rows,
            col_fmt='lrrrr',
        )
        distance_tables.append(tt)

    write_tables('prs_pricing', '\n\n'.join(
        [t1, t2, t3, t4, t5, t6] + terrain_tables + distance_tables))

    # ----------------------------------------------------------------
    # JSON terrain grid (for interactive UI repricing)
    # ----------------------------------------------------------------
    import json
    from models.hazard.terrain_grid import compute_terrain_grid
    grid = compute_terrain_grid()
    grid_path = Path(__file__).resolve().parents[3] / 'prs_pricing' / 'terrain_grid.json'
    with open(grid_path, 'w') as f:
        json.dump(grid, f, indent=2)

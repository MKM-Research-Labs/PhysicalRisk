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

"""Wind Damage (MKM-WD-001) sensitivity analysis.

Exercises the vulnerability curve along its three axes: peak sustained wind
(severity), duration above threshold (persistence) and building resilience
(the BRI shift of $v_{50}$). A fourth table covers the PRS damage-onset
trigger, which is the binary event count the spread consumes.
"""

from docs.models.sensitivities import latex_table, write_tables


# Representative BRI score pairs by letter grade — the mid-points of the
# rating bands used by the resilience module (AA >= 0.87, A >= 0.62,
# B >= 0.38, NR < 0.38).
_GRADES = [
    ('NR', 0.190),
    ('B', 0.500),
    ('A', 0.745),
    ('AA', 0.935),
]


def generate():
    """Generate Wind Damage sensitivity tables."""
    from config.bri import WIND_V50_SHIFT_MAX_MS
    from config.damage import (
        WIND_PERSISTENCE_GUST_FLOOR,
        WIND_PERSISTENCE_TAU_H,
        WIND_SIGMOID_A_PER_MS,
        WIND_V50_BASE_MS,
    )
    from models.winddamage.bri_shift import bri_v50_shift
    from models.winddamage.threshold import is_prs_wind
    from models.winddamage.vulnerability import (
        bri_peak_damage,
        bri_wind_damage,
        persistence_factor,
        scalar_peak_damage,
    )

    winds = [0.0, 10.0, 17.5, 22.0, 27.8, 33.0, 40.0, 50.0, 60.0, 70.0]

    # -- Table 1: pure severity curve --------------------------------------
    rows = [[v, round(scalar_peak_damage(v), 4)] for v in winds]
    t1 = latex_table(
        'Pure vulnerability curve: damage ratio by peak sustained wind, at the '
        f'configured base $v_{{50}}={WIND_V50_BASE_MS}$~m/s and slope '
        f'$a={WIND_SIGMOID_A_PER_MS}$~m$^{{-1}}$s.',
        'sens_wd_scalar',
        ['Peak wind (m/s)', 'Damage ratio'], rows,
    )

    # -- Table 2: BRI shift of v_50 ----------------------------------------
    # Signed, capped at +/- WIND_V50_SHIFT_MAX_MS. The wind sub-score carries
    # twice the weight of the composite.
    headers = ['BRI wind score'] + [f'Composite {g} ({s:.3f})' for g, s in _GRADES]
    rows = []
    for _, wind_score in _GRADES:
        shifts = [round(bri_v50_shift(wind_score, comp), 3) for _, comp in _GRADES]
        rows.append([round(wind_score, 3)] + shifts)

    t2 = latex_table(
        'Signed $v_{50}$ shift (m/s) by BRI wind sub-score and composite score, '
        f'capped at $\\pm{WIND_V50_SHIFT_MAX_MS}$~m/s. Positive shifts move the '
        'curve rightward (the building tolerates more wind before damage).',
        'sens_wd_bri_shift', headers, rows,
    )

    # -- Table 3: BRI-adjusted damage by grade -----------------------------
    # Same operational threshold, four resilience grades. The spread between
    # NR and AA at a given wind is the resilience credit the model prices.
    threshold = WIND_V50_BASE_MS
    headers = ['Peak wind (m/s)'] + [f'{g} grade' for g, _ in _GRADES]
    rows = []
    for v in winds:
        cells = [round(bri_peak_damage(v, threshold, s, s), 4) for _, s in _GRADES]
        rows.append([v] + cells)

    t3 = latex_table(
        f'BRI-adjusted damage ratio by resilience grade at a common operational '
        f'threshold of {threshold}~m/s (wind sub-score and composite both set to '
        'the grade mid-point).',
        'sens_wd_by_grade', headers, rows,
    )

    # -- Table 4: persistence (duration-of-load) ---------------------------
    durations = [0.0, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 24.0]
    rows = [[t, round(persistence_factor(t), 4)] for t in durations]
    t4 = latex_table(
        'Persistence multiplier $\\Phi(t)$ by hours above the damage-onset '
        f'threshold ($\\phi_{{gust}}={WIND_PERSISTENCE_GUST_FLOOR}$, '
        f'$\\tau={WIND_PERSISTENCE_TAU_H}$~h). A momentary gust realises only the '
        'floor; a prolonged blow saturates at the full peak-curve damage.',
        'sens_wd_persistence',
        ['Duration above threshold (h)', '$\\Phi(t)$'], rows,
    )

    # -- Table 5: severity x persistence -----------------------------------
    # The full bri_wind_damage surface for a B-grade building.
    b_score = dict(_GRADES)['B']
    hours = [0.0, 1.0, 2.0, 4.0, 8.0, 24.0]
    headers = ['Peak wind (m/s)'] + [f'$t={h:.0f}$~h' for h in hours]
    rows = []
    for v in [22.0, 27.8, 33.0, 40.0, 50.0, 60.0]:
        cells = [round(bri_wind_damage(v, h, threshold, b_score, b_score), 4)
                 for h in hours]
        rows.append([v] + cells)

    t5 = latex_table(
        'Persistence-aware damage ratio (severity $\\times$ duration) for a '
        'B-grade building at a 27.8~m/s operational threshold.',
        'sens_wd_severity_duration', headers, rows,
    )

    # -- Table 6: PRS damage-onset trigger ---------------------------------
    # The binary event count the PRS spread consumes: peak >= v_50_eff.
    rows = []
    for grade, score in _GRADES:
        v_50_eff = threshold + bri_v50_shift(score, score)
        fires = [is_prs_wind({'peak_sustained_ms': v, 'v_50_eff_ms': v_50_eff})
                 for v in [30.0, 35.0, 40.0, 45.0]]
        rows.append([grade, round(v_50_eff, 2)] +
                    ['yes' if f else 'no' for f in fires])

    t6 = latex_table(
        'PRS damage-onset trigger by resilience grade. The trigger fires when '
        'the peak sustained wind reaches the BRI-adjusted effective threshold, '
        'so a resilient building fires less readily at the same wind.',
        'sens_wd_prs_trigger',
        ['Grade', '$v_{50,eff}$ (m/s)', '30 m/s', '35 m/s', '40 m/s', '45 m/s'],
        rows,
    )

    write_tables('wind_damage', '\n\n'.join([t1, t2, t3, t4, t5, t6]))

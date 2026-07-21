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

"""BRI-Adjusted Floor Level (MKM-BRF-001) sensitivity analysis.

Exercises the additive floor-level credit along its two axes: the BRI flood
sub-score (which sets the uplift) and the surveyed floor level (which the
uplift is added to). Further tables show the grade-mapping fallback for assets
carrying a letter rating, and the downstream effect on the flood trigger --- the
mechanism by which the credit suppresses PRS flood counts.
"""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate BRI-Adjusted Floor Level sensitivity tables."""
    from config.bri import (
        BRI_FLOOR_UPLIFT_MAX_M,
        BRI_FLOOR_UPLIFT_SCORE_HI,
        BRI_FLOOR_UPLIFT_SCORE_LO,
    )
    from models.floodrisk.depth_damage import (
        bri_adjusted_floor_level,
        bri_floor_uplift,
        flood_rating_to_score,
        scalar_depth_damage,
    )

    scores = [0.0, 0.19, 0.30, 0.38, 0.50, 0.62, 0.745, 0.87, 0.935, 1.0]

    # -- Table 1: the uplift ramp ------------------------------------------
    # Zero below SCORE_LO, full credit above SCORE_HI, linear in between.
    rows = []
    for s in scores:
        uplift = bri_floor_uplift(s)
        if s <= BRI_FLOOR_UPLIFT_SCORE_LO:
            band = 'no credit'
        elif s >= BRI_FLOOR_UPLIFT_SCORE_HI:
            band = 'full credit'
        else:
            band = 'linear ramp'
        rows.append([s, round(uplift, 3), band])

    t1 = latex_table(
        'Floor-level uplift (m) by BRI flood sub-score. No credit at or below '
        f'{BRI_FLOOR_UPLIFT_SCORE_LO}, the full {BRI_FLOOR_UPLIFT_MAX_M}~m at or '
        f'above {BRI_FLOOR_UPLIFT_SCORE_HI}, linear in between.',
        'sens_brf_uplift',
        ['BRI flood score', 'Uplift (m)', 'Band'], rows,
    )

    # -- Table 2: adjusted floor level by surveyed floor -------------------
    # The credit is additive and never subtractive: the adjusted level is
    # always at least the surveyed level.
    floors = [0.0, 0.15, 0.30, 0.60, 1.00, 1.50]
    grade_scores = [('NR', 0.190), ('B', 0.500), ('A', 0.745), ('AA', 0.935)]
    headers = ['Surveyed floor (m)'] + [f'{g} ({s:.3f})' for g, s in grade_scores]
    rows = []
    for f in floors:
        cells = [round(bri_adjusted_floor_level(f, s), 3) for _, s in grade_scores]
        rows.append([f] + cells)

    t2 = latex_table(
        'Adjusted floor level (m) by surveyed floor level and BRI grade '
        'mid-point score. The adjustment is additive, so the adjusted level '
        'never falls below the surveyed level.',
        'sens_brf_adjusted', headers, rows,
    )

    # -- Table 3: letter-grade fallback ------------------------------------
    # Commercial assets carry a grade envelope rather than a numeric score.
    rows = []
    for rating in ['AA', 'AA+', 'A', 'A+', 'B', 'NR', 'N/A', 'ZZ']:
        score = flood_rating_to_score(rating)
        if score is None:
            rows.append([rating, 'not mappable', 'n/a'])
        else:
            rows.append([rating, round(score, 3), round(bri_floor_uplift(score), 3)])

    t3 = latex_table(
        'Letter-grade fallback: representative flood score and resulting uplift. '
        'A trailing $+$ modifier is stripped before lookup; unknown or '
        'non-applicable grades return no representative score.',
        'sens_brf_grades',
        ['BRI rating', 'Representative score', 'Uplift (m)'], rows,
    )

    # -- Table 4: effect on the flood trigger ------------------------------
    # A property floods when the water-surface elevation exceeds
    # ground + adjusted floor. Higher grades need deeper water to flood.
    surveyed = 0.30
    depths = [0.25, 0.50, 1.00, 1.50, 2.00, 3.00, 4.00]
    headers = ['Water above ground (m)'] + [f'{g} grade' for g, _ in grade_scores]
    rows = []
    for d in depths:
        cells = []
        for _, s in grade_scores:
            adjusted = bri_adjusted_floor_level(surveyed, s)
            cells.append('yes' if d > adjusted else 'no')
        rows.append([d] + cells)

    t4 = latex_table(
        f'Flood trigger by BRI grade for a property with a {surveyed}~m surveyed '
        'floor level. The credit raises the depth at which the property first '
        'floods, which is how the model suppresses PRS flood event counts.',
        'sens_brf_trigger', headers, rows,
    )

    # -- Table 5: residual damage after the credit -------------------------
    # Effective depth above the adjusted floor, through the baseline curve.
    headers = ['Water above ground (m)'] + [f'{g} grade' for g, _ in grade_scores]
    rows = []
    for d in depths:
        cells = []
        for _, s in grade_scores:
            adjusted = bri_adjusted_floor_level(surveyed, s)
            cells.append(round(scalar_depth_damage(max(0.0, d - adjusted)), 4))
        rows.append([d] + cells)

    t5 = latex_table(
        'Damage ratio through the baseline depth-damage curve, evaluated at the '
        'depth above the adjusted floor level. The gap between NR and AA at a '
        'given water level is the resilience credit expressed as avoided loss.',
        'sens_brf_residual_damage', headers, rows,
    )

    write_tables('bri_floor', '\n\n'.join([t1, t2, t3, t4, t5]))

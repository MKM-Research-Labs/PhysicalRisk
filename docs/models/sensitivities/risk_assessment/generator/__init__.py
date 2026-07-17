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

"""Risk Assessment sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate risk assessment sensitivity tables."""
    from models.risk.risk_assessor import RiskAssessor

    # Table 1: Combined risk score matrix (flood risk x LTV)
    flood_levels = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
    ltvs = [0.50, 0.70, 0.85, 0.96]
    headers = ['Flood Risk'] + [f'LTV={l*100:.0f}\\%' for l in ltvs]
    rows = []
    for fl in flood_levels:
        scores = [round(RiskAssessor.calculate_combined_risk_score(fl, ltv), 1) for ltv in ltvs]
        rows.append([fl] + scores)

    t1 = latex_table(
        'Combined risk score by flood risk level and LTV ratio (no age/construction adjustment).',
        'sens_combined_score', headers, rows,
        col_fmt='l' + 'r' * len(ltvs),
    )

    # Table 2: Combined score with age and construction
    configs = [
        ('Brick, 30yr', 30, 'brick'), ('Brick, 80yr', 80, 'brick'),
        ('Brick, 120yr', 120, 'brick'), ('Timber, 30yr', 30, 'timber'),
        ('Timber, 80yr', 80, 'timber'), ('Steel, 30yr', 30, 'steel'),
        ('Concrete, 30yr', 30, 'concrete'),
    ]
    headers = ['Configuration'] + ['Low', 'Medium', 'High']
    rows = []
    for label, age, constr in configs:
        scores = [round(RiskAssessor.calculate_combined_risk_score(fl, 0.85, age, constr), 1)
                  for fl in ['Low', 'Medium', 'High']]
        rows.append([label] + scores)

    t2 = latex_table(
        'Combined risk score by construction type and age (LTV=85\\%).',
        'sens_construction_age', headers, rows,
        col_fmt='lrrr',
    )

    # Table 3: Value at risk
    depths = [None, 0.3, 0.5, 1.0, 2.0, 3.0]
    risk_levels = ['Low', 'Medium', 'High', 'Very High']
    pv = 300000
    headers = ['Depth'] + risk_levels
    rows = []
    for d in depths:
        vals = [round(RiskAssessor.calculate_value_at_risk(pv, rl, d), 0) for rl in risk_levels]
        d_str = f'{d:.1f}m' if d is not None else 'None'
        rows.append([d_str] + vals)

    t3 = latex_table(
        'Value at risk (\\pounds) by risk level and flood depth (property value = \\pounds300{,}000).',
        'sens_var', headers, rows,
        col_fmt='l' + 'r' * len(risk_levels),
    )

    # Table 4: Insurance premium factor
    headers = ['Risk Level'] + [f'd={d}m' for d in [0, 0.5, 1.0, 2.0]]
    rows = []
    for rl in ['Very Low', 'Low', 'Medium', 'High', 'Very High']:
        premiums = []
        for d in [0, 0.5, 1.0, 2.0]:
            p = RiskAssessor.calculate_insurance_premium_factor(rl, pv, d if d > 0 else None)
            premiums.append(f'{p:.4f}')
        rows.append([rl] + premiums)

    t4 = latex_table(
        'Insurance premium factor (fraction of property value) by risk level and flood depth.',
        'sens_insurance', headers, rows,
        col_fmt='l' + 'r' * 4,
    )

    # Table 5: Distance risk decay
    distances = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    rows = [[d, round(RiskAssessor.calculate_distance_risk_factor(d), 2)] for d in distances]

    t5 = latex_table(
        'Distance risk decay factor.',
        'sens_distance_decay',
        ['Distance (km)', 'Risk Factor'], rows,
    )

    write_tables('risk_assessment', '\n\n'.join([t1, t2, t3, t4, t5]))

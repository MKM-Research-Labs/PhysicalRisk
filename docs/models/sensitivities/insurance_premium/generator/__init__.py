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

"""Insurance Premium Model sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate insurance premium sensitivity tables."""
    from models.valuation.insurance import apply_insurance_factors

    # Base case: GBP 250k property, mid-range factors
    base = dict(
        property_value=250_000,
        base_rate_per_1000=3.5,
        type_factor=1.0,
        flood_factor=1.0,
        age_factor=1.0,
        construction_factor=1.0,
        area_factor=1.0,
        security_factor=1.0,
        claims_factor=1.0,
    )

    # Table 1: Sensitivity to flood risk factor
    flood_factors = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]
    rows = []
    for ff in flood_factors:
        params = {**base, 'flood_factor': ff}
        premium = apply_insurance_factors(**params)
        rows.append([ff, premium])

    t1 = latex_table(
        'Premium sensitivity to flood risk factor (base property \\pounds250k).',
        'sens_flood',
        ['Flood factor', 'Premium (\\pounds)'],
        rows,
    )

    # Table 2: Sensitivity to property value
    values = [100_000, 150_000, 200_000, 250_000, 350_000, 500_000, 750_000]
    rows = []
    for v in values:
        params = {**base, 'property_value': v}
        premium = apply_insurance_factors(**params)
        rows.append([f'{v:,}', premium])

    t2 = latex_table(
        'Premium sensitivity to property value (all factors at 1.0).',
        'sens_value',
        ['Property value (\\pounds)', 'Premium (\\pounds)'],
        rows,
        col_fmt='rr',
    )

    # Table 3: Sensitivity to claims factor
    claims_factors = [0.8, 0.9, 1.0, 1.2, 1.5, 2.0, 2.5]
    rows = []
    for cf in claims_factors:
        params = {**base, 'claims_factor': cf}
        premium = apply_insurance_factors(**params)
        rows.append([cf, premium])

    t3 = latex_table(
        'Premium sensitivity to claims history factor.',
        'sens_claims',
        ['Claims factor', 'Premium (\\pounds)'],
        rows,
    )

    # Table 4: Combined stress — flood factor x age factor
    flood_vals = [1.0, 2.0, 3.0]
    age_vals = [0.8, 1.0, 1.3, 1.6]
    rows = []
    for ff in flood_vals:
        for af in age_vals:
            params = {**base, 'flood_factor': ff, 'age_factor': af}
            premium = apply_insurance_factors(**params)
            rows.append([ff, af, premium])

    t4 = latex_table(
        'Premium sensitivity to flood factor $\\times$ age factor interaction.',
        'sens_cross',
        ['Flood factor', 'Age factor', 'Premium (\\pounds)'],
        rows,
    )

    write_tables('insurance_premium', '\n\n'.join([t1, t2, t3, t4]))

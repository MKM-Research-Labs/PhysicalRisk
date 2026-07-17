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

"""Property Valuation sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate property valuation sensitivity tables."""
    from models.valuation.property_value import apply_valuation_factors

    base_area = 85
    base_price = 8000

    # Table 1: Flood risk factor sensitivity
    flood_factors = [
        ('Very Low', 1.01), ('Low', 0.99), ('Medium', 0.95),
        ('High', 0.88), ('Very High', 0.80),
    ]
    rows = []
    for label, factor in flood_factors:
        val = apply_valuation_factors(
            area=base_area, price_per_sqm=base_price,
            value_factor=1.0, age_factor=1.0, condition_factor=1.0,
            flood_risk_factor=factor, epc_factor=1.0,
            proximity_factor=1.0, noise_factor=1.0,
        )
        rows.append([label, factor, round(val, 0)])

    t1 = latex_table(
        'Property value by flood risk factor (area=85\\,m$^2$, \\pounds8{,}000/m$^2$, all other factors=1.0).',
        'sens_flood_factor',
        ['Flood Risk', 'Factor', 'Value (\\pounds)'], rows,
        col_fmt='lrr',
    )

    # Table 2: Age factor sensitivity
    age_factors = [
        ('New build', 1.10), ('Modern', 1.00), ('Established', 0.95),
        ('Period', 0.90), ('Heritage', 0.85),
    ]
    rows = []
    for label, factor in age_factors:
        val = apply_valuation_factors(
            area=base_area, price_per_sqm=base_price,
            value_factor=1.0, age_factor=factor, condition_factor=1.0,
            flood_risk_factor=1.0, epc_factor=1.0,
            proximity_factor=1.0, noise_factor=1.0,
        )
        rows.append([label, factor, round(val, 0)])

    t2 = latex_table(
        'Property value by age factor (area=85\\,m$^2$, \\pounds8{,}000/m$^2$, all other factors=1.0).',
        'sens_age_factor',
        ['Age Band', 'Factor', 'Value (\\pounds)'], rows,
        col_fmt='lrr',
    )

    # Table 3: Condition factor sensitivity
    condition_factors = [
        ('Excellent', 1.15), ('Good', 1.05), ('Fair', 0.95),
        ('Poor', 0.80), ('Very poor', 0.60),
    ]
    rows = []
    for label, factor in condition_factors:
        val = apply_valuation_factors(
            area=base_area, price_per_sqm=base_price,
            value_factor=1.0, age_factor=1.0, condition_factor=factor,
            flood_risk_factor=1.0, epc_factor=1.0,
            proximity_factor=1.0, noise_factor=1.0,
        )
        rows.append([label, factor, round(val, 0)])

    t3 = latex_table(
        'Property value by condition factor (area=85\\,m$^2$, \\pounds8{,}000/m$^2$, all other factors=1.0).',
        'sens_condition_factor',
        ['Condition', 'Factor', 'Value (\\pounds)'], rows,
        col_fmt='lrr',
    )

    write_tables('property_valuation', '\n\n'.join([t1, t2, t3]))

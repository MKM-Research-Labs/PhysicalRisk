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

"""Mortgage Pricer sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate mortgage pricer sensitivity tables."""
    from models.mortgage.mortgage_pricer import MortgagePricer

    pricer = MortgagePricer()

    # Table 1: LTV impact
    ltvs = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 1.00]
    rows = []
    for ltv in ltvs:
        pv = 300000
        loan = pv * ltv
        multiplier = pricer.calculate_loan_to_value_impact(loan, pv)
        rows.append([f'{ltv*100:.0f}\\%', round(loan, 0), round(multiplier, 2)])

    t1 = latex_table(
        'LTV risk multiplier by loan-to-value ratio (property value = \\pounds300{,}000).',
        'sens_ltv',
        ['LTV', 'Loan (\\pounds)', 'Risk Multiplier'], rows,
        col_fmt='rrr',
    )

    # Table 2: Mortgage value sensitivity
    interest_rates = [0.02, 0.03, 0.04, 0.05, 0.06]
    insurance_rates = [0.002, 0.005, 0.01, 0.02]
    headers = ['Interest rate'] + [f'Ins={r*100:.1f}\\%' for r in insurance_rates]
    rows = []
    for ir in interest_rates:
        vals = []
        for ins in insurance_rates:
            result = pricer.price_mortgage(
                loan_amount=200000, property_value=300000,
                gross_annual_income=50000, interest_rate=ir,
                insurance_rate=ins, original_maturity=25,
                current_term=20, recovery_haircut=0.30, tax_rate=0.20,
            )
            vals.append(round(result['mortgage_value'], 0))
        rows.append([f'{ir*100:.0f}\\%'] + vals)

    t2 = latex_table(
        'Mortgage value (\\pounds) by interest rate and insurance rate (loan=\\pounds200k, income=\\pounds50k, 20yr remaining).',
        'sens_mortgage_value', headers, rows,
        col_fmt='r' * (1 + len(insurance_rates)),
    )

    # Table 3: Credit spread sensitivity to affordability
    incomes = [30000, 40000, 50000, 60000, 80000, 100000]
    rows = []
    for inc in incomes:
        result = pricer.price_mortgage(
            loan_amount=200000, property_value=300000,
            gross_annual_income=inc, interest_rate=0.04,
            insurance_rate=0.005, original_maturity=25,
            current_term=20, recovery_haircut=0.30, tax_rate=0.20,
        )
        rows.append([f'\\pounds{inc:,}'.replace(',', '{,}'),
                      round(result['credit_spread'] * 100, 2),
                      round(result['mortgage_value'], 0)])

    t3 = latex_table(
        'Credit spread and mortgage value by gross annual income (loan=\\pounds200k, rate=4\\%, 20yr remaining).',
        'sens_affordability',
        ['Income', 'Spread (\\%)', 'Mortgage Value (\\pounds)'], rows,
        col_fmt='rrr',
    )

    # Table 4: Flood risk impact
    flood_categories = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
    rows = []
    for cat in flood_categories:
        flood_factor = pricer.calculate_flood_risk_impact(cat)
        result = pricer.price_mortgage(
            loan_amount=200000, property_value=300000,
            gross_annual_income=50000, interest_rate=0.04,
            insurance_rate=0.005, original_maturity=25,
            current_term=20, recovery_haircut=0.30, tax_rate=0.20,
            flood_risk_category=cat,
        )
        rows.append([cat, round(flood_factor, 2),
                      round(result['credit_spread'] * 100, 2),
                      round(result['mortgage_value'], 0)])

    t4 = latex_table(
        'Credit spread and mortgage value by flood risk category (loan=\\pounds200k, rate=4\\%, income=\\pounds50k).',
        'sens_flood_risk',
        ['Flood Risk', 'Multiplier', 'Spread (\\%)', 'Mortgage Value (\\pounds)'], rows,
        col_fmt='lrrr',
    )

    write_tables('mortgage_pricer', '\n\n'.join([t1, t2, t3, t4]))

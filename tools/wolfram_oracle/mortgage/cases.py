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
"""MP-001's pricing, from its document (``mortgage_pricer.pdf`` v1.1, s3), and the loans.

The reference implements Eqs. 1-24 at 50 digits. Beside the document's fair value
(Eq. 24) it computes the *pathwise* value: the expectation, over the month of
default, of the payments received before it and the recovery received in it. That
is what the loan is worth to the lender under the document's own default model, and
it carries no separate loss term, because the loss is already the shortfall of the
recovery. Wolfram computes both independently, the pathwise one as an expectation
over a geometric default time.
"""

import mpmath as mp

from config.models import (
    ORACLE_MP_DISCOUNTS,
    ORACLE_MP_HAIRCUTS,
    ORACLE_MP_INCOMES,
    ORACLE_MP_INSURANCE,
    ORACLE_MP_LTVS,
    ORACLE_MP_PROPERTY_VALUE,
    ORACLE_MP_RATES,
    ORACLE_MP_TERMS,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_list, wl_precise

# Table 1, as the code holds it (decimals), and the LTV bands of Eq. 9.
NODES = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
SPREADS = (0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35)
LTV_BANDS = ((0.95, 1.5), (0.9, 1.3), (0.8, 1.1))
FLOOR, TAX = 0.001, 0.20


def loans():
    """Every loan in the grid, as the keyword arguments ``price_loan`` takes."""
    out = []
    for ltv in ORACLE_MP_LTVS:
        for hc in ORACLE_MP_HAIRCUTS:
            for y in ORACLE_MP_INCOMES:
                for r in ORACLE_MP_RATES:
                    for orig, cur in ORACLE_MP_TERMS:
                        for d in ORACLE_MP_DISCOUNTS:
                            out.append(dict(
                                loan_amount=ltv * ORACLE_MP_PROPERTY_VALUE,
                                property_value=ORACLE_MP_PROPERTY_VALUE,
                                gross_annual_income=y, interest_rate=r,
                                insurance_rate=ORACLE_MP_INSURANCE, original_maturity=orig,
                                current_term=cur, recovery_haircut=hc, discount_rate=d))
    return out


def case_id(k):
    disc = "coupon" if k["discount_rate"] is None else f"rf{k['discount_rate']:g}"
    return (f"ltv={k['loan_amount'] / k['property_value']:g},hc={k['recovery_haircut']:g},"
            f"y={k['gross_annual_income']:g},r={k['interest_rate']:g},"
            f"T={k['original_maturity']}/{k['current_term']},{disc}")


def _interp(a):
    for (x0, y0), (x1, y1) in zip(zip(NODES, SPREADS), zip(NODES[1:], SPREADS[1:])):
        if a <= x1:
            return mp.mpf(y0) + (mp.mpf(y1) - mp.mpf(y0)) * (a - mp.mpf(x0)) / (mp.mpf(x1) - mp.mpf(x0))
    return mp.mpf(SPREADS[-1])  # pragma: no cover - alpha is clamped to 1


def spread(k, payment, flood=1):
    """Eqs. 6-13; the LTV taken as the double the code compares against its bands."""
    alpha = ((12 * payment + mp.mpf(k["insurance_rate"]) * mp.mpf(k["property_value"]))
             / (mp.mpf(k["gross_annual_income"]) * (1 - mp.mpf(TAX))))
    alpha = min(max(alpha, mp.mpf(NODES[0])), mp.mpf(NODES[-1]))
    phi = 1 + (mp.mpf(k["current_term"]) - mp.mpf(k["original_maturity"]) / 2) / 100
    ltv = k["loan_amount"] / k["property_value"]
    rho = next((f for edge, f in LTV_BANDS if ltv > edge), 1.0)
    return max(mp.mpf(FLOOR), _interp(alpha) * phi) * mp.mpf(rho) * mp.mpf(flood)


def value(k):
    """The document's fair value and its parts, and the pathwise value, at 50 digits."""
    p, r = mp.mpf(k["loan_amount"]), mp.mpf(k["interest_rate"]) / 12
    n = int(k["current_term"] * 12)
    m = p * r / (1 - (1 + r) ** -n)
    b = [p]
    for _ in range(n):
        b.append(max(mp.mpf(0), b[-1] - (m - b[-1] * r)))
    s = spread(k, m)
    h = 1 - mp.exp(-s / 12)
    rec_value = (1 - mp.mpf(k["recovery_haircut"])) * mp.mpf(k["property_value"])
    d = mp.mpf(k["interest_rate"] if k["discount_rate"] is None else k["discount_rate"]) / 12
    pv_cf = pv_el = excess = 0
    for i in range(1, n + 1):
        disc, pd = (1 + d) ** -i, (1 - h) ** (i - 1) * h
        lgd = max(mp.mpf(0), b[i] - rec_value)
        pv_cf += (m * (1 - h) ** i + (b[i - 1] - lgd) * pd) * disc       # Eq. 19
        pv_el += lgd * pd * disc                                         # Eq. 20
        excess += (b[i - 1] - lgd - min(b[i - 1], rec_value)) * pd * disc
    return {"payment": m, "spread": s, "pv_cf": pv_cf, "pv_el": pv_el, "fv": pv_cf - pv_el,
            "excess": excess, "sum_el": mp.fsum(max(mp.mpf(0), b[i] - rec_value) * (1 - h) ** (i - 1) * h
                                                for i in range(1, n + 1))}


_OUT = ("payment", "spread", "pv_cf", "pv_el", "fv")
_MODEL = {"payment": "monthly_payment", "spread": "credit_spread", "pv_cf": "pv_cashflows",
          "pv_el": "pv_losses", "fv": "mortgage_value"}


def run(pricer):
    """Each loan priced by the model and by the reference."""
    lp, rows = pricer.LoanPricer(), []
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for k in loans():
            got, ref = lp.price_loan(**k), value(k)
            row = {"id": case_id(k), **k, "pathwise": mp.nstr(ref["pv_cf"], 30),
                   "double_count": float(ref["pv_el"] / mp.mpf(k["loan_amount"])),
                   "excess_recovery": float(ref["excess"] / mp.mpf(k["loan_amount"])),
                   "el_over_par": float(ref["sum_el"] / mp.mpf(k["loan_amount"]))}
            for key in _OUT:
                row[f"{key}_model"] = repr(float(got[_MODEL[key]]))
                row[f"{key}_ref"] = mp.nstr(ref[key], 30)
                row[f"{key}_rel_err"] = rel_err(got[_MODEL[key]], ref[key])
            rows.append(row)
    return rows


def _wl_case(k):
    """A Module evaluating Eqs. 1-24 from the inputs; the value of ``out`` is returned."""
    p, v = wl_precise(k["loan_amount"]), wl_precise(k["property_value"])
    rate = wl_precise(k["interest_rate"])
    disc = rate if k["discount_rate"] is None else wl_precise(k["discount_rate"])
    rho = next((f for edge, f in LTV_BANDS if k["loan_amount"] / k["property_value"] > edge), 1.0)
    nodes = "Transpose[{" + wl_list(NODES, wl_precise) + ", " + wl_list(SPREADS, wl_precise) + "}]"
    return (
        f"r = {rate}/12; n = {int(k['current_term'] * 12)}; m = {p} r/(1 - (1 + r)^-n); "
        f"b = FoldList[Max[0, #1 - (m - #1 r)] &, {p}, Range[n]]; "
        f"a = Clip[(12 m + {wl_precise(k['insurance_rate'])} {v})/({wl_precise(k['gross_annual_income'])} "
        f"(1 - {wl_precise(TAX)})), {{{wl_precise(NODES[0])}, {wl_precise(NODES[-1])}}}]; "
        f"s = Max[{wl_precise(FLOOR)}, Interpolation[{nodes}, InterpolationOrder -> 1][a] "
        f"(1 + ({k['current_term']} - {k['original_maturity']}/2)/100)] {wl_precise(rho)}; "
        f"h = 1 - Exp[-s/12]; rv = (1 - {wl_precise(k['recovery_haircut'])}) {v}; "
        f"lgd = Table[Max[0, b[[i + 1]] - rv], {{i, n}}]; rec = Most[b] - lgd; "
        f"dsc = Table[(1 + {disc}/12)^-i, {{i, n}}]; ")


def wl_items(rows, lookup):
    """Per loan: the document's fair value (Eq. 24), and the pathwise value as an
    expectation over the default month, tau - 1 ~ Geometric(h)."""
    dg, items = ORACLE_WOLFRAM_DIGITS, []
    for row in rows:
        body = _wl_case(lookup[row["id"]])
        fv = ("sv = Table[(1 - h)^i, {i, 0, n}]; pd = Most[sv] - Rest[sv]; "
              "out = Total[(m Rest[sv] + rec pd) dsc] - Total[lgd pd dsc]")
        path = ("g = GeometricDistribution[h]; pay = Accumulate[m dsc]; "
                "out = Total[Table[PDF[g, i - 1], {i, n}] (Prepend[Most[pay], 0] + rec dsc)] "
                "+ (1 - CDF[g, n - 1]) Last[pay]")
        for tag, tail in (("fv", fv), ("path", path)):
            items.append((f"{row['id']}/{tag}",
                          f"Module[{{r, n, m, b, a, s, h, rv, lgd, rec, dsc, sv, pd, g, pay, out}}, "
                          f"{body}{tail}; N[out, {dg}]]"))
    return items

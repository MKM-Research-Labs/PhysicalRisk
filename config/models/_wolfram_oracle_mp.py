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
"""Wolfram oracle benchmark parameters for MKM-MP-001 (Mortgage Pricing Model).

The loans a benchmark run prices, the claims in MP-001's model document
(``mortgage_pricer.pdf`` v1.1) it tests, and where it files its evidence. Shared
settings -- kernel, precision -- are in ``_wolfram_oracle``.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_MP_PACKAGE = "models.loan.pricer"
ORACLE_MP_SOURCES = ("src/models/loan/pricer/_pricing.py",
                     "src/models/loan/pricer/credit.py",
                     "src/models/loan/pricer/engine.py")

ORACLE_MP_OUT_DIR = "docs/models/mortgage_pricing_benchmark"
ORACLE_MP_DOC = "MKM-MP-001_wolfram_benchmark"
ORACLE_MP_CSV = "mortgage.csv"
ORACLE_MP_WL = "mortgage.wl"
ORACLE_MP_TABLE_PREFIX = "evidence_tables_"

ORACLE_MP_MODEL_ID = "MKM-MP-001"
ORACLE_MP_MODEL_NAME = "Mortgage Pricing Model"

# The loan grid, about the document's own baseline (s6, recovered from its Table 7:
# property GBP 300k, insurance 0.5%, original maturity 25 years). LTV and haircut
# span the region where the recovery falls short of the balance, which the
# baseline (LTV 0.67) never reaches.
ORACLE_MP_PROPERTY_VALUE = 300_000.0
ORACLE_MP_INSURANCE = 0.005
ORACLE_MP_LTVS = (0.5, 0.8, 0.9, 0.95, 1.0)
ORACLE_MP_HAIRCUTS = (0.0, 0.25, 0.4)
ORACLE_MP_INCOMES = (30_000.0, 60_000.0)
ORACLE_MP_RATES = (0.03, 0.06)
ORACLE_MP_TERMS = ((25, 25), (25, 10), (30, 5))    # (original maturity, remaining term)
# Discounting: None is the contractual coupon (the document's s3.8); a number is
# the risk-free rate the production route (routes/_loan_pricing) passes.
ORACLE_MP_DISCOUNTS = (None, 0.035)

# Model against reference: sums of up to 360 terms in double precision.
ORACLE_MP_REL_TOL = 1e-12

# The document's baseline, for its Tables 5-7 (loan GBP 200k, income GBP 50k,
# 20 years remaining, rate 4%) and the values its Table 7 quotes by flood category.
ORACLE_MP_BASELINE = {"loan_amount": 200_000.0, "property_value": 300_000.0,
                      "gross_annual_income": 50_000.0, "interest_rate": 0.04,
                      "insurance_rate": 0.005, "original_maturity": 25,
                      "current_term": 20, "recovery_haircut": 0.25}
ORACLE_MP_CLAIM_TABLE7 = (("Very Low", 3.25, 199_844.0), ("Low", 3.41, 199_838.0),
                          ("Medium", 3.90, 199_820.0), ("High", 4.55, 199_797.0),
                          ("Very High", 5.68, 199_761.0))

# The document's other claims, tested as stated:
#   s6.1    a 100 bp rise in the rate raises the payment by 6-8% on a 25-year term;
#   s3.2.4  zero or negative income gives a 15% spread;
#   s3.2.2  the spread schedule is extrapolated beyond its nodes (s8.5: clamped).
ORACLE_MP_CLAIM_RATE_STEP = (0.06, 0.08)
ORACLE_MP_CLAIM_RATE_GRID = (0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09)
ORACLE_MP_CLAIM_ZERO_INCOME_SPREAD = 0.15

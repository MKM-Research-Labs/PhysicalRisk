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

"""
Basel counterparty-capital constants, shared by MKM-CR-001 and MKM-XV-001 (D-07).

SA-CCR (BCBS CRE52 / BCBS 279, whose Annex 4a worked examples the tests
reproduce), the reduced basic approach to CVA risk (BA-CVA,
MAR50), standardised risk weights for the counterparty (CRE20) and the FRTB
residual risk add-on (MAR23). The values are the published Basel standard.
UK Basel 3.1 (PRA PS9/24) follows it on every number used here. Where the
text leaves a choice open, the choice is named and marked for the regulatory
paper (``docs/xva/regulatory_characterisation.md``).
"""

from typing import Dict, Tuple

# --- SA-CCR (CRE52) ---------------------------------------------------------
SACCR_ALPHA = 1.4
SACCR_MULTIPLIER_FLOOR = 0.05
SACCR_DAYS_PER_YEAR = 250            # business days in the maturity factor
SACCR_MIN_MATURITY_DAYS = 10         # floor on M for the unmargined MF
SACCR_SD_RATE = 0.05                 # supervisory duration discount rate

#: Single-name credit supervisory factor by rating letter grade.
SACCR_CREDIT_SF: Dict[str, float] = {
    "AAA": 0.0038, "AA": 0.0038, "A": 0.0042, "BBB": 0.0054,
    "BB": 0.0106, "B": 0.0160, "CCC": 0.0600,
}
SACCR_CREDIT_SINGLE_NAME_CORRELATION = 0.50
#: Credit index supervisory factor and correlation (needed for the Basel worked
#: example; a PRS is never an index).
SACCR_CREDIT_INDEX_SF: Dict[str, float] = {"IG": 0.0038, "SG": 0.0106}
SACCR_CREDIT_INDEX_CORRELATION = 0.80

#: Commodity supervisory factors; a PRS would sit in "other" (question Q2).
SACCR_COMMODITY_SF: Dict[str, float] = {
    "electricity": 0.40, "oil_gas": 0.18, "metals": 0.18,
    "agricultural": 0.18, "other": 0.18,
}
SACCR_COMMODITY_CORRELATION = 0.40

#: The two candidate treatments in the regulatory paper (Q2).
SACCR_ASSET_CLASSES: Tuple[str, ...] = ("commodity_other", "credit_single_name")

# --- Counterparty risk weights (CRE20, standardised) ------------------------
#: Corporate exposures by rating letter grade; unrated 100%.
SA_RW_CORPORATE: Dict[str, float] = {
    "AAA": 0.20, "AA": 0.20, "A": 0.50, "BBB": 0.75, "BB": 1.00,
    "B": 1.50, "CCC": 1.50, "unrated": 1.00,
}
#: Bank exposures, external credit risk assessment approach (ECRA).
SA_RW_BANK: Dict[str, float] = {
    "AAA": 0.20, "AA": 0.20, "A": 0.30, "BBB": 0.50, "BB": 1.00,
    "B": 1.00, "CCC": 1.50, "unrated": 1.00,
}

# --- BA-CVA, reduced version (MAR50) ----------------------------------------
BA_CVA_DISCOUNT_SCALAR = 0.65        # DS
BA_CVA_CORRELATION = 0.50            # rho between counterparties
BA_CVA_SD_RATE = 0.05                # in the netting-set discount factor
#: Choice for the regulatory paper: MAR50 applies CRE32's effective maturity
#: without its five-year cap. Whether CRE32's one-year floor carries over is
#: read here as yes; set to 0 to drop it.
BA_CVA_MATURITY_FLOOR_YEARS = 1.0

#: Counterparty risk weight by sector, (investment grade, high yield / unrated).
BA_CVA_RW: Dict[str, Tuple[float, float]] = {
    "sovereign": (0.005, 0.020),
    "local_government": (0.010, 0.040),
    "financials": (0.050, 0.120),
    "basic_materials_energy_industrials": (0.030, 0.070),
    "consumer_transport_admin": (0.030, 0.085),
    "technology_telecoms": (0.020, 0.055),
    "health_utilities_professional": (0.015, 0.050),
    "other": (0.050, 0.120),
}

# --- FRTB residual risk add-on (MAR23) ---------------------------------------
#: Exotic underlyings (natural disasters, weather) attract 1% of gross notional.
RRAO_EXOTIC_RATE = 0.01

#: Minimum capital ratio the Basel formulas are calibrated to. Capital held is
#: RWA x the bank's ratio (``config.capital.CapitalConfig.capital_ratio``).
BASEL_MINIMUM_RATIO = 0.08

INVESTMENT_GRADE = ("AAA", "AA", "A", "BBB")

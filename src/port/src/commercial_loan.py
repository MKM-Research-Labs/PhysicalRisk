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

"""
Commercial loan portfolio generator.

One commercial loan per commercial asset. Reads commercial.json, writes
commercial_loan.json. Uses the existing LoanCDM schema (which keys
'Mortgage' / 'MortgageID' for back-compat with the residential loan
shape) but populates it with commercial-flavoured values:

  - LTV ~55-65% (vs ~70-80% residential)
  - Interest-only or part-and-part repayment more common
  - Term 5-15 years (vs 20-25 residential)
  - Rate 4.5-7% (above residential)
  - OccupancyType = Investment
  - MortgageType = Buy-to-Let  (closest existing menu option; the schema
                                menu doesn't yet have a 'CRE Term' value)
  - BorrowerAge / BorrowerCreditScore left null (commercial loans run through
    SPVs / corporates, not individuals)
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import database
from config import config
from port.cdm import LoanCDM

logger = logging.getLogger(__name__)


_BORROWER_TYPE_BY_COMMERCIAL = {
    "Office":      ["SPV", "PropertyCo", "Corporate"],
    "MultiFamily": ["SPV", "PRS Fund", "PropertyCo"],
    "Hotel":       ["OpCo", "PropertyCo", "SPV"],
    "Retail":      ["SPV", "PropertyCo", "REIT"],
    "MixedUse":    ["SPV", "PropertyCo"],
}


def _commercial_loan_id() -> str:
    return f"CLOAN-{uuid.uuid4().hex[:8]}"


def _years_ago(years: float) -> str:
    return (datetime.now() - timedelta(days=int(years * 365.25))).date().isoformat()


def _build_commercial_loan(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Build a single commercial loan record for the given commercial asset."""
    ca = asset.get('CommercialAsset', {})
    header = ca.get('Header', {})
    attrs = ca.get('CommercialAttributes', {})
    val = ca.get('Valuation', {})

    property_id = header.get('PropertyID')
    uprn = header.get('UPRN')
    commercial_type = attrs.get('CommercialType', 'Office')
    property_value = val.get('PropertyValue', 10_000_000)

    ltv = round(random.triangular(0.55, 0.65, 0.70), 4)
    original_loan = round(property_value * ltv, -3)

    rate = round(random.uniform(0.045, 0.07), 4)
    term_years = random.choice([5, 7, 10, 15])
    term_months = term_years * 12
    months_elapsed = random.randint(0, max(0, term_months - 12))
    elapsed_ratio = months_elapsed / term_months

    repayment_type = random.choices(
        ["Interest only", "Part and part", "Repayment"],
        weights=[0.55, 0.30, 0.15])[0]

    if repayment_type == "Interest only":
        outstanding = original_loan
    elif repayment_type == "Part and part":
        outstanding = original_loan * (1 - 0.5 * elapsed_ratio)
    else:
        outstanding = original_loan * (1 - elapsed_ratio * (1.1 - 0.2 * elapsed_ratio))

    outstanding = round(max(outstanding, original_loan * 0.2), 2)
    current_ltv = round(outstanding / max(property_value, 1), 4)
    remaining_term = term_months - months_elapsed

    disbursal_date = _years_ago(months_elapsed / 12)
    maturity_date = (datetime.fromisoformat(disbursal_date)
                     + timedelta(days=term_months * 30)).date().isoformat()

    borrower_type = random.choice(_BORROWER_TYPE_BY_COMMERCIAL.get(commercial_type, ["SPV"]))

    return {
        "Mortgage": {
            "Header": {
                "MortgageID": _commercial_loan_id(),
                "CatchmentID": config.CATCHMENT,
                "PropertyID": property_id,
                "UPRN": uprn,
            },
            "Application": {
                "MemberID": f"COM-{borrower_type[:3].upper()}-{uuid.uuid4().hex[:6]}",
                "MortgageProvider": random.choice([
                    "HSBC Real Estate Finance", "Lloyds Commercial",
                    "Barclays CRE", "NatWest Real Estate",
                    "AIB UK Commercial", "Aviva Investors",
                    "MetLife Real Estate", "Allianz Real Estate",
                ]),
                "ApplicationDate": _years_ago(months_elapsed / 12 + random.uniform(0.1, 0.5)),
                "ApplicationChannel": random.choice(["Broker", "Correspondent"]),
                "LoanPurpose": random.choices(
                    ["Purchase", "Refinancing", "Other"],
                    weights=[0.55, 0.40, 0.05])[0],
                "OccupancyType": "Investment",
            },
            "FinancialTerms": {
                "currency": config.CURRENCY,
                "DisbursalDate": disbursal_date,
                "PurchaseValue": property_value,
                "OriginalLoan": original_loan,
                "OriginalTerm": term_months,
                "OriginalLendingRate": rate,
                "OriginalRateType": random.choices(
                    ["Fixed", "Variable", "Tracker"],
                    weights=[0.65, 0.20, 0.15])[0],
                "OriginalLTV": ltv,
                "MaturityDate": maturity_date,
                "DebtToIncomeRatio": round(random.uniform(1.2, 2.5), 2),  # ~DSCR proxy
            },
            "Features": {
                "MortgageType": "Buy-to-Let",  # closest existing menu value
                "RepaymentType": repayment_type,
                "FlexibleFeatures": random.choices(
                    ["None", "Overpayments", "Drawdown"],
                    weights=[0.55, 0.25, 0.20])[0],
            },
            "CurrentStatus": {
                "OutstandingBalance": outstanding,
                "CurrentLTV": current_ltv,
                "CurrentInterestRate": rate,
                "RemainingTerm": remaining_term,
                "AccountStatus": random.choices(
                    ["Current", "Arrears"], weights=[0.97, 0.03])[0],
                "DefaultFlag": False,
                "ArrearsMonths": 0,
            },
            "BorrowerDetails": {
                # Commercial loans are corporate / SPV — individual fields N/A.
                "NumberOfBorrowers": 1,
                "EmploymentType": "Other",
            },
            "RiskAssessment": {
                "BehavioralScore": random.randint(70, 95),
                "PrepaymentRisk": random.randint(10, 60),
                "FloodRiskCategory": ca.get('RiskAssessment', {})
                                       .get('OverallFloodRisk', 'Low'),
            },
        },
        "_commercial_meta": {
            "borrower_type": borrower_type,
            "commercial_type": commercial_type,
        },
    }


class CommercialLoanPortfolioGenerator:
    """Generates commercial loans 1:1 with commercial assets."""

    def __init__(self, catchment: Optional[str] = None, verbose: bool = True):
        # Run-scoped catchment identity; storage location lives in ``database``.
        self.catchment = catchment or database.active_catchment()
        self.loan_cdm = LoanCDM()
        self.verbose = verbose

    def log(self, message: str, level: str = "INFO"):
        getattr(logger, level.lower(), logger.info)(message)

    def generate(self) -> Dict:
        start = datetime.now()
        self.log("=" * 60, "INFO")
        self.log("COMMERCIAL LOAN PORTFOLIO GENERATOR", "INFO")
        self.log("=" * 60, "INFO")

        commercial_data = database.get_commercial_portfolio(self.catchment)
        if commercial_data is None:
            raise FileNotFoundError(
                f"Commercial portfolio not found for catchment {self.catchment}. "
                "Generate it first with --commercial.")
        assets = commercial_data.get('commercial_assets', [])
        self.log(f"Loaded {len(assets)} commercial assets", "INFO")

        loans: List[Dict] = []
        for i, asset in enumerate(assets):
            try:
                loan = _build_commercial_loan(asset)
                loans.append(loan)
                pid = loan['Mortgage']['Header']['PropertyID']
                lid = loan['Mortgage']['Header']['MortgageID']
                ol = loan['Mortgage']['FinancialTerms']['OriginalLoan']
                ltv = loan['Mortgage']['FinancialTerms']['OriginalLTV']
                self.log(f"  [{i+1}/{len(assets)}] {lid} -> {pid}  loan=£{ol/1e6:.1f}M  LTV={ltv:.0%}", "INFO")
            except Exception as e:
                self.log(f"Failed to build loan for asset {i+1}: {e}", "ERROR")

        output_data = {
            "commercial_loans": loans,
            "generation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "CommercialLoan v0.1 (first slice)",
                "catchment": config.CATCHMENT,
                "total_loans_generated": len(loans),
                "linked_commercial_assets": len(assets),
            }
        }
        # Persist through the database seam (catchment-keyed, storage-agnostic).
        database.save_commercial_loans(self.catchment, output_data)

        elapsed = (datetime.now() - start).total_seconds()
        self.log(f"Wrote {len(loans)} commercial loans for catchment {self.catchment} in {elapsed:.1f}s", "INFO")
        return {"data": {"commercial_loans": loans},
                "catchment": self.catchment,
                "processing_stats": {"successful": len(loans), "total": len(assets)}}


def generate_commercial_loans(catchment: Optional[str] = None) -> Dict:
    return CommercialLoanPortfolioGenerator(catchment=catchment).generate()

# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial loan overview — from commercial_loan.json.

The commercial loan record reuses the ``Mortgage`` top-level CDM key
(same shape as residential mortgage.json) plus a ``_commercial_meta``
sidecar (borrower_type, commercial_type). Phase B should promote this
to a shared ``reports.asset.loan`` and have the residential mortgage
pages call into it.
"""

from typing import Any, Dict, List, Optional

from reportlab.platypus import Paragraph

from reports.asset._helpers import auto_rows, section_block

from ..base import CommercialBasePage

_APPLICATION_FIELDS = [
    ("MemberID",            "Member ID"),
    ("MortgageProvider",    "Lender"),
    ("ApplicationDate",     "Application Date"),
    ("ApplicationChannel",  "Application Channel"),
    ("LoanPurpose",         "Loan Purpose"),
    ("OccupancyType",       "Occupancy Type"),
]

_FINANCIAL_FIELDS = [
    ("currency",             "Currency"),
    ("DisbursalDate",        "Disbursal Date"),
    ("PurchaseValue",        "Purchase Value"),
    ("OriginalLoan",         "Original Loan"),
    ("OriginalTerm",         "Original Term (months)"),
    ("OriginalLendingRate",  "Original Lending Rate"),
    ("OriginalRateType",     "Original Rate Type"),
    ("OriginalLTV",          "Original LTV"),
    ("MaturityDate",         "Maturity Date"),
    ("DebtToIncomeRatio",    "DTI Ratio"),
]

_CURRENT_FIELDS = [
    ("OutstandingBalance",   "Outstanding Balance"),
    ("CurrentLTV",           "Current LTV"),
    ("CurrentInterestRate",  "Current Interest Rate"),
    ("RemainingTerm",        "Remaining Term (months)"),
    ("AccountStatus",        "Account Status"),
    ("DefaultFlag",          "Default Flag"),
    ("ArrearsMonths",        "Arrears (months)"),
]

_FEATURES_FIELDS = [
    ("MortgageType",     "Loan Type"),
    ("RepaymentType",    "Repayment Type"),
    ("FlexibleFeatures", "Flexible Features"),
]

_BORROWER_FIELDS = [
    ("NumberOfBorrowers", "Number of Borrowers"),
    ("EmploymentType",    "Employment Type"),
]

_RISK_FIELDS = [
    ("BehavioralScore",     "Behavioural Score"),
    ("PrepaymentRisk",      "Prepayment Risk"),
    ("FloodRiskCategory",   "Flood Risk Category"),
]

_META_FIELDS = [
    ("borrower_type",   "Borrower Type"),
    ("commercial_type", "Commercial Type"),
]


class CLoanOverviewPage(CommercialBasePage):
    """Renders the commercial loan record linked to this asset.

    Reads from ``loan_data['Mortgage']`` and the optional
    ``_commercial_meta`` sidecar. Pass ``loan_data=None`` when no loan
    is linked — the page emits a single placeholder paragraph.
    """

    def generate_elements(
        self,
        commercial_data: Dict[str, Any],
        loan_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List:
        elements: List = [
            Paragraph("Commercial Loan Overview", self.styles["SectionHeader"]),
        ]
        if not loan_data:
            elements.append(Paragraph(
                "No loan record linked to this asset.",
                self.styles["Normal"],
            ))
            return elements

        mortgage = loan_data.get("Mortgage", {}) or {}
        meta = loan_data.get("_commercial_meta", {}) or {}

        elements.extend(section_block(
            "Application",
            self,
            auto_rows(mortgage.get("Application", {}) or {}, _APPLICATION_FIELDS),
            style="financial",
            header=("Field", "Value"),
        ))
        elements.extend(section_block(
            "Financial Terms",
            self,
            auto_rows(mortgage.get("FinancialTerms", {}) or {}, _FINANCIAL_FIELDS),
            style="financial",
            header=("Term", "Value"),
        ))
        elements.extend(section_block(
            "Current Status",
            self,
            auto_rows(mortgage.get("CurrentStatus", {}) or {}, _CURRENT_FIELDS),
            style="financial",
            header=("Metric", "Value"),
        ))
        elements.extend(section_block(
            "Features",
            self,
            auto_rows(mortgage.get("Features", {}) or {}, _FEATURES_FIELDS),
            style="financial",
            header=("Feature", "Value"),
        ))
        elements.extend(section_block(
            "Borrower",
            self,
            auto_rows(mortgage.get("BorrowerDetails", {}) or {}, _BORROWER_FIELDS),
            style="financial",
            header=("Field", "Value"),
        ))
        elements.extend(section_block(
            "Lender Risk Assessment",
            self,
            auto_rows(mortgage.get("RiskAssessment", {}) or {}, _RISK_FIELDS),
            style="risk",
            header=("Field", "Value"),
        ))
        if meta:
            elements.extend(section_block(
                "Commercial Loan Metadata",
                self,
                auto_rows(meta, _META_FIELDS),
                style="standard",
                header=("Field", "Value"),
            ))
        return elements

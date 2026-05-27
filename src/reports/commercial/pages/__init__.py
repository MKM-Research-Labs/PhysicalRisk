# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial report pages.

Pages divide into two groups:
  - **Shared sections** (header, valuation, location, construction,
    risk_assessment, energy, protection, history, transactions): thin
    page classes that pull the relevant slice out of the
    ``CommercialAsset`` dict and delegate to ``reports.asset.render_*``.
  - **Commercial-only sections** (title, attributes, accessibility,
    tenancy, loan_overview): full pages, defined here.
"""

from .accessibility import AccessibilityPage
from .attributes import CommercialAttributesPage
from .loan_overview import LoanOverviewPage
from .shared_pages import (
    ConstructionPage,
    EnergyPage,
    HeaderPage,
    HistoryPage,
    LocationPage,
    ProtectionPage,
    RiskAssessmentPage,
    TransactionsPage,
    ValuationPage,
)
from .tenancy import TenancyPage
from .title_overview import TitleOverviewPage

__all__ = [
    "TitleOverviewPage",
    "HeaderPage",
    "LocationPage",
    "CommercialAttributesPage",
    "AccessibilityPage",
    "TenancyPage",
    "ConstructionPage",
    "ValuationPage",
    "RiskAssessmentPage",
    "EnergyPage",
    "ProtectionPage",
    "HistoryPage",
    "TransactionsPage",
    "LoanOverviewPage",
]

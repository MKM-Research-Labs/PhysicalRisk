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
from .loan_overview import CLoanOverviewPage
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
    "CLoanOverviewPage",
]

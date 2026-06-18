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

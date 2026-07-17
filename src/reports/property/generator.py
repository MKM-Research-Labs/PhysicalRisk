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

"""PropertyReportGenerator — orchestrates page modules into a full property PDF."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from reportlab.lib import colors

from reports.shared import BaseReportGenerator

from .property_page_01_title_overview import TitleOverviewPage
from .property_page_02_location import LocationPage
from .property_page_03_attributes import AttributesPage
from .property_page_04_construction import ConstructionPage
from .property_page_05_risk_assessment import RiskAssessmentPage
from .property_page_06_financial import FinancialPage
from .property_page_07_protection import ProtectionPage
from .property_page_09_history import HistoryPage
from .property_page_10_transactions import TransactionsPage
from .property_page_11_rloan_overview import RLoanOverviewPage
from .property_page_11a_rloan_details import RLoanDetailsPage
from .property_page_11b_rloan_costs import RLoanCostsPage
from .property_page_11c_regulatory import RegulatoryPage
from .property_page_12_current_status import CurrentStatusPage
from .property_page_13_risk_analysis import RiskAnalysisPage
from .property_page_14_borrower_profile import BorrowerProfilePage
from .property_page_15_data_summary import DataSummaryPage

logger = logging.getLogger(__name__)


class PropertyReportGenerator(BaseReportGenerator):
    """Clean, focused report generator that orchestrates page modules."""

    REPORT_TITLE = "Property Analysis Report"
    HEADER_COLOR = colors.navy
    SUBTITLE_COLOR = colors.darkblue

    def _get_default_output_dir(self) -> Path:
        from config import config
        return config.get_property_reports_dir()

    def _initialize_pages(self):
        """Initialize page generators and define page categories."""
        self.pages = {
            # Property pages
            'title_overview': TitleOverviewPage(),
            'location': LocationPage(),
            'attributes': AttributesPage(),
            'construction': ConstructionPage(),
            'risk_assessment': RiskAssessmentPage(),
            'financial': FinancialPage(),
            'protection': ProtectionPage(),
            'history': HistoryPage(),
            'transactions': TransactionsPage(),

            # Mortgage pages
            'mortgage_overview': RLoanOverviewPage(),
            'mortgage_details': RLoanDetailsPage(),
            'mortgage_costs': RLoanCostsPage(),
            'regulatory': RegulatoryPage(),
            'current_status': CurrentStatusPage(),
            'borrower_profile': BorrowerProfilePage(),

            # Analysis pages
            'risk_analysis': RiskAnalysisPage(),
            'data_summary': DataSummaryPage()
        }

        self.categories = {
            'property': [
                'title_overview', 'location', 'attributes', 'construction',
                'risk_assessment', 'financial', 'protection',
                'history', 'transactions'
            ],
            'mortgage': [
                'mortgage_overview', 'mortgage_details', 'mortgage_costs',
                'regulatory', 'current_status', 'borrower_profile'
            ],
            'analysis': [
                'risk_analysis', 'data_summary'
            ]
        }

    def generate_report(self, property_data: Dict[str, Any],
                       rloan_data: Optional[Dict[str, Any]] = None,
                       pages_to_include: Optional[List[str]] = None,
                       output_filename: Optional[str] = None) -> Path:
        """Generate a property report."""
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(property_data, rloan_data)

        if output_filename is None:
            output_filename = self._generate_filename(property_data)

        output_path = self.output_dir / output_filename
        return self._build_pdf(
            output_path, pages_to_include,
            property_data=property_data, rloan_data=rloan_data
        )

    def _auto_select_pages(self, property_data: Dict[str, Any],
                          rloan_data: Optional[Dict[str, Any]]) -> List[str]:
        """Auto-select appropriate pages based on available data."""
        pages = self.categories['property'].copy()

        if rloan_data:
            pages.extend(self.categories['mortgage'])

        pages.extend(self.categories['analysis'])
        return pages

    def _generate_filename(self, property_data: Dict[str, Any]) -> str:
        """Generate output filename based on property data."""
        try:
            property_id = property_data['PropertyHeader']['Header']['PropertyID']
        except (KeyError, TypeError):
            property_id = 'unknown'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"property_report_{property_id}_{timestamp}.pdf"

    def generate_property_only_report(self, property_data: Dict[str, Any],
                                    output_filename: Optional[str] = None) -> Path:
        """Generate property-only report."""
        pages = self.categories['property'] + self.categories['analysis']
        return self.generate_report(property_data, None, pages, output_filename)

    def generate_mortgage_focused_report(self, property_data: Dict[str, Any],
                                       rloan_data: Dict[str, Any],
                                       output_filename: Optional[str] = None) -> Path:
        """Generate mortgage-focused report."""
        essential_property = ['title_overview', 'location', 'risk_assessment', 'financial']
        pages = essential_property + self.categories['mortgage'] + self.categories['analysis']
        return self.generate_report(property_data, rloan_data, pages, output_filename)

    def generate_risk_focused_report(self, property_data: Dict[str, Any],
                                   rloan_data: Optional[Dict[str, Any]] = None,
                                   output_filename: Optional[str] = None) -> Path:
        """Generate risk-focused report."""
        risk_pages = ['title_overview', 'risk_assessment', 'protection', 'history']

        if rloan_data:
            risk_pages.extend(['current_status', 'borrower_profile'])

        risk_pages.extend(['risk_analysis', 'data_summary'])
        return self.generate_report(property_data, rloan_data, risk_pages, output_filename)

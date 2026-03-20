# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""PropertyReportGenerator — orchestrates page modules into a full property PDF."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, SimpleDocTemplate

from .property_page_01_title_overview import TitleOverviewPage
from .property_page_02_location import LocationPage
from .property_page_03_attributes import AttributesPage
from .property_page_04_construction import ConstructionPage
from .property_page_05_risk_assessment import RiskAssessmentPage
from .property_page_06_financial import FinancialPage
from .property_page_07_protection import ProtectionPage
from .property_page_09_history import HistoryPage
from .property_page_10_transactions import TransactionsPage
from .property_page_11_mortgage_overview import MortgageOverviewPage
from .property_page_11a_mortgage_details import MortgageDetailsPage
from .property_page_11b_mortgage_costs import MortgageCostsPage
from .property_page_11c_regulatory import RegulatoryPage
from .property_page_12_current_status import CurrentStatusPage
from .property_page_13_risk_analysis import RiskAnalysisPage
from .property_page_14_borrower_profile import BorrowerProfilePage
from .property_page_15_data_summary import DataSummaryPage

logger = logging.getLogger(__name__)


class PropertyReportGenerator:
    """Clean, focused report generator that orchestrates page modules."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """Initialize the report generator."""
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            from config import config
            self.output_dir = config.get_property_reports_dir()
        os.makedirs(self.output_dir, exist_ok=True)
        self._initialize_pages()

    def _initialize_pages(self):
        """Initialize page generators and define page categories."""
        self.property_pages = {
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
            'mortgage_overview': MortgageOverviewPage(),
            'mortgage_details': MortgageDetailsPage(),
            'mortgage_costs': MortgageCostsPage(),
            'regulatory': RegulatoryPage(),
            'current_status': CurrentStatusPage(),
            'borrower_profile': BorrowerProfilePage(),

            # Analysis pages
            'risk_analysis': RiskAnalysisPage(),
            'data_summary': DataSummaryPage()
        }

        # Define page categories
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
                       mortgage_data: Optional[Dict[str, Any]] = None,
                       pages_to_include: Optional[List[str]] = None,
                       output_filename: Optional[str] = None) -> Path:
        """Generate a property report."""
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(property_data, mortgage_data)

        if output_filename is None:
            output_filename = self._generate_filename(property_data)

        output_path = self.output_dir / output_filename

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch,
            topMargin=1.2*inch,
            bottomMargin=1*inch
        )

        elements = self._generate_elements(property_data, mortgage_data, pages_to_include)
        element_count = len(elements)

        doc.build(elements,
                onFirstPage=self._create_header_footer,
                onLaterPages=self._create_header_footer)

        logger.info(f"Report generated: {output_path}")
        logger.info(f"Pages: {len(pages_to_include)} | Elements: {element_count}")

        return output_path

    def _auto_select_pages(self, property_data: Dict[str, Any],
                          mortgage_data: Optional[Dict[str, Any]]) -> List[str]:
        """Auto-select appropriate pages based on available data."""
        pages = self.categories['property'].copy()

        if mortgage_data:
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

    def _generate_elements(self, property_data: Dict[str, Any],
                          mortgage_data: Optional[Dict[str, Any]],
                          pages_to_include: List[str]) -> List:
        """Generate all report elements."""
        elements = []

        for i, page_name in enumerate(pages_to_include):
            if page_name not in self.property_pages:
                logger.warning(f"Skipping unknown page: {page_name}")
                continue

            try:
                if i > 0:
                    elements.append(PageBreak())

                page_elements = self.property_pages[page_name].generate_elements(
                    property_data, mortgage_data
                )
                elements.extend(page_elements)

                logger.info(f"Generated {page_name}")

            except Exception as e:
                logger.error(f"Error generating {page_name}: {str(e)}")
                continue

        return elements

    def _create_header_footer(self, canvas, doc):
        """Add headers and footers to pages."""
        canvas.saveState()

        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(colors.navy)
        canvas.drawString(0.5*inch, doc.height + doc.topMargin, "MKM Research Labs")

        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.darkblue)
        canvas.drawRightString(doc.width + 0.5*inch, doc.height + doc.topMargin - 0.1*inch,
                              "Property Analysis Report")
        canvas.drawRightString(doc.width + 0.5*inch, doc.height + doc.topMargin - 0.3*inch,
                              f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(0.5*inch, doc.bottomMargin - 0.5*inch, f"Page {canvas.getPageNumber()}")
        canvas.drawCentredString(doc.width/2.0 + 0.5*inch, doc.bottomMargin - 0.5*inch,
                               "CONFIDENTIAL - For authorized use only")

        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(0.5*inch, doc.bottomMargin - 0.25*inch,
                   doc.width + 0.5*inch, doc.bottomMargin - 0.25*inch)

        canvas.restoreState()

    def generate_property_only_report(self, property_data: Dict[str, Any],
                                    output_filename: Optional[str] = None) -> Path:
        """Generate property-only report."""
        pages = self.categories['property'] + self.categories['analysis']
        return self.generate_report(property_data, None, pages, output_filename)

    def generate_mortgage_focused_report(self, property_data: Dict[str, Any],
                                       mortgage_data: Dict[str, Any],
                                       output_filename: Optional[str] = None) -> Path:
        """Generate mortgage-focused report."""
        essential_property = ['title_overview', 'location', 'risk_assessment', 'financial']
        pages = essential_property + self.categories['mortgage'] + self.categories['analysis']
        return self.generate_report(property_data, mortgage_data, pages, output_filename)

    def generate_risk_focused_report(self, property_data: Dict[str, Any],
                                   mortgage_data: Optional[Dict[str, Any]] = None,
                                   output_filename: Optional[str] = None) -> Path:
        """Generate risk-focused report."""
        risk_pages = ['title_overview', 'risk_assessment', 'protection', 'history']

        if mortgage_data:
            risk_pages.extend(['current_status', 'borrower_profile'])

        risk_pages.extend(['risk_analysis', 'data_summary'])
        return self.generate_report(property_data, mortgage_data, risk_pages, output_filename)

    def list_available_pages(self) -> List[str]:
        """Return list of available pages."""
        return list(self.property_pages.keys())

    def get_page_categories(self) -> Dict[str, List[str]]:
        """Return page categories."""
        return self.categories.copy()

    def validate_pages(self, pages: List[str]) -> tuple[List[str], List[str]]:
        """Validate page list, return (valid_pages, invalid_pages)."""
        valid = [p for p in pages if p in self.property_pages]
        invalid = [p for p in pages if p not in self.property_pages]
        return valid, invalid

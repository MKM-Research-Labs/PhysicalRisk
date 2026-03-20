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

"""GaugeReportGenerator class — orchestrates page modules to create gauge reports."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import reportlab.platypus as _rl_platypus
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak

logger = logging.getLogger(__name__)

# Import gauge page modules
from .gauge_page_01_title_overview import GaugeTitleOverviewPage
from .gauge_page_02_sensor_details import GaugeSensorDetailsPage
from .gauge_page_03_location import GaugeLocationPage
from .gauge_page_04_measurements import GaugeMeasurementsPage
from .gauge_page_05_flood_stages import GaugeFloodStagesPage
from .gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
from .gauge_page_07_data_summary import GaugeDataSummaryPage
from .gauge_page_08_flood_history import GaugeFloodHistoryPage
from .gauge_page_09_hazard_curves import GaugeHazardCurvesPage
from .gauge_page_10_prs_pricing import GaugePRSPricingPage
from .gauge_page_11_current_risk import GaugeCurrentRiskPage
from .gauge_page_12_trading import GaugeTradingPage


class GaugeReportGenerator:
    """Clean, focused gauge report generator that orchestrates page modules."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """Initialize the gauge report generator."""
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            from config import config
            self.output_dir = config.get_gauge_reports_dir()
        os.makedirs(self.output_dir, exist_ok=True)
        self._initialize_pages()

    def _initialize_pages(self):
        """Initialize page generators and define page categories."""
        self.pages = {
            # Gauge pages
            'title_overview': GaugeTitleOverviewPage(),
            'sensor_details': GaugeSensorDetailsPage(),
            'location': GaugeLocationPage(),
            'measurements': GaugeMeasurementsPage(),
            'flood_stages': GaugeFloodStagesPage(),
            'risk_assessment': GaugeRiskAssessmentPage(),
            'data_summary': GaugeDataSummaryPage(),
            'flood_history': GaugeFloodHistoryPage(),
            'hazard_curves': GaugeHazardCurvesPage(),
            'prs_pricing': GaugePRSPricingPage(),
            'current_risk': GaugeCurrentRiskPage(),
            'trading': GaugeTradingPage(),
        }

        # Define page categories
        self.categories = {
            'gauge_info': [
                'title_overview', 'sensor_details', 'location'
            ],
            'operational': [
                'measurements', 'flood_stages'
            ],
            'analysis': [
                'risk_assessment', 'flood_history', 'hazard_curves', 'prs_pricing', 'current_risk', 'trading'
            ],
            'summary': [
                'data_summary'
            ]
        }

    def generate_report(self, gauge_data: Dict[str, Any],
                  timeseries_data: Optional[Dict[str, Any]] = None,
                  pages_to_include: Optional[List[str]] = None,
                  output_filename: Optional[str] = None) -> Path:
        """
        Generate a gauge report.

        Args:
            gauge_data: Gauge information
            timeseries_data: Timeseries data (optional)
            pages_to_include: Specific pages to include (auto-selected if None)
            output_filename: Custom filename (auto-generated if None)

        Returns:
            Path to generated PDF
        """
        # Auto-select pages if not specified
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(gauge_data, timeseries_data)

        # Generate filename if not provided
        if output_filename is None:
            output_filename = self._generate_filename(gauge_data)

        output_path = self.output_dir / output_filename

        # Create PDF document
        doc = _rl_platypus.SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch,
            topMargin=1.2*inch,
            bottomMargin=1*inch
        )

        # Generate all page elements
        elements = self._generate_elements(gauge_data, timeseries_data, pages_to_include)

        # Store count before doc.build() consumes the elements
        element_count = len(elements)

        # Build PDF
        doc.build(elements,
                    onFirstPage=self._create_header_footer,
                    onLaterPages=self._create_header_footer)

        logger.info(f"Gauge report generated: {output_path}")
        logger.info(f"Pages: {len(pages_to_include)} | Elements: {element_count}")

        return output_path

    def _auto_select_pages(self, gauge_data: Dict[str, Any],
                          timeseries_data: Optional[Dict[str, Any]]) -> List[str]:
        """Auto-select appropriate pages based on available data."""
        pages = self.categories['gauge_info'].copy()

        # Add operational pages when available
        pages.extend(self.categories['operational'])

        # Add analysis pages if timeseries or hazard data available
        if timeseries_data or gauge_data.get('hazard_curve'):
            pages.extend(self.categories['analysis'])

        # Always add summary
        pages.extend(self.categories['summary'])

        # Filter out pages that don't exist yet
        available_pages = [page for page in pages if page in self.pages]
        return available_pages

    def _generate_filename(self, gauge_data: Dict[str, Any]) -> str:
        """Generate output filename based on gauge data."""
        try:
            gauge_id = gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            gauge_id = 'unknown'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"gauge_report_{gauge_id}_{timestamp}.pdf"

    def _generate_elements(self, gauge_data: Dict[str, Any],
                     timeseries_data: Optional[Dict[str, Any]],
                     pages_to_include: List[str]) -> List:
        """Generate all report elements."""
        elements = []

        for i, page_name in enumerate(pages_to_include):
            if page_name not in self.pages:
                logger.warning(f"Skipping unknown page: {page_name}")
                continue

            try:
                # Add page break (except for first page)
                if i > 0:
                    elements.append(PageBreak())

                # Generate page elements
                page_elements = self.pages[page_name].generate_elements(
                    gauge_data, timeseries_data
                )

                logger.debug(f"Page {page_name} generated {len(page_elements)} elements")
                elements.extend(page_elements)

                logger.info(f"Generated {page_name}")

            except Exception as e:
                logger.error(f"Error generating {page_name}: {str(e)}", exc_info=True)
                continue

        logger.debug(f"Total elements in _generate_elements: {len(elements)}")
        return elements

    def _create_header_footer(self, canvas, doc):
        """Add headers and footers to pages."""
        canvas.saveState()

        # Header
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(colors.darkblue)
        canvas.drawString(0.5*inch, doc.height + doc.topMargin, "MKM Research Labs")

        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.blue)
        canvas.drawRightString(doc.width + 0.5*inch, doc.height + doc.topMargin - 0.1*inch,
                              "Flood Gauge Analysis Report")
        canvas.drawRightString(doc.width + 0.5*inch, doc.height + doc.topMargin - 0.3*inch,
                              f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(0.5*inch, doc.bottomMargin - 0.5*inch, f"Page {canvas.getPageNumber()}")
        canvas.drawCentredString(doc.width/2.0 + 0.5*inch, doc.bottomMargin - 0.5*inch,
                               "CONFIDENTIAL - For authorized use only")

        # Footer line
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(0.5*inch, doc.bottomMargin - 0.25*inch,
                   doc.width + 0.5*inch, doc.bottomMargin - 0.25*inch)

        canvas.restoreState()

    # Specialized report generators
    def generate_basic_report(self, gauge_data: Dict[str, Any],
                         timeseries_data: Optional[Dict[str, Any]] = None,
                         output_filename: Optional[str] = None) -> Path:
        """Generate basic gauge report."""
        pages = ['title_overview', 'sensor_details', 'location', 'measurements',
                 'flood_stages', 'risk_assessment', 'flood_history', 'hazard_curves',
                 'prs_pricing', 'trading', 'data_summary']
        return self.generate_report(gauge_data, timeseries_data, pages, output_filename)

    def generate_monitoring_report(self, gauge_data: Dict[str, Any],
                                  timeseries_data: Dict[str, Any],
                                  output_filename: Optional[str] = None) -> Path:
        """Generate monitoring-focused report."""
        essential_gauge = ['title_overview']
        pages = essential_gauge
        return self.generate_report(gauge_data, timeseries_data, pages, output_filename)

    def generate_analysis_report(self, gauge_data: Dict[str, Any],
                                timeseries_data: Optional[Dict[str, Any]] = None,
                                output_filename: Optional[str] = None) -> Path:
        """Generate analysis-focused report."""
        analysis_pages = ['title_overview']
        return self.generate_report(gauge_data, timeseries_data, analysis_pages, output_filename)

    # Utility methods
    def list_available_pages(self) -> List[str]:
        """Return list of available pages."""
        return list(self.pages.keys())

    def get_page_categories(self) -> Dict[str, List[str]]:
        """Return page categories."""
        return self.categories.copy()

    def validate_pages(self, pages: List[str]) -> tuple[List[str], List[str]]:
        """Validate page list, return (valid_pages, invalid_pages)."""
        valid = [p for p in pages if p in self.pages]
        invalid = [p for p in pages if p not in self.pages]
        return valid, invalid

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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reports.shared import BaseReportGenerator

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


class GaugeReportGenerator(BaseReportGenerator):
    """Clean, focused gauge report generator that orchestrates page modules."""

    REPORT_TITLE = "Flood Gauge Analysis Report"

    def _get_default_output_dir(self) -> Path:
        from config import config
        return config.get_gauge_reports_dir()

    def _initialize_pages(self):
        """Initialize page generators and define page categories."""
        self.pages = {
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

        self.categories = {
            'gauge_info': [
                'title_overview', 'sensor_details', 'location'
            ],
            'operational': [
                'measurements', 'flood_stages'
            ],
            'analysis': [
                'risk_assessment', 'flood_history', 'hazard_curves',
                'prs_pricing', 'current_risk', 'trading'
            ],
            'summary': [
                'data_summary'
            ]
        }

    def generate_report(self, gauge_data: Dict[str, Any],
                  timeseries_data: Optional[Dict[str, Any]] = None,
                  pages_to_include: Optional[List[str]] = None,
                  output_filename: Optional[str] = None) -> Path:
        """Generate a gauge report."""
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(gauge_data, timeseries_data)

        if output_filename is None:
            output_filename = self._generate_filename(gauge_data)

        output_path = self.output_dir / output_filename
        return self._build_pdf(
            output_path, pages_to_include,
            gauge_data=gauge_data, timeseries_data=timeseries_data
        )

    def _auto_select_pages(self, gauge_data: Dict[str, Any],
                          timeseries_data: Optional[Dict[str, Any]]) -> List[str]:
        """Auto-select appropriate pages based on available data."""
        pages = self.categories['gauge_info'].copy()
        pages.extend(self.categories['operational'])

        if timeseries_data or gauge_data.get('hazard_curve'):
            pages.extend(self.categories['analysis'])

        pages.extend(self.categories['summary'])

        return [page for page in pages if page in self.pages]

    def _generate_filename(self, gauge_data: Dict[str, Any]) -> str:
        """Generate output filename based on gauge data."""
        try:
            gauge_id = gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            gauge_id = 'unknown'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"gauge_report_{gauge_id}_{timestamp}.pdf"

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

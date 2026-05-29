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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Flood Risk Report Generator
Orchestrates page modules to create comprehensive flood risk reports.
Following the exact patterns of the gauge report system.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from reports.shared import BaseReportGenerator

logger = logging.getLogger(__name__)

# Import flood risk page modules
from .risk_page_01_title import RiskTitlePage
from .risk_page_02_executive_summary import RiskExecutiveSummaryPage
from .risk_page_03_portfolio_overview import RiskPortfolioOverviewPage
from .risk_page_04_risk_analysis import RiskAnalysisPage
from .risk_page_05_rloan_analysis import RiskRLoanAnalysisPage
from .risk_page_06_property_details import RiskPropertyDetailsPage
from .risk_page_07_appendix import RiskAppendixPage


class RiskReportGenerator(BaseReportGenerator):
    """Flood risk report generator following gauge system patterns."""

    REPORT_TITLE = "Flood Risk Analysis Report"

    def _get_default_output_dir(self) -> Path:
        from config import config
        return config.get_reports_dir("risk")

    def _initialize_pages(self):
        """Initialize page generators and define page categories."""
        self.pages = {
            'title': RiskTitlePage(),
            'executive_summary': RiskExecutiveSummaryPage(),
            'portfolio_overview': RiskPortfolioOverviewPage(),
            'risk_analysis': RiskAnalysisPage(),
            'mortgage_analysis': RiskRLoanAnalysisPage(),
            'property_details': RiskPropertyDetailsPage(),
            'appendix': RiskAppendixPage(),
        }

        self.categories = {
            'overview': ['title', 'executive_summary', 'portfolio_overview'],
            'analysis': ['risk_analysis', 'mortgage_analysis', 'property_details'],
            'appendix': ['appendix']
        }

    def generate_report(self,
                       flood_data: Dict[str, Any],
                       output_filename: Optional[str] = None,
                       pages_to_include: Optional[List[str]] = None) -> Path:
        """Generate a flood risk report."""
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(flood_data)

        if output_filename is None:
            output_filename = self._generate_filename()

        output_path = self.output_dir / output_filename
        return self._build_pdf(
            output_path, pages_to_include,
            flood_data=flood_data
        )

    def _auto_select_pages(self, flood_data: Dict[str, Any]) -> List[str]:
        """Auto-select appropriate pages based on available data."""
        pages = self.categories['overview'].copy()
        pages.extend(self.categories['analysis'])
        pages.extend(self.categories['appendix'])

        return [page for page in pages if page in self.pages]

    def _generate_filename(self) -> str:
        """Generate output filename."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"flood_risk_report_{timestamp}.pdf"

    # Specialized report generators
    def generate_basic_report(self, flood_data: Dict[str, Any],
                             output_filename: Optional[str] = None) -> Path:
        """Generate basic flood risk report."""
        pages = ['title', 'executive_summary', 'portfolio_overview', 'risk_analysis', 'appendix']
        return self.generate_report(flood_data, output_filename, pages)

    def generate_detailed_report(self, flood_data: Dict[str, Any],
                                output_filename: Optional[str] = None) -> Path:
        """Generate detailed flood risk report with all pages."""
        pages = ['title', 'executive_summary', 'portfolio_overview', 'risk_analysis',
                'mortgage_analysis', 'property_details', 'appendix']
        return self.generate_report(flood_data, output_filename, pages)

    def generate_summary_report(self, flood_data: Dict[str, Any],
                               output_filename: Optional[str] = None) -> Path:
        """Generate summary-focused report."""
        pages = ['title', 'executive_summary', 'appendix']
        return self.generate_report(flood_data, output_filename, pages)

    def generate_analysis_report(self, flood_data: Dict[str, Any],
                                output_filename: Optional[str] = None) -> Path:
        """Generate analysis-focused report."""
        pages = ['title', 'risk_analysis', 'property_details', 'appendix']
        return self.generate_report(flood_data, output_filename, pages)


# Convenience function
def generate_risk_report(flood_data: Dict[str, Any],
                        output_dir: Optional[Union[str, Path]] = None,
                        report_type: str = "basic") -> Path:
    """
    Simple convenience function to generate a flood risk report.

    Args:
        flood_data: Flood risk analysis data
        output_dir: Output directory
        report_type: Type of report ('basic', 'detailed', 'summary', 'analysis')

    Returns:
        Path to generated PDF
    """
    generator = RiskReportGenerator(output_dir)

    if report_type == 'basic':
        return generator.generate_basic_report(flood_data)
    elif report_type == 'detailed':
        return generator.generate_detailed_report(flood_data)
    elif report_type == 'summary':
        return generator.generate_summary_report(flood_data)
    elif report_type == 'analysis':
        return generator.generate_analysis_report(flood_data)
    else:
        return generator.generate_report(flood_data)


if __name__ == "__main__":
    import json
    import sys

    from reports.shared.base_generator import build_report_cli, handle_info_requests

    def _add_risk_args(parser):
        parser.add_argument('--flood-file', required=True, help='Flood risk JSON file path')

    args = build_report_cli(
        description='Generate flood risk reports using modular page system.',
        report_type_choices=['basic', 'detailed', 'summary', 'analysis'],
        default_report_type='basic',
        extra_args_fn=_add_risk_args,
    )

    logging.basicConfig(level=logging.INFO)
    handle_info_requests(args, RiskReportGenerator())

    try:
        # Load data
        with open(args.flood_file) as f:
            flood_data = json.load(f)

        # Generate report
        generator = RiskReportGenerator(args.output_dir)

        if args.report_type == 'basic':
            report_path = generator.generate_basic_report(flood_data)
        elif args.report_type == 'detailed':
            report_path = generator.generate_detailed_report(flood_data)
        elif args.report_type == 'summary':
            report_path = generator.generate_summary_report(flood_data)
        elif args.report_type == 'analysis':
            report_path = generator.generate_analysis_report(flood_data)
        else:
            report_path = generator.generate_report(flood_data, pages_to_include=args.pages)

        logger.info("Flood risk report generated successfully!")
        logger.info(f"File: {report_path}")
        logger.info(f"Type: {args.report_type}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

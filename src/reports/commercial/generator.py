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

"""CommercialReportGenerator — orchestrates commercial page modules into a PDF."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from reportlab.lib import colors

from reports.shared import BaseReportGenerator

from .pages import (
    AccessibilityPage,
    CommercialAttributesPage,
    ConstructionPage,
    EnergyPage,
    HeaderPage,
    HistoryPage,
    CLoanOverviewPage,
    LocationPage,
    ProtectionPage,
    RiskAssessmentPage,
    TenancyPage,
    TitleOverviewPage,
    TransactionsPage,
    ValuationPage,
)

logger = logging.getLogger(__name__)


class CommercialReportGenerator(BaseReportGenerator):
    """Generates a full commercial-asset PDF report.

    Same orchestrator pattern as PropertyReportGenerator: a dict of
    named page instances + a categories dict picking which run for
    each report mode. Forwards ``commercial_data`` and ``cloan_data``
    kwargs to every page's ``generate_elements``; pages that don't
    care simply ignore the extras.
    """

    REPORT_TITLE = "Commercial Asset Report"
    HEADER_COLOR = colors.teal
    SUBTITLE_COLOR = colors.steelblue

    def _get_default_output_dir(self) -> Path:
        from config import config
        # Mirror the property-report convention but under data/output/commercial/.
        # Avoids stomping over data/output/property/ artefacts.
        return config.get_reports_dir("commercial")

    def _initialize_pages(self):
        self.pages = {
            # Commercial-asset pages (asset-shared sections come from reports.asset)
            "title_overview":  TitleOverviewPage(),
            "header":          HeaderPage(),
            "location":        LocationPage(),
            "attributes":      CommercialAttributesPage(),
            "accessibility":   AccessibilityPage(),
            "tenancy":         TenancyPage(),
            "construction":    ConstructionPage(),
            "valuation":       ValuationPage(),
            "risk_assessment": RiskAssessmentPage(),
            "energy":          EnergyPage(),
            "protection":      ProtectionPage(),
            "history":         HistoryPage(),
            "transactions":    TransactionsPage(),
            # Loan
            "loan_overview":   CLoanOverviewPage(),
        }
        self.categories = {
            "commercial": [
                "title_overview", "header", "location", "attributes",
                "accessibility", "tenancy", "construction", "valuation",
                "risk_assessment", "energy", "protection", "history",
                "transactions",
            ],
            "loan": ["loan_overview"],
        }

    def generate_report(
        self,
        commercial_data: Dict[str, Any],
        cloan_data: Optional[Dict[str, Any]] = None,
        pages_to_include: Optional[List[str]] = None,
        output_filename: Optional[str] = None,
    ) -> Path:
        """Generate a commercial report PDF.

        Args:
            commercial_data: A single commercial record (one element from
                ``commercial.json['commercial_assets']``).
            cloan_data: Optional commercial_loan record linked by PropertyID.
            pages_to_include: Specific pages, or None for auto.
            output_filename: Override filename, or None for auto.
        """
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(commercial_data, cloan_data)
        if output_filename is None:
            output_filename = self._generate_filename(commercial_data)

        output_path = self.output_dir / output_filename
        return self._build_pdf(
            output_path,
            pages_to_include,
            commercial_data=commercial_data,
            cloan_data=cloan_data,
        )

    def _auto_select_pages(
        self,
        commercial_data: Dict[str, Any],
        cloan_data: Optional[Dict[str, Any]],
    ) -> List[str]:
        pages = list(self.categories["commercial"])
        if cloan_data:
            pages.extend(self.categories["loan"])
        return pages

    def generate_cloan_focused_report(
        self,
        commercial_data: Dict[str, Any],
        cloan_data: Dict[str, Any],
        output_filename: Optional[str] = None,
    ) -> Path:
        """Generate a loan-focused PDF (title + location + loan overview).

        Same pages as the full commercial report's ``loan`` category
        plus a title page and location for context — equivalent to
        the residential ``generate_mortgage_focused_report`` mode on
        PropertyReportGenerator. Output filename is prefixed
        ``commercial_loan_report_…`` so it doesn't collide with the
        full commercial-report file.
        """
        pages = ["title_overview", "location", "loan_overview"]
        if output_filename is None:
            output_filename = self._generate_filename(
                commercial_data, kind="loan_report",
            )
        output_path = self.output_dir / output_filename
        return self._build_pdf(
            output_path,
            pages,
            commercial_data=commercial_data,
            cloan_data=cloan_data,
        )

    def _generate_filename(
        self,
        commercial_data: Dict[str, Any],
        kind: str = "report",
    ) -> str:
        try:
            pid = commercial_data["CommercialAsset"]["Header"]["PropertyID"]
        except (KeyError, TypeError):
            pid = "unknown"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "commercial_loan_report" if kind == "loan_report" else "commercial_report"
        return f"{prefix}_{pid}_{ts}.pdf"

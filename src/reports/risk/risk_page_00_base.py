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
Base class for all flood risk report pages.
Provides common functionality, styles, and utilities for flood risk reports.
"""

from abc import abstractmethod
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

from reports.shared import ReportBasePage


class RiskBasePage(ReportBasePage):
    """Base class for all flood risk report page generators."""

    ABBREVIATIONS = {
        'Id': 'ID', 'Pdf': 'PDF', 'Api': 'API',
        'Uk': 'UK', 'Sqm': 'sqm'
    }

    def _setup_styles(self):
        """Set up paragraph styles including risk level styles."""
        super()._setup_styles()

        if 'HighRisk' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='HighRisk',
                parent=self.styles['Normal'],
                textColor=colors.red,
                fontSize=12,
                leftIndent=20
            ))

        if 'MediumRisk' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='MediumRisk',
                parent=self.styles['Normal'],
                textColor=colors.orange,
                fontSize=12,
                leftIndent=20
            ))

        if 'LowRisk' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='LowRisk',
                parent=self.styles['Normal'],
                textColor=colors.green,
                fontSize=12,
                leftIndent=20
            ))

    def _setup_table_styles(self):
        """Set up table styles for flood risk content types."""
        super()._setup_table_styles()
        self.table_styles['risk_summary'] = self._make_table_style(
            colors.darkred, colors.darkred, colors.mistyrose
        )
        self.table_styles['property'] = self._make_table_style(
            colors.darkgreen, colors.darkgreen, colors.lightgreen
        )

    def _setup_dimensions(self):
        """Set up dimensions including five-column layout."""
        super()._setup_dimensions()
        self.table_widths['five_col'] = [
            1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch
        ]

    def _format_percentage(self, value: Any) -> str:
        """Format percentage values with 1 decimal place."""
        return super()._format_percentage(value, decimals=1)

    def _format_depth(self, value: Any) -> str:
        """Format flood depth values."""
        if isinstance(value, (int, float)):
            return f"{value:.2f}m"
        return self._format_value(value)

    @abstractmethod
    def generate_elements(self, flood_data: Dict[str, Any]) -> List:
        """Generate page elements. Must be implemented by subclasses."""
        pass

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


# src/utilities/gauge_base_page.py

"""
Base class for all gauge report pages.
Provides common functionality, styles, and utilities for gauge reports.
"""

from abc import abstractmethod
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.units import inch

from reports.shared import ReportBasePage


class GaugeBasePage(ReportBasePage):
    """Base class for all gauge report page generators."""

    ABBREVIATIONS = {
        'Gauge': 'Gauge', 'Id': 'ID', 'Gps': 'GPS', 'Api': 'API',
        'Uk': 'UK', 'Usrn': 'USRN', 'Sqm': 'sqm', 'Ea': 'EA',
        'Metres': 'Metres', 'Meters': 'Meters'
    }

    def _setup_table_styles(self):
        """Set up table styles for gauge content types."""
        super()._setup_table_styles()
        self.table_styles['flood_risk'] = self._make_table_style(
            colors.darkred, colors.darkred, colors.mistyrose
        )
        self.table_styles['sensor'] = self._make_table_style(
            colors.darkgreen, colors.darkgreen, colors.mintcream
        )
        self.table_styles['measurement'] = self._make_table_style(
            colors.orange, colors.orange, colors.papayawhip
        )
        self.table_styles['historical'] = self._make_table_style(
            colors.purple, colors.purple, colors.lavender
        )
        self.table_styles['location'] = self._make_table_style(
            colors.brown, colors.brown, colors.wheat
        )

    def _setup_dimensions(self):
        """Set up dimensions including gauge table layout."""
        super()._setup_dimensions()
        self.table_widths['gauge_table'] = [
            2.8 * inch, 2.8 * inch, 1.4 * inch, 0.9 * inch
        ]

    def _format_measurement(self, value: Any, unit: str = 'm') -> str:
        """Format measurement values with units."""
        if isinstance(value, (int, float)):
            return f"{value:.3f} {unit}"
        return self._format_value(value)

    def _format_coordinate(self, value: Any) -> str:
        """Format coordinate values."""
        if isinstance(value, (int, float)):
            return f"{value:.6f}"
        return self._format_value(value)

    def _format_frequency(self, value: Any) -> str:
        """Format frequency values."""
        if isinstance(value, (int, float)) and value > 0:
            return f"{value} times"
        elif isinstance(value, (int, float)) and value == 0:
            return "Never"
        return self._format_value(value)

    @abstractmethod
    def generate_elements(self, gauge_data: Dict[str, Any],
                         timeseries_data: Dict[str, Any] = None) -> List:
        """Generate page elements. Must be implemented by subclasses."""
        pass

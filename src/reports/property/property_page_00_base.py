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

"""
Base class for all property report pages.
Provides common functionality, styles, and utilities.
"""

from abc import abstractmethod
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

from reports.shared import ReportBasePage


class PropertyBasePage(ReportBasePage):
    """Base class for all property report page generators."""

    ABBREVIATIONS = {
        'Gbp': 'GBP', 'Kwh': 'kWh', 'Epc': 'EPC', 'Co2e': 'CO2e',
        'Sqm': 'sqm', 'Uprn': 'UPRN', 'Usrn': 'USRN', 'Ea': 'EA',
        'Ltv': 'LTV', 'Dti': 'DTI', 'Id': 'ID'
    }

    def _setup_styles(self):
        """Set up paragraph styles with property-specific title colours."""
        super()._setup_styles()
        # Property uses navy/darkblue instead of darkblue/blue for Title/SubTitle
        self.styles['Title'].textColor = colors.navy
        self.styles['SubTitle'].textColor = colors.darkblue

        # TableHeader — used inside Paragraph cells of styled tables
        # (page_13 risk analysis + page_07 recommendation table). The style
        # itself doesn't paint the table-header *background* (that's the
        # TableStyle's BACKGROUND directive); it just provides the bold
        # white text used for individual header cells.
        if 'TableHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='TableHeader',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.white,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
            ))

    def _setup_table_styles(self):
        """Set up table styles for property content types."""
        super()._setup_table_styles()
        # Property 'standard' uses navy header and whitesmoke rows
        self.table_styles['standard'] = self._make_table_style(
            colors.navy, colors.black, colors.whitesmoke
        )
        self.table_styles['risk'] = self._make_table_style(
            colors.darkred, colors.darkred, colors.mistyrose
        )
        self.table_styles['financial'] = self._make_table_style(
            colors.darkgreen, colors.darkgreen, colors.mintcream
        )
        self.table_styles['energy'] = self._make_table_style(
            colors.orange, colors.orange, colors.papayawhip
        )
        self.table_styles['protection'] = self._make_table_style(
            colors.purple, colors.purple, colors.lavender
        )
        self.table_styles['history'] = self._make_table_style(
            colors.brown, colors.brown, colors.wheat
        )

    def _setup_dimensions(self):
        """Set up dimensions including risk table layout."""
        super()._setup_dimensions()
        self.table_widths['risk_table'] = [
            2.0 * inch, 0.9 * inch, 0.7 * inch, 3.9 * inch
        ]

    def _emit_or_fallback(
        self,
        section,
        section_title: str,
        render_fn,
        empty_message: str,
    ) -> List:
        """Render `section` via ``render_fn`` or emit a placeholder message.

        Used by the residential property page wrappers that delegate to
        ``reports.asset.render_*`` — when the section dict is empty/missing
        the shared renderer has no fallback string to emit, so wrappers
        provide one here. Returns the same flowable shape as the renderer.
        """
        from reportlab.platypus import Paragraph
        if not section:
            return [
                Paragraph(section_title, self.styles["SectionHeader"]),
                Paragraph(empty_message, self.styles["Normal"]),
            ]
        return render_fn(section, self)

    @abstractmethod
    def generate_elements(self, property_data: Dict[str, Any],
                         rloan_data: Dict[str, Any] = None) -> List:
        """Generate page elements. Must be implemented by subclasses."""
        pass

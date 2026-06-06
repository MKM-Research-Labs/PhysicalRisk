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

# src/utilities/gauge_page_07_data_summary.py

"""Two-column data-table builder mixin for the gauge data summary page."""

from typing import Callable, List, Optional

from reportlab.platypus import Spacer, Table


class _DataTableMixin:
    """Provides ``_add_data_table`` (mixed into GaugeDataSummaryPage)."""

    def _add_data_table(
        self,
        elements: List,
        headers: List[str],
        fields: List[tuple],
        style_key: str = 'standard',
        col_widths: Optional[List[float]] = None,
        value_formatter: Optional[Callable] = None,
    ) -> None:
        """Build a two-column data table and append it to *elements*.

        Parameters
        ----------
        elements:
            The list to which the Table and trailing Spacer are appended.
        headers:
            Column header strings, e.g. ``["Parameter", "Value"]``.
        fields:
            Sequence of ``(raw_value, label)`` pairs.  Rows where
            *raw_value* is ``None`` are silently skipped.
        style_key:
            Key into ``self.table_styles`` (default ``'standard'``).
        col_widths:
            Explicit column widths; falls back to ``self.table_widths['two_col']``.
        value_formatter:
            Optional ``(value, label) -> str`` callable.  When *None* the
            default ``self._format_value`` is used.
        """
        data = [headers]
        for raw_value, label in fields:
            if raw_value is None:
                continue
            if value_formatter is not None:
                formatted = value_formatter(raw_value, label)
            else:
                formatted = self._format_value(raw_value)
            data.append([label, formatted])

        if len(data) <= 1:
            # Nothing beyond the header row — skip the table entirely.
            return

        widths = col_widths or self.table_widths['two_col']
        tbl = Table(data, colWidths=widths)
        tbl.setStyle(self.table_styles[style_key])
        elements.append(tbl)
        elements.append(Spacer(1, self.spacing['table_bottom']))

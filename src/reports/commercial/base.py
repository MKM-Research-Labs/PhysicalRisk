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

"""CommercialBasePage — adds commercial-themed table styles."""

from reportlab.lib import colors

from reports.asset import AssetBasePage


class CommercialBasePage(AssetBasePage):
    """Base class for commercial-specific report pages.

    Extends AssetBasePage with two commercial-only table styles
    (``tenancy`` for lease / yield data, ``accessibility`` for
    accessibility-features grid) so the commercial report has a
    distinct visual identity from the residential one.
    """

    def _setup_styles(self):
        super()._setup_styles()
        # Commercial palette: teal title / steelblue subtitle to
        # distinguish from property's navy/darkblue.
        self.styles["Title"].textColor = colors.teal
        self.styles["SubTitle"].textColor = colors.steelblue

    def _setup_table_styles(self):
        super()._setup_table_styles()
        self.table_styles["tenancy"] = self._make_table_style(
            colors.teal, colors.teal, colors.lightcyan
        )
        self.table_styles["accessibility"] = self._make_table_style(
            colors.darkslategray, colors.darkslategray, colors.lightgrey
        )

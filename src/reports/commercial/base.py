# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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

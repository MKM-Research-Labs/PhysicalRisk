# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""AssetBasePage — shared base for residential + commercial report pages.

Sits between ``reports.shared.ReportBasePage`` (raw ReportLab primitives)
and the asset-type-specific bases (PropertyBasePage / CommercialBasePage).
Adds the table styles and abbreviations that are common to any asset
report — currency, area, energy, risk, financial, protection, history.

Subclasses can override colours/abbreviations to skin their report but
won't need to redefine the underlying TableStyle structure.
"""

from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.units import inch

from reports.shared import ReportBasePage


class AssetBasePage(ReportBasePage):
    """Common base for any per-asset (residential or commercial) page."""

    ABBREVIATIONS: Dict[str, str] = {
        # currency / units
        'Gbp': 'GBP', 'Usd': 'USD', 'Eur': 'EUR', 'Vnd': 'VND',
        'Kwh': 'kWh', 'Co2e': 'CO2e', 'Sqm': 'sqm', 'Pga': 'PGA',
        # ids / authorities
        'Uprn': 'UPRN', 'Usrn': 'USRN', 'Ea': 'EA', 'Epc': 'EPC',
        'Bri': 'BRI', 'Id': 'ID', 'Vs30': 'Vs30', 'Mps': 'm/s',
        # loan terms
        'Ltv': 'LTV', 'Dti': 'DTI',
        # commercial-specific
        'Uko': 'UKO', 'Wault': 'WAULT',
    }

    def _setup_table_styles(self):
        """Add per-asset table styles on top of the shared 'standard'."""
        super()._setup_table_styles()
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
        super()._setup_dimensions()
        self.table_widths['risk_table'] = [
            2.0 * inch, 0.9 * inch, 0.7 * inch, 3.9 * inch
        ]

    def generate_elements(self, *args: Any, **kwargs: Any) -> List:
        """Default no-op; concrete page subclasses override."""
        return []

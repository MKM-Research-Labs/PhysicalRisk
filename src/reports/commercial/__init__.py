# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial asset PDF report.

Mirrors the property report shape but:
  - reads CommercialAsset.* (CDM root differs from PropertyHeader.* used
    by the residential CDM);
  - replaces residential-only sections (PropertyAttributes, Contents)
    with commercial-only sections (CommercialAttributes,
    AccessibilityFeatures, Tenancy);
  - reads the commercial_loan.json sibling rather than mortgage.json;
  - shares all other section renderers via ``reports.asset``.
"""

from .commercial_report import generate_commercial_report, generate_cloan_report
from .generator import CommercialReportGenerator

__all__ = [
    "CommercialReportGenerator",
    "generate_commercial_report",
    "generate_cloan_report",
]

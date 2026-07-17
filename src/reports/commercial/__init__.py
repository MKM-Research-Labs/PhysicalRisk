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

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

"""
Hazard curve package for Physical Risk Swap (PRS) pricing.

Provides:
- GEV distribution fitting to peak water levels
- Gauge response modelling (storm → water level)
- Hazard curve construction with term structures
- QuantLib credit curve pricing integration

Usage:
    from models.hazard import HazardCurveBuilder, GEVFitter
    from models.hazard import build_hazard_curves
    from models.hazard.pricing import hazard_points_to_credit_curve  # requires QuantLib
"""

from .builder import HazardCurveBuilder
from .data_structures import (
    GaugeHazardCurve,
    GaugeResponse,
    HazardCurvePoint,
    TermStructurePoint,
)
from .gev import GEVFitter, compute_term_structure
from .io import (
    build_hazard_curves,
    load_gauges,
    load_storms,
    load_storms_from_sequences,
    save_gauge_storm_responses,
    save_hazard_curves,
)
from .response_model import GaugeResponseModel

# NOTE: models.hazard.pricing is intentionally NOT imported here.
# pricing.py has `import QuantLib as ql` at module level and requires
# QuantLib to be installed.  Eagerly importing it would prevent the rest
# of the hazard package (GEV fitting, curve building, I/O) from being used
# in environments where QuantLib is absent.
# Import directly: `from models.hazard.pricing import hazard_points_to_credit_curve`

__all__ = [
    # Data structures
    "GaugeResponse",
    "HazardCurvePoint",
    "TermStructurePoint",
    "GaugeHazardCurve",
    # Model components
    "GaugeResponseModel",
    "GEVFitter",
    "compute_term_structure",
    "HazardCurveBuilder",
    # I/O
    "load_storms",
    "load_storms_from_sequences",
    "load_gauges",
    "save_hazard_curves",
    "save_gauge_storm_responses",
    "build_hazard_curves",
]

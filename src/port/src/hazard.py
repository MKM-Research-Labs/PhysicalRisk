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
Re-export shim — hazard code has moved to models.hazard package.
"""

from models.hazard import (
    GaugeHazardCurve,
    GaugeResponse,
    GaugeResponseModel,
    GEVFitter,
    HazardCurveBuilder,
    HazardCurvePoint,
    TermStructurePoint,
    build_hazard_curves,
    compute_term_structure,
    load_gauges,
    load_storms,
    load_storms_from_sequences,
    save_gauge_storm_responses,
    save_hazard_curves,
)

__all__ = [
    "GaugeResponse",
    "HazardCurvePoint",
    "TermStructurePoint",
    "GaugeHazardCurve",
    "GaugeResponseModel",
    "GEVFitter",
    "compute_term_structure",
    "HazardCurveBuilder",
    "load_storms",
    "load_storms_from_sequences",
    "load_gauges",
    "save_hazard_curves",
    "save_gauge_storm_responses",
    "build_hazard_curves",
]

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
Model A — Occurrence and fault-geometry spatial draw (MKM-SEIS-001).

A homogeneous Poisson process produces per-scenario earthquakes with
``lambda_i = lambda_zone * m_fault * m_soil``. For each instantiated event the
magnitude is drawn from the truncated Gutenberg-Richter law, the rupture
centroid is sampled by arc-length along the catchment fault trace, the surface
rupture length follows Wells-Coppersmith scaling, and the Joyner-Boore distance
R_JB is computed against the rupture segment with the flood module's polyline
primitive.

The package is split into:
- ``_fault``    — fault-trace loading (Appendix B) and rupture geometry
- ``_rates``    — zone / site-class resolution, lambda_i, magnitude sampling
- ``_simulate`` — the per-asset and portfolio orchestrators
"""

from models.seismic.occurrence._fault import (
    FAULT_TRACE_FILENAME,
    Coord,
    cumulative_arclengths,
    fault_trace_path,
    joyner_boore_distance_km,
    load_fault_trace,
    parse_fault_trace,
)
from models.seismic.occurrence._rates import (
    asset_fault_distance_km,
    asset_lambda,
    fault_proximity_modifier,
    resolve_site_class,
    resolve_zone,
    sample_magnitude,
)
from models.seismic.occurrence._simulate import (
    simulate_asset_occurrence,
    simulate_portfolio_occurrence,
)

__all__ = [
    "FAULT_TRACE_FILENAME",
    "Coord",
    "parse_fault_trace",
    "load_fault_trace",
    "fault_trace_path",
    "cumulative_arclengths",
    "joyner_boore_distance_km",
    "resolve_zone",
    "resolve_site_class",
    "asset_fault_distance_km",
    "fault_proximity_modifier",
    "asset_lambda",
    "sample_magnitude",
    "simulate_asset_occurrence",
    "simulate_portfolio_occurrence",
]

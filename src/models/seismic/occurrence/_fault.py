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

"""Fault-trace loading and geometry (Model A — spatial sub-layer).

The fault trace is a per-catchment polyline stored beside the river polyline
under data/catch/<catchment>/. On disk it is ``[[lon, lat], ...]`` (Appendix B),
identical to the storm river-centreline files; the flood spatial primitives
expect ``(lat, lon)``, so the pair order is flipped on load. The rupture
sub-segment extraction and Joyner-Boore distance reuse the same flat-Earth
polyline primitive the flood module uses for river-bank distance.
"""

import json
from pathlib import Path
from typing import List, Tuple

from models.floodrisk.spatial import haversine_distance, nearest_point_on_polyline

# Per-catchment fault polyline filename (see Appendix B for the format).
FAULT_TRACE_FILENAME = "fault_trace.json"

Coord = Tuple[float, float]  # (lat, lon)


# ===========================================================================
# Loading (Appendix B)
# ===========================================================================


def parse_fault_trace(raw: list) -> List[Coord]:
    """Parse a [[lon, lat], ...] array into ordered ``(lat, lon)`` vertices."""
    fault: List[Coord] = []
    for pair in raw:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            raise ValueError(f"fault trace vertex must be [lon, lat]: {pair!r}")
        lon, lat = float(pair[0]), float(pair[1])
        fault.append((lat, lon))
    if len(fault) < 2:
        raise ValueError("fault trace needs at least two vertices")
    return fault


def load_fault_trace(path: Path) -> List[Coord]:
    """Load a fault-trace polyline from a JSON file (see :func:`parse_fault_trace`)."""
    return parse_fault_trace(json.loads(Path(path).read_text()))


def fault_trace_path(catchment_dir: Path) -> Path:
    """The conventional fault-trace path for a catchment input directory."""
    return Path(catchment_dir) / FAULT_TRACE_FILENAME


# ===========================================================================
# Geometry
# ===========================================================================


def cumulative_arclengths(fault: List[Coord]) -> List[float]:
    """Cumulative arc-length (km) at each vertex, starting at 0.0."""
    cum = [0.0]
    for (lat0, lon0), (lat1, lon1) in zip(fault, fault[1:]):
        cum.append(cum[-1] + haversine_distance(lat0, lon0, lat1, lon1) / 1000.0)
    return cum


def locate(cum: List[float], s: float) -> Tuple[int, float]:
    """Return ``(segment_index, fraction)`` for arc-length *s* along the trace."""
    for i in range(len(cum) - 1):
        if s <= cum[i + 1]:
            seg = cum[i + 1] - cum[i]
            return i, (0.0 if seg <= 0.0 else (s - cum[i]) / seg)
    return len(cum) - 2, 1.0


def point_at(fault: List[Coord], cum: List[float], s: float) -> Coord:
    """Interpolate the ``(lat, lon)`` point at arc-length *s* along the trace."""
    i, frac = locate(cum, s)
    (lat0, lon0), (lat1, lon1) = fault[i], fault[i + 1]
    return (lat0 + frac * (lat1 - lat0), lon0 + frac * (lon1 - lon0))


def rupture_segment(
    fault: List[Coord], cum: List[float], s0: float, s1: float,
) -> List[Coord]:
    """The sub-polyline of the fault between arc-lengths s0 and s1 (clipped)."""
    total = cum[-1]
    s0 = max(0.0, min(s0, total))
    s1 = max(0.0, min(s1, total))
    i0, _ = locate(cum, s0)
    i1, _ = locate(cum, s1)
    segment = [point_at(fault, cum, s0)]
    segment.extend(fault[k] for k in range(i0 + 1, i1 + 1))
    segment.append(point_at(fault, cum, s1))
    return segment


def joyner_boore_distance_km(lat: float, lon: float, segment: List[Coord]) -> float:
    """Minimum distance (km) from ``(lat, lon)`` to the rupture *segment*."""
    if len(segment) == 1:
        return haversine_distance(lat, lon, segment[0][0], segment[0][1]) / 1000.0
    return nearest_point_on_polyline(lat, lon, segment)[2] / 1000.0

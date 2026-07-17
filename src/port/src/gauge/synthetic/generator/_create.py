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

"""Polyline construction, single-gauge placement, and dedup checks."""

from typing import Dict, List, Optional, Tuple

from config import config
from config.port import SYNTH_DEDUP_DISTANCE_M as DEDUP_DISTANCE_M
from models.floodrisk.spatial import haversine_distance

from ..geometry import _snap_to_river, _lerp
from ._ids import SYNTH_PREFIX, _synth_gauge_id


class _CreateMixin:
    """Build the gauge polyline and create/dedup individual synthetic gauges."""

    def _build_gauge_polyline(self, gauge_lookup: Dict) -> List[Tuple]:
        """
        Build ordered gauge polyline from catchment GAUGE_POINTS.

        Returns list of (lat, lon, elevation, gauge_id) tuples.
        """
        params = config.load_params_module()
        gauge_points = getattr(params, "GAUGE_POINTS",
                               getattr(params, "GAUGEPOINTS", None))
        if not gauge_points or len(gauge_points) < 2:
            return []

        polyline = []
        for pt in gauge_points:
            pt_lat, pt_lon = pt[0], pt[1]
            pt_elev = pt[2] if len(pt) > 2 else 0.0

            best_gid = None
            best_dist = float("inf")
            for gid, ginfo in gauge_lookup.items():
                if gid.startswith(SYNTH_PREFIX):
                    continue
                d = haversine_distance(pt_lat, pt_lon, ginfo["lat"], ginfo["lon"])
                if d < best_dist:
                    best_dist = d
                    best_gid = gid

            if best_gid is not None and best_dist < 500:
                polyline.append((pt_lat, pt_lon, pt_elev, best_gid))

        return polyline

    def _create_synthetic_at_position(
        self,
        seg_idx: int,
        t: float,
        gauge_lookup: Dict,
        polyline: List[Tuple],
    ) -> Optional[Tuple[Dict, str]]:
        """
        Create a synthetic gauge at a specific position on the polyline.

        Args:
            seg_idx: Segment index on the polyline.
            t: Parameter along the segment (0.0–1.0).
            gauge_lookup: Real gauge properties lookup.
            polyline: Ordered (lat, lon, elev, gauge_id) tuples.

        Returns:
            (gauge_cdm_dict, gauge_id) or None if flanking gauges missing.
        """
        # Interpolate position on the coarse polyline
        a = polyline[seg_idx]
        b = polyline[seg_idx + 1]
        nx = _lerp(a[0], b[0], t)
        ny = _lerp(a[1], b[1], t)

        # Snap to high-resolution river polyline
        nx, ny = _snap_to_river(nx, ny)

        ga_id = a[3]
        gb_id = b[3]
        ga = gauge_lookup.get(ga_id)
        gb = gauge_lookup.get(gb_id)
        if ga is None or gb is None:
            return None

        alpha = t
        synth_id = _synth_gauge_id(ga_id, gb_id, alpha)

        # Interpolate properties from flanking real gauges
        elev = round(_lerp(ga["elevation"], gb["elevation"], alpha), 2)
        alert = round(_lerp(ga["flood_alert"], gb["flood_alert"], alpha), 2)
        warning = round(_lerp(ga["flood_warning"], gb["flood_warning"], alpha), 2)
        severe = round(_lerp(ga["severe_flood_warning"], gb["severe_flood_warning"], alpha), 2)
        hist_high = round(_lerp(ga["historical_high_level"], gb["historical_high_level"], alpha), 2)

        # Build CDM structure matching real gauges
        gauge_cdm = {
            "FloodGauge": {
                "Header": {
                    "GaugeID": synth_id,
                    "CatchmentID": config.CATCHMENT,
                    "GaugeName": f"Synthetic {ga_id[-8:]}-{gb_id[-8:]}",
                },
                "SensorStats": {
                    "HistoricalHighLevel": hist_high,
                    "HistoricalHighDate": ga.get("historical_high_date", ""),
                },
                "SensorDetails": {
                    "GaugeInformation": {
                        "DataSourceType": "Synthetic",
                        "GaugeOwner": "MKM Research Labs",
                        "GaugeType": "Synthetic interpolation",
                        "OperationalStatus": "Fully operational",
                        "GaugeLatitude": round(nx, 6),
                        "GaugeLongitude": round(ny, 6),
                        "GroundLevelMeters": elev,
                        "elevation": elev,
                        "TidalInfluence": "Non-tidal",
                    },
                },
                "FloodStage": {
                    "UK": {
                        "FloodAlert": alert,
                        "FloodWarning": warning,
                        "SevereFloodWarning": severe,
                    },
                },
                "Location": {
                    "GaugeLatitude": round(nx, 6),
                    "GaugeLongitude": round(ny, 6),
                    "GaugeElevation": elev,
                },
            }
        }

        return gauge_cdm, synth_id

    def _is_duplicate(self, candidate: Dict, existing: List[Dict]) -> bool:
        """Check if a synthetic gauge is within DEDUP_DISTANCE_M of any existing one."""
        c_loc = candidate["FloodGauge"]["Location"]
        c_lat = c_loc["GaugeLatitude"]
        c_lon = c_loc["GaugeLongitude"]

        for eg in existing:
            e_loc = eg["FloodGauge"]["Location"]
            d = haversine_distance(
                c_lat, c_lon,
                e_loc["GaugeLatitude"], e_loc["GaugeLongitude"])
            if d < DEDUP_DISTANCE_M:
                return True
        return False

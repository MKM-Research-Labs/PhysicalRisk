# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Synthetic gauge generator — creates virtual gauges on the river
centreline at the nearest point to each property.

Run as port step 2.5 (after properties, before gaugehd/stressm).
Synthetic gauges are appended to gauge.json so they flow through
stressm, gaugehc, and propertyts as first-class entities.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import config
from models.floodrisk.spatial import (
    haversine_distance,
    nearest_point_on_polyline,
)

logger = logging.getLogger(__name__)

SYNTH_PREFIX = "SYNTH"
DEDUP_DISTANCE_M = 50  # merge synthetic gauges within this distance


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation: a*(1-t) + b*t."""
    return a * (1 - t) + b * t


def _synth_gauge_id(ga_id: str, gb_id: str, alpha: float) -> str:
    """Deterministic synthetic gauge ID from flanking IDs + alpha."""
    key = f"{ga_id}:{gb_id}:{alpha:.3f}"
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    return f"{SYNTH_PREFIX}-{h}"


class SyntheticGaugeGenerator:
    """
    Creates one synthetic gauge per property on the river centreline.

    For each property, projects its location onto the gauge-point polyline,
    identifies the two flanking real gauges, and interpolates gauge
    properties (location, elevation, flood stages) using the segment
    parameter alpha.

    Nearby synthetic gauges (within DEDUP_DISTANCE_M) are merged so
    multiple properties near the same river point share one gauge.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()

    def generate(self) -> Dict:
        """
        Generate synthetic gauges and append to gauge.json.

        Returns:
            Dict with 'count' and 'gauge_ids' of created synthetic gauges.
        """
        gauge_path = self.output_dir / "gauge.json"
        property_path = self.output_dir / "property.json"

        if not gauge_path.exists():
            logger.warning("gauge.json not found — skipping synthetic gauges")
            return {"count": 0, "gauge_ids": []}
        if not property_path.exists():
            logger.warning("property.json not found — skipping synthetic gauges")
            return {"count": 0, "gauge_ids": []}

        # Load existing gauges
        with open(gauge_path) as f:
            gauge_data = json.load(f)
        gauges = gauge_data.get("flood_gauges", [])

        # Build gauge lookup {gauge_id: {lat, lon, elevation, ...}}
        gauge_lookup = {}
        for g in gauges:
            fg = g.get("FloodGauge", {})
            hdr = fg.get("Header", {})
            loc = fg.get("Location", {})
            sensor = fg.get("SensorDetails", {}).get("GaugeInformation", {})
            stages = fg.get("FloodStage", {}).get("UK", fg.get("FloodStages", {}))
            gid = hdr.get("GaugeID", "")
            gauge_lookup[gid] = {
                "lat": loc.get("GaugeLatitude", sensor.get("GaugeLatitude", 0)),
                "lon": loc.get("GaugeLongitude", sensor.get("GaugeLongitude", 0)),
                "elevation": loc.get("GaugeElevation", sensor.get("GroundLevelMeters", 0)),
                "flood_alert": stages.get("FloodAlert", 0),
                "flood_warning": stages.get("FloodWarning", 0),
                "severe_flood_warning": stages.get("SevereFloodWarning", 0),
                "historical_high_level": stages.get("HistoricalHighLevel", 0),
                "historical_high_date": stages.get("HistoricalHighDate", ""),
            }

        # Build ordered gauge polyline from catchment GAUGE_POINTS
        polyline = self._build_gauge_polyline(gauge_lookup)
        if len(polyline) < 2:
            logger.warning("Gauge polyline has < 2 points — skipping synthetic gauges")
            return {"count": 0, "gauge_ids": []}

        # Load properties
        with open(property_path) as f:
            prop_data = json.load(f)
        properties = prop_data.get("properties", [])

        # Create synthetic gauges for each property
        synth_gauges: List[Dict] = []
        synth_ids: List[str] = []

        for prop in properties:
            ph = prop.get("PropertyHeader", {})
            loc = ph.get("Location", {})
            prop_lat = loc.get("LatitudeDegrees", 0)
            prop_lon = loc.get("LongitudeDegrees", 0)

            if prop_lat == 0 or prop_lon == 0:
                continue

            result = self._create_synthetic_gauge(
                prop_lat, prop_lon, gauge_lookup, polyline)
            if result is None:
                continue

            synth_cdm, synth_id = result

            # Dedup: check if a nearby synthetic gauge already exists
            if self._is_duplicate(synth_cdm, synth_gauges):
                continue

            synth_gauges.append(synth_cdm)
            synth_ids.append(synth_id)

        # Append to gauge.json
        if synth_gauges:
            gauge_data["flood_gauges"].extend(synth_gauges)
            with open(gauge_path, "w") as f:
                json.dump(gauge_data, f, indent=2)
            logger.info("Appended %d synthetic gauges to gauge.json", len(synth_gauges))

        return {"count": len(synth_gauges), "gauge_ids": synth_ids}

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

    def _create_synthetic_gauge(
        self,
        prop_lat: float,
        prop_lon: float,
        gauge_lookup: Dict,
        polyline: List[Tuple],
    ) -> Optional[Tuple[Dict, str]]:
        """
        Create a synthetic gauge CDM dict at the nearest river point.

        Returns (gauge_cdm_dict, gauge_id) or None if at polyline edge.
        """
        nx, ny, dist_m, seg_idx, t = nearest_point_on_polyline(
            prop_lat, prop_lon, polyline)

        # Skip if projection clamps to polyline endpoints
        if seg_idx == 0 and t < 1e-6:
            return None
        if seg_idx == len(polyline) - 2 and t > 1 - 1e-6:
            return None

        ga_id = polyline[seg_idx][3]
        gb_id = polyline[seg_idx + 1][3]
        ga = gauge_lookup.get(ga_id)
        gb = gauge_lookup.get(gb_id)
        if ga is None or gb is None:
            return None

        alpha = t
        synth_id = _synth_gauge_id(ga_id, gb_id, alpha)

        # Interpolate properties
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

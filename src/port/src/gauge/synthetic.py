# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Synthetic gauge generator — creates virtual gauges at random positions
along the river centreline.

Run as port step 2 (after real gauges, before properties).
Properties are then placed relative to their assigned synthetic gauge.
Synthetic gauges are appended to gauge.json so they flow through
stressm, gaugehc, and propertyts as first-class entities.
"""

import hashlib
import json
import logging
import math
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import config
from models.floodrisk.spatial import (
    haversine_distance,
    nearest_point_on_polyline,
)

logger = logging.getLogger(__name__)

from config.port import SYNTH_DEDUP_DISTANCE_M as DEDUP_DISTANCE_M

SYNTH_PREFIX = "SYNTH"
_RIVER_POLYLINE_CACHE = None  # cached high-res river polyline


def _load_river_polyline() -> Optional[List[Tuple]]:
    """Load high-resolution river polyline from cached JSON.

    Falls back to None if the cache file doesn't exist, in which case
    synthetic gauges use the coarser gauge-point polyline coordinates.
    """
    global _RIVER_POLYLINE_CACHE
    if _RIVER_POLYLINE_CACHE is not None:
        return _RIVER_POLYLINE_CACHE

    cache_path = Path(__file__).resolve().parents[4] / "data" / "catch" / (
        f"{config.CATCHMENT}_river_polyline.json"
    )
    if not cache_path.exists():
        logger.info("No river polyline cache at %s — using gauge points", cache_path)
        return None

    with open(cache_path) as f:
        points = json.load(f)
    _RIVER_POLYLINE_CACHE = [(p[0], p[1]) for p in points]
    logger.info("Loaded river polyline: %d points from %s",
                len(_RIVER_POLYLINE_CACHE), cache_path.name)
    return _RIVER_POLYLINE_CACHE


def _snap_to_river(lat: float, lon: float) -> Tuple[float, float]:
    """Snap coordinates to the high-resolution river polyline.

    Returns the snapped (lat, lon) or the original coordinates if
    no river polyline is available.
    """
    river = _load_river_polyline()
    if river is None or len(river) < 2:
        return lat, lon

    best_lat, best_lon = lat, lon
    best_dist = float("inf")

    for i in range(len(river) - 1):
        ax, ay = river[i]
        bx, by = river[i + 1]

        # Project point onto segment (locally scaled Cartesian)
        cos_lat = math.cos(math.radians(lat))
        dx = bx - ax
        dy = (by - ay) * cos_lat
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq < 1e-18:
            continue

        t = ((lat - ax) * dx + (lon - ay) * cos_lat * dy) / seg_len_sq
        t = max(0.0, min(1.0, t))
        nx = ax + t * (bx - ax)
        ny = ay + t * (by - ay)

        d = haversine_distance(lat, lon, nx, ny)
        if d < best_dist:
            best_dist = d
            best_lat = nx
            best_lon = ny

    return round(best_lat, 6), round(best_lon, 6)


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
    Creates synthetic gauges at random positions along the river centreline.

    Each synthetic gauge is placed by:
    1. Picking a random segment on the gauge polyline (weighted by length)
    2. Picking a random position along that segment
    3. Interpolating elevation and flood stages from flanking real gauges
    4. Snapping to the high-resolution river polyline

    Properties are subsequently placed relative to these synthetic gauges
    in the property generator (step 3).
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()

    def generate(self, count: int = 200) -> Dict:
        """
        Generate synthetic gauges and append to gauge.json.

        Args:
            count: Number of synthetic gauges to create (default 200,
                   typically one per property).

        Returns:
            Dict with 'count' and 'gauge_ids' of created synthetic gauges.
        """
        gauge_path = self.output_dir / "gauge.json"

        if not gauge_path.exists():
            logger.warning("gauge.json not found — skipping synthetic gauges")
            return {"count": 0, "gauge_ids": []}

        # Load existing gauges
        with open(gauge_path) as f:
            gauge_data = json.load(f)
        gauges = gauge_data.get("flood_gauges", [])

        # Remove any existing synthetic gauges (from previous runs)
        gauge_data["flood_gauges"] = [
            g for g in gauges
            if not g.get("FloodGauge", {}).get("Header", {}).get(
                "GaugeID", "").startswith(SYNTH_PREFIX)
        ]

        # Build gauge lookup {gauge_id: {lat, lon, elevation, ...}}
        gauge_lookup = {}
        for g in gauge_data["flood_gauges"]:
            fg = g.get("FloodGauge", {})
            hdr = fg.get("Header", {})
            loc = fg.get("Location", {})
            sensor = fg.get("SensorDetails", {}).get("GaugeInformation", {})
            stages = fg.get("FloodStage", {}).get("UK", fg.get("FloodStages", {}))
            stats = fg.get("SensorStats", {})
            gid = hdr.get("GaugeID", "")
            gauge_lookup[gid] = {
                "lat": loc.get("GaugeLatitude", sensor.get("GaugeLatitude", 0)),
                "lon": loc.get("GaugeLongitude", sensor.get("GaugeLongitude", 0)),
                "elevation": loc.get("GaugeElevation", sensor.get("GroundLevelMeters", 0)),
                "flood_alert": stages.get("FloodAlert", 0),
                "flood_warning": stages.get("FloodWarning", 0),
                "severe_flood_warning": stages.get("SevereFloodWarning", 0),
                "historical_high_level": stats.get("HistoricalHighLevel", 0),
                "historical_high_date": stats.get("HistoricalHighDate", ""),
            }

        # Build ordered gauge polyline from catchment GAUGE_POINTS
        polyline = self._build_gauge_polyline(gauge_lookup)
        if len(polyline) < 2:
            logger.warning("Gauge polyline has < 2 points — skipping synthetic gauges")
            return {"count": 0, "gauge_ids": []}

        # Compute segment lengths for weighted random selection
        seg_lengths = []
        for i in range(len(polyline) - 1):
            d = haversine_distance(
                polyline[i][0], polyline[i][1],
                polyline[i + 1][0], polyline[i + 1][1])
            seg_lengths.append(d)
        total_length = sum(seg_lengths)

        # Generate synthetic gauges at random positions along the polyline
        synth_gauges: List[Dict] = []
        synth_ids: List[str] = []
        attempts = 0
        max_attempts = count * 5  # allow retries for dedup collisions

        while len(synth_gauges) < count and attempts < max_attempts:
            attempts += 1

            # Pick random segment weighted by length
            r = random.uniform(0, total_length)
            cumulative = 0.0
            seg_idx = 0
            for i, sl in enumerate(seg_lengths):
                cumulative += sl
                if cumulative >= r:
                    seg_idx = i
                    break

            # Random position along the segment
            t = random.uniform(0.05, 0.95)  # avoid exact endpoints

            result = self._create_synthetic_at_position(
                seg_idx, t, gauge_lookup, polyline)
            if result is None:
                continue

            synth_cdm, synth_id = result

            # Dedup: skip if too close to existing synthetic
            if self._is_duplicate(synth_cdm, synth_gauges):
                continue

            synth_gauges.append(synth_cdm)
            synth_ids.append(synth_id)

        # Append to gauge.json
        if synth_gauges:
            gauge_data["flood_gauges"].extend(synth_gauges)
            with open(gauge_path, "w") as f:
                json.dump(gauge_data, f, indent=2)
            logger.info("Generated %d synthetic gauges → gauge.json", len(synth_gauges))

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

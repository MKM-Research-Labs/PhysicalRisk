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

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import config
from models.floodrisk.spatial import haversine_distance

from ._create import _CreateMixin
from ._ids import SYNTH_PREFIX

logger = logging.getLogger(__name__)


class SyntheticGaugeGenerator(_CreateMixin):
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

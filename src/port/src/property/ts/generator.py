# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Property Flood Time Series Generator.

Propagates gauge-level flood events to property-level using:
- IDW interpolation from nearest 3 gauges (1/d^2 weighting)
- Elevation differential (gauge ground level vs property ground level)
- Floor level (step) as flood threshold
- Manning's velocity model for travel time and attenuation

Output: per-property JSON files in propertyts/ directory plus a
portfolio flood summary.

Usage:
    from port.src.property.ts import PropertyTimeSeriesGenerator

    generator = PropertyTimeSeriesGenerator()
    result = generator.generate()
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

from config import config
from port.utils.generator_base import GeneratorInitMixin

from .encoder import DateTimeEncoder
from .flood import FloodMixin
from .loader import LoaderMixin

logger = logging.getLogger(__name__)


class PropertyTimeSeriesGenerator(LoaderMixin, FloodMixin, GeneratorInitMixin):
    """
    Property Flood Time Series Generator.

    For each property in the portfolio, finds the nearest gauges, identifies
    storms that cause flooding at gauge level, then propagates flood events
    to the property using IDW interpolation, velocity-based travel time,
    and distance attenuation.
    """

    # Map mode -> output subdirectory name
    _MODE_DIRS = {"normal": "propertyts", "shd": "propertytsd", "she": "propertytse"}

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        verbose: bool = True,
        mode: str = "normal",
    ):
        self._init_generator(output_dir, mode, verbose)
        self._storm_to_sequence: Dict[str, str] = self._load_storm_sequence_map()

    def generate(self) -> Dict:
        """
        Generate property-level flood timeseries.

        Returns:
            Dictionary with generation metadata and summary statistics.
        """
        mode_label = f" [{self.mode}]" if self.mode != "normal" else ""
        self.log(f"Property Flood Time Series Generator{mode_label}")
        self.log(f"Catchment: {config.CATCHMENT}")

        properties = self._load_properties()
        gauges = self._load_gauges()
        gaugets = self._load_gaugets()

        self.log(f"Loaded {len(properties)} properties, {len(gauges)} gauges, {len(gaugets)} gaugets")

        # Build gauge lookup by ID
        gauge_lookup = {}
        for g in gauges:
            fg = g.get('FloodGauge', {})
            hdr = fg.get('Header', {})
            sensor = fg.get('SensorDetails', {}).get('GaugeInformation', {})
            flood_stage = fg.get('FloodStage', {}).get('UK', {})
            gid = hdr.get('GaugeID')
            gauge_lookup[gid] = {
                'gauge_id': gid,
                'lat': sensor.get('GaugeLatitude', 0),
                'lon': sensor.get('GaugeLongitude', 0),
                'elevation': sensor.get('GroundLevelMeters', sensor.get('elevation', 0)),
                'alert_level': flood_stage.get('FloodAlert', 0),
                'warning_level': flood_stage.get('FloodWarning', 0),
                'severe_level': flood_stage.get('SevereFloodWarning', 0),
            }

        pts_dir = self.output_dir / self._MODE_DIRS[self.mode]
        pts_dir.mkdir(parents=True, exist_ok=True)

        # Remove stale PROP-*.json files from previous runs
        for stale in pts_dir.glob('PROP-*.json'):
            stale.unlink()

        summary_stats = {
            'total_properties': len(properties),
            'total_gauges': len(gauges),
            'properties_with_floods': 0,
            'total_flood_events': 0,
            'total_storms_at_gauge': 0,
            'total_severe_at_gauge': 0,
            'total_storms_at_property': 0,
            'max_depth_m': 0.0,
            'max_damage_ratio': 0.0,
            'property_summaries': [],
        }

        for i, prop in enumerate(properties):
            result = self._process_property(prop, gauge_lookup, gaugets, pts_dir, mode=self.mode)
            if result:
                summary_stats['property_summaries'].append(result['summary'])
                if result['summary']['floods_at_property'] > 0:
                    summary_stats['properties_with_floods'] += 1
                summary_stats['total_flood_events'] += result['summary']['floods_at_property']
                summary_stats['total_storms_at_gauge'] += result['summary']['floods_at_nearest_gauge']
                summary_stats['total_severe_at_gauge'] += result['summary'].get('severe_at_nearest_gauge', 0)
                summary_stats['total_storms_at_property'] += result['summary']['floods_at_property']
                summary_stats['max_depth_m'] = max(
                    summary_stats['max_depth_m'], result['summary']['max_depth_m']
                )
                summary_stats['max_damage_ratio'] = max(
                    summary_stats['max_damage_ratio'], result['summary']['max_damage_ratio']
                )

            if (i + 1) % 50 == 0:
                self.log(f"  Processed {i + 1}/{len(properties)} properties")

        severe_total = summary_stats['total_severe_at_gauge']
        if severe_total > 0:
            summary_stats['gauge_to_property_ratio'] = round(
                summary_stats['total_storms_at_property'] /
                severe_total * 100, 1
            )
        else:
            summary_stats['gauge_to_property_ratio'] = 0.0

        summary_path = pts_dir / 'portfolio_flood_summary.json'
        with open(summary_path, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'catchment': config.CATCHMENT,
                'summary': {
                    'total_properties': summary_stats['total_properties'],
                    'total_gauges': summary_stats['total_gauges'],
                    'properties_with_floods': summary_stats['properties_with_floods'],
                    'total_flood_events': summary_stats['total_flood_events'],
                    'gauge_flood_events': summary_stats['total_storms_at_gauge'],
                    'gauge_severe_events': summary_stats['total_severe_at_gauge'],
                    'property_flood_events': summary_stats['total_storms_at_property'],
                    'gauge_to_property_ratio_pct': summary_stats['gauge_to_property_ratio'],
                    'max_depth_m': round(summary_stats['max_depth_m'], 4),
                    'max_damage_ratio': round(summary_stats['max_damage_ratio'], 4),
                },
                'properties': summary_stats['property_summaries'],
            }, f, indent=2, cls=DateTimeEncoder)

        self.log(f"Portfolio summary: {summary_path.name}")
        self.log(f"  Properties with floods: {summary_stats['properties_with_floods']}/{len(properties)}")
        self.log(f"  Gauge alert: {summary_stats['total_storms_at_gauge']}")
        self.log(f"  Gauge severe: {summary_stats['total_severe_at_gauge']}")
        self.log(f"  Property floods: {summary_stats['total_storms_at_property']}")
        self.log(f"  Gauge→Property ratio: {summary_stats['gauge_to_property_ratio']}%")
        self.log(f"  Max depth: {summary_stats['max_depth_m']:.2f}m")

        from models.audit import log_model_usage
        log_model_usage("depth_damage", "depth_damage_batch", parameters={
            "properties_processed": len(properties),
            "properties_with_floods": summary_stats['properties_with_floods'],
            "total_flood_events": summary_stats['total_flood_events'],
            "max_depth_m": round(summary_stats['max_depth_m'], 4),
            "max_damage_ratio": round(summary_stats['max_damage_ratio'], 4),
        }, context="Property flood timeseries batch complete")
        log_model_usage("spatial", "idw_interpolation_batch", parameters={
            "properties_processed": len(properties),
            "gauges_available": len(gauges),
        }, context="IDW spatial interpolation batch complete")

        return summary_stats

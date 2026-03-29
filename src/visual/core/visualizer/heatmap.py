# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Worst-case storm flood heatmap overlay."""

import json
import logging
from pathlib import Path

import folium
from folium.plugins import HeatMap

logger = logging.getLogger(__name__)


def add_flood_heatmap(base_map, input_dir: Path, loaded_data) -> None:
    """Add a heatmap overlay showing worst-case storm flood severity.

    Args:
        base_map: Folium map to add the heatmap to
        input_dir: Data input directory containing gaugets/ and propertyts/
        loaded_data: LoadedData container with gauge data
    """
    gaugets_dir = input_dir / 'gaugets'
    if not gaugets_dir.exists():
        return

    # Collect gauge locations and storm peak levels
    gauge_data = loaded_data.gauge_data
    if not gauge_data:
        return

    # Build gauge location lookup
    gauge_locations = {}
    gauges = gauge_data.get('items', gauge_data.get('floodGauges', []))
    for gauge in gauges:
        fg = gauge.get('FloodGauge', {})
        gid = fg.get('Header', {}).get('GaugeID')
        loc = fg.get('Location', {})
        lat = loc.get('GaugeLatitude')
        lon = loc.get('GaugeLongitude')
        if gid and lat and lon:
            gauge_locations[gid] = (lat, lon)

    # Load storm responses from gaugets files
    storm_peaks = {}  # storm_id -> [(lat, lon, peak_level)]
    for gt_file in sorted(gaugets_dir.glob('GAUGE-*.json')):
        try:
            with open(gt_file) as f:
                gt_data = json.load(f)
            gid = gt_data.get('gauge_id')
            if gid not in gauge_locations:
                continue
            lat, lon = gauge_locations[gid]
            sr_data = gt_data.get('storm_responses', {})
            responses = sr_data.get('responses', sr_data) if isinstance(sr_data, dict) else sr_data
            for sr in responses:
                sid = sr.get('storm_id')
                peak = sr.get('peak_level_m', sr.get('peak_water_level_m', 0))
                if sid and peak > 0:
                    storm_peaks.setdefault(sid, []).append((lat, lon, peak))
        except Exception:
            continue

    if not storm_peaks:
        return

    # Find worst storm (highest mean peak across gauges)
    worst_storm = max(storm_peaks.items(),
                      key=lambda item: sum(p[2] for p in item[1]) / len(item[1]))
    worst_id, worst_points = worst_storm

    # Build heatmap data: [lat, lon, intensity]
    # Normalize intensity relative to max peak in this storm
    max_peak = max(p[2] for p in worst_points)
    heat_data = [[p[0], p[1], p[2] / max_peak] for p in worst_points]

    # Add property-level flood depths for the worst storm
    pts_dir = input_dir / 'propertyts'
    prop_count = 0
    if pts_dir.exists():
        for pf in pts_dir.glob('PROP-*.json'):
            try:
                with open(pf) as f:
                    pdata = json.load(f)
                ploc = pdata.get('location', {})
                plat, plon = ploc.get('lat'), ploc.get('lon')
                if not plat or not plon:
                    continue
                for ev in pdata.get('flood_events', []):
                    if ev.get('storm_id') == worst_id and ev.get('flood_depth_m', 0) > 0:
                        intensity = min(1.0, ev['flood_depth_m'] / max_peak)
                        heat_data.append([plat, plon, intensity])
                        prop_count += 1
                        break
            except Exception:
                continue

    # Add as toggleable layer
    heatmap_group = folium.FeatureGroup(name='Worst Case Flood Extent', show=False)
    HeatMap(
        heat_data,
        radius=80,
        blur=50,
        max_zoom=13,
        gradient={'0.2': '#2196F3', '0.5': '#FFA726', '0.8': '#EF5350', '1.0': '#B71C1C'}
    ).add_to(heatmap_group)
    heatmap_group.add_to(base_map)
    logger.info("Added worst-case flood heatmap (storm %s, %d gauges, %d properties)",
                worst_id, len(worst_points), prop_count)

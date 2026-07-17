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

"""Shared frame-building helpers for the storm-animation endpoints."""

import logging

from config.port import EVENT_WINDOW_HOURS as STORM_HOURS  # 7-day storm window

from flask import jsonify

import database
from config import config

logger = logging.getLogger(__name__)


def _build_gauge_lookup(gauge_data):
    """Parse gauge JSON into a lookup dict keyed by GaugeID."""
    gauge_lookup = {}
    for g in gauge_data.get('flood_gauges', []):
        fg = g.get('FloodGauge', {})
        hdr = fg.get('Header', {})
        sensor = fg.get('SensorDetails', {}).get('GaugeInformation', {})
        flood_stage = fg.get('FloodStage', {}).get('UK', {})
        gid = hdr.get('GaugeID')
        gauge_lookup[gid] = {
            'gauge_id': gid,
            'name': hdr.get('GaugeName', ''),
            'lat': sensor.get('GaugeLatitude', 0),
            'lon': sensor.get('GaugeLongitude', 0),
            'elevation': sensor.get('GroundLevelMeters', 0),
            'alert_level': flood_stage.get('FloodAlert', 0),
            'warning_level': flood_stage.get('FloodWarning', 0),
            'severe_level': flood_stage.get('SevereFloodWarning', 0),
        }
    return gauge_lookup


def _load_gauge_readings():
    """Load gauge timeseries readings from the gauge-timeseries collection."""
    gauge_readings = {}
    for key in database.iter_gauge_timeseries_ids(config.catchment_id):
        if not key.startswith('GAUGE-'):
            continue
        gdata = database.get_gauge_timeseries(config.catchment_id, key)
        if gdata is None:
            continue
        gid = gdata.get('gauge_id', key)
        readings = gdata.get('flood_simulation', {}).get('readings', [])
        gauge_readings[gid] = readings
    return gauge_readings


def _build_gauge_frame(gauge_lookup, gauge_readings, hour):
    """Build gauge states for a single animation frame."""
    gauge_states = []
    for gid, ginfo in gauge_lookup.items():
        readings = gauge_readings.get(gid, [])
        level = 0
        if hour < len(readings):
            r = readings[hour]
            level = r.get('waterLevel', r.get('water_level_m', 0))
        gauge_states.append({
            'gauge_id': gid,
            'name': ginfo.get('name', ''),
            'lat': ginfo['lat'],
            'lon': ginfo['lon'],
            'water_level_m': level,
            'alert_level': ginfo['alert_level'],
            'status': (
                'severe' if level >= ginfo['severe_level'] else
                'warning' if level >= ginfo['warning_level'] else
                'alert' if level >= ginfo['alert_level'] else
                'normal'
            ),
        })
    return gauge_states


def _build_animation_frames(gauge_lookup, gauge_readings, property_events,
                            prop_state_fn):
    """Build animation frames for STORM_HOURS.

    Parameters
    ----------
    gauge_lookup, gauge_readings : dicts
        As returned by _build_gauge_lookup / _load_gauge_readings.
    property_events : list[dict]
        Each must have 'readings', 'property_id', 'lat', 'lon',
        and 'arrival_time_hrs'.
    prop_state_fn : callable(pe, hour, reading_or_none) -> dict
        Returns the per-property state dict for one hour.  ``reading_or_none``
        is the reading dict when ``hour < len(readings)``, else ``None``.
    """
    frames = []
    for hour in range(STORM_HOURS):
        gauge_states = _build_gauge_frame(gauge_lookup, gauge_readings, hour)

        prop_states = []
        for pe in property_events:
            readings = pe.get('readings', [])
            r = readings[hour] if hour < len(readings) else None
            prop_states.append(prop_state_fn(pe, hour, r))

        frames.append({
            'hour': hour,
            'gauges': gauge_states,
            'properties': prop_states,
            'stats': {
                'gauges_flooded': sum(1 for g in gauge_states if g['status'] != 'normal'),
                'properties_flooded': sum(1 for p in prop_states if p['flooded']),
                'total_depth_m': round(sum(p['depth_m'] for p in prop_states), 2),
            }
        })
    return frames


def _load_animation_context():
    """Load property ids, gauge_lookup, and gauge_readings.

    Returns (property_ids, gauge_lookup, gauge_readings) on success, or
    a (response, status_code) tuple on failure.
    """
    if not database.property_timeseries_exists(config.catchment_id):
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated'
        }), 404

    gauge_data = database.get_gauge_portfolio(config.catchment_id)

    gauge_lookup = _build_gauge_lookup(gauge_data)
    gauge_readings = _load_gauge_readings()
    property_ids = [
        pid for pid in database.iter_property_timeseries_ids(config.catchment_id)
        if pid.startswith('PROP-')
    ]
    return property_ids, gauge_lookup, gauge_readings

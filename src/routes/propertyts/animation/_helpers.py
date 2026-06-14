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

"""Shared frame-building helpers for the storm-animation endpoints."""

import json
import logging

from config.port import EVENT_WINDOW_HOURS as STORM_HOURS  # 7-day storm window

from flask import jsonify

from config import config
from .. import _get_propertyts_dir

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


def _load_gauge_readings(gaugets_dir):
    """Load gauge timeseries readings from GAUGE-*.json files."""
    gauge_readings = {}
    for gf in gaugets_dir.glob('GAUGE-*.json'):
        with open(gf, 'r') as f:
            gdata = json.load(f)
        gid = gdata.get('gauge_id', gf.stem)
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
    """Load pts_dir, gauge_lookup, and gauge_readings.

    Returns (pts_dir, gauge_lookup, gauge_readings) on success, or
    a (response, status_code) tuple on failure.
    """
    pts_dir = _get_propertyts_dir()
    if not pts_dir.exists():
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated'
        }), 404

    gauge_path = config.get_input_path('gauge.json')
    with open(gauge_path, 'r') as f:
        gauge_data = json.load(f)

    gauge_lookup = _build_gauge_lookup(gauge_data)
    gauge_readings = _load_gauge_readings(config.get_gaugets_dir())
    return pts_dir, gauge_lookup, gauge_readings

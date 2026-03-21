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

"""
Property flood timeseries — storm animation endpoints.

Per-storm and composite worst-case animation frames (STORM_HOURS long)
with gauge water levels and property flood states.
"""

import json
import logging

from config.port import EVENT_WINDOW_HOURS as STORM_HOURS  # 7-day storm window

from flask import jsonify, request

from config import config
from . import propertyts_bp, _get_propertyts_dir

logger = logging.getLogger(__name__)


@propertyts_bp.route('/propertyts/animate/<storm_id>', methods=['GET', 'OPTIONS'])
def animate_storm(storm_id: str):
    """
    Get animation frame data for a specific storm.

    Returns per-hour frames with gauge and property flood states
    for rendering the animated flood zone visualisation.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    pts_dir = _get_propertyts_dir()
    if not pts_dir.exists():
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated'
        }), 404

    # Load gauge data for positions and flood stages
    gauge_path = config.get_input_path('gauge.json')
    with open(gauge_path, 'r') as f:
        gauge_data = json.load(f)

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

    # Load gauge timeseries for this storm's gauge readings
    gaugets_dir = config.get_gaugets_dir()
    gauge_readings = {}
    for gf in gaugets_dir.glob('GAUGE-*.json'):
        with open(gf, 'r') as f:
            gdata = json.load(f)
        gid = gdata.get('gauge_id', gf.stem)
        readings = gdata.get('flood_simulation', {}).get('readings', [])
        gauge_readings[gid] = readings

    # Collect all properties affected by this storm
    property_events = []
    for pf in pts_dir.glob('PROP-*.json'):
        with open(pf, 'r') as f:
            pdata = json.load(f)

        for event in pdata.get('flood_events', []):
            if event.get('storm_id') == storm_id:
                property_events.append({
                    'property_id': pdata['property_id'],
                    'lat': pdata['location']['lat'],
                    'lon': pdata['location']['lon'],
                    'elevation_m': pdata['elevation_m'],
                    'floor_level_m': pdata['floor_level_m'],
                    'flood_depth_m': event['flood_depth_m'],
                    'damage_ratio': event['damage_ratio'],
                    'arrival_time_hrs': event.get('arrival_time_hrs'),
                    'peak_time_hrs': event.get('peak_time_hrs'),
                    'travel_time_hrs': event.get('travel_time_hrs', 0),
                    'attenuation_factor': event.get('attenuation_factor', 1),
                    'readings': event.get('readings', []),
                })
                break

    if not property_events:
        return jsonify({
            'status': 'error',
            'message': f'Storm {storm_id} not found or causes no property flooding'
        }), 404

    # Build frame data
    n_hours = STORM_HOURS
    frames = []
    for hour in range(n_hours):
        gauge_states = []
        for gid, ginfo in gauge_lookup.items():
            readings = gauge_readings.get(gid, [])
            if hour < len(readings):
                r = readings[hour]
                level = r.get('waterLevel', r.get('water_level_m', 0))
            else:
                level = 0
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

        prop_states = []
        for pe in property_events:
            readings = pe.get('readings', [])
            if hour < len(readings):
                r = readings[hour]
                prop_states.append({
                    'property_id': pe['property_id'],
                    'lat': pe['lat'],
                    'lon': pe['lon'],
                    'wse_m': r['wse_m'],
                    'depth_m': r['depth_m'],
                    'flooded': r['flooded'],
                    'arrived': pe['arrival_time_hrs'] is not None and hour >= pe['arrival_time_hrs'],
                })
            else:
                prop_states.append({
                    'property_id': pe['property_id'],
                    'lat': pe['lat'],
                    'lon': pe['lon'],
                    'wse_m': 0,
                    'depth_m': 0,
                    'flooded': False,
                    'arrived': False,
                })

        gauges_flooded = sum(1 for g in gauge_states if g['status'] != 'normal')
        props_flooded = sum(1 for p in prop_states if p['flooded'])

        frames.append({
            'hour': hour,
            'gauges': gauge_states,
            'properties': prop_states,
            'stats': {
                'gauges_flooded': gauges_flooded,
                'properties_flooded': props_flooded,
                'total_depth_m': round(sum(p['depth_m'] for p in prop_states), 2),
            }
        })

    return jsonify({
        'status': 'success',
        'storm_id': storm_id,
        'n_frames': n_hours,
        'n_properties_affected': len(property_events),
        'frames': frames,
    })


@propertyts_bp.route('/propertyts/animate/composite', methods=['GET', 'OPTIONS'])
def animate_composite():
    """
    Get animation frame data for a composite worst-case across all storms.

    For each property, picks the storm with the highest flood depth and uses
    that event's readings. Shows the full portfolio worst-case scenario.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    pts_dir = _get_propertyts_dir()
    if not pts_dir.exists():
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated'
        }), 404

    # Load gauge data
    gauge_path = config.get_input_path('gauge.json')
    with open(gauge_path, 'r') as f:
        gauge_data = json.load(f)

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
            'alert_level': flood_stage.get('FloodAlert', 0),
            'warning_level': flood_stage.get('FloodWarning', 0),
            'severe_level': flood_stage.get('SevereFloodWarning', 0),
        }

    # Load gauge readings (use first available set)
    gaugets_dir = config.get_gaugets_dir()
    gauge_readings = {}
    for gf in gaugets_dir.glob('GAUGE-*.json'):
        with open(gf, 'r') as f:
            gdata = json.load(f)
        gid = gdata.get('gauge_id', gf.stem)
        readings = gdata.get('flood_simulation', {}).get('readings', [])
        gauge_readings[gid] = readings

    # For each property, find worst storm event
    property_events = []
    for pf in pts_dir.glob('PROP-*.json'):
        with open(pf, 'r') as f:
            pdata = json.load(f)
        events = pdata.get('flood_events', [])
        if not events:
            continue
        worst = max(events, key=lambda e: e.get('flood_depth_m', 0))
        if worst.get('flood_depth_m', 0) <= 0:
            continue
        property_events.append({
            'property_id': pdata['property_id'],
            'lat': pdata['location']['lat'],
            'lon': pdata['location']['lon'],
            'flood_depth_m': worst['flood_depth_m'],
            'damage_ratio': worst['damage_ratio'],
            'arrival_time_hrs': worst.get('arrival_time_hrs'),
            'peak_time_hrs': worst.get('peak_time_hrs'),
            'travel_time_hrs': worst.get('travel_time_hrs', 0),
            'readings': worst.get('readings', []),
        })

    if not property_events:
        return jsonify({
            'status': 'error',
            'message': 'No property flooding found across any storm'
        }), 404

    # Build frames
    n_hours = STORM_HOURS
    frames = []
    for hour in range(n_hours):
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
                'status': (
                    'severe' if level >= ginfo['severe_level'] else
                    'warning' if level >= ginfo['warning_level'] else
                    'alert' if level >= ginfo['alert_level'] else
                    'normal'
                ),
            })

        prop_states = []
        for pe in property_events:
            readings = pe.get('readings', [])
            if hour < len(readings):
                r = readings[hour]
                prop_states.append({
                    'property_id': pe['property_id'],
                    'lat': pe['lat'],
                    'lon': pe['lon'],
                    'depth_m': r['depth_m'],
                    'flooded': r['flooded'],
                    'arrived': pe['arrival_time_hrs'] is not None and hour >= pe['arrival_time_hrs'],
                    'peak': pe['peak_time_hrs'] is not None and hour >= pe['peak_time_hrs'],
                })
            else:
                prop_states.append({
                    'property_id': pe['property_id'],
                    'lat': pe['lat'],
                    'lon': pe['lon'],
                    'depth_m': 0,
                    'flooded': False,
                    'arrived': False,
                    'peak': False,
                })

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

    return jsonify({
        'status': 'success',
        'storm_id': 'COMPOSITE',
        'n_frames': n_hours,
        'n_properties_affected': len(property_events),
        'frames': frames,
    })

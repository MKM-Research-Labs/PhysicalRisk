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

"""Storm-animation endpoints, registered on ``propertyts_bp``."""

import json

from flask import jsonify, request

from .. import propertyts_bp
from ._helpers import STORM_HOURS, _build_animation_frames, _load_animation_context


@propertyts_bp.route('/propertyts/animate/<storm_id>', methods=['GET', 'OPTIONS'])
def animate_storm(storm_id: str):
    """
    Get animation frame data for a specific storm.

    Returns per-hour frames with gauge and property flood states
    for rendering the animated flood zone visualisation.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    ctx = _load_animation_context()
    if len(ctx) == 2:
        return ctx  # error response
    pts_dir, gauge_lookup, gauge_readings = ctx

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
                    'retention_factor': event.get('retention_factor',
                                                      event.get('attenuation_factor', 1)),
                    'readings': event.get('readings', []),
                })
                break

    if not property_events:
        return jsonify({
            'status': 'error',
            'message': f'Storm {storm_id} not found or causes no property flooding'
        }), 404

    # Build frame data
    def _storm_prop_state(pe, hour, r):
        if r is not None:
            return {
                'property_id': pe['property_id'],
                'lat': pe['lat'],
                'lon': pe['lon'],
                'wse_m': r['wse_m'],
                'depth_m': r['depth_m'],
                'flooded': r['flooded'],
                'arrived': pe['arrival_time_hrs'] is not None and hour >= pe['arrival_time_hrs'],
            }
        return {
            'property_id': pe['property_id'],
            'lat': pe['lat'],
            'lon': pe['lon'],
            'wse_m': 0,
            'depth_m': 0,
            'flooded': False,
            'arrived': False,
        }

    frames = _build_animation_frames(
        gauge_lookup, gauge_readings, property_events, _storm_prop_state)

    return jsonify({
        'status': 'success',
        'storm_id': storm_id,
        'n_frames': STORM_HOURS,
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

    ctx = _load_animation_context()
    if len(ctx) == 2:
        return ctx  # error response
    pts_dir, gauge_lookup, gauge_readings = ctx

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
    def _composite_prop_state(pe, hour, r):
        if r is not None:
            return {
                'property_id': pe['property_id'],
                'lat': pe['lat'],
                'lon': pe['lon'],
                'depth_m': r['depth_m'],
                'flooded': r['flooded'],
                'arrived': pe['arrival_time_hrs'] is not None and hour >= pe['arrival_time_hrs'],
                'peak': pe['peak_time_hrs'] is not None and hour >= pe['peak_time_hrs'],
            }
        return {
            'property_id': pe['property_id'],
            'lat': pe['lat'],
            'lon': pe['lon'],
            'depth_m': 0,
            'flooded': False,
            'arrived': False,
            'peak': False,
        }

    frames = _build_animation_frames(
        gauge_lookup, gauge_readings, property_events, _composite_prop_state)

    return jsonify({
        'status': 'success',
        'storm_id': 'COMPOSITE',
        'n_frames': STORM_HOURS,
        'n_properties_affected': len(property_events),
        'frames': frames,
    })

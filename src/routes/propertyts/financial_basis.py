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
Synthetic gauge basis analysis endpoint.

Groups properties by their controlling synthetic gauge and shows
flood transmission: how many properties linked to each synthetic
gauge actually flooded vs didn't.  Helps the REIT understand
where the gauge-to-property attenuation kills the flood signal.
"""

import json
import logging

from flask import jsonify, request

from config import config

from ._helpers import _get_propertyts_dir
from .blueprint import propertyts_bp

logger = logging.getLogger(__name__)


@propertyts_bp.route('/propertyts/<storm_id>/basis', methods=['GET', 'OPTIONS'])
def storm_basis(storm_id: str):
    """Synthetic gauge basis analysis for a storm.

    Groups properties by their controlling synthetic gauge and shows
    flood transmission: how many properties linked to each synthetic
    gauge actually flooded vs didn't.  Helps the REIT understand
    where the gauge-to-property attenuation kills the flood signal.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    pts_dir = _get_propertyts_dir()
    if not pts_dir or not pts_dir.exists():
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated',
        }), 404

    gauge_thresholds = _load_gauge_thresholds()
    storm_gauge_peaks = _load_storm_gauge_peaks(storm_id)
    synth_data = _accumulate_synth_data(pts_dir, storm_id, gauge_thresholds)
    gauges = _build_gauge_response(synth_data, storm_gauge_peaks)

    # Sort: severe first, then gauges with flooding before those without,
    # then by properties linked descending
    _THRESHOLD_ORDER = {'severe': 0, 'warning': 1, 'alert': 2, 'clean': 3}
    gauges.sort(key=lambda g: (
        _THRESHOLD_ORDER.get(g['threshold'], 3),
        0 if g['properties_flooded'] > 0 else 1,
        -g['properties_linked'],
    ))

    # Summary
    total_linked = sum(g['properties_linked'] for g in gauges)
    total_flooded = sum(g['properties_flooded'] for g in gauges)
    severe_gauges = [g for g in gauges if g['threshold'] == 'severe']
    basis_gauges = [
        g for g in severe_gauges if g['properties_flooded'] == 0]

    return jsonify({
        'status': 'success',
        'storm_id': storm_id,
        'gauges': gauges,
        'summary': {
            'num_synthetic_gauges': len(gauges),
            'gauges_severe': len(severe_gauges),
            'gauges_with_flooding': sum(
                1 for g in gauges if g['properties_flooded'] > 0),
            'gauges_basis_only': len(basis_gauges),
            'total_properties': total_linked,
            'total_flooded': total_flooded,
            'portfolio_transmission_pct': round(
                total_flooded / total_linked * 100, 1
            ) if total_linked > 0 else 0,
        },
    })


def _load_gauge_thresholds():
    """Load gauge threshold metadata from gaugehc.json."""
    gauge_thresholds = {}
    gaugehc_path = config.get_input_dir() / 'gaugehc.json'
    if gaugehc_path.exists():
        try:
            with open(gaugehc_path) as f:
                ghc = json.load(f)
            for gid, gc in ghc.get('hazard_curves', {}).items():
                gauge_thresholds[gid] = {
                    'gauge_name': gc.get('gauge_name', gid),
                    'alert_m': gc.get('flood_alert_m', 0),
                    'warning_m': gc.get('flood_warning_m', 0),
                    'severe_m': gc.get('severe_flood_warning_m', 0),
                    'elevation_m': gc.get('elevation_m', 0),
                    'latitude': gc.get('latitude', 0),
                    'longitude': gc.get('longitude', 0),
                }
        except Exception as e:
            logger.warning('Could not load gaugehc.json: %s', e)
    return gauge_thresholds


def _load_storm_gauge_peaks(storm_id):
    """Load real-gauge peak levels for a storm from stress_storms/<storm_id>.json."""
    storm_gauge_peaks = {}
    try:
        storm_path = config.get_input_path('stress_storms') / f'{storm_id}.json'
        if storm_path.exists():
            with open(storm_path) as f:
                storm_data = json.load(f)
            for gr in storm_data.get('gauge_responses', []):
                storm_gauge_peaks[gr['gauge_id']] = {
                    'peak_level_m': gr.get('peak_level_m', 0),
                    'exceeded_severe': gr.get('exceeded_severe', False),
                    'exceeded_warning': gr.get('exceeded_warning', False),
                    'exceeded_alert': gr.get('exceeded_alert', False),
                }
    except Exception as e:
        logger.warning('Could not load storm %s: %s', storm_id, e)
    return storm_gauge_peaks


def _accumulate_synth_data(pts_dir, storm_id, gauge_thresholds):
    """Group property flood records by their controlling synthetic gauge."""
    synth_data = {}  # gauge_id -> accumulator

    for pf in pts_dir.glob('PROP-*.json'):
        try:
            with open(pf, 'r') as f:
                pfdata = json.load(f)
        except Exception:
            continue

        nearest = pfdata.get('nearest_gauges', [])
        if not nearest:
            continue

        # Synthetic gauge is first in nearest_gauges
        synth = nearest[0]
        synth_id = synth.get('gauge_id', '')
        if not synth_id:
            continue

        # Find the nearest real gauge (second in list)
        real_gauge_id = ''
        if len(nearest) > 1:
            real_gauge_id = nearest[1].get('gauge_id', '')

        # Find the flood event for this storm
        flood_event = None
        for event in pfdata.get('flood_events', []):
            if event.get('storm_id') == storm_id:
                flood_event = event
                break

        # Initialise accumulator for this synthetic gauge
        if synth_id not in synth_data:
            thresholds = gauge_thresholds.get(synth_id, {})
            synth_data[synth_id] = {
                'gauge_id': synth_id,
                'gauge_name': thresholds.get('gauge_name', synth_id),
                'gauge_type': (
                    'Synthetic' if synth_id.startswith('SYNTH') else 'Real'),
                'severe_m': thresholds.get('severe_m', 0),
                'warning_m': thresholds.get('warning_m', 0),
                'alert_m': thresholds.get('alert_m', 0),
                'elevation_m': thresholds.get('elevation_m', 0),
                'latitude': thresholds.get('latitude', 0),
                'longitude': thresholds.get('longitude', 0),
                'real_gauge_id': real_gauge_id,
                'properties_linked': 0,
                'properties_flooded': 0,
                'total_damage': 0,
                'total_flood_depth': 0,
                'total_retention': 0,
                'retention_count': 0,
                'peak_wse_m': 0,
                'exceeded_severe': False,
            }

        acc = synth_data[synth_id]
        acc['properties_linked'] += 1

        if flood_event:
            wse = flood_event.get('interpolated_wse_m', 0)
            if wse > acc['peak_wse_m']:
                acc['peak_wse_m'] = wse
            if flood_event.get('exceeded_severe', False):
                acc['exceeded_severe'] = True

            retention = flood_event.get('retention_factor', 0)
            if retention > 0:
                acc['total_retention'] += retention
                acc['retention_count'] += 1

            if flood_event.get('flooded', False):
                acc['properties_flooded'] += 1
                acc['total_damage'] += flood_event.get('damage_ratio', 0)
                acc['total_flood_depth'] += flood_event.get('flood_depth_m', 0)

    return synth_data


def _build_gauge_response(synth_data, storm_gauge_peaks):
    """Build the per-gauge response list from accumulated synth data."""
    gauges = []
    for gid, acc in synth_data.items():
        linked = acc['properties_linked']
        flooded = acc['properties_flooded']
        transmission = (
            round(flooded / linked * 100, 1) if linked > 0 else 0)
        avg_retention = (
            round(acc['total_retention'] / acc['retention_count'], 4)
            if acc['retention_count'] > 0 else 0)
        avg_depth = (
            round(acc['total_flood_depth'] / flooded, 3)
            if flooded > 0 else 0)
        avg_damage = (
            round(acc['total_damage'] / flooded, 4)
            if flooded > 0 else 0)

        # Determine threshold breach label
        if acc['exceeded_severe']:
            threshold = 'severe'
        elif acc['peak_wse_m'] >= acc['warning_m'] > 0:
            threshold = 'warning'
        elif acc['peak_wse_m'] >= acc['alert_m'] > 0:
            threshold = 'alert'
        else:
            threshold = 'clean'

        # Real gauge peak (from storm data)
        real_peak = storm_gauge_peaks.get(acc['real_gauge_id'], {})

        gauges.append({
            'gauge_id': gid,
            'gauge_name': acc['gauge_name'],
            'gauge_type': acc['gauge_type'],
            'threshold': threshold,
            'peak_wse_m': round(acc['peak_wse_m'], 3),
            'severe_m': acc['severe_m'],
            'properties_linked': linked,
            'properties_flooded': flooded,
            'properties_not_flooded': linked - flooded,
            'transmission_pct': transmission,
            'avg_retention': avg_retention,
            'avg_flood_depth_m': avg_depth,
            'avg_damage_ratio': avg_damage,
            'real_gauge_id': acc['real_gauge_id'],
            'real_gauge_peak_m': real_peak.get('peak_level_m', 0),
            'real_gauge_severe': real_peak.get('exceeded_severe', False),
        })

    return gauges

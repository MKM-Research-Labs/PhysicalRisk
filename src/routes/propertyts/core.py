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
Core property timeseries endpoints.

Handles the portfolio summary, per-property flood list, per-property
storm analysis, and the portfolio-wide storm list.

Endpoints
---------
GET /propertyts/summary
GET /properties/<prop_id>/floods
GET /properties/<prop_id>/storms
GET /propertyts/storms
"""

import json
import logging

from flask import jsonify, request

from config import config

from . import _get_propertyts_dir, propertyts_bp

logger = logging.getLogger(__name__)


@propertyts_bp.route('/propertyts/summary', methods=['GET', 'OPTIONS'])
def propertyts_summary():
    """Get portfolio flood summary statistics."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    summary_path = _get_propertyts_dir() / 'portfolio_flood_summary.json'
    if not summary_path.exists():
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated. Run: python app.py port --propertyts'
        }), 404

    with open(summary_path, 'r') as f:
        data = json.load(f)

    return jsonify({
        'status': 'success',
        'data': data
    })


@propertyts_bp.route('/properties/<prop_id>/floods', methods=['GET', 'OPTIONS'])
def property_floods(prop_id: str):
    """
    Get flood events for a specific property.

    Query params:
        include_readings: bool (default false) - include hourly hydrograph readings
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    pts_dir = _get_propertyts_dir()
    prop_file = pts_dir / f'{prop_id}.json'

    if not prop_file.exists():
        return jsonify({
            'status': 'error',
            'message': f'Property {prop_id} not found in flood timeseries'
        }), 404

    with open(prop_file, 'r') as f:
        data = json.load(f)

    include_readings = request.args.get('include_readings', 'false').lower() == 'true'
    if not include_readings:
        for event in data.get('flood_events', []):
            event.pop('readings', None)

    return jsonify({
        'status': 'success',
        'data': data
    })


@propertyts_bp.route('/properties/<prop_id>/storms', methods=['GET', 'OPTIONS'])
def property_storms(prop_id: str):
    """
    Get storm scenario analysis for a property.

    Returns flood events with hydrograph readings, nearest gauge info,
    and summary statistics — structured for the property storm analysis panel.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    pts_dir = _get_propertyts_dir()
    prop_file = pts_dir / f'{prop_id}.json'

    if not prop_file.exists():
        return jsonify({
            'status': 'error',
            'message': f'Property {prop_id} not found in flood timeseries'
        }), 404

    with open(prop_file, 'r') as f:
        pdata = json.load(f)

    # Build sequence_id → sequence_type lookup
    seq_lookup = {}
    try:
        seq_path = config.get_input_path('storm_sequences.json')
        with open(seq_path, 'r') as f:
            sdata = json.load(f)
        for seq in sdata.get('sequences', []):
            seq_lookup[seq['sequence_id']] = seq.get('sequence_type', 'isolated')
    except Exception:
        pass

    # Tag each flood event with sequence_type
    # storm_id IS the sequence_id (sequences are the unit of risk)
    for event in pdata.get('flood_events', []):
        sid = event.get('storm_id', '')
        event['sequence_type'] = seq_lookup.get(sid, 'isolated') if sid else 'isolated'

    # Enrich nearest gauge info with flood stages
    gauge_path = config.get_input_path('gauge.json')
    gauge_stages = {}
    try:
        with open(gauge_path, 'r') as f:
            gdata = json.load(f)
        for g in gdata.get('flood_gauges', []):
            fg = g.get('FloodGauge', {})
            gid = fg.get('Header', {}).get('GaugeID', '')
            stages = fg.get('FloodStage', {}).get('UK', {})
            gauge_stages[gid] = {
                'alert': stages.get('FloodAlert', 0),
                'warning': stages.get('FloodWarning', 0),
                'severe': stages.get('SevereFloodWarning', 0),
            }
    except Exception:
        pass

    nearest = pdata.get('nearest_gauges', [])
    for ng in nearest:
        gid = ng.get('gauge_id', '')
        stages = gauge_stages.get(gid, {})
        ng['flood_stages'] = stages

    return jsonify({
        'status': 'success',
        'property_id': prop_id,
        'property_info': {
            'elevation_m': pdata.get('elevation_m', 0),
            'floor_level_m': pdata.get('floor_level_m', 0),
            'location': pdata.get('location', {}),
        },
        'nearest_gauges': nearest,
        'flood_events': pdata.get('flood_events', []),
        'summary': pdata.get('summary', {}),
    })


@propertyts_bp.route('/propertyts/storms', methods=['GET', 'OPTIONS'])
def list_flood_storms():
    """List all storms with property flooding enrichment."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    # Build storm set from stress_storms index (sequence-level IDs).
    # Sequences are the unit of risk — individual pulses within a
    # sequence are implementation detail.
    storm_set = {}

    ss_index = config.get_input_path('stress_storms') / '_index.json'
    ss_legacy = config.get_input_path('stress_storms.json')
    ss_path = ss_index if ss_index.exists() else (ss_legacy if ss_legacy.exists() else None)

    if ss_path and ss_path.exists():
        try:
            with open(ss_path, 'r') as f:
                ss_data = json.load(f)
            for s in ss_data.get('storms', []):
                sid = s.get('storm_id', '')
                if not sid:
                    continue
                ts = s.get('trigger_summary', {})
                storm_set[sid] = {
                    'storm_id': sid,
                    'name': s.get('name', ''),
                    'intensity_category': s.get('intensity_category', ''),
                    'effective_precipitation_mm': s.get('effective_precipitation_mm', 0),
                    'gauges_severe': ts.get('gauges_severe', 0),
                    'properties_flooded': 0,
                    'max_depth_m': 0,
                    'max_damage_ratio': 0,
                }
        except Exception:
            pass

    # If no stress_storms, fall back to gaugets individual storms
    if not storm_set:
        gaugets_dir = config.get_gaugets_dir()
        if not gaugets_dir.exists():
            return jsonify({'status': 'error',
                            'message': 'gaugets directory not found'}), 404
        for gf in gaugets_dir.glob('GAUGE-*.json'):
            try:
                with open(gf, 'r') as f:
                    gdata = json.load(f)
                for resp in gdata.get('storm_responses', {}).get('responses', []):
                    sid = resp.get('storm_id', '')
                    if not sid:
                        continue
                    if sid not in storm_set:
                        storm_set[sid] = {
                            'storm_id': sid,
                            'name': '',
                            'intensity_category': '',
                            'effective_precipitation_mm': 0,
                            'gauges_severe': 0,
                            'properties_flooded': 0,
                            'max_depth_m': 0,
                            'max_damage_ratio': 0,
                        }
                    if resp.get('exceeded_severe'):
                        storm_set[sid]['gauges_severe'] += 1
            except Exception:
                continue

    # Enrich with metadata from storm_sequences.json (sequence-level)
    # or legacy storms.json
    _storm_meta = {}
    for meta_file in ('storm_sequences.json', 'storms.json'):
        meta_path = config.get_input_path(meta_file)
        if not meta_path.exists():
            continue
        try:
            with open(meta_path, 'r') as f:
                mdata = json.load(f)
            if 'sequences' in mdata:
                for seq in mdata['sequences']:
                    _storm_meta[seq.get('sequence_id', '')] = seq
            elif 'storms' in mdata:
                for s in mdata['storms']:
                    _storm_meta[s.get('storm_id', '')] = s
        except Exception:
            pass

    for sid, entry in storm_set.items():
        meta = _storm_meta.get(sid)
        if meta:
            cat = meta.get('intensity_category', '')
            entry['intensity_category'] = cat
            entry['name'] = meta.get('name', '') or (cat.capitalize() if cat else '')
            entry['effective_precipitation_mm'] = meta.get(
                'effective_precipitation_mm',
                meta.get('precipitation_mm', 0))

    # Classify storms without metadata by gauges_severe count
    for entry in storm_set.values():
        if not entry['name']:
            sev = entry['gauges_severe']
            if sev >= 10:
                cat = 'catastrophic'
            elif sev >= 5:
                cat = 'extreme'
            elif sev >= 2:
                cat = 'severe'
            elif sev >= 1:
                cat = 'moderate'
            else:
                cat = 'baseline'
            entry['intensity_category'] = cat
            entry['name'] = cat.capitalize()

    # Enrich with property flooding data
    pts_dir = _get_propertyts_dir()
    if pts_dir.exists():
        prop_path = config.get_input_path('property.json')
        valued_ids = set()
        try:
            with open(prop_path, 'r') as f:
                pdata = json.load(f)
            for p in pdata.get('properties', []):
                pid = p.get('PropertyHeader', {}).get('Header', {}).get('PropertyID', '')
                if pid:
                    valued_ids.add(pid)
        except Exception:
            pass

        for pf in pts_dir.glob('PROP-*.json'):
            with open(pf, 'r') as f:
                pdata = json.load(f)
            prop_id = pdata.get('property_id', pf.stem)
            if valued_ids and prop_id not in valued_ids:
                continue
            for event in pdata.get('flood_events', []):
                depth = event.get('flood_depth_m', 0)
                if depth <= 0:
                    continue
                sid = event.get('storm_id', '')
                if sid in storm_set:
                    storm_set[sid]['properties_flooded'] += 1
                    storm_set[sid]['max_depth_m'] = max(
                        storm_set[sid]['max_depth_m'], depth
                    )
                    storm_set[sid]['max_damage_ratio'] = max(
                        storm_set[sid]['max_damage_ratio'], event.get('damage_ratio', 0)
                    )

    # Severity rank (lower = worse) used as tie-breaker on equal gauge counts.
    # Consistent with /trading/stress/portfolio-storms sort order.
    _INTENSITY_RANK = {
        'catastrophic': 0, 'extreme': 1, 'severe': 2,
        'moderate': 3, 'baseline': 4,
    }

    # Only include storms that actually cause property flooding — storms
    # with zero affected properties would produce errors in portfolio-impact.
    flooding_storms = [s for s in storm_set.values() if s['properties_flooded'] > 0]

    storms = sorted(flooding_storms, key=lambda s: (
        -s['gauges_severe'],
        -s['properties_flooded'],
        -s['max_depth_m'],
        _INTENSITY_RANK.get(s.get('intensity_category', ''), 99),
    ))

    return jsonify({
        'status': 'success',
        'count': len(storms),
        'storms': storms,
    })

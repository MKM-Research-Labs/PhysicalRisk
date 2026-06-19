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
Core property timeseries endpoints — portfolio-wide storm list.

Endpoints
---------
GET /propertyts/storms
"""

import logging

from flask import jsonify, request

import database
from config import config
from port.storm_typhoon_pairing import get_pairing

from . import propertyts_bp

logger = logging.getLogger(__name__)


@propertyts_bp.route('/propertyts/storms', methods=['GET', 'OPTIONS'])
def list_flood_storms():
    """List all storms with property flooding enrichment."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    # Build storm set from stress_storms index (sequence-level IDs).
    # Sequences are the unit of risk — individual pulses within a
    # sequence are implementation detail.
    storm_set = {}

    # Primary: sharded stress_storms/_index.json; fall back to the legacy
    # single-file stress_storms.json on portfolios from before the shard split.
    try:
        ss_data = database.get_stress_storm_index(config.catchment_id)
        if ss_data is None:
            ss_data = database.get_legacy_stress_storms(config.catchment_id)
        if ss_data:
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
                    'estimated_damage': 0,
                }
    except Exception:
        pass

    # If no stress_storms, fall back to gaugets individual storms
    if not storm_set:
        if not database.gauge_timeseries_exists(config.catchment_id):
            return jsonify({'status': 'error',
                            'message': 'gaugets directory not found'}), 404
        for gid in database.iter_gauge_timeseries_ids(config.catchment_id):
            if not gid.startswith('GAUGE-'):
                continue
            try:
                gdata = database.get_gauge_timeseries(config.catchment_id, gid)
                if gdata is None:
                    continue
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
                            'estimated_damage': 0,
                        }
                    if resp.get('exceeded_severe'):
                        storm_set[sid]['gauges_severe'] += 1
            except Exception:
                continue

    # Enrich with metadata from storm_sequences.json (sequence-level)
    # or legacy storms.json. Both are read and merged, legacy last.
    _storm_meta = {}
    for _meta_getter in (database.get_storm_sequences,
                         database.get_legacy_storm_sequences):
        try:
            mdata = _meta_getter(config.catchment_id)
            if not mdata:
                continue
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
            # Only update name if not already set from stress_storms index
            if not entry.get('name'):
                entry['name'] = meta.get('name', '')
            entry['effective_precipitation_mm'] = meta.get(
                'effective_precipitation_mm',
                meta.get('total_precipitation_mm',
                         meta.get('precipitation_mm', 0)))

    # Classify storms without metadata by gauges_severe count
    for entry in storm_set.values():
        if not entry.get('intensity_category'):
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
    if database.property_timeseries_exists(config.catchment_id):
        valued_ids = set()
        prop_values = {}  # property_id → estimated market value
        try:
            pdata = database.get_property_portfolio(config.catchment_id) or {}
            for p in pdata.get('properties', []):
                hdr = p.get('PropertyHeader', {})
                pid = hdr.get('Header', {}).get('PropertyID', '')
                if pid:
                    valued_ids.add(pid)
                    val = hdr.get('Valuation', {})
                    prop_values[pid] = val.get('PropertyValue', 0)
        except Exception:
            pass

        for pid in database.iter_property_timeseries_ids(config.catchment_id):
            if not pid.startswith('PROP-'):
                continue
            pdata = database.get_property_timeseries(config.catchment_id, pid)
            if pdata is None:
                continue
            prop_id = pdata.get('property_id', pid)
            if valued_ids and prop_id not in valued_ids:
                continue
            pval = prop_values.get(prop_id, 0)
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
                    dmg_ratio = event.get('damage_ratio', 0)
                    storm_set[sid]['estimated_damage'] = (
                        storm_set[sid].get('estimated_damage', 0)
                        + pval * dmg_ratio
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

    # Round estimated_damage for JSON
    for entry in flooding_storms:
        entry['estimated_damage'] = round(entry.get('estimated_damage', 0))

    # Attach the typhoon "additional circumstance" via the true 1:1 pairing
    # (shared event_id). Storms whose typhoon stage didn't run stay water-only
    # (typhoon=None) — no breaking change for existing consumers.
    storm_to_typhoon = get_pairing().get('storm_to_typhoon', {})
    for entry in flooding_storms:
        entry['typhoon'] = storm_to_typhoon.get(entry['storm_id'])

    # Sort order — ?sort= query parameter, default 'damage'
    sort_mode = request.args.get('sort', 'damage')
    if sort_mode == 'damage':
        storms = sorted(flooding_storms, key=lambda s: (
            -s['estimated_damage'],
            -s['properties_flooded'],
            -s['max_depth_m'],
            _INTENSITY_RANK.get(s.get('intensity_category', ''), 99),
        ))
    elif sort_mode == 'flooded':
        storms = sorted(flooding_storms, key=lambda s: (
            -s['properties_flooded'],
            -s['max_depth_m'],
            -s['gauges_severe'],
            _INTENSITY_RANK.get(s.get('intensity_category', ''), 99),
        ))
    else:  # 'severity' — meteorological severity
        storms = sorted(flooding_storms, key=lambda s: (
            -s['gauges_severe'],
            -s['properties_flooded'],
            -s['max_depth_m'],
            _INTENSITY_RANK.get(s.get('intensity_category', ''), 99),
        ))

    return jsonify({
        'status': 'success',
        'count': len(storms),
        'total_storms': len(storm_set),
        'storms': storms,
    })

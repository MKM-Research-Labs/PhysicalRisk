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
Core property timeseries endpoints — per-property storm analysis.

Endpoints
---------
GET /properties/<prop_id>/storms
"""

import json
import logging

from flask import jsonify

from config import config

from . import propertyts_bp
from .core_summary import _load_property_or_404

logger = logging.getLogger(__name__)


@propertyts_bp.route('/properties/<prop_id>/storms', methods=['GET', 'OPTIONS'])
def property_storms(prop_id: str):
    """
    Get storm scenario analysis for a property.

    Returns flood events with hydrograph readings, nearest gauge info,
    and summary statistics — structured for the property storm analysis panel.
    """
    early, pdata = _load_property_or_404(prop_id)
    if early is not None:
        return early

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

    # Build storm metadata lookup (name, category, precipitation, severity)
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

    # Build storm_id → gauges_severe from stress_storms
    _storm_severe = {}
    ss_index = config.get_input_path('stress_storms') / '_index.json'
    ss_legacy = config.get_input_path('stress_storms.json')
    ss_path = ss_index if ss_index.exists() else (ss_legacy if ss_legacy.exists() else None)
    if ss_path and ss_path.exists():
        try:
            with open(ss_path, 'r') as f:
                ss_data = json.load(f)
            for s in ss_data.get('storms', []):
                sid = s.get('storm_id', '')
                if sid:
                    ts = s.get('trigger_summary', {})
                    _storm_severe[sid] = ts.get('gauges_severe', 0)
        except Exception:
            pass

    # Tag each flood event with sequence_type and storm metadata
    # storm_id IS the sequence_id (sequences are the unit of risk)
    for event in pdata.get('flood_events', []):
        sid = event.get('storm_id', '')
        event['sequence_type'] = seq_lookup.get(sid, 'isolated') if sid else 'isolated'
        # Storm metadata for canonical display format
        meta = _storm_meta.get(sid)
        if meta:
            cat = meta.get('intensity_category', '')
            event.setdefault('intensity_category', cat)
            event.setdefault('name', meta.get('name', '') or (cat.capitalize() if cat else ''))
            event.setdefault('effective_precipitation_mm',
                             meta.get('effective_precipitation_mm',
                                      meta.get('precipitation_mm', 0)))
        event.setdefault('gauges_severe', _storm_severe.get(sid, 0))

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

    # Gauge severe counts from GEV annual_flood_prob_severe in gaugehc.
    # Compute per-gauge and use synthetic as the controlling total.
    severe_at_gauge = 0
    try:
        hc_path = config.get_input_dir() / 'gaugehc.json'
        seq_path = config.get_input_path('storm_sequences.json')
        with open(hc_path, 'r') as f:
            hc_data = json.load(f)
        with open(seq_path, 'r') as f:
            seq_data = json.load(f)
        num_sequences = seq_data.get('num_sequences', len(seq_data.get('sequences', [])))

        synth = next((ng for ng in nearest if ng.get('gauge_id', '').startswith('SYNTH')), None)
        controlling = synth or (nearest[0] if nearest else None)

        for ng in nearest:
            gid = ng.get('gauge_id', '')
            gauge_hc = hc_data.get('hazard_curves', {}).get(gid, {})
            prob = gauge_hc.get('annual_flood_prob_severe', 0)
            ng['severe_count'] = round(prob * num_sequences)
            ng['severe_spread_bps'] = round(prob * 10000, 1)
            ng['gauge_name'] = gauge_hc.get('gauge_name', gid)

        if controlling:
            severe_at_gauge = controlling.get('severe_count', 0)
    except Exception:
        pass

    summary = pdata.get('summary', {})
    summary['severe_at_nearest_gauge'] = severe_at_gauge

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
        'summary': summary,
    })

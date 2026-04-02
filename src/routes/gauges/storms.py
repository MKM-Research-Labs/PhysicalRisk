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

"""Gauge storm scenario endpoint."""

import json as json_mod
import logging

from flask import jsonify

from config import config
from . import gauges_bp
from ._helpers import _get_registry

logger = logging.getLogger(__name__)


@gauges_bp.route('/gauges/<gauge_id>/storms', methods=['GET'])
def get_gauge_storms(gauge_id: str):
    """
    Get storm scenario data for a gauge.

    Returns flood simulation readings, storm responses, and flood stages
    from the per-gauge file in gaugets/ directory.
    """
    registry = _get_registry()
    gauge_loader = registry.get_gauge_loader()
    timeseries_loader = registry.get_timeseries_loader()

    gauge_data = gauge_loader.find_by_id(gauge_id)
    if not gauge_data:
        return jsonify({
            'status': 'error',
            'message': f'Gauge {gauge_id} not found'
        }), 404

    try:
        readings = timeseries_loader.get_readings_for_gauge(gauge_id)
        storm_responses = timeseries_loader.get_storm_responses(gauge_id)
        flood_stages = gauge_loader.get_flood_stages(gauge_id) or {}

        # Enrich storm responses with metadata from storm_sequences.json (storm_multi)
        sequences_path = config.get_input_path('storm_sequences.json')
        if sequences_path.exists():
            try:
                with open(sequences_path, 'r') as f:
                    sdata = json_mod.load(f)
                storm_meta = {}
                for seq in sdata.get('sequences', []):
                    for s in seq.get('storms', []):
                        storm_meta[s['storm_id']] = s
                for resp in storm_responses:
                    meta = storm_meta.get(resp.get('storm_id', ''), {})
                    resp['name'] = ''
                    resp['intensity_category'] = meta.get('intensity_category', '')
                    resp['effective_precipitation_mm'] = meta.get('precipitation_mm', 0)
                    resp['gauges_severe'] = 0
            except Exception:
                pass

        # Compute gauges_severe from per-gauge responses if trigger_summary empty
        gaugets_dir = config.get_gaugets_dir()
        if gaugets_dir.exists():
            # Count exceeded_severe per storm across all gauges
            severe_counts = {}
            for gf in gaugets_dir.glob('GAUGE-*.json'):
                try:
                    with open(gf, 'r') as f:
                        gdata = json_mod.load(f)
                    for gr in gdata.get('storm_responses', {}).get('responses', []):
                        if gr.get('exceeded_severe'):
                            sid = gr.get('storm_id', '')
                            severe_counts[sid] = severe_counts.get(sid, 0) + 1
                except Exception:
                    continue
            for resp in storm_responses:
                sid = resp.get('storm_id', '')
                if resp.get('gauges_severe', 0) == 0 and sid in severe_counts:
                    resp['gauges_severe'] = severe_counts[sid]

        # Sequence count (the unit of risk) from storm_sequences.json
        num_sequences = len(storm_responses)  # fallback
        seq_path = config.get_input_path('storm_sequences.json')
        if seq_path.exists():
            try:
                with open(seq_path, 'r') as f:
                    seq_meta = json_mod.load(f)
                num_sequences = seq_meta.get('num_sequences', len(seq_meta.get('sequences', [])))
            except Exception:
                pass

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'gauge_name': gauge_loader.get_gauge_name(gauge_id) or '',
            'flood_simulation': {
                'num_timesteps': len(readings),
                'readings': readings
            },
            'storm_responses': {
                'num_storms': len(storm_responses),
                'num_sequences': num_sequences,
                'responses': storm_responses
            },
            'flood_stages': flood_stages
        })

    except Exception as e:
        logger.error(f"Error getting storm data: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

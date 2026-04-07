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

        # Build storm→sequence mapping and aggregate to sequence-level peaks.
        # PRS pricing uses sequences (not individual storms) as the risk unit,
        # so the distribution panel must show one peak per sequence.
        sequences_path = config.get_input_path('storm_sequences.json')
        num_sequences = len(storm_responses)  # fallback
        sequence_responses = storm_responses  # fallback

        if sequences_path.exists():
            try:
                with open(sequences_path, 'r') as f:
                    sdata = json_mod.load(f)
                num_sequences = sdata.get('num_sequences',
                                          len(sdata.get('sequences', [])))

                # Map storm_id → sequence_id and store sequence metadata
                storm_to_seq = {}
                seq_meta = {}  # sequence_id → sequence metadata
                for seq in sdata.get('sequences', []):
                    seq_id = seq['sequence_id']
                    seq_meta[seq_id] = seq
                    for s in seq.get('storms', []):
                        storm_to_seq[s['storm_id']] = seq_id

                # Aggregate: keep the worst storm response per sequence
                seq_best = {}  # sequence_id → response with highest peak
                for resp in storm_responses:
                    sid = resp.get('storm_id', '')
                    seq_id = storm_to_seq.get(sid, sid)
                    resp['sequence_id'] = seq_id
                    prev = seq_best.get(seq_id)
                    if prev is None or resp['peak_level_m'] > prev['peak_level_m']:
                        seq_best[seq_id] = resp

                sequence_responses = list(seq_best.values())

                # Enrich responses with sequence metadata
                for resp in sequence_responses:
                    meta = seq_meta.get(resp.get('sequence_id', ''), {})
                    if not resp.get('intensity_category'):
                        resp['intensity_category'] = meta.get(
                            'intensity_category', '')
                    if not resp.get('effective_precipitation_mm'):
                        resp['effective_precipitation_mm'] = meta.get(
                            'total_precipitation_mm', 0)
                    if not resp.get('name'):
                        resp['name'] = meta.get('name', '')
            except Exception:
                pass

        # Enrich with metadata
        for resp in sequence_responses:
            resp.setdefault('name', '')
            resp.setdefault('intensity_category', '')
            resp.setdefault('effective_precipitation_mm', 0)
            resp.setdefault('gauges_severe', 0)

        # Compute gauges_severe from per-gauge responses
        gaugets_dir = config.get_gaugets_dir()
        if gaugets_dir.exists():
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
            for resp in sequence_responses:
                sid = resp.get('storm_id', '')
                if resp.get('gauges_severe', 0) == 0 and sid in severe_counts:
                    resp['gauges_severe'] = severe_counts[sid]

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'gauge_name': gauge_loader.get_gauge_name(gauge_id) or '',
            'flood_simulation': {
                'num_timesteps': len(readings),
                'readings': readings
            },
            'storm_responses': {
                'num_sequences': num_sequences,
                'responses': sequence_responses
            },
            'flood_stages': flood_stages
        })

    except Exception as e:
        logger.error(f"Error getting storm data: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

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

"""Gauge history, timeseries, and statistics endpoints."""

import logging

from flask import jsonify, request

from config import config
from . import gauges_bp
from ._helpers import _get_registry

logger = logging.getLogger(__name__)


@gauges_bp.route('/gauges/history/summary', methods=['GET'])
def get_gauge_history_summary():
    """Return count of gauges with pre-generated historical daily data."""
    import pathlib
    gaugehd_dir = pathlib.Path(config.get_gaugehd_dir())
    files = list(gaugehd_dir.glob('gauge_GAUGE-*.json')) if gaugehd_dir.exists() else []
    return jsonify({
        'status': 'success',
        'count': len(files),
        'gauges': len(files),
    })


@gauges_bp.route('/gauges/<gauge_id>/history', methods=['GET'])
def get_gauge_history(gauge_id: str):
    """
    Get historical daily water level data for a gauge.

    Query params:
        days: Number of recent days to return (default: all)

    Returns gauge metadata, statistics, flood stages, and daily observations
    from the pre-generated gaugehd JSON files.
    """
    import json as json_mod

    gaugehd_dir = config.get_gaugehd_dir()
    history_file = gaugehd_dir / f"gauge_{gauge_id}_hd.json"

    if not history_file.exists():
        return jsonify({
            'status': 'error',
            'message': f'No historical data for gauge {gauge_id}'
        }), 404

    try:
        with open(history_file, 'r') as f:
            data = json_mod.load(f)

        # Filter daily observations by days param
        days = request.args.get('days', type=int)
        if days is not None and days != 0 and (days < 1 or days > 3650):
            return jsonify({'status': 'error', 'message': 'days must be between 1 and 3650'}), 400
        observations = data.get('daily_observations', [])

        if days and days > 0 and len(observations) > days:
            observations = observations[-days:]

        return jsonify({
            'status': 'success',
            'gauge_metadata': data.get('gauge_metadata', {}),
            'statistics': data.get('statistics', {}),
            'flood_stages': data.get('gauge_metadata', {}).get('flood_stages', {}),
            'daily_observations': observations
        })

    except (FileNotFoundError, json_mod.JSONDecodeError) as e:
        logger.error("Error reading gauge history for %s: %s", gauge_id, e)
        return jsonify({'status': 'error', 'message': 'Failed to read gauge history'}), 500
    except Exception:
        logger.exception("Unexpected error reading gauge history for %s", gauge_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@gauges_bp.route('/gauges/<gauge_id>/timeseries', methods=['GET'])
def get_gaugets(gauge_id: str):
    """Get timeseries data for a gauge."""
    registry = _get_registry()
    gauge_loader = registry.get_gauge_loader()
    timeseries_loader = registry.get_timeseries_loader()

    # Verify gauge exists
    gauge_data = gauge_loader.find_by_id(gauge_id)
    if not gauge_data:
        return jsonify({
            'status': 'error',
            'message': f'Gauge {gauge_id} not found'
        }), 404

    try:
        gauge_name = gauge_loader.get_gauge_name(gauge_id)
        readings = timeseries_loader.get_readings_for_gauge(gauge_id, gauge_name)

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'count': len(readings) if readings else 0,
            'readings': readings or []
        })

    except Exception:
        logger.exception("Error getting timeseries for %s", gauge_id)
        return jsonify({'status': 'error', 'message': 'Failed to load timeseries'}), 500


@gauges_bp.route('/gauges/<gauge_id>/statistics', methods=['GET'])
def get_gauge_statistics(gauge_id: str):
    """Get statistics for a gauge's readings."""
    registry = _get_registry()
    gauge_loader = registry.get_gauge_loader()
    timeseries_loader = registry.get_timeseries_loader()

    # Verify gauge exists
    if not gauge_loader.find_by_id(gauge_id):
        return jsonify({
            'status': 'error',
            'message': f'Gauge {gauge_id} not found'
        }), 404

    try:
        stats = timeseries_loader.get_gauge_statistics(gauge_id)
        return jsonify({
            'status': 'success',
            'statistics': stats
        })
    except Exception:
        logger.exception("Error getting statistics for %s", gauge_id)
        return jsonify({'status': 'error', 'message': 'Failed to load statistics'}), 500

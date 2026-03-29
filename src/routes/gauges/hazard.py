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

"""Gauge hazard curve and PRS pricing endpoints."""

import logging

from flask import jsonify, request

from config import config

from . import gauges_bp
from ._helpers import _get_registry

logger = logging.getLogger(__name__)


@gauges_bp.route('/gauges/<gauge_id>/hazard', methods=['GET'])
def get_gauge_hazard(gauge_id: str):
    """
    Get hazard curve data for a gauge.

    Returns GEV parameters, curve points, return period levels,
    flood stage thresholds, annual flood probabilities, and term structures.
    """
    import json as json_mod

    registry = _get_registry()
    gauge_loader = registry.get_gauge_loader()

    gauge_data = gauge_loader.find_by_id(gauge_id)
    if not gauge_data:
        return jsonify({
            'status': 'error',
            'message': f'Gauge {gauge_id} not found'
        }), 404

    hazard_file = config.get_input_dir() / 'gaugehc.json'
    if not hazard_file.exists():
        return jsonify({
            'status': 'error',
            'message': 'Hazard curves data not available'
        }), 404

    try:
        with open(hazard_file, 'r') as f:
            hazard_data = json_mod.load(f)

        gauge_hazard = hazard_data.get('hazard_curves', {}).get(gauge_id)
        if not gauge_hazard:
            return jsonify({
                'status': 'error',
                'message': f'No hazard curve data for gauge {gauge_id}'
            }), 404

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'gauge_name': gauge_hazard.get('gauge_name', ''),
            'gev_parameters': {
                'location': gauge_hazard.get('gev_location'),
                'scale': gauge_hazard.get('gev_scale'),
                'shape': gauge_hazard.get('gev_shape')
            },
            'curve_points': gauge_hazard.get('curve_points', []),
            'return_period_levels': gauge_hazard.get('return_period_levels', {}),
            'flood_stages': {
                'FloodAlert': gauge_hazard.get('flood_alert_m'),
                'FloodWarning': gauge_hazard.get('flood_warning_m'),
                'SevereFloodWarning': gauge_hazard.get('severe_flood_warning_m')
            },
            'annual_flood_probs': {
                'alert': gauge_hazard.get('annual_flood_prob_alert'),
                'warning': gauge_hazard.get('annual_flood_prob_warning'),
                'severe': gauge_hazard.get('annual_flood_prob_severe')
            },
            'term_structures': {
                'alert': gauge_hazard.get('term_structure_alert', []),
                'warning': gauge_hazard.get('term_structure_warning', []),
                'severe': gauge_hazard.get('term_structure_severe', [])
            }
        })

    except Exception as e:
        logger.error(f"Error reading hazard curve data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@gauges_bp.route('/price_prs', methods=['POST', 'OPTIONS'])
def price_prs_endpoint():
    """
    Price a Physical Risk Swap for a gauge.

    Request JSON:
        gauge_id: Gauge ID
        trigger_level: 'alert', 'warning', or 'severe'
        notional: Notional amount (default 10M)
        tenor_years: Contract tenor (default 5)
        running_spread: Annual spread as decimal (default 0.01 = 100bps)
        risk_free_rate: Risk-free rate (default 0.03)
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    data = request.get_json()
    if data is None:
        return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400

    gauge_id = data.get('gauge_id')
    if not gauge_id:
        return jsonify({'status': 'error', 'message': 'gauge_id is required'}), 400

    trigger_level = data.get('trigger_level', 'warning')
    if trigger_level not in ('alert', 'warning', 'severe'):
        return jsonify({'status': 'error', 'message': 'trigger_level must be alert, warning, or severe'}), 400

    try:
        import json as json_mod

        from models.prs.prshc import price_prs

        hazard_file = config.get_input_dir() / 'gaugehc.json'
        if not hazard_file.exists():
            return jsonify({'status': 'error', 'message': 'Hazard curves data not available'}), 404

        with open(hazard_file, 'r') as f:
            hazard_data = json_mod.load(f)

        gauge_hazard = hazard_data.get('hazard_curves', {}).get(gauge_id)
        if not gauge_hazard:
            return jsonify({'status': 'error', 'message': f'No hazard data for gauge {gauge_id}'}), 404

        results = price_prs(
            gauge_data=gauge_hazard,
            trigger_level=trigger_level,
            notional=data.get('notional', 10_000_000),
            tenor_years=data.get('tenor_years', 5),
            running_spread=data.get('running_spread', 0.01),
            recovery_rate=0.0,
            risk_free_rate=data.get('risk_free_rate', 0.03),
            use_term_structure=True
        )

        from models.audit import log_model_usage
        log_model_usage("prs", "prs_pricing_api", parameters={
            "gauge_id": gauge_id,
            "trigger_level": trigger_level,
            "notional": data.get('notional', 10_000_000),
            "tenor_years": data.get('tenor_years', 5),
            "fair_spread_bps": results.get('fair_spread_bps'),
        }, context="API PRS pricing request", source="api")

        return jsonify({
            'status': 'success',
            **results
        })

    except Exception as e:
        logger.error(f"Error pricing PRS: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

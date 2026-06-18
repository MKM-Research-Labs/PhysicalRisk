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

"""P&L series and curve history endpoints."""

import json
import logging

from flask import jsonify, request

from . import trading_bp
from ._helpers import _get_engines

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# P&L Series
# ------------------------------------------------------------------

@trading_bp.route("/trading/pnl-series", methods=["GET"])
def get_pnl_series():
    """Get P&L time series for charting."""
    try:
        _, _, pnl_eng = _get_engines()
        series = pnl_eng.get_pnl_series()

        return jsonify({
            'status': 'success',
            'series': series,
        })

    except Exception as e:
        logger.error("P&L series error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


# ------------------------------------------------------------------
# Curve History
# ------------------------------------------------------------------

@trading_bp.route("/trading/curve-history", methods=["GET"])
def get_curve_history():
    """Get hazard term structure history from EOD snapshots.

    Query params:
        gauge_id: Gauge to extract curves for
        trigger: Trigger level (alert, warning, severe) — default severe
    """
    gauge_id = request.args.get('gauge_id')
    trigger = request.args.get('trigger', 'severe')

    if not gauge_id:
        return jsonify({"status": "error", "message": "gauge_id required"}), 400

    try:
        _, _, pnl_eng = _get_engines()
        eod_files = sorted(pnl_eng.eod_dir.glob('EOD-*.json'))

        history = []
        for f in eod_files:
            with open(f) as fh:
                snapshot = json.load(fh)
            ms = snapshot.get('market_state_snapshot', {})
            ts = ms.get('hazard_term_structure', {}).get(gauge_id, {}).get(trigger, {})
            if ts:
                history.append({
                    'date': snapshot.get('date', ''),
                    'hazard_rates': ts,
                })

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'trigger': trigger,
            'history': history,
        })

    except Exception as e:
        logger.error("Curve history error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

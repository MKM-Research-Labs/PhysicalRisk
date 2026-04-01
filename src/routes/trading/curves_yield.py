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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Yield curve endpoints."""

import logging

from flask import jsonify, request

from . import trading_bp
from ._helpers import _get_engines, _load_open_trades

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Yield Curve
# ------------------------------------------------------------------

@trading_bp.route("/trading/yield-curve", methods=["GET"])
def get_yield_curve():
    """Get current yield curve."""
    try:
        market_mgr, _, _ = _get_engines()
        state = market_mgr.load()

        return jsonify({
            'status': 'success',
            'yield_curve': state.get('yield_curve', {}),
            'risk_free_rate': state.get('risk_free_rate', 0.04),
        })

    except Exception as e:
        logger.error("Yield curve error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/yield-curve", methods=["POST"])
def update_yield_curve():
    """Update a yield curve point."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error",
                            "message": "No JSON body"}), 400

        tenor = int(data.get('tenor', 0))
        rate = float(data.get('rate', 0))

        if tenor < 1 or tenor > 30:
            return jsonify({"status": "error",
                            "message": "Tenor must be 1-30"}), 400

        market_mgr, _, _ = _get_engines()
        state = market_mgr.update_yield_curve(tenor, rate)

        return jsonify({
            'status': 'success',
            'yield_curve': state.get('yield_curve', {}),
            'message': f"Yield curve updated: {tenor}Y = {rate*100:.2f}%",
        })

    except Exception as e:
        logger.error("Yield curve update error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/yield-curve/commit", methods=["POST"])
def commit_yield_curve():
    """Commit the full yield curve and revalue all trades with P&L impact."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error",
                            "message": "No JSON body"}), 400

        rates = data.get('rates', {})
        if not rates:
            return jsonify({"status": "error",
                            "message": "rates required"}), 400

        market_mgr, delta_eng, _ = _get_engines()
        trades = _load_open_trades()

        # Revalue BEFORE commit to compute P&L impact
        state_before = market_mgr.load()
        enriched_before = delta_eng.revalue_all(trades, state_before)
        mtm_before = {}
        for t in enriched_before:
            if t.get('trade_status', 'Open').lower() != 'closed':
                mtm_before[t['swap_id']] = t.get('mtm', 0)

        # Commit yield curve
        state = market_mgr.commit_yield_curve(rates)

        # Revalue AFTER commit
        enriched_after = delta_eng.revalue_all(trades, state)
        affected = [
            t for t in enriched_after
            if t.get('trade_status', 'Open').lower() != 'closed'
        ]

        # P&L impact = change in MTM from yield curve edit
        per_trade_impact = [
            t.get('mtm', 0) - mtm_before.get(t['swap_id'], 0)
            for t in affected
        ]
        total_pnl_impact = sum(per_trade_impact)
        gross_pnl_impact = sum(abs(v) for v in per_trade_impact)
        total_fs01 = sum(t.get('gauge_fs01', 0) for t in affected)

        return jsonify({
            'status': 'success',
            'affected_trades': len(affected),
            'total_pnl_impact': round(total_pnl_impact, 2),
            'gross_pnl_impact': round(gross_pnl_impact, 2),
            'total_fs01': round(total_fs01, 2),
            'yield_curve': state.get('yield_curve', {}),
            'message': f"Committed yield curve, revalued {len(affected)} trades",
        })

    except Exception as e:
        logger.error("Yield curve commit error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/yield-curve/reset", methods=["POST"])
def reset_yield_curve():
    """Reset yield curve to default."""
    try:
        market_mgr, _, _ = _get_engines()
        state = market_mgr.reset_yield_curve()

        return jsonify({
            'status': 'success',
            'yield_curve': state.get('yield_curve', {}),
            'message': 'Yield curve reset to default',
        })

    except Exception as e:
        logger.error("Yield curve reset error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

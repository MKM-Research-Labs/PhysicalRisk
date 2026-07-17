# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Market state management endpoints."""

import logging

from flask import jsonify, request

from config.auth import FUNC_TRADE_PRS, WRITE

from .._rbac import require
from . import trading_bp
from ._helpers import _get_engines, _load_open_trades

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Market State
# ------------------------------------------------------------------

@trading_bp.route("/trading/market-state", methods=["GET"])
def get_market_state():
    """Get current market state with all effective rates."""
    try:
        market_mgr, _, _ = _get_engines()
        state = market_mgr.load()
        effective = market_mgr.get_all_effective_rates(state)

        return jsonify({
            'status': 'success',
            'market_state': {
                'last_updated': state.get('last_updated', ''),
                'risk_free_rate': state.get('risk_free_rate', 0.04),
                'yield_curve': state.get('yield_curve', {}),
                'hazard_term_structure': state.get(
                    'hazard_term_structure', {}),
                'num_adjusted': len(state.get('gauge_adjustments', {})),
            },
            'gauges': effective,
        })

    except Exception as e:
        logger.error("Market state error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/market-state", methods=["POST"])
@require(FUNC_TRADE_PRS, WRITE)
def update_market_state():
    """Update a gauge's hazard rate and revalue affected trades."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error",
                            "message": "No JSON body"}), 400

        gauge_id = data.get('gauge_id', '')
        trigger = data.get('trigger', 'warning')
        new_rate = float(data.get('new_rate', 0))
        notes = data.get('notes', '')

        if not gauge_id:
            return jsonify({"status": "error",
                            "message": "gauge_id required"}), 400

        market_mgr, delta_eng, pnl_eng = _get_engines()

        # Update market state
        state = market_mgr.update_gauge_rate(gauge_id, trigger, new_rate,
                                              notes)

        # Revalue trades
        trades = _load_open_trades()
        enriched = delta_eng.revalue_all(trades, state)

        # Count affected trades
        affected = [
            t for t in enriched
            if t.get('gauge_id') == gauge_id
            and t.get('trade_status', 'Open').lower() != 'closed'
        ]

        total_pnl_impact = sum(t.get('mtm', 0) for t in affected)

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'trigger': trigger,
            'new_rate': new_rate,
            'affected_trades': len(affected),
            'total_pnl_impact': round(total_pnl_impact, 2),
            'message': (f"Updated {gauge_id} {trigger} to "
                        f"{new_rate * 10000:.1f} bps, "
                        f"revalued {len(affected)} trades"),
        })

    except Exception as e:
        logger.error("Market state update error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/market-state/reset", methods=["POST"])
@require(FUNC_TRADE_PRS, WRITE)
def reset_market_state():
    """Reset market state to base curves."""
    try:
        data = request.get_json() or {}
        gauge_id = data.get('gauge_id')  # None = reset all

        market_mgr, _, _ = _get_engines()
        state = market_mgr.reset(gauge_id)

        return jsonify({
            'status': 'success',
            'message': ("Market state reset"
                        + (f" for {gauge_id}" if gauge_id else " (all)")),
        })

    except Exception as e:
        logger.error("Market reset error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

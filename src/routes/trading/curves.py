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

"""Yield curve, hazard term structure, P&L series, and curve history endpoints."""

import json
import logging

from flask import jsonify, request

from . import trading_bp
from ._helpers import _get_engines, _load_open_trades

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
        return jsonify({"status": "error", "message": str(e)}), 500


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
        return jsonify({"status": "error", "message": str(e)}), 500


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
        return jsonify({"status": "error", "message": str(e)}), 500


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
        return jsonify({"status": "error", "message": str(e)}), 500


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
        return jsonify({"status": "error", "message": str(e)}), 500


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
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------------------------------------------------------------
# Hazard Term Structure
# ------------------------------------------------------------------

@trading_bp.route("/trading/hazard-term-structure", methods=["GET"])
def get_hazard_term_structure():
    """Get hazard term structures for all gauges."""
    try:
        market_mgr, _, _ = _get_engines()
        state = market_mgr.load()

        return jsonify({
            'status': 'success',
            'hazard_term_structure': state.get(
                'hazard_term_structure', {}),
            'base_rates': state.get('base_rates', {}),
        })

    except Exception as e:
        logger.error("Hazard TS error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@trading_bp.route("/trading/hazard-term-structure", methods=["POST"])
def update_hazard_term_structure():
    """Update a hazard term structure point."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error",
                            "message": "No JSON body"}), 400

        gauge_id = data.get('gauge_id', '')
        trigger = data.get('trigger', 'warning')
        tenor = int(data.get('tenor', 0))
        rate = float(data.get('rate', 0))

        if not gauge_id:
            return jsonify({"status": "error",
                            "message": "gauge_id required"}), 400
        if tenor < 1 or tenor > 10:
            return jsonify({"status": "error",
                            "message": "Tenor must be 1-10"}), 400

        market_mgr, _, _ = _get_engines()
        state = market_mgr.update_hazard_term_point(
            gauge_id, trigger, tenor, rate)

        return jsonify({
            'status': 'success',
            'message': (f"Hazard TS updated: {gauge_id} {trigger} "
                        f"{tenor}Y = {rate*10000:.1f}bps"),
        })

    except Exception as e:
        logger.error("Hazard TS update error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@trading_bp.route("/trading/hazard-term-structure/commit",
                   methods=["POST"])
def commit_hazard_term_structure():
    """Commit a hazard term structure and revalue affected trades."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error",
                            "message": "No JSON body"}), 400

        gauge_id = data.get('gauge_id', '')
        trigger = data.get('trigger', 'warning')
        rates = data.get('rates', {})

        if not gauge_id:
            return jsonify({"status": "error",
                            "message": "gauge_id required"}), 400
        if not rates:
            return jsonify({"status": "error",
                            "message": "rates required"}), 400

        market_mgr, delta_eng, pnl_eng = _get_engines()
        trades = _load_open_trades()

        # Revalue BEFORE commit to compute P&L impact
        state_before = market_mgr.load()
        enriched_before = delta_eng.revalue_all(trades, state_before)
        mtm_before = {}
        for t in enriched_before:
            if (t.get('gauge_id') == gauge_id
                    and t.get('trade_status', 'Open').lower() != 'closed'):
                mtm_before[t['swap_id']] = t.get('mtm', 0)

        # Commit the full curve in one save
        state = market_mgr.commit_hazard_term_structure(
            gauge_id, trigger, rates)

        # Revalue AFTER commit
        enriched_after = delta_eng.revalue_all(trades, state)
        affected = [
            t for t in enriched_after
            if t.get('gauge_id') == gauge_id
            and t.get('trade_status', 'Open').lower() != 'closed'
        ]

        # P&L impact = change in MTM from curve edit
        per_trade_impact = [
            t.get('mtm', 0) - mtm_before.get(t['swap_id'], 0)
            for t in affected
        ]
        total_pnl_impact = sum(per_trade_impact)
        gross_pnl_impact = sum(abs(v) for v in per_trade_impact)
        total_fs01 = sum(t.get('gauge_fs01', 0) for t in affected)

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'trigger': trigger,
            'affected_trades': len(affected),
            'total_pnl_impact': round(total_pnl_impact, 2),
            'gross_pnl_impact': round(gross_pnl_impact, 2),
            'total_fs01': round(total_fs01, 2),
            'message': (f"Committed {gauge_id} {trigger} curve, "
                        f"revalued {len(affected)} trades"),
        })

    except Exception as e:
        logger.error("Hazard TS commit error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@trading_bp.route("/trading/hazard-term-structure/reset",
                   methods=["POST"])
def reset_hazard_term_structure():
    """Reset hazard term structure to defaults."""
    try:
        data = request.get_json() or {}
        gauge_id = data.get('gauge_id')

        market_mgr, _, _ = _get_engines()
        state = market_mgr.reset_hazard_term_structure(gauge_id)

        return jsonify({
            'status': 'success',
            'message': ('Hazard TS reset'
                        + (f' for {gauge_id}' if gauge_id else ' (all)')),
        })

    except Exception as e:
        logger.error("Hazard TS reset error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

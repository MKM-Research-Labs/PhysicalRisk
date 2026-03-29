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

"""Trading blotter and close-out endpoints."""

import base64
import json
import logging
from datetime import date, timedelta

from flask import jsonify, request

from config import config

from . import trading_bp
from ._helpers import _get_engines, _load_gauge_locations, _load_open_trades

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Trade Blotter
# ------------------------------------------------------------------

@trading_bp.route("/trading/blotter", methods=["GET"])
def get_blotter():
    """Get all open trades with deltas, MTM, and P&L."""
    try:
        market_mgr, delta_eng, pnl_eng = _get_engines()
        trades = _load_open_trades()
        market_state = market_mgr.load()

        # Enrich all trades
        enriched = delta_eng.revalue_all(trades, market_state)

        # Inject gauge_name from gauge locations for trades missing it
        gauge_locations = _load_gauge_locations()
        for t in enriched:
            if not t.get('gauge_name') and t.get('gauge_id'):
                gloc = gauge_locations.get(t['gauge_id'], {})
                t['gauge_name'] = gloc.get('name', t['gauge_id'])

        # Filter to open trades only (unless include_closed=true)
        include_closed = request.args.get('include_closed', 'false') == 'true'
        if not include_closed:
            enriched = [
                t for t in enriched
                if t.get('trade_status', 'Open').lower() != 'closed'
            ]

        # Compute P&L summary and merge per-trade P&L into enriched trades
        pnl = pnl_eng.compute_daily_pnl(enriched,
                                          pnl_eng._get_previous_eod(
                                              __import__('datetime').date.today().isoformat()))

        # Merge per-trade daily/market P&L back into enriched trades
        pnl_by_swap = {p['swap_id']: p for p in pnl.get('positions', [])}
        # Previous EOD fair spreads for curve-move indication
        prev_eod = pnl_eng._get_previous_eod(
            __import__('datetime').date.today().isoformat())
        prev_by_swap = {}
        if prev_eod:
            prev_by_swap = {
                p['swap_id']: p for p in prev_eod.get('positions', [])
            }
        for t in enriched:
            pnl_entry = pnl_by_swap.get(t.get('swap_id', ''), {})
            t['daily_pnl'] = pnl_entry.get('daily_pnl', 0)
            t['market_pnl'] = pnl_entry.get('market_pnl', 0)
            t['new_trade_pnl'] = pnl_entry.get('new_trade_pnl', 0)
            t['running_pnl'] = pnl_entry.get('running_pnl', 0)
            # Previous EOD fair spread for curve-move colouring
            prev_pos = prev_by_swap.get(t.get('swap_id', ''), {})
            t['prev_fair_spread_bps'] = prev_pos.get(
                'fair_spread_bps', t.get('fair_spread_bps', 0))

        return jsonify({
            'status': 'success',
            'trades': enriched,
            'summary': {
                'num_trades': pnl['num_open_trades'],
                'total_notional': pnl['total_notional'],
                'total_daily_pnl': pnl['total_daily_pnl'],
                'total_running_pnl': pnl['total_running_pnl'],
                'daily_pnl_from_trades': pnl['daily_pnl_from_trades'],
                'daily_pnl_from_market': pnl['daily_pnl_from_market'],
                'total_realized_pnl': pnl.get('total_realized_pnl', 0),
            },
        })

    except Exception as e:
        logger.error("Blotter error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------------------------------------------------------------
# Active Gauges (lightweight — for disabling empty blotter items)
# ------------------------------------------------------------------

@trading_bp.route("/trading/blotter/active-gauges", methods=["GET"])
def get_active_gauges():
    """Return gauge IDs that have at least one open trade.

    Scans PRS files and trade marks directly — no engine instantiation needed.
    """
    try:
        prs_dir = config.get_reports_dir("prs")
        trading_dir = config.get_trading_dir()

        # Load trade marks to check closed status
        marks = {}
        marks_path = trading_dir / "trade_marks.json"
        if marks_path.exists():
            with open(marks_path) as f:
                marks = json.load(f)

        active = set()
        for trade_file in sorted(prs_dir.glob("PRS-*.json")):
            try:
                with open(trade_file) as f:
                    trade = json.load(f)
                swap_id = trade.get('PhysicalSwap', {}).get('Header', {}).get('SwapID', '')
                mark = marks.get(swap_id, {})
                status = mark.get('trade_status', 'Open')
                if status.lower() != 'closed':
                    gauge_basket = trade.get('PhysicalSwap', {}).get(
                        'GaugeSet', {}).get('GaugeBasket', [])
                    gauge_id = gauge_basket[0].get('GaugeID', '') if gauge_basket else ''
                    if gauge_id:
                        active.add(gauge_id)
            except Exception:
                continue

        return jsonify({'status': 'success', 'gauge_ids': sorted(active)})
    except Exception as e:
        logger.warning("active-gauges error: %s", e)
        raise  # Let Flask return 500 so JS .catch() triggers fail-open behaviour


# ------------------------------------------------------------------
# Trade Close-Out
# ------------------------------------------------------------------

@trading_bp.route("/trading/close/<swap_id>", methods=["POST"])
def close_trade(swap_id: str):
    """Close out a trade at a user-negotiated closeout spread.

    Expects JSON body: { "closeout_spread_bps": <float> }
    Full revaluation is performed at the closeout spread using the model's
    risky annuity, giving the authoritative settlement amount.
    """
    from models.trading.delta_engine import compute_mark_to_market

    try:
        body = request.get_json(silent=True) or {}
        closeout_spread_bps = body.get('closeout_spread_bps')
        if closeout_spread_bps is None:
            return jsonify({"status": "error",
                            "message": "closeout_spread_bps is required"}), 400
        closeout_spread_bps = float(closeout_spread_bps)

        market_mgr, delta_eng, pnl_eng = _get_engines()

        # Find the trade
        trades = _load_open_trades()
        market_state = market_mgr.load()

        target = None
        for t in trades:
            sid = t.get('PhysicalSwap', {}).get('Header', {}).get('SwapID', '')
            if sid == swap_id:
                target = t
                break

        if not target:
            return jsonify({"status": "error",
                            "message": f"Trade {swap_id} not found"}), 404

        # Full revaluation: enrich to get model inputs (risky annuity, trade spread, etc.)
        enriched = delta_eng.enrich_trade(target, market_state)
        notional = enriched.get('original_notional', enriched.get('notional', 0))
        trade_spread = enriched['trade_spread_bps']
        risky_annuity = enriched['risky_annuity']
        is_payer = enriched.get('is_payer', True)

        # Settlement = full revaluation at negotiated closeout spread
        final_pnl = compute_mark_to_market(
            trade_spread, closeout_spread_bps, risky_annuity, notional, is_payer)
        settlement_amount = abs(final_pnl)
        close_spread = closeout_spread_bps

        # Compute T+2 settlement date
        today = date.today()
        settle = today
        days_added = 0
        while days_added < 2:
            settle += timedelta(days=1)
            if settle.weekday() < 5:
                days_added += 1
        settlement_date = settle.isoformat()

        mark = pnl_eng.close_trade(
            swap_id, close_spread, final_pnl, notional)

        # Update original trade JSON with close-out metadata
        prs_dir = config.get_reports_dir("prs")
        trade_path = prs_dir / f"{swap_id}.json"
        pdf_b64 = None
        if trade_path.exists():
            with open(trade_path) as f:
                cdm_record = json.load(f)

            ps_header = cdm_record.get('PhysicalSwap', {}).get('Header', {})
            ps_header['CloseOutDate'] = today.isoformat()
            ps_header['CloseOutSpread'] = round(close_spread, 2)
            ps_header['SettlementAmount'] = round(settlement_amount, 2)
            ps_header['SettlementDirection'] = (
                'Receivable' if final_pnl >= 0 else 'Payable')
            ps_header['SettlementDate'] = settlement_date

            with open(trade_path, 'w') as f:
                json.dump(cdm_record, f, indent=2)

            # Regenerate trade PDF with close-out section
            try:
                from routes.prs import _generate_trade_pdf
                cashflows = cdm_record.get('PhysicalSwap', {}).get(
                    'Pricing', {}).get('Cashflows', [])
                pdf_path = _generate_trade_pdf(
                    cdm_record, cashflows, prs_dir)
                with open(pdf_path, 'rb') as pf:
                    pdf_b64 = base64.b64encode(pf.read()).decode()
            except Exception as pdf_err:
                logger.warning("PDF regen failed for %s: %s",
                               swap_id, pdf_err)

        return jsonify({
            'status': 'success',
            'swap_id': swap_id,
            'close_spread_bps': close_spread,
            'final_pnl': final_pnl,
            'settlement_amount': settlement_amount,
            'settlement_date': settlement_date,
            'pdf_base64': pdf_b64,
            'message': f"Trade {swap_id} closed at {close_spread:.1f} bps",
        })

    except Exception as e:
        logger.error("Close trade error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

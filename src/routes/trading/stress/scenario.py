# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Stress scenario endpoint — hourly revaluation for a storm at a gauge."""

import json
import math
import logging

from flask import jsonify, request

from config import config
from .. import trading_bp
from .._helpers import _get_engines, _load_open_trades
from ._helpers import (
    STORM_HOURS,
    _load_stress_storms,
    _load_stress_storm,
    _get_predictor,
)

logger = logging.getLogger(__name__)


@trading_bp.route("/trading/stress/run", methods=["POST"])
def run_stress_scenario():
    """Run hourly stress revaluation for a storm at a gauge.

    Cash pricing (CDS in stress):
      cash_price = notional × P(flood) × direction
      stress_pnl = cash_price - mtm
    """
    try:
        body = request.get_json()
        if not body:
            return jsonify({"status": "error",
                            "message": "No JSON body"}), 400

        gauge_id = body.get('gauge_id', '')
        storm_id = body.get('storm_id', '')
        if not gauge_id or not storm_id:
            return jsonify({"status": "error",
                            "message": "gauge_id and storm_id required"}), 400

        # 1. Load storm data for this gauge
        storm = _load_stress_storm(storm_id)
        if not storm:
            return jsonify({"status": "error",
                            "message": f"Storm {storm_id} not found"}), 404

        gauge_resp = None
        for gr in storm.get('gauge_responses', []):
            if gr.get('gauge_id') == gauge_id:
                gauge_resp = gr
                break

        if not gauge_resp:
            return jsonify({"status": "error",
                            "message": "Storm/gauge combination not found"}), 404

        # 2. Load and enrich trades for this gauge
        market_mgr, delta_eng, _ = _get_engines()
        all_trades = _load_open_trades()
        market_state = market_mgr.load()
        enriched = delta_eng.revalue_all(all_trades, market_state)

        # Filter to open trades at this gauge
        gauge_trades = [
            t for t in enriched
            if t.get('gauge_id') == gauge_id
            and t.get('trade_status', 'Open').lower() != 'closed'
        ]

        if not gauge_trades:
            return jsonify({"status": "error",
                            "message": f"No open trades at {gauge_id}"}), 404

        # 3. Build hydrograph by scaling the gauge's flood simulation
        #    Same approach as Storm Scenarios (gsa_timeline.py)
        hydrograph = None
        gaugets_file = config.get_gaugets_dir() / f'{gauge_id}.json'
        if gaugets_file.exists():
            try:
                with open(gaugets_file) as gf:
                    gts_data = json.load(gf)
                readings = gts_data.get('flood_simulation', {}).get('readings', [])
                if readings:
                    raw_levels = [r.get('waterLevel', r.get('level', 0))
                                  for r in readings]
                    sim_base = min(raw_levels)
                    sim_peak = max(raw_levels)
                    sim_rise = sim_peak - sim_base
                    storm_rise = gauge_resp['peak_level_m'] - sim_base
                    scale_factor = (storm_rise / sim_rise
                                    if sim_rise > 0 else 1.0)
                    scaled = [round(sim_base + (v - sim_base) * scale_factor, 4)
                              for v in raw_levels]
                    # Pad or truncate to STORM_HOURS
                    if len(scaled) >= STORM_HOURS:
                        hydrograph = scaled[:STORM_HOURS]
                    else:
                        hydrograph = scaled + [scaled[-1]] * (STORM_HOURS - len(scaled))
            except Exception:
                logger.warning("Failed to load gaugets for %s, using fallback",
                               gauge_id)

        # Gaugets data is required — stress scenarios are tail events
        # that need real timeseries data, not synthetic approximations
        if hydrograph is None:
            return jsonify({
                "status": "error",
                "message": (
                    f"No gaugets data for {gauge_id}. "
                    "Run: python app.py port --stressm"
                ),
            }), 404

        # 4. Load flood predictor
        predictor = _get_predictor()
        if not predictor:
            return jsonify({"status": "error",
                            "message": "Stress models not found"}), 404

        # Read model AUC for this gauge from training summary
        model_auc = None
        try:
            summary = predictor._load_summary()
            for g in summary.get('gauges', []):
                if g.get('gauge_id') == gauge_id and g.get('status') == 'trained':
                    model_auc = g.get('metrics', {}).get('auc_roc')
                    break
        except Exception:
            pass

        # Get flood trigger levels from gauge data
        gaugehc_path = config.get_input_dir() / 'gaugehc.json'
        alert_level = 0
        warning_level = 0
        severe_level = 0
        if gaugehc_path.exists():
            with open(gaugehc_path) as f:
                ghc = json.load(f)
            gc = ghc.get('hazard_curves', {}).get(gauge_id, {})
            alert_level = gc.get('flood_alert_m', 0)
            warning_level = gc.get('flood_warning_m', 0)
            severe_level = gc.get('severe_flood_warning_m', 0)

        # 5. Build trade summary and map trigger to level
        trigger_levels = {
            'alert': alert_level,
            'warning': warning_level,
            'severe': severe_level,
        }
        trade_summary = []
        # Track knock-out state per trade: once trigger breached, contract
        # pays full notional and expires (no further P&L change)
        trade_triggered_hour = {}  # swap_id -> hour of knock-out
        for t in gauge_trades:
            direction = 1.0 if t['is_payer'] else -1.0
            trade_summary.append({
                'swap_id': t['swap_id'],
                'is_payer': t['is_payer'],
                'notional': t['notional'] * direction,  # signed: +Pay, -Rcv
                'tenor': t.get('tenor', 0),
                'trigger': t.get('trigger', ''),
                'trade_spread_bps': t.get('trade_spread_bps', 0),
                'fair_spread_bps': t.get('fair_spread_bps', 0),
                'mtm': t['mtm'],
                'counterparty': t.get('counterparty', ''),
            })

        # 6. Hourly revaluation with knock-out
        #    Once severe threshold is breached, P(flood) = 100% thereafter
        hourly = []
        severe_breached = False
        for h in range(STORM_HOURS):
            water_level = hydrograph[h]

            # Compute velocity and acceleration from hydrograph
            prev_level = hydrograph[h - 1] if h > 0 else water_level
            delta_w = water_level - prev_level
            prev_delta = (prev_level - hydrograph[h - 2]) if h > 1 else 0.0
            delta2_w = delta_w - prev_delta

            # Severe breach latches P(flood) to 100%
            if severe_level > 0 and water_level >= severe_level:
                severe_breached = True
            if severe_breached:
                p_flood = 1.0
            else:
                p_flood = predictor.predict(gauge_id, water_level,
                                            h, delta_w, delta2_w)

            per_trade = []
            portfolio_cash = 0
            portfolio_stress_pnl = 0

            for t in gauge_trades:
                swap_id = t['swap_id']
                direction = 1.0 if t['is_payer'] else -1.0
                signed_notional = t['notional'] * direction
                trig = t.get('trigger', 'severe')
                trig_level = trigger_levels.get(trig, severe_level)

                if swap_id in trade_triggered_hour:
                    # Already triggered — full notional payout, expired
                    cash_price = signed_notional
                    stress_pnl = signed_notional - t['mtm']
                elif trig_level > 0 and water_level >= trig_level:
                    # Trigger breached this hour — knock-out
                    trade_triggered_hour[swap_id] = h
                    cash_price = signed_notional
                    stress_pnl = signed_notional - t['mtm']
                else:
                    # Not yet triggered — probability-based pricing
                    cash_price = signed_notional * p_flood
                    stress_pnl = cash_price - t['mtm']

                per_trade.append({
                    'swap_id': swap_id,
                    'cash_price': round(cash_price, 2),
                    'stress_pnl': round(stress_pnl, 2),
                    'triggered': swap_id in trade_triggered_hour,
                })

                portfolio_cash += cash_price
                portfolio_stress_pnl += stress_pnl

            hourly.append({
                'hour': h,
                'water_level': water_level,
                'p_flood': round(p_flood, 6),
                'portfolio_cash': round(portfolio_cash, 2),
                'portfolio_stress_pnl': round(portfolio_stress_pnl, 2),
                'per_trade': per_trade,
            })

        # 7. Add triggered_hour to trade summaries
        for ts in trade_summary:
            th = trade_triggered_hour.get(ts['swap_id'])
            ts['triggered_hour'] = th  # None if never triggered

        # 8. Summary stats
        peak_idx = max(range(STORM_HOURS), key=lambda i: hourly[i]['p_flood'])
        max_stress_idx = max(range(STORM_HOURS),
                             key=lambda i: abs(hourly[i]['portfolio_stress_pnl']))
        num_triggered = len(trade_triggered_hour)
        first_trigger_hour = (min(trade_triggered_hour.values())
                              if trade_triggered_hour else None)

        # Blank P(flood) after KO — all trades settled, line should disappear
        if first_trigger_hour is not None:
            for h_idx in range(first_trigger_hour + 1, STORM_HOURS):
                hourly[h_idx]['p_flood'] = None

        # 9. Probability surface: P(flood) grid for height × time table
        # Always show full 168h horizon — table is horizontally scrollable.
        # Post-KO cells are blanked client-side using null probabilities.
        surface_hours = list(range(0, STORM_HOURS, 4))

        # Cap rows at severe level — above severe is obviously ~100%
        level_lo = math.floor(min(hydrograph) * 2) / 2 - 0.5
        level_hi = severe_level if severe_level > 0 else (
            math.ceil(max(hydrograph) * 2) / 2 + 0.5)
        if alert_level > 0:
            level_lo = min(level_lo, alert_level - 1.0)
        surface_levels = []
        lv = level_hi
        while lv >= level_lo - 0.01:
            surface_levels.append(round(lv, 1))
            lv -= 0.5
        # Compute P(flood) at each (level, hour) grid point
        surface_probs = []
        for lv in surface_levels:
            row = []
            for h in surface_hours:
                p = predictor.predict(gauge_id, lv, h, 0.0, 0.0)
                row.append(round(p * 100, 1))
            surface_probs.append(row)

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'storm_id': storm_id,
            'storm_name': storm.get('name', ''),
            'intensity_category': storm.get('intensity_category', ''),
            'model_auc': model_auc,
            'effective_precipitation_mm': storm.get(
                'effective_precipitation_mm', 0),
            'gauges_severe': storm.get('trigger_summary', {}).get(
                'gauges_severe', 0),
            'alert_level': alert_level,
            'warning_level': warning_level,
            'severe_level': severe_level,
            'hydrograph_source': (
                f"Gauge response: peak={gauge_resp.get('peak_level_m', 0.0):.2f}m, "
                f"{storm['duration_hours']}h storm"),
            'trades': trade_summary,
            'hourly': hourly,
            'summary': {
                'num_trades': len(gauge_trades),
                'total_notional': sum(
                    t['notional'] * (1.0 if t['is_payer'] else -1.0)
                    for t in gauge_trades),
                'total_mtm': round(sum(t['mtm'] for t in gauge_trades), 2),
                'peak_p_flood': round(hourly[peak_idx]['p_flood'], 4),
                'peak_p_flood_hour': peak_idx,
                'peak_water_level': hydrograph[peak_idx],
                'max_stress_pnl': hourly[max_stress_idx]['portfolio_stress_pnl'],
                'max_stress_hour': max_stress_idx,
                'peak_portfolio_cash': round(
                    hourly[peak_idx]['portfolio_cash'], 2),
                'num_triggered': num_triggered,
                'first_trigger_hour': first_trigger_hour,
            },
            'probability_surface': {
                'water_levels': surface_levels,
                'hours': surface_hours,
                'probabilities': surface_probs,
            },
        })

    except Exception as e:
        logger.error("Stress run error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

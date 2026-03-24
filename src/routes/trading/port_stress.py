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

"""Portfolio stress endpoints — cross-portfolio storm impact assessment."""

import json
import logging
from pathlib import Path

from flask import jsonify, request

from config import config
from . import trading_bp
from ._helpers import _get_engines, _load_open_trades, _load_gauge_locations
from .stress._helpers import (
    _load_stress_storms,
    _load_stress_storm,
    _synthesize_hydrograph,
    _get_predictor,
    STORM_HOURS,
)

logger = logging.getLogger(__name__)

# Module-level predictor cache (stressm directory, falls back to stress)
_stressm_predictor_cache = None


def invalidate_stressm_predictor():
    """Clear the cached predictor (call after classifier clear/retrain)."""
    global _stressm_predictor_cache
    _stressm_predictor_cache = None


def _get_stressm_predictor():
    """Load and cache FloodPredictor — tries stressm first, falls back to stress."""
    global _stressm_predictor_cache
    if _stressm_predictor_cache is None:
        try:
            from models.stress.flood_classifier import FloodPredictor
            model_dir = config.get_classifiers_dir()  # data/input/<catchment>/classifiers/
            if model_dir.exists():
                _stressm_predictor_cache = FloodPredictor(model_dir)
                return _stressm_predictor_cache
        except Exception:
            pass
        # Fall back to the standard stress predictor
        _stressm_predictor_cache = _get_predictor()
    return _stressm_predictor_cache


# ------------------------------------------------------------------
# Portfolio Storms List
# ------------------------------------------------------------------

@trading_bp.route("/trading/stress/portfolio-storms", methods=["GET"])
def get_portfolio_storms():
    """Get all stress storms sorted by portfolio impact (gauges_severe desc)."""
    try:
        data = _load_stress_storms()
        if not data:
            return jsonify({
                "status": "error",
                "message": "stress_storms not found"
            }), 404

        storms = []
        for s in data.get('storms', []):
            ts = s.get('trigger_summary', {})
            storm_id = s['storm_id']
            # Prefer the named label; never let the name field silently equal
            # the storm_id (that produces "STORM-xxx (STORM-xxx)" in the UI)
            name = s.get('name') or ''
            if not name or name == storm_id:
                name = storm_id   # JS `name || storm_id` handles the fallback
            storms.append({
                'storm_id': storm_id,
                'name': name,
                'intensity_category': s.get('intensity_category', ''),
                'duration_hours': s.get('duration_hours', 0),
                'peak_position': s.get('peak_position', 0.5),
                'effective_precipitation_mm': s.get('effective_precipitation_mm', 0),
                'gauges_severe': ts.get('gauges_severe', 0),
                'gauges_warning': ts.get('gauges_warning', 0),
                'gauges_alert': ts.get('gauges_alert', 0),
                'gauges_impacted': ts.get('gauges_impacted', 0),
            })

        # Severity rank (lower = worse) used as tie-breaker on equal gauge counts
        _INTENSITY_RANK = {
            'catastrophic': 0, 'extreme': 1, 'severe': 2,
            'moderate': 3, 'baseline': 4,
        }

        # Sort: most severe first, then most warnings, then most alerts,
        # then by named intensity category as a final tie-breaker
        storms.sort(key=lambda s: (
            -s['gauges_severe'],
            -s['gauges_warning'],
            -s['gauges_alert'],
            _INTENSITY_RANK.get(s.get('intensity_category', ''), 99),
        ))

        return jsonify({
            'status': 'success',
            'storms': storms,
            'count': len(storms),
        })

    except Exception as e:
        logger.error("Portfolio storms error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------------------------------------------------------------
# Portfolio Stress Run
# ------------------------------------------------------------------

# Severity ordering — centralised in config/port.py
from config.port import SEVERITY_ORDER as _SEVERITY_ORDER


@trading_bp.route("/trading/stress/portfolio-run", methods=["POST"])
def run_portfolio_stress():
    """Run portfolio-wide stress scenario for a storm.

    For each gauge with open trades, computes P(flood) at peak hour and
    calculates CDS-in-stress cash pricing for all trades.
    """
    try:
        body = request.get_json()
        if not body:
            return jsonify({"status": "error", "message": "No JSON body"}), 400

        storm_id = body.get('storm_id', '')
        if not storm_id:
            return jsonify({"status": "error",
                            "message": "storm_id required"}), 400

        # 1. Load storm data (individual file from stress_storms/ directory)
        storm = _load_stress_storm(storm_id)
        if not storm:
            return jsonify({"status": "error",
                            "message": f"Storm {storm_id} not found"}), 404

        # 2. Load flood thresholds from gaugehc.json
        gaugehc_path = config.get_input_dir() / 'gaugehc.json'
        gauge_thresholds = {}
        if gaugehc_path.exists():
            with open(gaugehc_path) as f:
                ghc = json.load(f)
            for gid, gc in ghc.get('hazard_curves', {}).items():
                gauge_thresholds[gid] = {
                    'alert': gc.get('flood_alert_m', 0),
                    'warning': gc.get('flood_warning_m', 0),
                    'severe': gc.get('severe_flood_warning_m', 0),
                }

        # 3. Load gauge locations
        gauge_locations = _load_gauge_locations()

        # 4. Load and revalue all trades
        market_mgr, delta_eng, _ = _get_engines()
        all_trades = _load_open_trades()
        market_state = market_mgr.load()
        enriched = delta_eng.revalue_all(all_trades, market_state)

        # Index open trades by gauge_id
        trades_by_gauge = {}
        for t in enriched:
            if t.get('trade_status', 'Open').lower() == 'closed':
                continue
            gid = t.get('gauge_id', '')
            if gid:
                trades_by_gauge.setdefault(gid, []).append(t)

        # 5. Load predictor
        predictor = _get_stressm_predictor()

        # 6. Build gauge response lookup from storm
        gauge_resp_lookup = {}
        for gr in storm.get('gauge_responses', []):
            gauge_resp_lookup[gr['gauge_id']] = gr

        # 7. Process each gauge that has open trades
        gauge_results = []

        for gid, gloc in gauge_locations.items():
            gauge_trades = trades_by_gauge.get(gid, [])
            thresholds = gauge_thresholds.get(gid, {})
            alert_level = thresholds.get('alert', 0)
            warning_level = thresholds.get('warning', 0)
            severe_level = thresholds.get('severe', 0)

            gauge_resp = gauge_resp_lookup.get(gid)

            # Build hydrograph (only if storm has a response for this gauge)
            hydrograph = None
            if gauge_resp:
                gaugets_file = config.get_gaugets_dir() / f'{gid}.json'
                if gaugets_file.exists():
                    try:
                        with open(gaugets_file) as gf:
                            gts_data = json.load(gf)
                        readings = gts_data.get(
                            'flood_simulation', {}).get('readings', [])
                        if readings:
                            raw_levels = [
                                r.get('waterLevel', r.get('level', 0))
                                for r in readings
                            ]
                            sim_base = min(raw_levels)
                            sim_peak = max(raw_levels)
                            sim_rise = sim_peak - sim_base
                            storm_rise = (gauge_resp['peak_level_m']
                                          - gauge_resp.get('base_level_m',
                                                           sim_base))
                            scale_factor = (storm_rise / sim_rise
                                            if sim_rise > 0 else 1.0)
                            scaled = [
                                round(sim_base + (v - sim_base) * scale_factor, 4)
                                for v in raw_levels
                            ]
                            if len(scaled) >= STORM_HOURS:
                                hydrograph = scaled[:STORM_HOURS]
                            else:
                                hydrograph = scaled + [scaled[-1]] * (
                                    STORM_HOURS - len(scaled))
                    except Exception:
                        logger.debug(
                            "Failed to load gaugets for %s, using fallback", gid)

                if hydrograph is None:
                    hydrograph = _synthesize_hydrograph(
                        gauge_resp.get('base_level_m', 0),
                        gauge_resp.get('level_change_m', 0),
                        storm['duration_hours'],
                        storm['peak_position'],
                    )

            # Determine peak water level and P(flood)
            peak_wl = 0.0
            peak_idx = 0
            p_flood = 0.0

            if hydrograph:
                peak_idx = max(range(STORM_HOURS), key=lambda i: hydrograph[i])
                peak_wl = hydrograph[peak_idx]

                # Compute derivatives at peak
                prev_wl = hydrograph[peak_idx - 1] if peak_idx > 0 else peak_wl
                delta_w = peak_wl - prev_wl
                prev_delta = (
                    (prev_wl - hydrograph[peak_idx - 2])
                    if peak_idx > 1 else 0.0
                )
                delta2_w = delta_w - prev_delta

                if severe_level > 0 and peak_wl >= severe_level:
                    p_flood = 1.0
                elif predictor:
                    try:
                        p_flood = predictor.predict(
                            gid, peak_wl, peak_idx, delta_w, delta2_w)
                    except Exception:
                        p_flood = 0.0

            # Determine threshold label
            if peak_wl > 0 and severe_level > 0 and peak_wl >= severe_level:
                threshold = 'severe'
            elif peak_wl > 0 and warning_level > 0 and peak_wl >= warning_level:
                threshold = 'warning'
            elif peak_wl > 0 and alert_level > 0 and peak_wl >= alert_level:
                threshold = 'alert'
            else:
                threshold = 'clean'

            impacted = threshold != 'clean' or (gauge_resp is not None)

            # Compute trade-level stress P&L
            trade_details = []
            gauge_stress_pnl = 0.0
            gauge_mtm = 0.0

            for t in gauge_trades:
                is_payer = t.get('is_payer', True)
                direction = 1.0 if is_payer else -1.0
                notional = t.get('notional', 0)
                signed_notional = notional * direction
                mtm = t.get('mtm', 0)
                cash_price = signed_notional * p_flood
                stress_pnl = cash_price - mtm

                gauge_stress_pnl += stress_pnl
                gauge_mtm += mtm

                trade_details.append({
                    'swap_id': t.get('swap_id', ''),
                    'trigger': t.get('trigger', ''),
                    'notional': round(signed_notional, 2),
                    'mtm': round(mtm, 2),
                    'cash_price': round(cash_price, 2),
                    'stress_pnl': round(stress_pnl, 2),
                    'is_payer': is_payer,
                    'tenor': t.get('tenor', 0),
                    'counterparty': t.get('counterparty', ''),
                })

            gauge_results.append({
                'gauge_id': gid,
                'gauge_name': gloc.get('name', gid),
                'lon': gloc.get('lon', 0),
                'lat': gloc.get('lat', 0),
                'p_flood': round(p_flood, 6),
                'p_flood_pct': round(p_flood * 100, 2),
                'threshold': threshold,
                'peak_water_level_m': round(peak_wl, 4),
                'alert_level': alert_level,
                'warning_level': warning_level,
                'severe_level': severe_level,
                'stress_pnl': round(gauge_stress_pnl, 2),
                'mtm': round(gauge_mtm, 2),
                'num_trades': len(gauge_trades),
                'trades': trade_details,
                'impacted': impacted,
            })

        # 8. Sort gauge results: by severity then stress_pnl ascending
        gauge_results.sort(key=lambda g: (
            _SEVERITY_ORDER.get(g['threshold'], 3),
            g['stress_pnl'],
        ))

        # 9. Portfolio aggregates
        portfolio_stress_pnl = sum(g['stress_pnl'] for g in gauge_results)
        portfolio_mtm = sum(g['mtm'] for g in gauge_results)
        gauges_severe = [g['gauge_id'] for g in gauge_results
                         if g['threshold'] == 'severe']
        gauges_warning = [g['gauge_id'] for g in gauge_results
                          if g['threshold'] == 'warning']
        gauges_alert = [g['gauge_id'] for g in gauge_results
                        if g['threshold'] == 'alert']

        ts = storm.get('trigger_summary', {})
        return jsonify({
            'status': 'success',
            'storm_id': storm_id,
            'storm_name': storm.get('name', ''),
            'intensity_category': storm.get('intensity_category', ''),
            'effective_precipitation_mm': storm.get(
                'effective_precipitation_mm', 0),
            'duration_hours': storm.get('duration_hours', 0),
            'portfolio_stress_pnl': round(portfolio_stress_pnl, 2),
            'portfolio_mtm': round(portfolio_mtm, 2),
            'num_gauges': len(gauge_results),
            'gauges_severe': gauges_severe,
            'gauges_warning': gauges_warning,
            'gauges_alert': gauges_alert,
            'gauges': gauge_results,
        })

    except Exception as e:
        logger.error("Portfolio stress run error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

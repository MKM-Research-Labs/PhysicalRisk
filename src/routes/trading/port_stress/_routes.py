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

from flask import jsonify, request

from config import config
from config.port import SEVERITY_ORDER as _SEVERITY_ORDER

from .. import trading_bp
from .._helpers import _get_engines, _load_gauge_locations, _load_open_trades
from ..stress._helpers import _load_stress_storm, _load_stress_storms
from ._compute import compute_gauge_results

logger = logging.getLogger(__name__)


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

        all_storms = data.get('storms', [])
        return jsonify({
            'status': 'success',
            'storms': storms,
            'count': len(storms),
            'total_storms': len(all_storms),
        })

    except Exception as e:
        logger.error("Portfolio storms error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


# ------------------------------------------------------------------
# Portfolio Stress Run
# ------------------------------------------------------------------

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

        # 5. Build gauge response lookup from storm
        gauge_resp_lookup = {}
        for gr in storm.get('gauge_responses', []):
            gauge_resp_lookup[gr['gauge_id']] = gr

        # 6. Process each gauge that has open trades
        gauge_results = compute_gauge_results(
            gauge_locations, trades_by_gauge, gauge_thresholds, gauge_resp_lookup)

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
        return jsonify({"status": "error", "message": "Internal server error"}), 500

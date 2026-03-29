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

"""Portfolio risk grid and trade map endpoints."""

import json
import logging

from flask import jsonify

from config import config

from . import trading_bp
from ._helpers import _get_engines, _load_gauge_locations, _load_open_trades

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Portfolio Risk Grid
# ------------------------------------------------------------------

@trading_bp.route("/trading/risk-grid", methods=["GET"])
def get_risk_grid():
    """Get portfolio risk grid (gauge x maturity FS01)."""
    try:
        market_mgr, delta_eng, _ = _get_engines()
        trades = _load_open_trades()
        state = market_mgr.load()

        enriched = delta_eng.revalue_all(trades, state)

        # Load gauge locations for west-to-east ordering and names
        gauge_locations = _load_gauge_locations()
        grid = delta_eng.build_risk_grid(enriched, gauge_locations)

        return jsonify({
            'status': 'success',
            'grid': grid,
        })

    except Exception as e:
        logger.error("Risk grid error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------------------------------------------------------------
# Trade Map
# ------------------------------------------------------------------

@trading_bp.route("/trading/trade-map", methods=["GET"])
def get_trade_map():
    """Get trade positions with coordinates for map display."""
    try:
        market_mgr, delta_eng, pnl_eng = _get_engines()
        trades = _load_open_trades()
        state = market_mgr.load()
        enriched = delta_eng.revalue_all(trades, state)

        # Compute proper daily P&L (same as blotter endpoint)
        pnl_result = pnl_eng.compute_daily_pnl(
            enriched,
            pnl_eng._get_previous_eod(
                __import__('datetime').date.today().isoformat()))
        pnl_by_swap = {
            p['swap_id']: p for p in pnl_result.get('positions', [])
        }

        # Load gauge locations from gaugehc.json
        gauge_locations = _load_gauge_locations()

        # Load gauge locations from gauge.json if not in gaugehc
        gauge_path = config.get_input_dir() / 'gauge.json'
        if gauge_path.exists():
            with open(gauge_path) as f:
                gauge_data = json.load(f)
            for g in gauge_data.get('flood_gauges', gauge_data if isinstance(gauge_data, list) else []):
                fg = g.get('FloodGauge', {})
                gid = fg.get('GaugeID', '')
                if gid and gid not in gauge_locations:
                    loc = fg.get('Location', {})
                    if 'Latitude' in loc and 'Longitude' in loc:
                        gauge_locations[gid] = {
                            'lat': loc['Latitude'],
                            'lon': loc['Longitude'],
                            'name': fg.get('GaugeName', '')}

        # Load property locations
        prop_path = config.get_input_dir() / 'property.json'
        prop_locations = {}
        if prop_path.exists():
            with open(prop_path) as f:
                prop_data = json.load(f)
            for p in prop_data.get('properties', prop_data if isinstance(prop_data, list) else []):
                ph = p.get('PropertyHeader', {})
                pid = ph.get('PropertyID', '')
                loc = ph.get('Location', {})
                if pid and 'Latitude' in loc and 'Longitude' in loc:
                    prop_locations[pid] = {
                        'lat': loc['Latitude'],
                        'lon': loc['Longitude'],
                        'address': ph.get('Address', '')}

        # Hazard term structures for rate levels in popups
        hazard_ts = state.get('hazard_term_structure', {})

        # Build map data with per-tenor FS01 and P&L breakdown
        gauge_positions = {}
        property_positions = []

        for t in enriched:
            if t.get('trade_status', '').lower() == 'closed':
                continue

            gid = t.get('gauge_id', '')
            if gid not in gauge_positions:
                gloc = gauge_locations.get(gid, {})
                gauge_positions[gid] = {
                    'gauge_id': gid,
                    'lat': gloc.get('lat', 0),
                    'lon': gloc.get('lon', 0),
                    'gauge_name': gloc.get('name', gid),
                    'total_notional': 0,
                    'net_notional': 0,
                    'net_fs01': 0,
                    'num_trades': 0,
                    'fs01_by_tenor': {},
                    'hazard_by_tenor': {},
                    'daily_pnl': 0,
                    'running_pnl': 0,
                }

            notional = t.get('notional', 0)
            gauge_positions[gid]['total_notional'] += notional
            direction = 1 if t.get('is_payer') else -1
            gauge_positions[gid]['net_notional'] += notional * direction
            gauge_positions[gid]['net_fs01'] += t.get('gauge_fs01', 0)
            gauge_positions[gid]['num_trades'] += 1

            # FS01 by tenor
            tenor = t.get('tenor', 0)
            tenor_label = f"{tenor}Y"
            fs01_by_tenor = gauge_positions[gid]['fs01_by_tenor']
            fs01_by_tenor[tenor_label] = fs01_by_tenor.get(
                tenor_label, 0) + t.get('gauge_fs01', 0)

            # Hazard rate by tenor (bps) from market state
            trigger = t.get('trigger', 'severe')
            gauge_hts = hazard_ts.get(gid, {}).get(trigger, {})
            rate = gauge_hts.get(str(tenor), 0)
            gauge_positions[gid]['hazard_by_tenor'][tenor_label] = \
                round(rate * 10000, 1)  # decimal → bps

            # P&L accumulators — use PnL engine values (not enriched MTM)
            pnl_entry = pnl_by_swap.get(t.get('swap_id', ''), {})
            gauge_positions[gid]['daily_pnl'] += pnl_entry.get(
                'daily_pnl', 0)
            gauge_positions[gid]['running_pnl'] += pnl_entry.get(
                'running_pnl', 0)

            # Property positions
            pid = t.get('property_id')
            if pid:
                ploc = prop_locations.get(pid, {})
                property_positions.append({
                    'property_id': pid,
                    'lat': ploc.get('lat', 0),
                    'lon': ploc.get('lon', 0),
                    'address': ploc.get('address', ''),
                    'gauge_id': gid,
                    'gauge_lat': gauge_locations.get(gid, {}).get('lat', 0),
                    'gauge_lon': gauge_locations.get(gid, {}).get('lon', 0),
                    'basis_dv01': t.get('basis_dv01', 0),
                    'notional': t.get('notional', 0),
                    'swap_id': t.get('swap_id', ''),
                })

        # Round numeric values
        for gp in gauge_positions.values():
            gp['net_fs01'] = round(gp['net_fs01'], 2)
            gp['daily_pnl'] = round(gp['daily_pnl'], 2)
            gp['running_pnl'] = round(gp['running_pnl'], 2)
            gp['fs01_by_tenor'] = {
                k: round(v, 2) for k, v in
                sorted(gp['fs01_by_tenor'].items(),
                       key=lambda x: int(x[0].replace('Y', '')))
            }

        return jsonify({
            'status': 'success',
            'gauges': list(gauge_positions.values()),
            'properties': property_positions,
        })

    except Exception as e:
        logger.error("Trade map error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

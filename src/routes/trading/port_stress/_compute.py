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

"""Per-gauge stress computation for the portfolio-run endpoint."""

import logging

from models.stress.flood_poly import p_flood_simple

from ..stress._helpers import STORM_HOURS, build_scaled_hydrograph

logger = logging.getLogger(__name__)


def compute_gauge_results(gauge_locations, trades_by_gauge,
                          gauge_thresholds, gauge_resp_lookup):
    """Compute the per-gauge stress record for every gauge location.

    For each gauge: build the (scaled) hydrograph, derive peak water level and
    P(flood), classify the threshold band, and price every open trade's
    stress P&L. Returns the list of gauge result dicts.
    """
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
            hydrograph = build_scaled_hydrograph(gid, gauge_resp)
            if hydrograph is None:
                logger.warning(
                    "No gaugets data for %s — using flat hydrograph", gid)
                hydrograph = [gauge_resp.get('peak_level_m', 0.0)] * STORM_HOURS

        # Determine peak water level and P(flood)
        peak_wl = 0.0
        peak_idx = 0
        p_flood = 0.0

        if hydrograph:
            peak_idx = max(range(STORM_HOURS), key=lambda i: hydrograph[i])
            peak_wl = hydrograph[peak_idx]

            if severe_level > 0:
                p_flood = p_flood_simple(peak_wl, severe_level)

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

        gauge_rec = {
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
        }
        # Include hydrograph for gauges with trades (hourly P&L chart)
        if hydrograph and gauge_trades:
            gauge_rec['hydrograph'] = [round(v, 4) for v in hydrograph]
        gauge_results.append(gauge_rec)

    return gauge_results

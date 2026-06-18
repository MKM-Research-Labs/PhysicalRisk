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

"""Stress gauges endpoint — gauge list with trade counts for stress tab."""

import logging

from flask import jsonify

from .. import trading_bp
from .._helpers import _load_open_trades, _load_gauge_locations

logger = logging.getLogger(__name__)


@trading_bp.route("/trading/stress/gauges", methods=["GET"])
def get_stress_gauges():
    """Get all gauges with trade counts for stress tab dropdown."""
    try:
        gauge_locations = _load_gauge_locations()
        trades = _load_open_trades()

        # Count open trades per gauge
        trade_counts = {}
        for t in trades:
            ps = t.get('PhysicalSwap', {})
            basket = ps.get('GaugeSet', {}).get('GaugeBasket', [])
            gid = basket[0]['GaugeID'] if basket else ''
            status = t.get('TradingMetadata', {}).get(
                'trade_status', 'Open')
            if gid and status.lower() != 'closed':
                trade_counts[gid] = trade_counts.get(gid, 0) + 1

        gauges = []
        for gid, gloc in gauge_locations.items():
            if gid.startswith('SYNTH-'):
                continue
            gauges.append({
                'gauge_id': gid,
                'gauge_name': gloc.get('name', gid),
                'lon': gloc.get('lon', 0),
                'lat': gloc.get('lat', 0),
                'trade_count': trade_counts.get(gid, 0),
            })

        # Sort by longitude (west to east)
        gauges.sort(key=lambda g: g['lon'])

        return jsonify({
            'status': 'success',
            'gauges': gauges,
            'count': len(gauges),
        })

    except Exception as e:
        logger.error("Stress gauges error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

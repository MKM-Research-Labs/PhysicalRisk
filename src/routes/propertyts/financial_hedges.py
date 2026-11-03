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

"""
Storm hedge payouts endpoint.

GET /propertyts/<storm_id>/hedges
    The REIT's hedge payouts and the desk's net position for one storm from
    the storm list. A hedge pays when its gauge reaches severe in the storm.
"""

from flask import jsonify, request

from config import config
from models.trading.storm_hedges import storm_hedge_report

from .blueprint import propertyts_bp


@propertyts_bp.route('/propertyts/<storm_id>/hedges', methods=['GET', 'OPTIONS'])
def storm_hedges(storm_id: str):
    """REIT hedge payouts and desk position for ``storm_id``."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    report = storm_hedge_report(config.catchment_id, [storm_id])
    return jsonify({'status': 'success', 'storm_id': storm_id, **report})

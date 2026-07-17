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

"""Commercial asset / loan list endpoints (startup-preloader counts)."""

from flask import jsonify

import database
from config import config

from ..blueprint import commercial_bp


@commercial_bp.route('/commercial', methods=['GET'])
def list_commercial():
    """List all commercial assets in the active catchment.

    Mirrors GET /api/v1/properties — used by the startup preloader for
    the bottom-left status popup count and to build a PropertyID →
    BuildingName / address lookup for the right-click menu titles.

    Response shape::

        {"status": "success", "count": N, "commercial_assets": [...]}
    """
    assets = database.list_commercial(config.catchment_id)
    return jsonify({
        'status': 'success',
        'count': len(assets),
        'commercial_assets': assets,
    })


@commercial_bp.route('/commercial-loans', methods=['GET'])
def list_commercial_loans():
    """List all commercial loans in the active catchment.

    Mirrors GET /api/v1/rloans — used by the startup preloader for
    the count stat.

    Response shape::

        {"status": "success", "count": N, "commercial_loans": [...]}
    """
    loans = database.list_commercial_loans(config.catchment_id)
    return jsonify({
        'status': 'success',
        'count': len(loans),
        'commercial_loans': loans,
    })

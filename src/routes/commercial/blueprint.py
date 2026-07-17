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

"""Commercial-asset Flask blueprint + shared request helpers.

Creates the ``commercial_bp`` Blueprint and exposes the small helpers
shared across the sub-modules (request parsing). Each sub-module imports
``commercial_bp`` from here and registers its routes on it; the package
``__init__`` then imports every sub-module so the routes are live.
"""

import logging

from flask import jsonify, request, Blueprint

logger = logging.getLogger(__name__)

commercial_bp = Blueprint('commercial', __name__)


def _parse_commercial_request():
    """Pull and validate ``propertyId`` from the JSON body.

    Returns (property_id, data_or_error_response).
    Same convention as _parse_property_request in properties.py.
    """
    if request.method == 'OPTIONS':
        return None, ('', 204)
    data = request.get_json(silent=True) or {}
    property_id = data.get('propertyId') or data.get('property_id')
    if not property_id:
        return None, (jsonify({
            'status': 'error',
            'message': 'propertyId is required',
        }), 400)
    return property_id, data

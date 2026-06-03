# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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

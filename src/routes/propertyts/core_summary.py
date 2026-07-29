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
Core property timeseries endpoints — summary and per-property floods.

Endpoints
---------
GET /propertyts/summary
GET /properties/<prop_id>/floods
"""

import logging

from flask import jsonify, request

import database
from config import config

from . import propertyts_bp

logger = logging.getLogger(__name__)


def _load_property_or_404(prop_id):
    """Handle OPTIONS preflight, locate a property flood file, and load it.

    Returns ``(None, data)`` on success, or ``(response, None)`` when an
    early return (OPTIONS / 404) should be sent.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), None

    data = database.get_property_timeseries(config.catchment_id, prop_id)
    if data is None:
        return (jsonify({
            'status': 'error',
            'message': f'Property {prop_id} not found in flood timeseries'
        }), 404), None
    return None, data


@propertyts_bp.route('/propertyts/summary', methods=['GET', 'OPTIONS'])
def propertyts_summary():
    """Get portfolio flood summary statistics."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    data = database.get_portfolio_flood_summary(config.catchment_id)
    if data is None:
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated. Run: python phys.py port --propertyts'
        }), 404

    return jsonify({
        'status': 'success',
        'data': data
    })


@propertyts_bp.route('/properties/<prop_id>/floods', methods=['GET', 'OPTIONS'])
def property_floods(prop_id: str):
    """
    Get flood events for a specific property.

    Query params:
        include_readings: bool (default false) - include hourly hydrograph readings
    """
    early, data = _load_property_or_404(prop_id)
    if early is not None:
        return early

    include_readings = request.args.get('include_readings', 'false').lower() == 'true'
    if not include_readings:
        for event in data.get('flood_events', []):
            event.pop('readings', None)

    return jsonify({
        'status': 'success',
        'data': data
    })

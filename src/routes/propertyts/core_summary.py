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

"""
Core property timeseries endpoints — summary and per-property floods.

Endpoints
---------
GET /propertyts/summary
GET /properties/<prop_id>/floods
"""

import json
import logging

from flask import jsonify, request

from config import config

from . import _get_propertyts_dir, propertyts_bp

logger = logging.getLogger(__name__)


def _load_property_or_404(prop_id):
    """Handle OPTIONS preflight, locate a property flood file, and load it.

    Returns ``(None, data)`` on success, or ``(response, None)`` when an
    early return (OPTIONS / 404) should be sent.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), None

    pts_dir = _get_propertyts_dir()
    prop_file = pts_dir / f'{prop_id}.json'

    if not prop_file.exists():
        return (jsonify({
            'status': 'error',
            'message': f'Property {prop_id} not found in flood timeseries'
        }), 404), None

    with open(prop_file, 'r') as f:
        data = json.load(f)
    return None, data


@propertyts_bp.route('/propertyts/summary', methods=['GET', 'OPTIONS'])
def propertyts_summary():
    """Get portfolio flood summary statistics."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    summary_path = _get_propertyts_dir() / 'portfolio_flood_summary.json'
    if not summary_path.exists():
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated. Run: python app.py port --propertyts'
        }), 404

    with open(summary_path, 'r') as f:
        data = json.load(f)

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

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

"""Gauge CRUD endpoints — list and get."""

import logging

from flask import jsonify, request

from . import gauges_bp
from ._helpers import _get_registry

logger = logging.getLogger(__name__)


@gauges_bp.route('/gauges', methods=['GET', 'OPTIONS'])
@gauges_bp.route('/list_gauges', methods=['GET', 'OPTIONS'])
def list_gauges():
    """List all gauges."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    registry = _get_registry()
    loader = registry.get_gauge_loader()

    try:
        gauges = [
            g for g in loader.list_all()
            if not g.get('gauge_id', '').startswith('SYNTH-')
        ]
        return jsonify({
            'status': 'success',
            'message': f'Found {len(gauges)} available gauges',
            'count': len(gauges),
            'gauges': gauges
        })
    except Exception as e:
        logger.error(f"Error listing gauges: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@gauges_bp.route('/gauges/<gauge_id>', methods=['GET'])
def get_gauge(gauge_id: str):
    """Get a specific gauge by ID."""
    registry = _get_registry()
    loader = registry.get_gauge_loader()

    gauge_data = loader.find_by_id(gauge_id)
    if not gauge_data:
        return jsonify({
            'status': 'error',
            'message': f'Gauge {gauge_id} not found'
        }), 404

    return jsonify({
        'status': 'success',
        'gauge': gauge_data
    })

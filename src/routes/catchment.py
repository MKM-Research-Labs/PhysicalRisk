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
Catchment selection routes for MKM Research Labs PRS Platform.
"""

import logging
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

logger = logging.getLogger(__name__)

catchment_bp = Blueprint('catchment', __name__)


@catchment_bp.route('/select-catchment', methods=['GET'])
def serve_catchment_selector():
    """
    Serve the catchment selection landing page.
    This is the entry point for the application.
    """
    try:
        # Get the HTML file from project root
        src_root = Path(__file__).resolve().parent.parent
        html_path = src_root / 'static' / 'select_catchment.html'

        if not html_path.exists():
            return jsonify({
                'status': 'error',
                'message': 'Catchment selection page not found'
            }), 404

        return send_file(html_path, mimetype='text/html')

    except Exception as e:
        logger.error(f"Failed to serve catchment selector: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error loading catchment selector: {str(e)}'
        }), 500


@catchment_bp.route('/api/set-catchment', methods=['POST', 'OPTIONS'])
def set_catchment():
    """
    API endpoint to set the active catchment.
    Called by the catchment selector page.
    """
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400

        catchment_id = data.get('catchment')

        if not catchment_id:
            return jsonify({
                'status': 'error',
                'message': 'Catchment ID is required'
            }), 400

        logger.info(f"Setting catchment to: {catchment_id}")

        from config import config
        available = config.list_catchments()
        if catchment_id.lower() not in available:
            return jsonify({
                'status': 'error',
                'message': (
                    f'Catchment "{catchment_id}" not registered. '
                    f'Available: {", ".join(available)}.'
                )
            }), 400

        logger.info(f"Successfully validated catchment: {catchment_id}")

        # Return success with redirect to visualization
        return jsonify({
            'status': 'success',
            'message': f'Catchment set to {catchment_id}',
            'catchment': catchment_id,
            'redirect_url': '/visualization'  # Generate and show the interactive map
        }), 200

    except Exception as e:
        logger.error(f"Failed to set catchment: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error setting catchment: {str(e)}'
        }), 500

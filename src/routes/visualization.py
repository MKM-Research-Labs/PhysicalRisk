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
Visualization routes for MKM Research Labs PRS Platform.
"""

import logging

from flask import Blueprint, jsonify, redirect, send_file

from config import config

logger = logging.getLogger(__name__)

visualization_bp = Blueprint('visualization', __name__)


@visualization_bp.route('/visualization', methods=['GET'])
def serve_visualization():
    """
    Generate and serve the interactive visualization for the current catchment.

    This route:
    1. Gets the current catchment from config
    2. Generates the visualization using DataLoader with JSONFileConfig
    3. Serves the resulting HTML file
    """
    try:
        catchment = config.CATCHMENT
        logger.info(f"Generating visualization for catchment: {catchment}")

        from visual.core.visualizer import TCEventVisualization

        viz = TCEventVisualization(
            input_dir=config.get_input_dir(),
            output_dir=config.get_results_dir()
        )

        output_filename = f"visualization_{catchment}.html"

        logger.info(f"Creating map: {output_filename}")
        viz_path = viz.create_event_map(output_filename=output_filename)

        if not viz_path or not viz_path.exists():
            logger.error("Visualization generation failed - file not created")
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate visualization'
            }), 500

        logger.info(f"Visualization generated successfully: {viz_path}")

        # Serve the generated HTML file
        return send_file(
            viz_path,
            mimetype='text/html',
            as_attachment=False
        )

    except ImportError as e:
        logger.error(f"Visualization module not available: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'hint': 'Make sure the visualization package is installed'
        }), 503

    except Exception as e:
        logger.error(f"Error generating visualization: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error generating visualization: {str(e)}'
        }), 500


@visualization_bp.route('/visualization/<catchment_id>', methods=['GET'])
def serve_visualization_for_catchment(catchment_id: str):
    """
    Generate and serve visualization for a specific catchment.

    This allows direct access to a catchment's visualization without
    going through the selector.
    """
    try:
        # Validate catchment exists
        if catchment_id.lower() != 'thames':
            return jsonify({
                'status': 'error',
                'message': f'Catchment "{catchment_id}" not yet available. Only "thames" is supported.'
            }), 400

        # Temporarily set the catchment (in a real implementation, this would be session-based)
        logger.info(f"Generating visualization for specific catchment: {catchment_id}")

        # For now, just redirect to the main visualization route
        return redirect('/visualization')

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

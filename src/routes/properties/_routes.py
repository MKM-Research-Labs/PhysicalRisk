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

"""Property endpoint route handlers, registered on ``properties_bp``."""

import logging
import traceback

from flask import jsonify, request

from config import config
from loaders import LoaderRegistry

from . import properties_bp

logger = logging.getLogger(__name__)


def _get_registry() -> LoaderRegistry:
    """Get loader registry with configured data directory."""
    return LoaderRegistry(data_dir=config.get_input_dir())


def _parse_property_request():
    """Handle OPTIONS, parse JSON body, and validate propertyId.

    Returns (None, response) on error/OPTIONS, or (property_id, None) on success.
    """
    if request.method == 'OPTIONS':
        return None, jsonify({'status': 'ok'})

    data = request.get_json()
    if data is None:
        return None, (jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400)

    property_id = data.get('propertyId')
    if not property_id:
        return None, (jsonify({'status': 'error', 'message': 'Property ID is required'}), 400)

    return property_id, data


@properties_bp.route('/properties', methods=['GET'])
def list_properties():
    """List all properties."""
    registry = _get_registry()
    loader = registry.get_property_loader()

    try:
        properties = loader.list_all()
        return jsonify({
            'status': 'success',
            'count': len(properties),
            'properties': properties
        })
    except Exception as e:
        logger.error(f"Error listing properties: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@properties_bp.route('/properties/<property_id>', methods=['GET'])
def get_property(property_id: str):
    """Get a specific property by ID."""
    registry = _get_registry()
    loader = registry.get_property_loader()

    property_data = loader.find_by_id(property_id)
    if not property_data:
        return jsonify({
            'status': 'error',
            'message': f'Property {property_id} not found'
        }), 404

    return jsonify({
        'status': 'success',
        'property': property_data
    })


@properties_bp.route('/properties/report', methods=['POST', 'OPTIONS'])
@properties_bp.route('/generate_property_report', methods=['POST', 'OPTIONS'])
def generate_report():
    """
    Generate a property report.

    Request: {"propertyId": "..."}
    """
    property_id, result = _parse_property_request()
    if property_id is None:
        return result
    data = result

    registry = _get_registry()
    property_loader = registry.get_property_loader()
    rloan_loader = registry.get_rloan_loader()

    try:
        # Find property
        property_data = property_loader.find_by_id(property_id)
        if not property_data:
            return jsonify({
                'status': 'error',
                'message': f'Property {property_id} not found'
            }), 404

        # Find associated mortgage
        rloan_data = rloan_loader.find_by_property_id(property_id)

        # Import and generate report
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=property_data,
            rloan_data=rloan_data,
            output_dir=config.get_property_reports_dir(),
            report_type=data.get('reportType', 'full'),
            auto_open=False
        )

        logger.info(f"Generated property report: {report_path}")

        from routes.utils import pdf_success_response
        return pdf_success_response(report_path)

    except ImportError as e:
        logger.error(f"Import error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

    except Exception as e:
        logger.error(f"Error generating report: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@properties_bp.route('/properties/rloan-report', methods=['POST', 'OPTIONS'])
@properties_bp.route('/generate_rloan_report', methods=['POST', 'OPTIONS'])
def generate_rloan_report():
    """
    Generate a standalone mortgage report.

    Request: {"propertyId": "..."}
    """
    property_id, result = _parse_property_request()
    if property_id is None:
        return result

    registry = _get_registry()
    property_loader = registry.get_property_loader()
    rloan_loader = registry.get_rloan_loader()

    try:
        property_data = property_loader.find_by_id(property_id)
        if not property_data:
            return jsonify({
                'status': 'error',
                'message': f'Property {property_id} not found'
            }), 404

        rloan_data = rloan_loader.find_by_property_id(property_id)
        if not rloan_data:
            return jsonify({
                'status': 'error',
                'message': f'No mortgage found for property {property_id}'
            }), 404

        from reports.rloan.rloan_generator import generate_rloan_report as gen_mort_report

        report_path = gen_mort_report(
            property_data=property_data,
            rloan_data=rloan_data,
            output_dir=config.get_property_reports_dir(),
            auto_open=False
        )

        logger.info(f"Generated mortgage report: {report_path}")

        from routes.utils import pdf_success_response
        return pdf_success_response(report_path, 'Mortgage report generated successfully')

    except ImportError as e:
        logger.error(f"Import error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

    except Exception as e:
        logger.error(f"Error generating mortgage report: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@properties_bp.route('/rloans', methods=['GET'])
def list_rloans():
    """List all mortgages — used by the startup preloader for the count stat."""
    registry = _get_registry()
    rloan_loader = registry.get_rloan_loader()

    try:
        mortgages = rloan_loader.list_all()
        return jsonify({
            'status': 'success',
            'count': len(mortgages),
            'mortgages': mortgages,
        })
    except Exception as e:
        logger.error(f"Error listing mortgages: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

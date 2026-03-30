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
Property endpoints for MKM Research Labs PRS Platform.
"""

import logging
import traceback

from flask import Blueprint, jsonify, request

from config import config
from loaders import LoaderRegistry

logger = logging.getLogger(__name__)

properties_bp = Blueprint('properties', __name__)


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
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
    mortgage_loader = registry.get_mortgage_loader()

    try:
        # Find property
        property_data = property_loader.find_by_id(property_id)
        if not property_data:
            return jsonify({
                'status': 'error',
                'message': f'Property {property_id} not found'
            }), 404

        # Find associated mortgage
        mortgage_data = mortgage_loader.find_by_property_id(property_id)

        # Import and generate report
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=property_data,
            mortgage_data=mortgage_data,
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
            'message': f'Report generator not available: {e}'
        }), 500

    except Exception as e:
        logger.error(f"Error generating report: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Error generating report: {e}'
        }), 500


@properties_bp.route('/properties/mortgage-report', methods=['POST', 'OPTIONS'])
@properties_bp.route('/generate_mortgage_report', methods=['POST', 'OPTIONS'])
def generate_mortgage_report():
    """
    Generate a standalone mortgage report.

    Request: {"propertyId": "..."}
    """
    property_id, result = _parse_property_request()
    if property_id is None:
        return result

    registry = _get_registry()
    property_loader = registry.get_property_loader()
    mortgage_loader = registry.get_mortgage_loader()

    try:
        property_data = property_loader.find_by_id(property_id)
        if not property_data:
            return jsonify({
                'status': 'error',
                'message': f'Property {property_id} not found'
            }), 404

        mortgage_data = mortgage_loader.find_by_property_id(property_id)
        if not mortgage_data:
            return jsonify({
                'status': 'error',
                'message': f'No mortgage found for property {property_id}'
            }), 404

        from reports.mortgage.mortgage_generator import generate_mortgage_report as gen_mort_report

        report_path = gen_mort_report(
            property_data=property_data,
            mortgage_data=mortgage_data,
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
            'message': f'Mortgage report generator not available: {e}'
        }), 500

    except Exception as e:
        logger.error(f"Error generating mortgage report: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Error generating mortgage report: {e}'
        }), 500


@properties_bp.route('/mortgages', methods=['GET'])
def list_mortgages():
    """List all mortgages — used by the startup preloader for the count stat."""
    registry = _get_registry()
    mortgage_loader = registry.get_mortgage_loader()

    try:
        mortgages = mortgage_loader.list_all()
        return jsonify({
            'status': 'success',
            'count': len(mortgages),
            'mortgages': mortgages,
        })
    except Exception as e:
        logger.error(f"Error listing mortgages: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@properties_bp.route('/properties/<prop_id>/mortgage', methods=['GET', 'OPTIONS'])
def property_mortgage(prop_id: str):
    """Get mortgage details for a property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    registry = _get_registry()
    mortgage_loader = registry.get_mortgage_loader()

    try:
        mortgage_data = mortgage_loader.find_by_property_id(prop_id)
        if not mortgage_data:
            return jsonify({
                'status': 'error',
                'message': f'No mortgage found for property {prop_id}'
            }), 404

        # Return the full nested CDM structure
        mort = mortgage_data.get('Mortgage', mortgage_data)

        return jsonify({
            'status': 'success',
            'property_id': prop_id,
            'mortgage': mort,
        })

    except Exception as e:
        logger.error(f"Error loading mortgage for {prop_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error: {e}'
        }), 500

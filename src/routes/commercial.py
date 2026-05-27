# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial asset routes.

Currently exposes one endpoint:

  - POST /api/v1/commercial/report             (also /generate_commercial_report)
      Body: {"propertyId": "CPROP-…"}
      Returns: base64-encoded PDF.

Mirrors the property-report route in src/routes/properties.py — same
request shape, same response shape (via ``pdf_success_response``), so
the JS handler that fires on "Generate Commercial Report" right-click
can be a verbatim clone of ``generateReport``.
"""

import logging
import traceback

from flask import Blueprint, jsonify, request

from config import config
from routes.utils import pdf_success_response

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


@commercial_bp.route('/commercial/report', methods=['POST', 'OPTIONS'])
@commercial_bp.route('/generate_commercial_report', methods=['POST', 'OPTIONS'])
def generate_report():
    """Generate a commercial-asset PDF report for the given propertyId."""
    property_id, result = _parse_commercial_request()
    if property_id is None:
        return result

    try:
        from reports.commercial import generate_commercial_report

        report_path = generate_commercial_report(
            property_id=property_id,
            output_dir=config.get_reports_dir('commercial'),
            open_pdf=False,
        )
        if report_path is None:
            return jsonify({
                'status': 'error',
                'message': f'Commercial asset {property_id} not found',
            }), 404

        logger.info("Generated commercial report: %s", report_path)
        return pdf_success_response(report_path)

    except Exception as e:
        logger.error("Error generating commercial report: %s\n%s",
                     e, traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
        }), 500

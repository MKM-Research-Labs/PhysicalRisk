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

"""Commercial-asset PDF report endpoints.

  POST /api/v1/commercial/report             (also /generate_commercial_report)
      Body: {"propertyId": "CPROP-…"} -> base64-encoded full commercial PDF.

  POST /api/v1/commercial/loan-report
       (also /generate_commercial_loan_report)
      Body: {"propertyId": "CPROP-…"} -> base64-encoded loan-focused PDF
      (title + location + loan overview). 404 if no loan is linked.
"""

import traceback

from flask import jsonify

from config import config
from routes.utils import pdf_success_response

from .blueprint import commercial_bp, logger, _parse_commercial_request


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


@commercial_bp.route('/commercial/loan-report', methods=['POST', 'OPTIONS'])
@commercial_bp.route('/generate_commercial_loan_report', methods=['POST', 'OPTIONS'])
def generate_loan_report_route():
    """Generate a loan-focused commercial PDF (title + location + loan overview).

    Mirrors POST /api/v1/properties/rloan-report on the residential
    side. The frontend hits this for both the "Loan Details" and the
    "Generate Loan Report" right-click items.
    """
    property_id, result = _parse_commercial_request()
    if property_id is None:
        return result

    try:
        from reports.commercial import generate_cloan_report

        report_path = generate_cloan_report(
            property_id=property_id,
            output_dir=config.get_reports_dir('commercial'),
            open_pdf=False,
        )
        if report_path is None:
            # Disambiguate between "asset doesn't exist" and "asset exists
            # but has no loan" so the frontend can show a useful message.
            from reports.commercial.commercial_report import (
                _load_commercial_record,
            )
            if _load_commercial_record(property_id, config.get_input_dir()) is None:
                msg = f'Commercial asset {property_id} not found'
            else:
                msg = f'No loan linked to commercial asset {property_id}'
            return jsonify({'status': 'error', 'message': msg}), 404

        logger.info("Generated commercial loan report: %s", report_path)
        return pdf_success_response(report_path)

    except Exception as e:
        logger.error("Error generating commercial loan report: %s\n%s",
                     e, traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
        }), 500

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

"""Gauge report generation endpoint."""

import logging
import traceback

from flask import jsonify, request

from config import config

from . import gauges_bp
from ._helpers import _get_registry

logger = logging.getLogger(__name__)


@gauges_bp.route('/gauges/report', methods=['POST', 'OPTIONS'])
@gauges_bp.route('/generate_gauge_report', methods=['POST', 'OPTIONS'])
def generate_report():
    """
    Generate a gauge report.

    Request: {"gaugeId": "..."}
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    data = request.get_json()
    if data is None:
        return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400

    gauge_id = data.get('gaugeId')
    if not gauge_id:
        return jsonify({'status': 'error', 'message': 'Gauge ID is required'}), 400

    registry = _get_registry()
    gauge_loader = registry.get_gauge_loader()

    try:
        # Find gauge
        gauge_data = gauge_loader.find_by_id(gauge_id)
        if not gauge_data:
            return jsonify({
                'status': 'error',
                'message': f'Gauge {gauge_id} not found'
            }), 404

        # Always load timeseries (storm responses for flood history page)
        timeseries_data = None
        try:
            timeseries_loader = registry.get_timeseries_loader()
            storm_responses = timeseries_loader.get_storm_responses(gauge_id)
            if storm_responses:
                timeseries_data = {'storm_responses': storm_responses}
        except Exception as ts_err:
            logger.warning(f"Could not load timeseries for {gauge_id}: {ts_err}")

        # Load historical daily data for flood history graph
        try:
            gaugehd_dir = config.get_gaugehd_dir()
            hd_file = gaugehd_dir / f"gauge_{gauge_id}_hd.json"
            if hd_file.exists():
                import json as json_mod_hd
                with open(hd_file, 'r') as f:
                    hd_data = json_mod_hd.load(f)
                if timeseries_data is None:
                    timeseries_data = {}
                timeseries_data['historical_daily'] = hd_data
        except Exception as hd_err:
            logger.warning(f"Could not load historical daily data for {gauge_id}: {hd_err}")

        # Load hazard curve data for hazard_curves and prs_pricing pages
        try:
            import json as json_mod
            hazard_file = config.get_input_dir() / 'gaugehc.json'
            if hazard_file.exists():
                with open(hazard_file, 'r') as f:
                    all_hazard = json_mod.load(f)
                gauge_hazard = all_hazard.get('hazard_curves', {}).get(gauge_id, {})
                if gauge_hazard:
                    gauge_data['hazard_curve'] = gauge_hazard
        except Exception as hc_err:
            logger.warning(f"Could not load hazard data for {gauge_id}: {hc_err}")

        # Import and generate report
        from reports.gauge.gauge_generator import generate_gauge_report

        report_path = generate_gauge_report(
            gauge_data=gauge_data,
            timeseries_data=timeseries_data,
            output_dir=config.get_gauge_reports_dir(),
            report_type=data.get('reportType', 'basic'),
            auto_open=data.get('autoOpen', False)
        )

        logger.info(f"Generated gauge report: {report_path}")

        # Read PDF as base64 for inline display
        import base64
        with open(report_path, 'rb') as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

        return jsonify({
            'status': 'success',
            'message': 'Report generated successfully',
            'file_path': str(report_path),
            'pdf_base64': pdf_base64
        })

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

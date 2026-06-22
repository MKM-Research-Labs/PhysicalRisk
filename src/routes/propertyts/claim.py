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
Property flood damage claim report endpoint.

GET /api/v1/properties/<prop_id>/claim-report
    Generates and streams a PDF insurance claim report for a property,
    covering storm chronology, sequence type, flood depth progression,
    damage assessment (max-depth model) and mortgage impact.
"""

import logging

from flask import Response, jsonify

import database
from config import config
from . import propertyts_bp

logger = logging.getLogger(__name__)

_SEQUENCES_FILE = 'storm_sequences.json'


def _load_sequence_lookup():
    """Build sequence_id → {sequence_type, num_storms} lookup."""
    lookup = {}
    try:
        data = database.get_storm_sequences(config.catchment_id) or {}
        for seq in data.get('sequences', []):
            lookup[seq['sequence_id']] = {
                'sequence_type': seq.get('sequence_type', 'isolated'),
                'num_storms': seq.get('num_storms', 1),
                'intensity_category': seq.get('intensity_category', ''),
            }
    except Exception as e:
        logger.warning(f'Could not load sequence lookup: {e}')
    return lookup


def _load_prop_record(prop_id):
    """Find and return the CDM record for this property from property.json."""
    try:
        pdata = database.get_property_portfolio(config.catchment_id) or {}
        for p in pdata.get('properties', []):
            ph = p.get('PropertyHeader', {})
            pid = ph.get('Header', {}).get('PropertyID', '')
            if pid == prop_id:
                return ph
    except Exception:
        pass
    return {}


def _load_rloan_record(prop_id):
    """Find and return mortgage data for this property from loan.json."""
    try:
        mdata = database.get_loan_portfolio(config.catchment_id) or {}
        for m in mdata.get('loans', []):
            mg = m.get('RLoan', {})
            pid = mg.get('Header', {}).get('PropertyID', '')
            if pid == prop_id:
                return {
                    'FinancialTerms': mg.get('FinancialTerms', {}),
                    'CurrentStatus': mg.get('CurrentStatus', {}),
                }
    except Exception:
        pass
    return None


@propertyts_bp.route('/properties/<prop_id>/claim-report', methods=['GET'])
def property_claim_report(prop_id: str):
    """
    Generate and stream a PDF flood damage claim report for a property.

    The report covers:
    - Claim cover sheet with reference number
    - Storm sequence chronology (sequence type: isolated / doublet / cluster / persistent)
    - Flood damage assessment using the max-depth model
    - Mortgage LTV impact and negative equity analysis
    - Claim determination summary
    """
    prop_data = database.get_property_timeseries(config.catchment_id, prop_id)
    if prop_data is None:
        return jsonify({
            'status': 'error',
            'message': f'Property {prop_id} not found in flood timeseries. '
                       'Run: python app.py port --propertyts'
        }), 404

    if not prop_data.get('flood_events'):
        return jsonify({
            'status': 'error',
            'message': f'No flood events recorded for {prop_id}'
        }), 404

    prop_record = _load_prop_record(prop_id)
    rloan_record = _load_rloan_record(prop_id)
    sequence_lookup = _load_sequence_lookup()

    try:
        from reports.property.claim import ClaimReportGenerator
        gen = ClaimReportGenerator()
        pdf_bytes = gen.generate(prop_data, prop_record, rloan_record, sequence_lookup)
    except Exception as e:
        logger.error(f'Failed to generate claim report for {prop_id}: {e}', exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

    filename = f'claim_report_{prop_id}.pdf'
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(pdf_bytes)),
        }
    )

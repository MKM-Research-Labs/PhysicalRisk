# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Commercial loan-pricing endpoint.

  GET|POST /api/v1/commercial/<prop_id>/loan-pricer
      Price the loan linked to a commercial asset. Mirrors
      /api/v1/properties/<id>/loan-pricer.
"""

import traceback

from flask import jsonify, request

import database
from config import config

from .blueprint import commercial_bp, logger


def _find_commercial_loan(prop_id: str):
    """Return the commercial loan CDM record for an asset, or None.

    commercial_loan.json stores ``commercial_loans`` as a list of
    ``{"Mortgage": {...}}`` records — the same CDM shape as the
    residential mortgage.json — keyed by ``Mortgage.Header.PropertyID``.
    """
    for loan in database.list_commercial_loans(config.catchment_id):
        mg = loan.get('Mortgage', loan)
        if mg.get('Header', {}).get('PropertyID') == prop_id:
            return loan
    return None


@commercial_bp.route('/commercial/<prop_id>/loan-pricer',
                     methods=['GET', 'POST', 'OPTIONS'])
def commercial_loan_pricer(prop_id: str):
    """Price the loan linked to a commercial asset.

    Mirrors /api/v1/properties/<id>/loan-pricer. commercial_loan.json
    stores CurrentLTV as a decimal (0-1); the CDM->pricer adapter expects
    a percentage (it derives property_value from balance / LTV), so the
    LTV is normalised to a percentage before pricing — matching what the
    commercial blotter does.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        loan = _find_commercial_loan(prop_id)
        if not loan:
            return jsonify({
                'status': 'error',
                'message': f'No loan linked to commercial asset {prop_id}',
            }), 404

        mortgage_cdm = loan if 'Mortgage' in loan else {'Mortgage': loan}

        # Normalise decimal LTV -> percentage so to_pricer_inputs derives a
        # sane property value.
        status = mortgage_cdm['Mortgage'].setdefault('CurrentStatus', {})
        ltv = status.get('CurrentLTV')
        if isinstance(ltv, (int, float)) and 0 < ltv <= 1.5:
            status['CurrentLTV'] = ltv * 100

        overrides = None
        if request.method == 'POST':
            body = request.get_json(silent=True) or {}
            overrides = body.get('overrides', body)

        from routes._loan_pricing import compute_loan_pricing
        result = compute_loan_pricing(mortgage_cdm, overrides)

        return jsonify({'status': 'success', 'property_id': prop_id, **result})

    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 422
    except Exception as e:
        logger.error("Error pricing commercial loan for %s: %s\n%s",
                     prop_id, e, traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
        }), 500

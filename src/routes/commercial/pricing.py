# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial loan-pricing endpoint.

  GET|POST /api/v1/commercial/<prop_id>/loan-pricer
      Price the loan linked to a commercial asset. Mirrors
      /api/v1/properties/<id>/loan-pricer.
"""

import json
import traceback

from flask import jsonify, request

from config import config

from .blueprint import commercial_bp, logger


def _find_commercial_loan(prop_id: str):
    """Return the commercial loan CDM record for an asset, or None.

    commercial_loan.json stores ``commercial_loans`` as a list of
    ``{"Mortgage": {...}}`` records — the same CDM shape as the
    residential mortgage.json — keyed by ``Mortgage.Header.PropertyID``.
    """
    try:
        with open(config.get_input_path('commercial_loan.json'), 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    for loan in data.get('commercial_loans', []):
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

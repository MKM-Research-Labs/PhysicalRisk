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

"""Property loan / mortgage / loan-pricer route handlers."""

import logging
import traceback

from flask import jsonify, request

import routes.properties as _pp
from . import properties_bp

logger = logging.getLogger(__name__)


@properties_bp.route('/properties/<prop_id>/rloan', methods=['GET', 'OPTIONS'])
def property_rloan(prop_id: str):
    """Get mortgage details for a property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    registry = _pp._get_registry()
    rloan_loader = registry.get_rloan_loader()

    try:
        rloan_data = rloan_loader.find_by_property_id(prop_id)
        if not rloan_data:
            return jsonify({
                'status': 'error',
                'message': f'No mortgage found for property {prop_id}'
            }), 404

        # Return the full nested CDM structure
        mort = rloan_data.get('RLoan', rloan_data)

        return jsonify({
            'status': 'success',
            'property_id': prop_id,
            'mortgage': mort,
        })

    except Exception as e:
        logger.error(f"Error loading mortgage for {prop_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@properties_bp.route('/properties/<prop_id>/loan-pricer', methods=['GET', 'POST', 'OPTIONS'])
def property_loan_pricer(prop_id: str):
    """Price the mortgage linked to a residential property.

    GET returns the CDM-derived inputs + pricing. POST accepts an
    ``{"overrides": {...}}`` body so the editable Loan Pricer panel can
    re-price live against user-edited inputs.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    registry = _pp._get_registry()
    rloan_loader = registry.get_rloan_loader()

    try:
        rloan_data = rloan_loader.find_by_property_id(prop_id)
        if not rloan_data:
            return jsonify({
                'status': 'error',
                'message': f'No mortgage found for property {prop_id}'
            }), 404

        # Normalise to the {"RLoan": {...}} shape the CDM expects.
        if 'RLoan' in rloan_data:
            mortgage_cdm = rloan_data
        else:
            mortgage_cdm = {'RLoan': rloan_data}

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
        logger.error(f"Error pricing loan for {prop_id}: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@properties_bp.route('/loan-pricer', methods=['POST', 'OPTIONS'])
def standalone_loan_pricer():
    """Price a loan from user-supplied inputs alone — no property/loan record.

    Backs the standalone Loan Calculator launched from the asset right-click
    menu. The POST body supplies all pricing inputs directly, either as
    ``{"inputs": {...}}`` or as a bare ``{...}`` of pricing fields.
    ``loan_amount`` and ``property_value`` are required.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        body = request.get_json(silent=True) or {}
        inputs = body.get('inputs', body.get('overrides', body))
        asset_class = body.get('asset_class', 'residential')

        from routes._loan_pricing import compute_standalone_pricing
        result = compute_standalone_pricing(inputs, asset_class=asset_class)

        return jsonify({'status': 'success', **result})

    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 422
    except Exception as e:
        logger.error(f"Error in standalone loan pricer: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

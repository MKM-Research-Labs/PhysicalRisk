# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial asset / loan list endpoints (startup-preloader counts)."""

import json

from flask import jsonify

from config import config

from ..blueprint import commercial_bp


@commercial_bp.route('/commercial', methods=['GET'])
def list_commercial():
    """List all commercial assets in the active catchment.

    Mirrors GET /api/v1/properties — used by the startup preloader for
    the bottom-left status popup count and to build a PropertyID →
    BuildingName / address lookup for the right-click menu titles.

    Response shape::

        {"status": "success", "count": N, "commercial_assets": [...]}
    """
    try:
        with open(config.get_input_path('commercial.json'), 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return jsonify({'status': 'success', 'count': 0,
                        'commercial_assets': []})
    assets = data.get('commercial_assets', [])
    return jsonify({
        'status': 'success',
        'count': len(assets),
        'commercial_assets': assets,
    })


@commercial_bp.route('/commercial-loans', methods=['GET'])
def list_commercial_loans():
    """List all commercial loans in the active catchment.

    Mirrors GET /api/v1/rloans — used by the startup preloader for
    the count stat.

    Response shape::

        {"status": "success", "count": N, "commercial_loans": [...]}
    """
    try:
        with open(config.get_input_path('commercial_loan.json'), 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return jsonify({'status': 'success', 'count': 0,
                        'commercial_loans': []})
    loans = data.get('commercial_loans', [])
    return jsonify({
        'status': 'success',
        'count': len(loans),
        'commercial_loans': loans,
    })

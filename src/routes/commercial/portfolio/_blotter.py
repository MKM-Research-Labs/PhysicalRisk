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

"""Commercial asset portfolio blotter endpoint."""

from flask import jsonify, request

import database
from config import config
from models.floodrisk import relative_elevation

from ..blueprint import commercial_bp


@commercial_bp.route('/commercial/blotter', methods=['GET', 'OPTIONS'])
def commercial_blotter():
    """Commercial asset portfolio blotter.

    Mirrors /api/v1/propertyts/blotter — returns each commercial asset
    with headline information (value, address, river distance, elevation
    above reference gauge, flood zone, anchor tenant) joined with its
    loan (outstanding balance, LTV, remaining term).
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    # Asset records --------------------------------------------------
    adata = database.get_commercial_portfolio(config.catchment_id)
    if adata is None:
        return jsonify({
            'status': 'success', 'assets': [],
            'summary': {'num_assets': 0, 'total_property_value': 0,
                        'total_loan_exposure': 0},
        })

    # Loan lookup ----------------------------------------------------
    loan_lookup = {}
    try:
        for l in database.list_commercial_loans(config.catchment_id):
            mg = l.get('Mortgage', {})
            pid = mg.get('Header', {}).get('PropertyID', '')
            status = mg.get('CurrentStatus', {})
            ltv = status.get('CurrentLTV', 0) or 0
            # commercial_loan.json stores LTV as a decimal (0-1); the
            # frontend fmtPct expects a percentage scale to match the
            # residential blotter.
            if ltv and ltv <= 1.5:
                ltv = ltv * 100
            loan_lookup[pid] = {
                'outstanding_balance': status.get('OutstandingBalance', 0),
                'current_ltv': round(ltv, 2),
                'remaining_term_months': status.get('RemainingTerm', 0),
            }
    except FileNotFoundError:
        pass

    # Per-asset nearest-gauge elevation (from commercialts/<id>.json) -
    # used to compute relative elevation in the same way as residential.
    assets = []
    for record in adata.get('commercial_assets', []):
        ca = record.get('CommercialAsset', {})
        hdr = ca.get('Header', {})
        pid = hdr.get('PropertyID', '')
        if not pid:
            continue
        loc = ca.get('Location', {})
        val = ca.get('Valuation', {})
        attrs = ca.get('CommercialAttributes', {})
        tenancy = ca.get('Tenancy', {})
        risk = ca.get('RiskAssessment', {})
        construction = ca.get('Construction', {})

        # Address: prefer BuildingName, otherwise number + street.
        address = (
            loc.get('BuildingName')
            or f"{loc.get('BuildingNumber', '')} "
               f"{loc.get('StreetName', '')}".strip()
            or ''
        )

        prop_ground_m = risk.get('GroundLevelMeters', 0) or 0
        floor_level_m = construction.get('FloorLevelMeters', 0) or 0
        river_distance_m = risk.get('RiverDistanceMeters', 0) or 0

        # Resolve gauge elevation from the asset's nearest gauge
        # recorded in commercialts/<id>.json.  Fall back to absolute
        # ground level if no timeseries file exists.
        gauge_elev = 0.0
        try:
            cts = database.get_commercial_timeseries(config.catchment_id, pid)
            ng = (cts or {}).get('nearest_gauges') or []
            if ng:
                gauge_elev = ng[0].get('gauge_elevation_m', 0) or 0
        except Exception:
            pass

        loan = loan_lookup.get(pid, {})
        entry = {
            'property_id': pid,
            'property_address': address,
            'postcode': loc.get('Postcode', ''),
            'property_value': val.get('PropertyValue', 0),
            'commercial_type': attrs.get('CommercialType', ''),
            'anchor_tenant': tenancy.get('AnchorTenant', ''),
            'river_distance_km': round(river_distance_m / 1000.0, 2),
            'elevation_m': round(relative_elevation(
                prop_ground_m, gauge_elev, floor_level_m), 2),
            'floor_level_m': floor_level_m,
            'ea_flood_zone': risk.get('EAFloodZone', ''),
            'has_loan': pid in loan_lookup,
            'outstanding_balance': loan.get('outstanding_balance', 0),
            'current_ltv': loan.get('current_ltv', 0),
            'remaining_term_months': loan.get('remaining_term_months', 0),
        }
        assets.append(entry)

    assets.sort(key=lambda a: a['property_value'], reverse=True)

    total_value = sum(a['property_value'] for a in assets)
    total_loans = sum(a['outstanding_balance'] for a in assets)

    return jsonify({
        'status': 'success',
        'assets': assets,
        'summary': {
            'num_assets': len(assets),
            'total_property_value': round(total_value, 2),
            'total_loan_exposure': round(total_loans, 2),
        },
    })

# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial list / blotter / per-storm portfolio-impact endpoints.

  GET /api/v1/commercial            (list all commercial assets)
  GET /api/v1/commercial-loans      (list all commercial loans)
      Used by the startup preloader for the bottom-left status popup
      and the in-browser asset-name lookup.

  GET /api/v1/commercial/blotter
      Commercial-asset portfolio blotter. Mirrors
      /api/v1/propertyts/blotter — used by the Storm Portfolio Table tab.

  GET /api/v1/commercial/<storm_id>/portfolio-impact
      Per-storm commercial damage. Mirrors
      /api/v1/propertyts/<storm_id>/portfolio-impact.
"""

import json

from flask import jsonify, request

from config import config
from models.floodrisk import relative_elevation
from models.floodrisk.depth_damage import is_prs_flood

from .blueprint import commercial_bp


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
    try:
        with open(config.get_input_path('commercial.json'), 'r') as f:
            adata = json.load(f)
    except FileNotFoundError:
        return jsonify({
            'status': 'success', 'assets': [],
            'summary': {'num_assets': 0, 'total_property_value': 0,
                        'total_loan_exposure': 0},
        })

    # Loan lookup ----------------------------------------------------
    loan_lookup = {}
    try:
        with open(config.get_input_path('commercial_loan.json'), 'r') as f:
            ldata = json.load(f)
        for l in ldata.get('commercial_loans', []):
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
    cts_dir = config.get_input_dir() / 'commercialts'

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
        cts_path = cts_dir / f'{pid}.json'
        if cts_path.exists():
            try:
                with open(cts_path, 'r') as f:
                    cts = json.load(f)
                ng = cts.get('nearest_gauges') or []
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


@commercial_bp.route('/commercial/<storm_id>/portfolio-impact',
                     methods=['GET', 'OPTIONS'])
def commercial_portfolio_impact(storm_id: str):
    """Per-storm commercial-asset damage.

    Mirrors /api/v1/propertyts/<storm_id>/portfolio-impact but reads
    commercialts/CPROP-*.json. Returns per-asset damage_amount,
    damage_ratio and post_damage_value joined with loan exposure.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    cts_dir = config.get_input_dir() / 'commercialts'
    if not cts_dir.exists():
        return jsonify({
            'status': 'error',
            'message': 'Commercial flood timeseries not yet generated',
        }), 404

    # Asset value + address + type lookup --------------------------
    asset_lookup = {}
    try:
        with open(config.get_input_path('commercial.json'), 'r') as f:
            adata = json.load(f)
        for record in adata.get('commercial_assets', []):
            ca = record.get('CommercialAsset', {})
            pid = ca.get('Header', {}).get('PropertyID', '')
            if not pid:
                continue
            loc = ca.get('Location', {})
            address = (
                loc.get('BuildingName')
                or f"{loc.get('BuildingNumber', '')} "
                   f"{loc.get('StreetName', '')}".strip()
                or ''
            )
            asset_lookup[pid] = {
                'property_value': ca.get('Valuation', {}).get('PropertyValue', 0),
                'property_address': address,
                'commercial_type': ca.get('CommercialAttributes', {}).get('CommercialType', ''),
            }
    except FileNotFoundError:
        pass

    # Loan join (for negative-equity flag in summary) --------------
    loan_lookup = {}
    try:
        with open(config.get_input_path('commercial_loan.json'), 'r') as f:
            ldata = json.load(f)
        for l in ldata.get('commercial_loans', []):
            mg = l.get('Mortgage', {})
            pid = mg.get('Header', {}).get('PropertyID', '')
            status = mg.get('CurrentStatus', {})
            ltv = status.get('CurrentLTV', 0) or 0
            if ltv and ltv <= 1.5:
                ltv = ltv * 100
            loan_lookup[pid] = {
                'outstanding_balance': status.get('OutstandingBalance', 0),
                'current_ltv': round(ltv, 2),
                'remaining_term_months': status.get('RemainingTerm', 0),
            }
    except FileNotFoundError:
        pass

    assets = []
    for cf in cts_dir.glob('CPROP-*.json'):
        with open(cf, 'r') as f:
            cdata = json.load(f)
        pid = cdata.get('property_id', cf.stem)
        if pid not in asset_lookup:
            continue
        for event in cdata.get('flood_events', []):
            if event.get('storm_id') != storm_id:
                continue
            if not is_prs_flood(event):
                continue
            meta = asset_lookup[pid]
            value = meta['property_value']
            damage_ratio = event.get('damage_ratio', 0)
            damage_amount = round(value * damage_ratio, 2)
            post_value = round(value - damage_amount, 2)
            loan = loan_lookup.get(pid, {})
            outstanding = loan.get('outstanding_balance', 0)
            post_ltv = round(
                (outstanding / post_value * 100) if post_value > 0 else 999, 1
            )
            assets.append({
                'property_id': pid,
                'property_address': meta['property_address'],
                'commercial_type': meta['commercial_type'],
                'property_value': value,
                'flood_depth_m': round(event.get('flood_depth_m', 0), 3),
                'damage_ratio': round(damage_ratio, 4),
                'damage_amount': damage_amount,
                'post_damage_value': post_value,
                'has_loan': pid in loan_lookup,
                'outstanding_balance': outstanding,
                'current_ltv': loan.get('current_ltv', 0),
                'post_damage_ltv': post_ltv,
                'remaining_term_months': loan.get('remaining_term_months', 0),
                'negative_equity': bool(outstanding and outstanding > post_value),
            })
            break

    assets.sort(key=lambda a: a['damage_amount'], reverse=True)

    total_value = sum(a['property_value'] for a in assets)
    total_damage = sum(a['damage_amount'] for a in assets)
    total_post = sum(a['post_damage_value'] for a in assets)
    total_outstanding = sum(a['outstanding_balance'] for a in assets if a['has_loan'])
    neg_equity = sum(1 for a in assets if a['negative_equity'])

    total_portfolio_value = sum(a['property_value'] for a in asset_lookup.values())
    total_portfolio_loans = sum(l['outstanding_balance'] for l in loan_lookup.values())

    return jsonify({
        'status': 'success',
        'storm_id': storm_id,
        'portfolio': {
            'total_assets': len(asset_lookup),
            'assets_affected': len(assets),
            'total_portfolio_value': round(total_portfolio_value, 2),
            'total_affected_value': round(total_value, 2),
            'total_damage': round(total_damage, 2),
            'total_post_damage_value': round(total_post, 2),
            'total_portfolio_loans': round(total_portfolio_loans, 2),
            'total_affected_loans': round(total_outstanding, 2),
            'loans_in_negative_equity': neg_equity,
            'damage_pct': round(total_damage / total_value * 100, 2) if total_value > 0 else 0,
        },
        'assets': assets,
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

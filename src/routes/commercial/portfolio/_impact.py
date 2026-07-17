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

"""Per-storm commercial-asset portfolio-impact endpoint."""

from flask import jsonify, request

import database
from config import config
from models.floodrisk.depth_damage import is_prs_flood

from ..blueprint import commercial_bp


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

    if not database.commercial_timeseries_exists(config.catchment_id):
        return jsonify({
            'status': 'error',
            'message': 'Commercial flood timeseries not yet generated',
        }), 404
    cts_ids = [i for i in database.iter_commercial_timeseries_ids(config.catchment_id)
               if i.startswith('CPROP-')]

    # Asset value + address + type lookup --------------------------
    asset_lookup = {}
    try:
        for record in database.list_commercial(config.catchment_id):
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
        for l in database.list_commercial_loans(config.catchment_id):
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
    for cid in cts_ids:
        cdata = database.get_commercial_timeseries(config.catchment_id, cid)
        if cdata is None:
            continue
        pid = cdata.get('property_id', cid)
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

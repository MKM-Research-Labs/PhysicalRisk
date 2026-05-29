# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Storm-level wind impact endpoint — per-property + per-commercial wind
damage for a single typhoon-paired storm.

Mirrors :func:`portfolio_impact` (flood) but reads the per-event damage
rolls from ``typhoon/damage/EVT-NNNN.json`` instead of the per-property
flood_events. Returns 200 with an empty list when the storm isn't paired
with a typhoon — frontend uses the empty case to show the appropriate
"no typhoon" placeholder.

GET /propertyts/<storm_id>/wind-impact
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from flask import jsonify

from config import config
from port.typhoon_storm_link import link_for_storm

from .blueprint import propertyts_bp
from .financial_loaders import _load_mortgage_lookup, _load_prop_values

logger = logging.getLogger(__name__)


def _typhoon_damage_path(event_id: str) -> Path:
    """Resolve typhoon/damage/EVT-NNNN.json for the active catchment."""
    return config.get_input_dir() / 'typhoon' / 'damage' / f'{event_id}.json'


def _load_commercial_lookup() -> Dict[str, Dict]:
    """Return commercial_id → {value, address, commercial_type} from commercial.json."""
    out: Dict[str, Dict] = {}
    cpath = config.get_input_path('commercial.json')
    if not cpath.exists():
        return out
    try:
        with open(cpath, 'r') as f:
            cdata = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning('wind_impact: cannot load commercial.json (%s)', exc)
        return out
    for c in cdata.get('commercials', []) or cdata.get('properties', []):
        ca = c.get('CommercialAsset') or c
        header = ca.get('Header', {})
        cid = header.get('PropertyID', '')
        if not cid:
            continue
        loc = ca.get('Location', {})
        attrs = ca.get('CommercialAttributes', {})
        out[cid] = {
            'value': ca.get('Valuation', {}).get('PropertyValue', 0),
            'address': (
                (loc.get('BuildingNumber', '') + ' ' + loc.get('StreetName', '')).strip()
            ),
            'commercial_type': attrs.get('CommercialType', 'Commercial'),
        }
    return out


def _load_property_address_lookup() -> Dict[str, Dict]:
    """Return property_id → {address, type} from property.json. Property
    values come from :func:`_load_prop_values` separately."""
    out: Dict[str, Dict] = {}
    try:
        with open(config.get_input_path('property.json'), 'r') as f:
            pdata = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning('wind_impact: cannot load property.json (%s)', exc)
        return out
    for p in pdata.get('properties', []):
        ph = p.get('PropertyHeader', {})
        pid = ph.get('Header', {}).get('PropertyID', '')
        if not pid:
            continue
        loc = ph.get('Location', {})
        attrs = ph.get('PropertyAttributes', {})
        out[pid] = {
            'address': (
                (loc.get('BuildingNumber', '') + ' ' + loc.get('StreetName', '')).strip()
            ),
            'type': attrs.get('PropertyType', 'Residential'),
        }
    return out


def _build_wind_entry(asset_id: str,
                      asset_class: str,
                      asset_value: float,
                      damage: Dict,
                      address: str,
                      asset_type: str,
                      mortgage_lookup: Dict) -> Dict:
    """Build one wind-impact row, mirroring the flood damage row shape."""
    damage_ratio = float(damage.get('damage_ratio', 0.0) or 0.0)
    damage_amount = round(asset_value * damage_ratio, 2)
    post_damage_value = round(asset_value - damage_amount, 2)
    entry = {
        'asset_id': asset_id,
        'asset_class': asset_class,
        'address': address,
        'type': asset_type,
        'value': asset_value,
        'peak_wind_ms': damage.get('peak_sustained_ms'),
        'wind_threshold_ms': damage.get('threshold_ms'),
        'v_50_eff_ms': damage.get('v_50_eff_ms'),
        'damage_ratio': round(damage_ratio, 4),
        'damage_amount': damage_amount,
        'post_damage_value': post_damage_value,
        'has_mortgage': asset_id in mortgage_lookup,
    }
    if asset_id in mortgage_lookup:
        mg = mortgage_lookup[asset_id]
        outstanding = mg.get('outstanding_balance', 0)
        post_ltv = round(
            (outstanding / post_damage_value * 100) if post_damage_value > 0 else 999, 1
        )
        entry.update({
            'outstanding_balance': outstanding,
            'current_ltv': mg.get('current_ltv', 0),
            'post_damage_ltv': post_ltv,
            'remaining_term_months': mg.get('remaining_term_months', 0),
        })
    return entry


@propertyts_bp.route('/propertyts/<storm_id>/wind-impact', methods=['GET', 'OPTIONS'])
def wind_impact(storm_id: str):
    """Per-property wind damage for the typhoon paired with ``storm_id``.

    Returns ``{status:'success', typhoon:None, rows:[]}`` for storms that
    aren't paired with a typhoon — the wind-damage panel uses the empty
    state to display the right message.
    """
    from flask import request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    link = link_for_storm(storm_id)
    if not link:
        return jsonify({
            'status': 'success',
            'storm_id': storm_id,
            'typhoon': None,
            'rows': [],
            'summary': {
                'properties_in_scope': 0,
                'commercials_in_scope': 0,
                'total_wind_damage': 0,
                'max_damage_ratio': 0,
            },
        })

    event_id = link['event_id']
    damage_path = _typhoon_damage_path(event_id)
    if not damage_path.exists():
        return jsonify({
            'status': 'error',
            'message': f'Typhoon damage file missing for {event_id}',
        }), 404
    try:
        with open(damage_path, 'r') as f:
            damage_data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return jsonify({
            'status': 'error',
            'message': f'Could not read damage file: {exc}',
        }), 500

    prop_values = _load_prop_values()
    prop_meta = _load_property_address_lookup()
    commercial_lookup = _load_commercial_lookup()
    mortgage_lookup = _load_mortgage_lookup()

    rows: List[Dict] = []
    for d in damage_data.get('damages', []):
        asset_id: Optional[str] = d.get('property_id')
        if not asset_id:
            continue
        if asset_id.startswith('CPROP-'):
            meta = commercial_lookup.get(asset_id)
            if meta is None:
                continue
            asset_value = float(meta['value'] or 0.0)
            rows.append(_build_wind_entry(
                asset_id=asset_id,
                asset_class='commercial',
                asset_value=asset_value,
                damage=d,
                address=meta['address'],
                asset_type=meta['commercial_type'],
                mortgage_lookup=mortgage_lookup,
            ))
        else:
            asset_value = float(prop_values.get(asset_id, 0) or 0.0)
            if asset_value == 0:
                # Skip properties without a known valuation — same convention
                # as portfolio_impact.
                continue
            meta = prop_meta.get(asset_id, {})
            rows.append(_build_wind_entry(
                asset_id=asset_id,
                asset_class='residential',
                asset_value=asset_value,
                damage=d,
                address=meta.get('address', ''),
                asset_type=meta.get('type', 'Residential'),
                mortgage_lookup=mortgage_lookup,
            ))

    rows.sort(key=lambda r: r['damage_amount'], reverse=True)
    residential = [r for r in rows if r['asset_class'] == 'residential']
    commercial = [r for r in rows if r['asset_class'] == 'commercial']
    total_damage = round(sum(r['damage_amount'] for r in rows))
    max_ratio = max((r['damage_ratio'] for r in rows), default=0.0)

    return jsonify({
        'status': 'success',
        'storm_id': storm_id,
        'typhoon': {
            'event_id': event_id,
            'scenario_family': link.get('scenario_family'),
            'peak_wind_ms': link.get('peak_wind_ms'),
            'mean_damage_ratio': link.get('mean_damage_ratio'),
            'horizon_hours': damage_data.get('horizon_hours'),
        },
        'rows': rows,
        'summary': {
            'properties_in_scope': len(residential),
            'commercials_in_scope': len(commercial),
            'total_wind_damage': total_damage,
            'max_damage_ratio': round(max_ratio, 4),
        },
    })

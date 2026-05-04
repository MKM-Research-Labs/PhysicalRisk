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
Property flood timeseries — shared data loaders and per-property entry builders.

Loaders for property values, mortgages, gauge elevations, and full property
details — used by the financial endpoints (blotter, portfolio-impact,
sequence-impact, basis).
"""

import json
import logging

from flask import jsonify, request

from config import config
from models.floodrisk import relative_elevation

from ._helpers import _get_propertyts_dir

logger = logging.getLogger(__name__)


def _check_options_and_dir():
    """Handle OPTIONS preflight and verify propertyts directory exists.

    Returns ``(None, pts_dir)`` on success, or ``(response, None)``
    when an early return (OPTIONS / 404) should be sent.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), None

    pts_dir = _get_propertyts_dir()
    if not pts_dir.exists():
        return (jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated'
        }), 404), None

    return None, pts_dir


def _load_prop_values():
    """Load property_id → value from property.json."""
    prop_values = {}
    try:
        with open(config.get_input_path('property.json'), 'r') as f:
            pdata = json.load(f)
        for p in pdata.get('properties', []):
            ph = p.get('PropertyHeader', {})
            pid = ph.get('Header', {}).get('PropertyID', '')
            val = ph.get('Valuation', {}).get('PropertyValue', 0)
            prop_values[pid] = val
    except Exception as e:
        logger.warning(f'Could not load property.json: {e}')
    return prop_values


def _load_mortgage_lookup():
    """Load property_id → mortgage info from mortgage.json."""
    mortgage_lookup = {}
    try:
        with open(config.get_input_path('mortgage.json'), 'r') as f:
            mdata = json.load(f)
        for m in mdata.get('mortgages', []):
            mg = m.get('Mortgage', {})
            pid = mg.get('Header', {}).get('PropertyID', '')
            status = mg.get('CurrentStatus', {})
            mortgage_lookup[pid] = {
                'outstanding_balance': status.get('OutstandingBalance', 0),
                'current_ltv': status.get('CurrentLTV', 0),
                'remaining_term_months': status.get('RemainingTerm', 0),
            }
    except Exception as e:
        logger.warning(f'Could not load mortgage.json: {e}')
    return mortgage_lookup


def _build_property_entry(prop_id, flood_depth, damage_ratio,
                           prop_values, mortgage_lookup):
    """Build a single property impact record with mortgage enrichment."""
    prop_value = prop_values[prop_id]
    damage_amount = round(prop_value * damage_ratio, 2)
    post_damage_value = round(prop_value - damage_amount, 2)

    entry = {
        'property_id': prop_id,
        'property_value': prop_value,
        'flood_depth_m': round(flood_depth, 3),
        'damage_ratio': round(damage_ratio, 4),
        'damage_amount': damage_amount,
        'post_damage_value': post_damage_value,
        'has_mortgage': prop_id in mortgage_lookup,
    }

    if prop_id in mortgage_lookup:
        mg = mortgage_lookup[prop_id]
        outstanding = mg['outstanding_balance']
        post_ltv = round(
            (outstanding / post_damage_value * 100) if post_damage_value > 0 else 999, 1
        )
        entry.update({
            'outstanding_balance': outstanding,
            'current_ltv': mg['current_ltv'],
            'post_damage_ltv': post_ltv,
            'remaining_term_months': mg['remaining_term_months'],
            'negative_equity': outstanding > post_damage_value,
        })
    else:
        entry.update({
            'outstanding_balance': 0,
            'current_ltv': 0,
            'post_damage_ltv': 0,
            'remaining_term_months': 0,
            'negative_equity': False,
        })

    return entry


def _portfolio_totals(properties, prop_values, mortgage_lookup):
    """Compute portfolio-level aggregate figures."""
    total_value = sum(p['property_value'] for p in properties)
    total_damage = sum(p['damage_amount'] for p in properties)
    total_post_value = sum(p['post_damage_value'] for p in properties)
    mortgaged = [p for p in properties if p['has_mortgage']]
    total_outstanding = sum(p['outstanding_balance'] for p in mortgaged)
    neg_equity_count = sum(1 for p in mortgaged if p['negative_equity'])
    total_portfolio_value = sum(prop_values.values())
    total_portfolio_mortgages = sum(m['outstanding_balance'] for m in mortgage_lookup.values())
    return {
        'total_properties': len(prop_values),
        'properties_affected': len(properties),
        'total_portfolio_value': round(total_portfolio_value, 2),
        'total_affected_value': round(total_value, 2),
        'total_damage': round(total_damage, 2),
        'total_post_damage_value': round(total_post_value, 2),
        'total_portfolio_mortgages': round(total_portfolio_mortgages, 2),
        'total_affected_mortgages': round(total_outstanding, 2),
        'mortgages_in_negative_equity': neg_equity_count,
        'damage_pct': round(total_damage / total_value * 100, 2) if total_value > 0 else 0,
    }


def _load_gauge_elevations():
    """Build {gauge_id: elevation_m} from gauge.json and gaugehc.json."""
    elevations: dict = {}
    try:
        with open(config.get_input_path('gauge.json'), 'r') as f:
            gdata = json.load(f)
        for fg in gdata.get('flood_gauges', []):
            g = fg.get('FloodGauge', {})
            gid = g.get('Header', {}).get('GaugeID', '')
            if gid:
                elevations[gid] = g.get('Location', {}).get(
                    'GaugeElevation', 0)
    except Exception as e:
        logger.warning('Could not load gauge.json elevations: %s', e)
    try:
        with open(config.get_input_path('gaugehc.json'), 'r') as f:
            hc = json.load(f)
        for gid, curve in hc.get('hazard_curves', {}).items():
            if gid not in elevations:
                elevations[gid] = curve.get('elevation_m', 0)
    except Exception as e:
        logger.warning('Could not load gaugehc.json elevations: %s', e)
    return elevations


def _load_property_details():
    """Load full property details for the blotter.

    Returns {property_id: {address, value, lat, lon, elevation_m,
    floor_level_m, river_distance_km, ea_flood_zone, ...}}.

    Elevation is the *relative* elevation of the property above its
    reference gauge (including the floor level), consistent with the
    flood threshold used by the PRS pricer and storm simulation.
    """
    gauge_elevations = _load_gauge_elevations()
    details = {}
    try:
        with open(config.get_input_path('property.json'), 'r') as f:
            pdata = json.load(f)
        for p in pdata.get('properties', []):
            ph = p.get('PropertyHeader', {})
            hdr = ph.get('Header', {})
            pid = hdr.get('PropertyID', '')
            if not pid:
                continue
            loc = ph.get('Location', {})
            val = ph.get('Valuation', {})
            construction = ph.get('Construction', {})
            risk = ph.get('RiskAssessment',
                          loc.get('RiskAssessment', {}))
            ref_gauges = ph.get('ReferenceGauges', [])

            address = (
                f"{loc.get('BuildingNumber', '')} "
                f"{loc.get('StreetName', '')}".strip()
            )

            prop_ground_m = risk.get('GroundLevelMeters', 0)
            floor_level_m = construction.get('FloorLevelMeters', 0)
            river_distance_m = risk.get('RiverDistanceMeters', 0)

            # Resolve gauge elevation from the first reference gauge
            gauge_elev = 0.0
            if ref_gauges:
                gauge_elev = gauge_elevations.get(ref_gauges[0], 0.0)

            details[pid] = {
                'property_id': pid,
                'property_address': address,
                'postcode': loc.get('Postcode', ''),
                'property_value': val.get('PropertyValue', 0),
                'latitude': loc.get('LatitudeDegrees', 0),
                'longitude': loc.get('LongitudeDegrees', 0),
                'elevation_m': round(relative_elevation(
                    prop_ground_m, gauge_elev, floor_level_m), 2),
                'floor_level_m': floor_level_m,
                'river_distance_km': round(river_distance_m / 1000.0, 2),
                'ea_flood_zone': risk.get('EAFloodZone', ''),
                'reference_gauges': ref_gauges,
            }
    except Exception as e:
        logger.warning('Could not load property details: %s', e)
    return details

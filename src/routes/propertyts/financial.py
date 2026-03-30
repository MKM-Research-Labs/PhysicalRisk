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
Property flood timeseries — portfolio financial impact endpoints.

Joins property flood data with valuations and mortgages to compute
damage amounts, post-damage LTV, and negative equity counts.

Endpoints
---------
GET /propertyts/<storm_id>/portfolio-impact
    Impact of a single storm event.

GET /propertyts/sequence/<sequence_id>/portfolio-impact
    Sequence-level impact: for each property, uses the maximum flood depth
    across all storms in the sequence (physical rationale: water remains
    elevated between storms in a 168h window, so damage = max depth reached).
"""

import json
import logging

from flask import jsonify, request

from config import config
from . import propertyts_bp, _get_propertyts_dir

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


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Per-storm endpoint
# ---------------------------------------------------------------------------

@propertyts_bp.route('/propertyts/<storm_id>/portfolio-impact', methods=['GET', 'OPTIONS'])
def portfolio_impact(storm_id: str):
    """
    Get portfolio-wide impact for a specific storm.

    Joins property flood data with property valuations and mortgage data
    to show total portfolio damage, mortgage exposure, and negative equity.
    """
    early, pts_dir = _check_options_and_dir()
    if early is not None:
        return early

    prop_values = _load_prop_values()
    mortgage_lookup = _load_mortgage_lookup()

    # Scan all property flood files for this storm
    properties = []
    for pf in pts_dir.glob('PROP-*.json'):
        with open(pf, 'r') as f:
            pfdata = json.load(f)

        prop_id = pfdata.get('property_id', pf.stem)
        for event in pfdata.get('flood_events', []):
            if event.get('storm_id') != storm_id:
                continue
            if event.get('flood_depth_m', 0) <= 0:
                break  # no flooding for this property in this storm
            if prop_id not in prop_values:
                break  # no valuation data for this property
            properties.append(_build_property_entry(
                prop_id,
                event['flood_depth_m'],
                event.get('damage_ratio', 0),
                prop_values,
                mortgage_lookup,
            ))
            break

    if not properties:
        return jsonify({
            'status': 'error',
            'message': f'Storm {storm_id} not found or causes no property flooding'
        }), 404

    properties.sort(key=lambda p: p['damage_amount'], reverse=True)

    return jsonify({
        'status': 'success',
        'storm_id': storm_id,
        'portfolio': _portfolio_totals(properties, prop_values, mortgage_lookup),
        'properties': properties,
    })


# ---------------------------------------------------------------------------
# Sequence-level endpoint  (max flood depth across all storms in sequence)
# ---------------------------------------------------------------------------

@propertyts_bp.route('/propertyts/sequence/<sequence_id>/portfolio-impact',
                     methods=['GET', 'OPTIONS'])
def sequence_portfolio_impact(sequence_id: str):
    """
    Get portfolio-wide impact for an entire multi-storm sequence.

    Physical rationale: within a 168-hour event window, ground water remains
    elevated between storms. A property that floods to 0.4m then 0.7m does
    not suffer additive damage — it suffers damage at the maximum depth
    reached (0.7m). This endpoint selects the worst flood event per property
    across all storms in the sequence.
    """
    early, pts_dir = _check_options_and_dir()
    if early is not None:
        return early

    prop_values = _load_prop_values()
    mortgage_lookup = _load_mortgage_lookup()

    # For each property, find the worst (max depth) flood event in this sequence
    properties = []
    storms_in_sequence = set()

    for pf in pts_dir.glob('PROP-*.json'):
        with open(pf, 'r') as f:
            pfdata = json.load(f)

        prop_id = pfdata.get('property_id', pf.stem)
        if prop_id not in prop_values:
            continue

        # Collect all flood events belonging to this sequence
        # storm_id IS the sequence_id in current format; fall back to
        # sequence_id field for legacy propertyts files
        seq_events = [
            e for e in pfdata.get('flood_events', [])
            if (e.get('storm_id') == sequence_id or e.get('sequence_id') == sequence_id)
            and e.get('flood_depth_m', 0) > 0
        ]

        if not seq_events:
            continue

        # Track which storm IDs belong to this sequence
        for e in seq_events:
            if e.get('storm_id'):
                storms_in_sequence.add(e['storm_id'])

        # Worst event = maximum flood depth (physical max-damage model)
        worst = max(seq_events, key=lambda e: e.get('flood_depth_m', 0))

        entry = _build_property_entry(
            prop_id,
            worst['flood_depth_m'],
            worst.get('damage_ratio', 0),
            prop_values,
            mortgage_lookup,
        )
        entry['worst_storm_id'] = worst.get('storm_id', '')
        entry['num_sequence_floods'] = len(seq_events)
        properties.append(entry)

    if not properties:
        return jsonify({
            'status': 'error',
            'message': f'Sequence {sequence_id} not found or causes no property flooding'
        }), 404

    properties.sort(key=lambda p: p['damage_amount'], reverse=True)

    return jsonify({
        'status': 'success',
        'sequence_id': sequence_id,
        'num_storms_in_sequence': len(storms_in_sequence),
        'damage_model': 'max_depth',
        'portfolio': _portfolio_totals(properties, prop_values, mortgage_lookup),
        'properties': properties,
    })

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
Storm-level and sequence-level portfolio impact endpoints.

GET /propertyts/<storm_id>/portfolio-impact
    Impact of a single storm event (with PRS derivative payouts).

GET /propertyts/sequence/<sequence_id>/portfolio-impact
    Sequence-level impact: for each property, uses the maximum flood depth
    across all storms in the sequence (physical rationale: water remains
    elevated between storms in a 168h window, so damage = max depth reached).
"""

import json

from flask import jsonify

from models.floodrisk.depth_damage import is_prs_flood

from .blueprint import propertyts_bp
from .financial_loaders import (
    _build_property_entry,
    _check_options_and_dir,
    _load_rloan_lookup,
    _load_prop_values,
    _load_property_details,
    _portfolio_totals,
)
from .financial_prs import _enrich_with_prs


@propertyts_bp.route('/propertyts/<storm_id>/portfolio-impact', methods=['GET', 'OPTIONS'])
def portfolio_impact(storm_id: str):
    """
    Get portfolio-wide impact for a specific storm.

    Joins property flood data with property valuations, mortgage data,
    and PRS derivative payouts for a complete REIT risk view.
    """
    early, pts_dir = _check_options_and_dir()
    if early is not None:
        return early

    prop_values = _load_prop_values()
    rloan_lookup = _load_rloan_lookup()
    prop_details = _load_property_details()

    # Scan all property flood files for this storm
    properties = []
    for pf in pts_dir.glob('PROP-*.json'):
        with open(pf, 'r') as f:
            pfdata = json.load(f)

        prop_id = pfdata.get('property_id', pf.stem)
        for event in pfdata.get('flood_events', []):
            if event.get('storm_id') != storm_id:
                continue
            if not is_prs_flood(event):
                continue  # not a PRS-countable flood (sub-severe or no depth)
            if prop_id not in prop_values:
                continue  # no valuation data for this property
            properties.append(_build_property_entry(
                prop_id,
                event['flood_depth_m'],
                event.get('damage_ratio', 0),
                prop_values,
                rloan_lookup,
            ))
            break

    if not properties:
        return jsonify({
            'status': 'error',
            'message': f'Storm {storm_id} not found or causes no property flooding'
        }), 404

    # Enrich with PRS derivative payouts
    derivatives = _enrich_with_prs(properties, prop_details)

    properties.sort(key=lambda p: p['damage_amount'], reverse=True)

    return jsonify({
        'status': 'success',
        'storm_id': storm_id,
        'portfolio': _portfolio_totals(properties, prop_values, rloan_lookup),
        'derivatives': derivatives,
        'properties': properties,
    })


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
    rloan_lookup = _load_rloan_lookup()
    prop_details = _load_property_details()

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
            and is_prs_flood(e)
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
            rloan_lookup,
        )
        entry['worst_storm_id'] = worst.get('storm_id', '')
        entry['num_sequence_floods'] = len(seq_events)
        properties.append(entry)

    if not properties:
        return jsonify({
            'status': 'error',
            'message': f'Sequence {sequence_id} not found or causes no property flooding'
        }), 404

    # Enrich with PRS derivative payouts
    derivatives = _enrich_with_prs(properties, prop_details)

    properties.sort(key=lambda p: p['damage_amount'], reverse=True)

    return jsonify({
        'status': 'success',
        'sequence_id': sequence_id,
        'num_storms_in_sequence': len(storms_in_sequence),
        'damage_model': 'max_depth',
        'portfolio': _portfolio_totals(properties, prop_values, rloan_lookup),
        'derivatives': derivatives,
        'properties': properties,
    })

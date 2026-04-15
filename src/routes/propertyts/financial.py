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
GET /propertyts/blotter
    REIT property portfolio blotter — headline info for all properties.

GET /propertyts/<storm_id>/portfolio-impact
    Impact of a single storm event (with PRS derivative payouts).

GET /propertyts/sequence/<sequence_id>/portfolio-impact
    Sequence-level impact: for each property, uses the maximum flood depth
    across all storms in the sequence (physical rationale: water remains
    elevated between storms in a 168h window, so damage = max depth reached).
"""

import json
import logging

from flask import jsonify, request

from config import config
from models.floodrisk import relative_elevation
from models.floodrisk.depth_damage import is_prs_flood

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
# PRS trade helpers
# ---------------------------------------------------------------------------

def _load_all_prs_trades():
    """Load all PRS trades (PropertyPRS and inter-dealer).

    Returns a list of flat dicts with swap_id, gauge_id, property_id,
    notional, is_payer, trigger, spread_bps, counterparty, trade_type.
    """
    prs_dir = config.get_reports_dir('prs')
    if not prs_dir.exists():
        return []

    trades = []
    for f in sorted(prs_dir.glob('*PRS-*.json')):
        try:
            with open(f) as fh:
                raw = json.load(fh)
            ps = raw.get('PhysicalSwap', {})
            header = ps.get('Header', {})
            leg = ps.get('LegData', {})
            pricing = ps.get('Pricing', {})
            gauge_set = ps.get('GaugeSet', {})
            prop_set = ps.get('PropertySet', {})

            gauge_basket = gauge_set.get('GaugeBasket', [])
            gauge_id = gauge_basket[0].get('GaugeID', '') if gauge_basket else ''

            trades.append({
                'swap_id': header.get('SwapID', ''),
                'trade_type': header.get('TradeType', 'PRS'),
                'counterparty': header.get('CounterPartyName', ''),
                'is_payer': leg.get('Payer', True),
                'notional': leg.get('Notional', 0),
                'trigger': pricing.get('TriggerLevel', 'severe'),
                'spread_bps': pricing.get('SpreadBps', 0),
                'gauge_id': gauge_id,
                'property_id': prop_set.get('PropertyID', ''),
            })
        except Exception as e:
            logger.warning('Skipping PRS file %s: %s', f.name, e)
    return trades


def _match_prs_to_properties(prs_trades, property_ids, property_gauges):
    """Match PRS trades to properties.

    Returns {property_id: [trade, ...]} mapping.

    Matching rules:
    - Direct: trade.property_id == property_id
    - Gauge: trade.gauge_id in property's reference gauges
    """
    by_prop = {}
    by_gauge = {}
    for t in prs_trades:
        if t['property_id']:
            by_prop.setdefault(t['property_id'], []).append(t)
        if t['gauge_id']:
            by_gauge.setdefault(t['gauge_id'], []).append(t)

    result = {pid: [] for pid in property_ids}
    for pid in property_ids:
        # Direct match
        if pid in by_prop:
            result[pid].extend(by_prop[pid])
        # Gauge match (avoid duplicates)
        seen = {t['swap_id'] for t in result[pid]}
        for gid in property_gauges.get(pid, []):
            for t in by_gauge.get(gid, []):
                if t['swap_id'] not in seen:
                    result[pid].append(t)
                    seen.add(t['swap_id'])
    return result


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


# ---------------------------------------------------------------------------
# REIT property blotter endpoint
# ---------------------------------------------------------------------------

@propertyts_bp.route('/propertyts/blotter', methods=['GET', 'OPTIONS'])
def property_blotter():
    """REIT property portfolio blotter.

    Returns all properties with headline information: value, location,
    distance from river, elevation, floor level, and mortgage summary.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    prop_details = _load_property_details()
    mortgage_lookup = _load_mortgage_lookup()

    properties = []
    for pid, d in prop_details.items():
        entry = dict(d)
        # Mortgage enrichment
        mg = mortgage_lookup.get(pid, {})
        entry['has_mortgage'] = pid in mortgage_lookup
        entry['outstanding_balance'] = mg.get('outstanding_balance', 0)
        entry['current_ltv'] = mg.get('current_ltv', 0)
        entry['remaining_term_months'] = mg.get('remaining_term_months', 0)
        properties.append(entry)

    properties.sort(key=lambda p: p['property_value'], reverse=True)

    total_value = sum(p['property_value'] for p in properties)
    total_mortgages = sum(p['outstanding_balance'] for p in properties)

    return jsonify({
        'status': 'success',
        'properties': properties,
        'summary': {
            'num_properties': len(properties),
            'total_property_value': round(total_value, 2),
            'total_mortgage_exposure': round(total_mortgages, 2),
        },
    })


# ---------------------------------------------------------------------------
# Per-storm endpoint
# ---------------------------------------------------------------------------

def _enrich_with_prs(properties, prop_details):
    """Enrich property entries with PRS derivative payouts.

    For each flooded property, finds matching PRS trades and computes
    the REIT payout (positive = protection received).

    Mutates ``properties`` in place and returns a derivatives summary dict.
    """
    prs_trades = _load_all_prs_trades()
    if not prs_trades:
        for p in properties:
            p['prs_trades'] = []
            p['prs_payout'] = 0
            p['net_pnl'] = -p['damage_amount']
        return {
            'total_prs_payout': 0,
            'total_prs_notional': 0,
            'num_trades_triggered': 0,
            'net_portfolio_pnl': -sum(p['damage_amount'] for p in properties),
        }

    # Build property → gauge mapping from property details
    property_gauges = {}
    for pid, d in prop_details.items():
        property_gauges[pid] = d.get('reference_gauges', [])

    prop_ids = [p['property_id'] for p in properties]
    matched = _match_prs_to_properties(prs_trades, prop_ids, property_gauges)

    total_prs_payout = 0
    total_prs_notional = 0
    num_triggered = 0

    for p in properties:
        pid = p['property_id']
        trades_for_prop = matched.get(pid, [])
        prs_entries = []
        prop_payout = 0

        for t in trades_for_prop:
            # REIT is payer (buys protection) → receives +notional on trigger
            # Trader is receiver (sells protection) → pays out notional
            notional = t['notional']
            payout = notional  # full binary payout on flood
            prop_payout += payout
            total_prs_notional += notional
            num_triggered += 1
            prs_entries.append({
                'swap_id': t['swap_id'],
                'notional': notional,
                'payout': round(payout, 2),
                'trigger': t['trigger'],
                'counterparty': t['counterparty'],
                'trade_type': t['trade_type'],
            })

        p['prs_trades'] = prs_entries
        p['prs_payout'] = round(prop_payout, 2)
        p['net_pnl'] = round(prop_payout - p['damage_amount'], 2)
        total_prs_payout += prop_payout

    total_damage = sum(p['damage_amount'] for p in properties)
    return {
        'total_prs_payout': round(total_prs_payout, 2),
        'total_prs_notional': round(total_prs_notional, 2),
        'num_trades_triggered': num_triggered,
        'net_portfolio_pnl': round(total_prs_payout - total_damage, 2),
    }


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
    mortgage_lookup = _load_mortgage_lookup()
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
                mortgage_lookup,
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
        'portfolio': _portfolio_totals(properties, prop_values, mortgage_lookup),
        'derivatives': derivatives,
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

    # Enrich with PRS derivative payouts
    derivatives = _enrich_with_prs(properties, prop_details)

    properties.sort(key=lambda p: p['damage_amount'], reverse=True)

    return jsonify({
        'status': 'success',
        'sequence_id': sequence_id,
        'num_storms_in_sequence': len(storms_in_sequence),
        'damage_model': 'max_depth',
        'portfolio': _portfolio_totals(properties, prop_values, mortgage_lookup),
        'derivatives': derivatives,
        'properties': properties,
    })


# ---------------------------------------------------------------------------
# Basis endpoint — synthetic gauge view for REIT
# ---------------------------------------------------------------------------

@propertyts_bp.route('/propertyts/<storm_id>/basis', methods=['GET', 'OPTIONS'])
def storm_basis(storm_id: str):
    """Synthetic gauge basis analysis for a storm.

    Groups properties by their controlling synthetic gauge and shows
    flood transmission: how many properties linked to each synthetic
    gauge actually flooded vs didn't.  Helps the REIT understand
    where the gauge-to-property attenuation kills the flood signal.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    pts_dir = _get_propertyts_dir()
    if not pts_dir or not pts_dir.exists():
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated',
        }), 404

    # Load gauge thresholds from gaugehc.json
    gauge_thresholds = {}
    gaugehc_path = config.get_input_dir() / 'gaugehc.json'
    if gaugehc_path.exists():
        try:
            with open(gaugehc_path) as f:
                ghc = json.load(f)
            for gid, gc in ghc.get('hazard_curves', {}).items():
                gauge_thresholds[gid] = {
                    'gauge_name': gc.get('gauge_name', gid),
                    'alert_m': gc.get('flood_alert_m', 0),
                    'warning_m': gc.get('flood_warning_m', 0),
                    'severe_m': gc.get('severe_flood_warning_m', 0),
                    'elevation_m': gc.get('elevation_m', 0),
                    'latitude': gc.get('latitude', 0),
                    'longitude': gc.get('longitude', 0),
                }
        except Exception as e:
            logger.warning('Could not load gaugehc.json: %s', e)

    # Load storm gauge responses for real gauge peak levels
    storm_gauge_peaks = {}
    try:
        storm_path = config.get_input_path('stress_storms') / f'{storm_id}.json'
        if storm_path.exists():
            with open(storm_path) as f:
                storm_data = json.load(f)
            for gr in storm_data.get('gauge_responses', []):
                storm_gauge_peaks[gr['gauge_id']] = {
                    'peak_level_m': gr.get('peak_level_m', 0),
                    'exceeded_severe': gr.get('exceeded_severe', False),
                    'exceeded_warning': gr.get('exceeded_warning', False),
                    'exceeded_alert': gr.get('exceeded_alert', False),
                }
    except Exception as e:
        logger.warning('Could not load storm %s: %s', storm_id, e)

    # Scan all property files, group by synthetic gauge
    synth_data = {}  # gauge_id -> accumulator

    for pf in pts_dir.glob('PROP-*.json'):
        try:
            with open(pf, 'r') as f:
                pfdata = json.load(f)
        except Exception:
            continue

        prop_id = pfdata.get('property_id', pf.stem)
        nearest = pfdata.get('nearest_gauges', [])
        if not nearest:
            continue

        # Synthetic gauge is first in nearest_gauges
        synth = nearest[0]
        synth_id = synth.get('gauge_id', '')
        if not synth_id:
            continue

        # Find the nearest real gauge (second in list)
        real_gauge_id = ''
        if len(nearest) > 1:
            real_gauge_id = nearest[1].get('gauge_id', '')

        # Find the flood event for this storm
        flood_event = None
        for event in pfdata.get('flood_events', []):
            if event.get('storm_id') == storm_id:
                flood_event = event
                break

        # Initialise accumulator for this synthetic gauge
        if synth_id not in synth_data:
            thresholds = gauge_thresholds.get(synth_id, {})
            synth_data[synth_id] = {
                'gauge_id': synth_id,
                'gauge_name': thresholds.get('gauge_name', synth_id),
                'gauge_type': (
                    'Synthetic' if synth_id.startswith('SYNTH') else 'Real'),
                'severe_m': thresholds.get('severe_m', 0),
                'warning_m': thresholds.get('warning_m', 0),
                'alert_m': thresholds.get('alert_m', 0),
                'elevation_m': thresholds.get('elevation_m', 0),
                'latitude': thresholds.get('latitude', 0),
                'longitude': thresholds.get('longitude', 0),
                'real_gauge_id': real_gauge_id,
                'properties_linked': 0,
                'properties_flooded': 0,
                'total_damage': 0,
                'total_flood_depth': 0,
                'total_retention': 0,
                'retention_count': 0,
                'peak_wse_m': 0,
                'exceeded_severe': False,
            }

        acc = synth_data[synth_id]
        acc['properties_linked'] += 1

        if flood_event:
            wse = flood_event.get('interpolated_wse_m', 0)
            if wse > acc['peak_wse_m']:
                acc['peak_wse_m'] = wse
            if flood_event.get('exceeded_severe', False):
                acc['exceeded_severe'] = True

            retention = flood_event.get('retention_factor', 0)
            if retention > 0:
                acc['total_retention'] += retention
                acc['retention_count'] += 1

            if flood_event.get('flooded', False):
                acc['properties_flooded'] += 1
                acc['total_damage'] += flood_event.get('damage_ratio', 0)
                acc['total_flood_depth'] += flood_event.get('flood_depth_m', 0)

    # Build response
    gauges = []
    for gid, acc in synth_data.items():
        linked = acc['properties_linked']
        flooded = acc['properties_flooded']
        transmission = (
            round(flooded / linked * 100, 1) if linked > 0 else 0)
        avg_retention = (
            round(acc['total_retention'] / acc['retention_count'], 4)
            if acc['retention_count'] > 0 else 0)
        avg_depth = (
            round(acc['total_flood_depth'] / flooded, 3)
            if flooded > 0 else 0)
        avg_damage = (
            round(acc['total_damage'] / flooded, 4)
            if flooded > 0 else 0)

        # Determine threshold breach label
        if acc['exceeded_severe']:
            threshold = 'severe'
        elif acc['peak_wse_m'] >= acc['warning_m'] > 0:
            threshold = 'warning'
        elif acc['peak_wse_m'] >= acc['alert_m'] > 0:
            threshold = 'alert'
        else:
            threshold = 'clean'

        # Real gauge peak (from storm data)
        real_peak = storm_gauge_peaks.get(acc['real_gauge_id'], {})

        gauges.append({
            'gauge_id': gid,
            'gauge_name': acc['gauge_name'],
            'gauge_type': acc['gauge_type'],
            'threshold': threshold,
            'peak_wse_m': round(acc['peak_wse_m'], 3),
            'severe_m': acc['severe_m'],
            'properties_linked': linked,
            'properties_flooded': flooded,
            'properties_not_flooded': linked - flooded,
            'transmission_pct': transmission,
            'avg_retention': avg_retention,
            'avg_flood_depth_m': avg_depth,
            'avg_damage_ratio': avg_damage,
            'real_gauge_id': acc['real_gauge_id'],
            'real_gauge_peak_m': real_peak.get('peak_level_m', 0),
            'real_gauge_severe': real_peak.get('exceeded_severe', False),
        })

    # Sort: severe first, then gauges with flooding before those without,
    # then by properties linked descending
    _THRESHOLD_ORDER = {'severe': 0, 'warning': 1, 'alert': 2, 'clean': 3}
    gauges.sort(key=lambda g: (
        _THRESHOLD_ORDER.get(g['threshold'], 3),
        0 if g['properties_flooded'] > 0 else 1,
        -g['properties_linked'],
    ))

    # Summary
    total_linked = sum(g['properties_linked'] for g in gauges)
    total_flooded = sum(g['properties_flooded'] for g in gauges)
    severe_gauges = [g for g in gauges if g['threshold'] == 'severe']
    basis_gauges = [
        g for g in severe_gauges if g['properties_flooded'] == 0]

    return jsonify({
        'status': 'success',
        'storm_id': storm_id,
        'gauges': gauges,
        'summary': {
            'num_synthetic_gauges': len(gauges),
            'gauges_severe': len(severe_gauges),
            'gauges_with_flooding': sum(
                1 for g in gauges if g['properties_flooded'] > 0),
            'gauges_basis_only': len(basis_gauges),
            'total_properties': total_linked,
            'total_flooded': total_flooded,
            'portfolio_transmission_pct': round(
                total_flooded / total_linked * 100, 1
            ) if total_linked > 0 else 0,
        },
    })

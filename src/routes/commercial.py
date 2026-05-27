# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial asset routes.

Exposes:

  POST /api/v1/commercial/report             (also /generate_commercial_report)
      Body: {"propertyId": "CPROP-…"}
      Returns: base64-encoded PDF.

  GET  /api/v1/commercial/<prop_id>/storms
      Mirrors GET /api/v1/properties/<prop_id>/storms — returns the
      flood-event hydrographs, nearest-gauge readings, and storm
      metadata used by the PropertyStormAnalysis panel.
"""

import json
import logging
import traceback

from flask import Blueprint, jsonify, request

from config import config
from routes.utils import pdf_success_response

logger = logging.getLogger(__name__)

commercial_bp = Blueprint('commercial', __name__)


def _parse_commercial_request():
    """Pull and validate ``propertyId`` from the JSON body.

    Returns (property_id, data_or_error_response).
    Same convention as _parse_property_request in properties.py.
    """
    if request.method == 'OPTIONS':
        return None, ('', 204)
    data = request.get_json(silent=True) or {}
    property_id = data.get('propertyId') or data.get('property_id')
    if not property_id:
        return None, (jsonify({
            'status': 'error',
            'message': 'propertyId is required',
        }), 400)
    return property_id, data


@commercial_bp.route('/commercial/report', methods=['POST', 'OPTIONS'])
@commercial_bp.route('/generate_commercial_report', methods=['POST', 'OPTIONS'])
def generate_report():
    """Generate a commercial-asset PDF report for the given propertyId."""
    property_id, result = _parse_commercial_request()
    if property_id is None:
        return result

    try:
        from reports.commercial import generate_commercial_report

        report_path = generate_commercial_report(
            property_id=property_id,
            output_dir=config.get_reports_dir('commercial'),
            open_pdf=False,
        )
        if report_path is None:
            return jsonify({
                'status': 'error',
                'message': f'Commercial asset {property_id} not found',
            }), 404

        logger.info("Generated commercial report: %s", report_path)
        return pdf_success_response(report_path)

    except Exception as e:
        logger.error("Error generating commercial report: %s\n%s",
                     e, traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
        }), 500


# ---------------------------------------------------------------------------
# GET /api/v1/commercial/<prop_id>/storms
#
# Counterpart to /api/v1/properties/<prop_id>/storms in
# src/routes/propertyts/core_storms.py. The per-asset flood timeseries
# files have identical shape between commercialts/ and propertyts/ —
# the only differences are which directory to read from and how to
# look up the asset's address (CommercialAsset.Header.PropertyID +
# CommercialAsset.Location vs PropertyHeader.Header.PropertyID +
# PropertyHeader.Location).  The catchment-level metadata enrichment
# (storm_sequences.json, stress_storms, gaugehc.json, gauge.json)
# applies to both asset types identically.
# ---------------------------------------------------------------------------

def _load_commercial_storms_or_404(prop_id: str):
    """Load commercialts/<prop_id>.json. Returns (response_or_None, data)."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), None

    cts_file = config.get_input_dir() / 'commercialts' / f'{prop_id}.json'
    if not cts_file.exists():
        return (jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not found in flood timeseries',
        }), 404), None

    with open(cts_file, 'r') as f:
        return None, json.load(f)


def _lookup_commercial_address(prop_id: str) -> str:
    """Resolve a commercial asset's display address from commercial.json."""
    try:
        commercial_path = config.get_input_path('commercial.json')
        with open(commercial_path, 'r') as f:
            data = json.load(f)
        for record in data.get('commercial_assets', []):
            ca = record.get('CommercialAsset', {})
            if ca.get('Header', {}).get('PropertyID') == prop_id:
                loc = ca.get('Location', {})
                # Prefer BuildingName for commercial; fall back to address.
                return (
                    loc.get('BuildingName')
                    or (str(loc.get('BuildingNumber', '')) + ' '
                        + str(loc.get('StreetName', ''))).strip()
                    or ''
                )
    except Exception:
        pass
    return ''


def _enrich_flood_events(pdata: dict) -> None:
    """Tag each flood_event with sequence_type + storm metadata + severe-count.

    Mutates `pdata` in place. Shared logic between the property and
    commercial storms routes — catchment-level data, so identical
    for both asset types.
    """
    # Build sequence_id → sequence_type lookup
    seq_lookup = {}
    try:
        seq_path = config.get_input_path('storm_sequences.json')
        with open(seq_path, 'r') as f:
            sdata = json.load(f)
        for seq in sdata.get('sequences', []):
            seq_lookup[seq['sequence_id']] = seq.get('sequence_type', 'isolated')
    except Exception:
        pass

    # Build storm metadata lookup (name, category, precipitation, severity)
    _storm_meta = {}
    for meta_file in ('storm_sequences.json', 'storms.json'):
        meta_path = config.get_input_path(meta_file)
        if not meta_path.exists():
            continue
        try:
            with open(meta_path, 'r') as f:
                mdata = json.load(f)
            if 'sequences' in mdata:
                for seq in mdata['sequences']:
                    _storm_meta[seq.get('sequence_id', '')] = seq
            elif 'storms' in mdata:
                for s in mdata['storms']:
                    _storm_meta[s.get('storm_id', '')] = s
        except Exception:
            pass

    # Build storm_id → gauges_severe from stress_storms
    _storm_severe = {}
    ss_index = config.get_input_path('stress_storms') / '_index.json'
    ss_legacy = config.get_input_path('stress_storms.json')
    ss_path = ss_index if ss_index.exists() else (ss_legacy if ss_legacy.exists() else None)
    if ss_path and ss_path.exists():
        try:
            with open(ss_path, 'r') as f:
                ss_data = json.load(f)
            for s in ss_data.get('storms', []):
                sid = s.get('storm_id', '')
                if sid:
                    ts = s.get('trigger_summary', {})
                    _storm_severe[sid] = ts.get('gauges_severe', 0)
        except Exception:
            pass

    for event in pdata.get('flood_events', []):
        sid = event.get('storm_id', '')
        event['sequence_type'] = seq_lookup.get(sid, 'isolated') if sid else 'isolated'
        meta = _storm_meta.get(sid)
        if meta:
            cat = meta.get('intensity_category', '')
            event.setdefault('intensity_category', cat)
            event.setdefault('name', meta.get('name', '') or (cat.capitalize() if cat else ''))
            event.setdefault('effective_precipitation_mm',
                             meta.get('effective_precipitation_mm',
                                      meta.get('total_precipitation_mm',
                                               meta.get('precipitation_mm', 0))))
        event.setdefault('gauges_severe', _storm_severe.get(sid, 0))


def _enrich_nearest_gauges(pdata: dict) -> int:
    """Add flood_stages + severe-count to each nearest gauge; return controlling severe count."""
    gauge_path = config.get_input_path('gauge.json')
    gauge_stages = {}
    try:
        with open(gauge_path, 'r') as f:
            gdata = json.load(f)
        for g in gdata.get('flood_gauges', []):
            fg = g.get('FloodGauge', {})
            gid = fg.get('Header', {}).get('GaugeID', '')
            stages = fg.get('FloodStage', {}).get('UK', {})
            gauge_stages[gid] = {
                'alert': stages.get('FloodAlert', 0),
                'warning': stages.get('FloodWarning', 0),
                'severe': stages.get('SevereFloodWarning', 0),
            }
    except Exception:
        pass

    nearest = pdata.get('nearest_gauges', [])
    for ng in nearest:
        ng['flood_stages'] = gauge_stages.get(ng.get('gauge_id', ''), {})

    # Gauge severe counts from GEV annual_flood_prob_severe in gaugehc.
    severe_at_gauge = 0
    try:
        hc_path = config.get_input_dir() / 'gaugehc.json'
        seq_path = config.get_input_path('storm_sequences.json')
        with open(hc_path, 'r') as f:
            hc_data = json.load(f)
        with open(seq_path, 'r') as f:
            seq_data = json.load(f)
        num_sequences = seq_data.get('num_sequences', len(seq_data.get('sequences', [])))

        synth = next((ng for ng in nearest if ng.get('gauge_id', '').startswith('SYNTH')), None)
        controlling = synth or (nearest[0] if nearest else None)

        for ng in nearest:
            gid = ng.get('gauge_id', '')
            gauge_hc = hc_data.get('hazard_curves', {}).get(gid, {})
            prob = gauge_hc.get('annual_flood_prob_severe', 0)
            ng['severe_count'] = round(prob * num_sequences)
            ng['severe_spread_bps'] = round(prob * 10000, 1)
            ng['gauge_name'] = gauge_hc.get('gauge_name', gid)

        if controlling:
            severe_at_gauge = controlling.get('severe_count', 0)
    except Exception:
        pass
    return severe_at_gauge


@commercial_bp.route('/commercial/<prop_id>/storms', methods=['GET', 'OPTIONS'])
def commercial_storms(prop_id: str):
    """Storm-scenario analysis for a commercial asset.

    Same response shape as /properties/<id>/storms so the
    PropertyStormAnalysis frontend panel can consume either without
    branching.
    """
    early, pdata = _load_commercial_storms_or_404(prop_id)
    if early is not None:
        return early

    _enrich_flood_events(pdata)
    severe_at_gauge = _enrich_nearest_gauges(pdata)

    summary = pdata.get('summary', {})
    summary['severe_at_nearest_gauge'] = severe_at_gauge

    return jsonify({
        'status': 'success',
        'property_id': prop_id,
        'property_address': _lookup_commercial_address(prop_id),
        'property_info': {
            'elevation_m': pdata.get('elevation_m', 0),
            'floor_level_m': pdata.get('floor_level_m', 0),
            'location': pdata.get('location', {}),
        },
        'nearest_gauges': pdata.get('nearest_gauges', []),
        'flood_events': pdata.get('flood_events', []),
        'summary': summary,
    })

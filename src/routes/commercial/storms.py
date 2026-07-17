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

"""Commercial storm-scenario endpoint + catchment enrichment helpers.

  GET /api/v1/commercial/<prop_id>/storms
      Counterpart to /api/v1/properties/<prop_id>/storms — returns the
      flood-event hydrographs, nearest-gauge readings, and storm metadata
      used by the PropertyStormAnalysis panel.

The per-asset flood timeseries files have identical shape between
commercialts/ and propertyts/; the only differences are which directory
to read from and how to look up the asset's address. The catchment-level
metadata enrichment (storm_sequences.json, stress_storms, gaugehc.json,
gauge.json) applies to both asset types identically.
"""

from flask import jsonify, request

import database
from config import config
from routes._storm_enrich import build_storm_lookups, enrich_nearest_gauges

from .blueprint import commercial_bp


def _load_commercial_storms_or_404(prop_id: str):
    """Load commercialts/<prop_id>.json. Returns (response_or_None, data)."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), None

    data = database.get_commercial_timeseries(config.catchment_id, prop_id)
    if data is None:
        return (jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not found in flood timeseries',
        }), 404), None
    return None, data


def _lookup_commercial_address(prop_id: str) -> str:
    """Resolve a commercial asset's display address from commercial.json."""
    try:
        for record in database.list_commercial(config.catchment_id):
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

    Mutates `pdata` in place. The catchment-level lookups are shared with the
    property storms route (see ``routes._storm_enrich.build_storm_lookups``);
    commercial assets don't carry the typhoon coupling, so ``seq_to_event`` is
    ignored and the tagging here is the flood-only subset.
    """
    seq_lookup, storm_meta, storm_severe, _ = build_storm_lookups()

    for event in pdata.get('flood_events', []):
        sid = event.get('storm_id', '')
        event['sequence_type'] = seq_lookup.get(sid, 'isolated') if sid else 'isolated'
        meta = storm_meta.get(sid)
        if meta:
            cat = meta.get('intensity_category', '')
            event.setdefault('intensity_category', cat)
            event.setdefault('name', meta.get('name', '') or (cat.capitalize() if cat else ''))
            event.setdefault('effective_precipitation_mm',
                             meta.get('effective_precipitation_mm',
                                      meta.get('total_precipitation_mm',
                                               meta.get('precipitation_mm', 0))))
        event.setdefault('gauges_severe', storm_severe.get(sid, 0))


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
    severe_at_gauge = enrich_nearest_gauges(pdata)

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

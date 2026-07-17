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

"""Shared, asset-agnostic storm-event enrichment for the storm routes.

Both the property (``routes.propertyts.core_storms``) and commercial
(``routes.commercial.storms``) storm endpoints enrich their payloads from the
same catchment-level data: storm sequences, storm metadata, stress-storm severe
counts, and gauge flood stages / GEV severe probabilities. That data is keyed by
gauge / storm and identical for both asset types, so the lookups and the
nearest-gauge enrichment live here once rather than being copied per asset class.
"""

import database
from config import config


def build_storm_lookups():
    """Build the catchment-level storm metadata lookups.

    Returns ``(seq_lookup, storm_meta, storm_severe, seq_to_event)``:
      - seq_lookup:   sequence_id → sequence_type
      - storm_meta:   sequence_id / storm_id → full storm metadata record
      - storm_severe: storm_id → gauges_severe (from stress_storms triggers)
      - seq_to_event: sequence_id → paired typhoon event_id (1:1 coupling)

    Callers that don't use the typhoon coupling can simply ignore the last
    element.
    """
    # Build sequence_id → sequence_type lookup
    seq_lookup = {}
    try:
        sdata = database.get_storm_sequences(config.catchment_id)
        if sdata:
            for seq in sdata.get('sequences', []):
                seq_lookup[seq['sequence_id']] = seq.get('sequence_type', 'isolated')
    except Exception:
        pass

    # Build storm metadata lookup (name, category, precipitation, severity).
    # Modern storm_sequences.json plus the legacy storms.json, merged legacy-last.
    storm_meta = {}
    for _getter in (database.get_storm_sequences, database.get_legacy_storm_sequences):
        try:
            mdata = _getter(config.catchment_id)
            if not mdata:
                continue
            if 'sequences' in mdata:
                for seq in mdata['sequences']:
                    storm_meta[seq.get('sequence_id', '')] = seq
            elif 'storms' in mdata:
                for s in mdata['storms']:
                    storm_meta[s.get('storm_id', '')] = s
        except Exception:
            pass

    # Build storm_id → gauges_severe from stress_storms (sharded index, with the
    # legacy single-file stress_storms.json as fallback).
    storm_severe = {}
    try:
        ss_data = database.get_stress_storm_index(config.catchment_id)
        if ss_data is None:
            ss_data = database.get_legacy_stress_storms(config.catchment_id)
        if ss_data:
            for s in ss_data.get('storms', []):
                sid = s.get('storm_id', '')
                if sid:
                    ts = s.get('trigger_summary', {})
                    storm_severe[sid] = ts.get('gauges_severe', 0)
    except Exception:
        pass

    # Typhoon "additional circumstance" lookup. The 1:1 coupling means each
    # storm sequence carries the event_id of its paired typhoon, so the join is
    # a direct sequence_id → event_id map straight off the storm metadata.
    seq_to_event = {
        sid: meta.get('event_id')
        for sid, meta in storm_meta.items()
        if meta.get('event_id')
    }
    return seq_lookup, storm_meta, storm_severe, seq_to_event


def enrich_nearest_gauges(pdata):
    """Attach flood stages and GEV severe counts to ``pdata['nearest_gauges']``.

    Mutates ``pdata`` in place and returns the controlling gauge's severe count
    (the synthetic gauge when present, else the first nearest gauge).
    """
    gauge_stages = {}
    try:
        gdata = database.get_gauge_portfolio(config.catchment_id)
        if gdata:
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
    # Compute per-gauge and use the synthetic gauge as the controlling total.
    severe_at_gauge = 0
    try:
        hc_data = database.get_gauge_hazard_curves(config.catchment_id)
        seq_data = database.get_storm_sequences(config.catchment_id)
        if hc_data and seq_data:
            num_sequences = seq_data.get(
                'num_sequences', len(seq_data.get('sequences', [])))

            synth = next(
                (ng for ng in nearest if ng.get('gauge_id', '').startswith('SYNTH')), None)
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

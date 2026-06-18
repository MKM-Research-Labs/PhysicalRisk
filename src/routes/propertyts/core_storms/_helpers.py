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

"""Lookup builders and per-property enrichment for the storms endpoint."""

import json
from typing import Dict

from config import config

# Catchment-level storm enrichment is asset-agnostic and shared with the
# commercial storms route; the implementations live in routes._storm_enrich.
from routes._storm_enrich import (  # noqa: F401  (re-exported for _routes.py)
    build_storm_lookups as _build_storm_lookups,
    enrich_nearest_gauges as _enrich_nearest_gauges,
)


def _load_typhoon_damage_for_property(prop_id: str) -> Dict[str, Dict]:
    """Walk typhoon/damage/EVT-*.json files and index this property's
    per-event wind impact by event_id.

    Returns {event_id: {scenario_family, peak_sustained_ms, threshold_ms,
    v_50_eff_ms, damage_ratio}} or empty dict when the typhoon stage hasn't
    run. ``scenario_family`` is the event-level label carried in the damage
    roll — surfaced here so the storm endpoint can build the typhoon block
    without a second pass over the linkage.
    """
    damage_dir = config.get_input_dir() / 'typhoon' / 'damage'
    if not damage_dir.exists():
        return {}
    result: Dict[str, Dict] = {}
    for fp in damage_dir.glob('EVT-*.json'):
        try:
            with open(fp, 'r') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        evt_id = data.get('event_id') or fp.stem
        scenario_family = data.get('scenario_family')
        for entry in data.get('damages', []):
            if entry.get('property_id') == prop_id:
                result[evt_id] = {
                    'scenario_family':   scenario_family,
                    'peak_sustained_ms': entry.get('peak_sustained_ms'),
                    'threshold_ms':      entry.get('threshold_ms'),
                    'v_50_eff_ms':       entry.get('v_50_eff_ms'),
                    'damage_ratio':      entry.get('damage_ratio'),
                }
                break
    return result


def _tag_flood_events(pdata, prop_id, seq_lookup, storm_meta, storm_severe, seq_to_event):
    """Tag each flood event with sequence type, storm metadata and typhoon block,
    and append synthetic rows for wind-only typhoons. Mutates ``pdata``."""
    wind_damage_by_event = (
        _load_typhoon_damage_for_property(prop_id) if seq_to_event else {}
    )

    # Tag each flood event with sequence_type and storm metadata
    # storm_id IS the sequence_id (sequences are the unit of risk)
    for event in pdata.get('flood_events', []):
        sid = event.get('storm_id', '')
        event['sequence_type'] = seq_lookup.get(sid, 'isolated') if sid else 'isolated'
        # Storm metadata for canonical display format
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

        # Typhoon block — present only when the storm's paired typhoon
        # (shared event_id) produced wind damage at this property.
        evt_id = seq_to_event.get(sid)
        wind = wind_damage_by_event.get(evt_id) if evt_id else None
        if wind:
            event['typhoon'] = {
                'event_id':         evt_id,
                'scenario_family':  wind.get('scenario_family'),
                'peak_wind_ms':     wind.get('peak_sustained_ms'),
                'wind_threshold_ms': wind.get('threshold_ms'),
                'v_50_eff_ms':      wind.get('v_50_eff_ms'),
                'wind_damage_ratio': wind.get('damage_ratio'),
            }
        else:
            event['typhoon'] = None

    # Append synthetic flood_event rows for typhoons that hit this property's
    # wind damage record but didn't otherwise appear in flood_events (wind-only
    # typhoons that didn't trigger gauge response). These show in the History tab.
    if seq_to_event:
        seen_sids = {e.get('storm_id') for e in pdata.get('flood_events', [])}
        for sid, evt_id in seq_to_event.items():
            if sid in seen_sids:
                continue
            wind = wind_damage_by_event.get(evt_id)
            if not wind:
                continue  # Property not present in this typhoon's damage file
            meta = storm_meta.get(sid, {})
            cat = meta.get('intensity_category', '')
            pdata.setdefault('flood_events', []).append({
                'storm_id':       sid,
                'sequence_type':  seq_lookup.get(sid, 'isolated'),
                'intensity_category': cat,
                'name':           meta.get('name', '') or (cat.capitalize() if cat else ''),
                'effective_precipitation_mm':
                    meta.get('effective_precipitation_mm',
                             meta.get('total_precipitation_mm',
                                      meta.get('precipitation_mm', 0))),
                'gauges_severe':  storm_severe.get(sid, 0),
                'flood_depth_m':  0.0,
                'damage_ratio':   0.0,
                'flooded':        False,
                'typhoon': {
                    'event_id':         evt_id,
                    'scenario_family':  wind.get('scenario_family'),
                    'peak_wind_ms':     wind.get('peak_sustained_ms'),
                    'wind_threshold_ms': wind.get('threshold_ms'),
                    'v_50_eff_ms':      wind.get('v_50_eff_ms'),
                    'wind_damage_ratio': wind.get('damage_ratio'),
                },
            })


def _lookup_property_address(prop_id: str) -> str:
    """Look up a property's display address from property.json."""
    prop_address = ''
    try:
        prop_path = config.get_input_path('property.json')
        with open(prop_path, 'r') as f:
            pjdata = json.load(f)
        for p in pjdata.get('properties', []):
            ph = p.get('PropertyHeader', {})
            if ph.get('Header', {}).get('PropertyID') == prop_id:
                loc = ph.get('Location', {})
                prop_address = (
                    (loc.get('BuildingNumber', '') + ' '
                     + loc.get('StreetName', '')).strip()
                )
                break
    except Exception:
        pass
    return prop_address

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

"""Shared loaders for joining storm sequences to their paired typhoon events.

The flood-time-series peril pipeline (``port.src.peril.peril_ts``) and the
property hazard-curve wind pricer (``port.src.property.hc.pricing._wind``) both
need the same two read-only joins off the typhoon stage's output:

  - the per-event wind-damage index (``typhoon/damage/EVT-*.json``), and
  - the ``sequence_id → event_id`` map (``storm_sequences.json``).

The loading is identical for both; only the per-instance caching differs, so the
file-reading lives here once and each caller keeps its own cache wrapper.
"""

from typing import Dict

import database


def load_wind_damage_index() -> Dict[str, Dict[str, Dict]]:
    """``event_id → {property_id → {peak_sustained_ms, threshold_ms, v_50_eff_ms}}``.

    Reads each typhoon damage event for the active catchment through the database
    seam, keyed on its event id (the same ``EVT-*`` key the storm stage writes;
    the internal ``event_id`` field can be mis-stamped by genesis, so it is not
    trusted for the join). Returns an empty dict when the typhoon stage hasn't run.
    """
    catchment = database.active_catchment()
    out: Dict[str, Dict[str, Dict]] = {}
    for eid in database.iter_typhoon_event_ids(catchment):
        try:
            data = database.get_typhoon_event(catchment, eid) or {}
        except (OSError, ValueError):
            continue
        pmap: Dict[str, Dict] = {}
        for d in data.get('damages', []):
            pid = d.get('property_id')
            if pid:
                pmap[pid] = {
                    'peak_sustained_ms': d.get('peak_sustained_ms'),
                    'threshold_ms': d.get('threshold_ms'),
                    'v_50_eff_ms': d.get('v_50_eff_ms'),
                    # Persistence (duration-of-load) — None on legacy peak-only
                    # rows; carried for the insurance-loss / traceability view.
                    'duration_above_hours': d.get('duration_above_hours'),
                    'persistence_factor': d.get('persistence_factor'),
                }
        if pmap:
            out[eid] = pmap
    return out


def load_seq_to_event_map() -> Dict[str, str]:
    """``sequence_id → event_id`` from the storm sequences (empty if absent or
    pre-coupling, i.e. no ``event_id`` field on the sequences). Read for the
    active catchment through the database seam."""
    catchment = database.active_catchment()
    out: Dict[str, str] = {}
    try:
        data = database.get_storm_sequences(catchment) or {}
    except (OSError, ValueError):
        return out
    for seq in data.get('sequences', []):
        sid = seq.get('sequence_id')
        eid = seq.get('event_id')
        if sid and eid:
            out[sid] = eid
    return out

# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared loaders for joining storm sequences to their paired typhoon events.

The flood-time-series peril pipeline (``port.src.peril.peril_ts``) and the
property hazard-curve wind pricer (``port.src.property.hc.pricing._wind``) both
need the same two read-only joins off the typhoon stage's output:

  - the per-event wind-damage index (``typhoon/damage/EVT-*.json``), and
  - the ``sequence_id → event_id`` map (``storm_sequences.json``).

The loading is identical for both; only the per-instance caching differs, so the
file-reading lives here once and each caller keeps its own cache wrapper.
"""

import json
from pathlib import Path
from typing import Dict, Union


def load_wind_damage_index(output_dir: Union[str, Path]) -> Dict[str, Dict[str, Dict]]:
    """``event_id → {property_id → {peak_sustained_ms, threshold_ms, v_50_eff_ms}}``.

    Walks ``typhoon/damage/EVT-*.json`` once, keyed on the filename stem (the
    canonical event id that matches ``storm_sequences``; the internal
    ``event_id`` field can be mis-stamped by genesis, so it is not trusted for
    the join). Returns an empty dict when the typhoon stage hasn't run.
    """
    out: Dict[str, Dict[str, Dict]] = {}
    damage_dir = Path(output_dir) / 'typhoon' / 'damage'
    if not damage_dir.exists():
        return out
    for fp in sorted(damage_dir.glob('EVT-*.json')):
        try:
            with open(fp, 'r') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        eid = fp.stem
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


def load_seq_to_event_map(output_dir: Union[str, Path]) -> Dict[str, str]:
    """``sequence_id → event_id`` from ``storm_sequences.json`` (empty if absent
    or pre-coupling, i.e. no ``event_id`` field on the sequences)."""
    out: Dict[str, str] = {}
    seq_path = Path(output_dir) / 'storm_sequences.json'
    if not seq_path.exists():
        return out
    try:
        with open(seq_path, 'r') as f:
            data = json.load(f)
        for seq in data.get('sequences', []):
            sid = seq.get('sequence_id')
            eid = seq.get('event_id')
            if sid and eid:
                out[sid] = eid
    except (OSError, json.JSONDecodeError):
        pass
    return out

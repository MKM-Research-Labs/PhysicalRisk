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

"""True 1:1 storm ↔ typhoon pairing via the shared ``event_id``.

Replaces the retired severity-bucket linkage (``typhoon_storm_link.py``).
Under the coupled event set (``coupling_spec.md``, Stages 2–3) each storm
sequence carries the ``event_id`` of its paired typhoon, and that typhoon's
damage roll is written to ``typhoon/damage/<event_id>.json`` under the **same**
key. The pairing is therefore a **direct join on ``event_id``** — no
precipitation/wind ranking, no bucket alignment, no surplus to drop.

Behaviour:

- A storm is paired iff its ``event_id`` matches a typhoon damage file.
- Storms with no ``event_id`` (pre-coupling data) or whose typhoon stage never
  ran (flood-only fallback) simply have no entry — ``typhoon_for_storm``
  returns ``None`` and callers fall back to water-only.

The block returned per storm keeps the shape the route layer already expects::

    {event_id, scenario_family, peak_wind_ms, mean_damage_ratio}

The mapping is computed once per process; call :func:`get_pairing` rather than
rebuilding manually.
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

import database

logger = logging.getLogger(__name__)


def _load_typhoon_index() -> List[Dict]:
    """Walk the typhoon damage events once and build the typhoon severity index.

    Returns a list of {event_id, scenario_family, peak_wind_ms,
    mean_damage_ratio} dicts. Empty if the typhoon stage hasn't run. Events are
    read for the active catchment through the ``database`` seam, keyed on the
    event id (the same ``EVT-*`` key the storm stage writes); a corrupt event is
    logged and skipped.
    """
    catchment = database.active_catchment()
    index: List[Dict] = []
    for eid in sorted(database.iter_typhoon_event_ids(catchment)):
        try:
            data = database.get_typhoon_event(catchment, eid) or {}
        except (OSError, ValueError) as exc:
            logger.warning("storm_typhoon_pairing: skipping %s (%s)", eid, exc)
            continue
        damages = data.get("damages") or []
        if not damages:
            continue
        peaks = [d.get("peak_sustained_ms", 0.0) for d in damages]
        ratios = [d.get("damage_ratio", 0.0) for d in damages]
        index.append({
            "event_id": data.get("event_id") or eid,
            "scenario_family": data.get("scenario_family", "unknown"),
            "peak_wind_ms": max(peaks) if peaks else 0.0,
            "mean_damage_ratio": sum(ratios) / len(ratios) if ratios else 0.0,
        })
    return index


def _load_storm_event_map() -> List[Dict]:
    """Read storm sequences → [{sequence_id, event_id}, …] in sequence order.

    Only sequences carrying both a ``sequence_id`` and a non-empty ``event_id``
    are returned — the ``event_id`` is the shared 1:1 key written by the storm
    stage (Stage 2). Empty when the sequences are absent/unreadable or
    pre-coupling. Read for the active catchment through the ``database`` seam.
    """
    catchment = database.active_catchment()
    try:
        data = database.get_storm_sequences(catchment) or {}
    except (OSError, ValueError) as exc:
        logger.warning("storm_typhoon_pairing: cannot read storm sequences (%s)", exc)
        return []
    out: List[Dict] = []
    for seq in data.get("sequences", []):
        sid = seq.get("sequence_id")
        eid = seq.get("event_id")
        if not sid or not eid:
            continue
        out.append({"sequence_id": sid, "event_id": eid})
    return out


def build_pairing() -> Dict:
    """Produce the 1:1 storm ↔ typhoon pairing for the active catchment.

    Returns::

        {
          "storm_to_typhoon": { "<sequence_id>": {event_id, scenario_family,
                                                  peak_wind_ms,
                                                  mean_damage_ratio}, … },
          "typhoon_to_storm": { "<event_id>": "<sequence_id>", … },
          "diagnostics": {
              "paired_storms": int,
              "flood_only_storms": int,     # storms with no typhoon match
              "unmatched_typhoons": [event_id, …],
          }
        }

    Empty mapping when either side is unavailable.
    """
    storms = _load_storm_event_map()
    typhoons_by_id = {t["event_id"]: t for t in _load_typhoon_index()}

    storm_to_typhoon: Dict[str, Dict] = {}
    typhoon_to_storm: Dict[str, str] = {}
    flood_only = 0

    for s in storms:
        eid = s["event_id"]
        typhoon = typhoons_by_id.get(eid)
        if typhoon is None:
            # event_id present but the typhoon stage produced no damage roll
            # for it (flood-only fallback for this catchment).
            flood_only += 1
            continue
        storm_to_typhoon[s["sequence_id"]] = {
            "event_id": eid,
            "scenario_family": typhoon["scenario_family"],
            "peak_wind_ms": typhoon["peak_wind_ms"],
            "mean_damage_ratio": typhoon["mean_damage_ratio"],
        }
        typhoon_to_storm[eid] = s["sequence_id"]

    matched = set(typhoon_to_storm)
    diagnostics = {
        "paired_storms": len(storm_to_typhoon),
        "flood_only_storms": flood_only,
        "unmatched_typhoons": [eid for eid in typhoons_by_id if eid not in matched],
    }
    logger.info("storm_typhoon_pairing: paired %d storms 1:1 (flood-only=%d, "
                "unmatched typhoons=%d)", len(storm_to_typhoon), flood_only,
                len(diagnostics["unmatched_typhoons"]))
    return {
        "storm_to_typhoon": storm_to_typhoon,
        "typhoon_to_storm": typhoon_to_storm,
        "diagnostics": diagnostics,
    }


# -- Cached access --------------------------------------------------------

_PAIR_CACHE: Optional[Dict] = None
_PAIR_CACHE_LOCK = threading.Lock()


def get_pairing() -> Dict:
    """Return the cached pairing; build it on first call."""
    global _PAIR_CACHE
    if _PAIR_CACHE is not None:
        return _PAIR_CACHE
    with _PAIR_CACHE_LOCK:
        if _PAIR_CACHE is None:
            _PAIR_CACHE = build_pairing()
    return _PAIR_CACHE


def invalidate_cache() -> None:
    """Force a rebuild on the next get_pairing() call (test hook)."""
    global _PAIR_CACHE
    with _PAIR_CACHE_LOCK:
        _PAIR_CACHE = None


def typhoon_for_storm(sequence_id: str) -> Optional[Dict]:
    """Return the typhoon block paired with a storm, or None if water-only."""
    if not sequence_id:
        return None
    return get_pairing()["storm_to_typhoon"].get(sequence_id)


def storm_for_typhoon(event_id: str) -> Optional[str]:
    """Return the storm sequence paired with a typhoon, or None if unmatched."""
    if not event_id:
        return None
    return get_pairing()["typhoon_to_storm"].get(event_id)

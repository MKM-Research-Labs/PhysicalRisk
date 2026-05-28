# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Severity-bucket mapping from flood storms to typhoon events.

The 10k flood storms and the 50 typhoon events live in separate ID
namespaces with no cross-reference. This module produces a deterministic
linkage: for each flood ``intensity_category`` bucket the top-N flood
storms (by precipitation) are paired with the typhoons in the matching
``scenario_family`` bucket (by peak property-level wind).

Bucket alignment::

    flood intensity_category   ->   typhoon scenario_family
    -------------------------       -----------------------
    catastrophic                    extreme
    extreme                         severe
    severe                          historical + moderate
    moderate                        baseline
    (no flood category)             (any remainder — unused)

If a flood bucket has more storms than there are typhoons in the
matching family, the surplus storms remain water-only (no typhoon
link). Conversely, if the typhoon side has more events than the flood
bucket can absorb, the surplus typhoons are dropped from the linkage —
flagged in :func:`build_linkage` diagnostics.

The mapping is computed once per Python process. Call sites should
invoke :func:`get_linkage` rather than rebuilding manually.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional

from config import config

logger = logging.getLogger(__name__)


# flood intensity_category -> ordered tuple of typhoon scenario_family
# (allows multiple typhoon families to feed one flood bucket).
_BUCKET_ALIGNMENT: Dict[str, tuple] = {
    "catastrophic": ("extreme",),
    "extreme":      ("severe",),
    "severe":       ("historical", "moderate"),
    "moderate":     ("baseline",),
}


def _typhoon_dir() -> Path:
    """Active catchment's typhoon directory under data/input/<catch>/."""
    return config.get_input_dir() / "typhoon"


def _load_typhoon_index() -> List[Dict]:
    """Walk damage/EVT-*.json once and build the typhoon severity index.

    Returns a list of {event_id, scenario_family, peak_wind_ms,
    mean_damage_ratio} dicts. Empty if the typhoon stage hasn't run.
    """
    damage_dir = _typhoon_dir() / "damage"
    if not damage_dir.exists():
        return []
    index: List[Dict] = []
    for fp in sorted(damage_dir.glob("EVT-*.json")):
        try:
            with open(fp, "r") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("typhoon_storm_link: skipping %s (%s)", fp.name, exc)
            continue
        damages = data.get("damages") or []
        if not damages:
            continue
        peaks = [d.get("peak_sustained_ms", 0.0) for d in damages]
        ratios = [d.get("damage_ratio", 0.0) for d in damages]
        index.append({
            "event_id": data.get("event_id") or fp.stem,
            "scenario_family": data.get("scenario_family", "unknown"),
            "peak_wind_ms": max(peaks) if peaks else 0.0,
            "mean_damage_ratio": sum(ratios) / len(ratios) if ratios else 0.0,
        })
    return index


def _load_flood_index() -> List[Dict]:
    """Walk storm_sequences.json and build the flood severity index.

    Returns a list of {sequence_id, intensity_category, precipitation_mm}
    dicts ordered by total_precipitation_mm descending. Empty if the
    sequences file is missing.
    """
    seq_path = config.get_input_path("storm_sequences.json")
    if not seq_path.exists():
        return []
    try:
        with open(seq_path, "r") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("typhoon_storm_link: cannot read %s (%s)", seq_path, exc)
        return []
    index: List[Dict] = []
    for seq in data.get("sequences", []):
        sid = seq.get("sequence_id")
        if not sid:
            continue
        index.append({
            "sequence_id": sid,
            "intensity_category": seq.get("intensity_category", "unknown"),
            "precipitation_mm": float(seq.get("total_precipitation_mm", 0.0)),
        })
    # Sort once: heaviest precipitation first. Within-bucket selection
    # below relies on this ordering being stable.
    index.sort(key=lambda x: x["precipitation_mm"], reverse=True)
    return index


def build_linkage() -> Dict:
    """Produce the storm ↔ typhoon mapping for the active catchment.

    Returns::

        {
          "storm_to_typhoon": { "STORM-xxx": {event_id, scenario_family,
                                              peak_wind_ms} , … },
          "typhoon_to_storm": { "EVT-NNNN": "STORM-xxx", … },
          "diagnostics": {
              "flood_bucket_counts": {catastrophic: …, …},
              "typhoon_family_counts": {extreme: 4, …},
              "linked_storms": 50,
              "unmatched_typhoons": [],  # surplus typhoons
          }
        }

    Empty mapping when either side is unavailable.
    """
    floods = _load_flood_index()
    typhoons = _load_typhoon_index()

    diagnostics: Dict = {
        "flood_bucket_counts": {},
        "typhoon_family_counts": {},
        "linked_storms": 0,
        "unmatched_typhoons": [],
    }
    if not floods or not typhoons:
        logger.info("typhoon_storm_link: skipping linkage (floods=%d, typhoons=%d)",
                    len(floods), len(typhoons))
        return {"storm_to_typhoon": {}, "typhoon_to_storm": {}, "diagnostics": diagnostics}

    # Group typhoons by scenario_family, sorted by peak wind descending so
    # the strongest event in a family lands on the strongest flood storm.
    by_family: Dict[str, List[Dict]] = {}
    for t in typhoons:
        by_family.setdefault(t["scenario_family"], []).append(t)
    for fam in by_family:
        by_family[fam].sort(key=lambda x: x["peak_wind_ms"], reverse=True)
        diagnostics["typhoon_family_counts"][fam] = len(by_family[fam])

    # Group floods by intensity_category preserving the precipitation sort.
    by_category: Dict[str, List[Dict]] = {}
    for s in floods:
        by_category.setdefault(s["intensity_category"], []).append(s)
    diagnostics["flood_bucket_counts"] = {k: len(v) for k, v in by_category.items()}

    storm_to_typhoon: Dict[str, Dict] = {}
    typhoon_to_storm: Dict[str, str] = {}

    for flood_cat, family_keys in _BUCKET_ALIGNMENT.items():
        flood_pool = by_category.get(flood_cat, [])
        if not flood_pool:
            continue
        typhoon_pool: List[Dict] = []
        for fam in family_keys:
            typhoon_pool.extend(by_family.get(fam, []))
        # Within the combined family pool, take strongest typhoons first.
        typhoon_pool.sort(key=lambda x: x["peak_wind_ms"], reverse=True)
        n_pair = min(len(flood_pool), len(typhoon_pool))
        for storm, typhoon in zip(flood_pool[:n_pair], typhoon_pool[:n_pair]):
            storm_to_typhoon[storm["sequence_id"]] = {
                "event_id": typhoon["event_id"],
                "scenario_family": typhoon["scenario_family"],
                "peak_wind_ms": typhoon["peak_wind_ms"],
                "mean_damage_ratio": typhoon["mean_damage_ratio"],
            }
            typhoon_to_storm[typhoon["event_id"]] = storm["sequence_id"]

    # Any typhoons left over after the alignment loop are unmatched.
    matched_ids = set(typhoon_to_storm.keys())
    for t in typhoons:
        if t["event_id"] not in matched_ids:
            diagnostics["unmatched_typhoons"].append(t["event_id"])
    diagnostics["linked_storms"] = len(storm_to_typhoon)

    logger.info("typhoon_storm_link: linked %d storms (typhoon families: %s)",
                len(storm_to_typhoon),
                diagnostics["typhoon_family_counts"])
    return {
        "storm_to_typhoon": storm_to_typhoon,
        "typhoon_to_storm": typhoon_to_storm,
        "diagnostics": diagnostics,
    }


# -- Cached access --------------------------------------------------------

_LINK_CACHE: Optional[Dict] = None
_LINK_CACHE_LOCK = threading.Lock()


def get_linkage() -> Dict:
    """Return the cached linkage; build it on first call."""
    global _LINK_CACHE
    if _LINK_CACHE is not None:
        return _LINK_CACHE
    with _LINK_CACHE_LOCK:
        if _LINK_CACHE is None:
            _LINK_CACHE = build_linkage()
    return _LINK_CACHE


def invalidate_cache() -> None:
    """Force a rebuild on the next get_linkage() call (test hook)."""
    global _LINK_CACHE
    with _LINK_CACHE_LOCK:
        _LINK_CACHE = None


def link_for_storm(sequence_id: str) -> Optional[Dict]:
    """Return the typhoon block for a flood storm, or None if water-only."""
    if not sequence_id:
        return None
    return get_linkage()["storm_to_typhoon"].get(sequence_id)


def storm_for_typhoon(event_id: str) -> Optional[str]:
    """Return the flood storm linked to a typhoon, or None if unmatched."""
    if not event_id:
        return None
    return get_linkage()["typhoon_to_storm"].get(event_id)

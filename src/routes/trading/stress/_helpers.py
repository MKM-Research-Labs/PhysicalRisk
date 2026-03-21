# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Shared helpers and caches for stress test endpoints."""

import json
import math
import logging
from pathlib import Path

from config import config

logger = logging.getLogger(__name__)

# Storm simulation horizon — centralised in config/port.py
from config.port import EVENT_WINDOW_HOURS as STORM_HOURS

# Module-level caches
_stress_index_cache = None
_stress_index_mtime = None   # last-seen mtime of _index.json; cache invalidated when it changes
_predictor_cache = None
# Keep old names alive so test teardown code (stress_helpers._stress_storms_cache = None) doesn't crash
_stress_storms_cache = None


def _get_stress_storms_dir() -> Path:
    """Return path to stress_storms/ directory."""
    return config.get_input_dir() / 'stress_storms'


def _load_stress_storms():
    """Load the stress storm index (lightweight metadata, no gauge_responses).

    Reads from ``stress_storms/_index.json``.  Falls back to the legacy
    single ``stress_storms.json`` file for backward compatibility with data
    generated before the directory split.

    The cache is invalidated automatically whenever the index file's
    modification time changes — regenerating storms via ``port --stressm``
    takes effect on the next request without requiring a server restart.
    """
    global _stress_index_cache, _stress_index_mtime

    # Primary: directory-based layout
    ss_dir = _get_stress_storms_dir()
    index_path = ss_dir / '_index.json'
    if index_path.exists():
        try:
            mtime = index_path.stat().st_mtime
        except OSError:
            return _stress_index_cache
        if _stress_index_cache is None or mtime != _stress_index_mtime:
            with open(index_path) as f:
                _stress_index_cache = json.load(f)
            _stress_index_mtime = mtime
            logger.info("stress_storms/_index.json loaded/reloaded (%d storms)",
                        len((_stress_index_cache or {}).get("storms", [])))
        return _stress_index_cache

    # Legacy fallback: single stress_storms.json
    legacy_path = config.get_input_dir() / 'stress_storms.json'
    if legacy_path.exists():
        try:
            mtime = legacy_path.stat().st_mtime
        except OSError:
            return _stress_index_cache
        if _stress_index_cache is None or mtime != _stress_index_mtime:
            with open(legacy_path) as f:
                _stress_index_cache = json.load(f)
            _stress_index_mtime = mtime
            logger.info("stress_storms.json (legacy) loaded (%d storms)",
                        len((_stress_index_cache or {}).get("storms", [])))
        return _stress_index_cache

    return None


def _load_stress_storm(storm_id: str) -> dict | None:
    """Load a single storm's full record (including gauge_responses).

    Reads from ``stress_storms/{storm_id}.json``.  Falls back to searching
    the legacy single-file format if the directory layout isn't present.
    """
    ss_dir = _get_stress_storms_dir()
    storm_file = ss_dir / f'{storm_id}.json'
    if storm_file.exists():
        with open(storm_file) as f:
            return json.load(f)

    # Legacy fallback: search inside the monolithic file
    data = _load_stress_storms()
    if data:
        for s in data.get('storms', []):
            if s.get('storm_id') == storm_id:
                return s
    return None


def _synthesize_hydrograph(base_level, level_change, duration_hours,
                            peak_position, num_hours=STORM_HOURS):
    """Generate hourly water levels using smooth rise-peak-decay.

    Uses sinusoidal rise and exponential decay — same shape as the
    storm simulator's gauge response model.
    """
    peak_hour = min(duration_hours * peak_position, num_hours - 1)
    levels = []
    for h in range(num_hours):
        if peak_hour <= 0:
            t_decay = h / max(num_hours - 1, 1)
            frac = math.exp(-3.0 * t_decay)
        elif h <= peak_hour:
            t_rise = h / peak_hour
            frac = math.sin(t_rise * math.pi / 2)
        else:
            remaining = num_hours - peak_hour
            if remaining <= 0:
                frac = 1.0
            else:
                t_decay = (h - peak_hour) / remaining
                frac = math.exp(-3.0 * t_decay)
        levels.append(round(base_level + level_change * frac, 4))
    return levels


def _get_predictor():
    """Load and cache the FloodPredictor.

    Tries the multi-storm classifiers (stressm) first — they are the canonical
    models trained by ``port --stressm``.  Falls back to the legacy single-storm
    ``stress/`` directory if the stressm directory is absent (e.g. first run).
    """
    global _predictor_cache
    if _predictor_cache is None:
        from models.stress.flood_classifier import FloodPredictor
        # Primary: multi-storm classifiers in data/input/<catchment>/stressm/
        stressm_dir = config.get_stressm_dir()
        if list(stressm_dir.glob('GAUGE-*.joblib')):
            _predictor_cache = FloodPredictor(stressm_dir)
            logger.info("FloodPredictor loaded from stressm dir (%s)", stressm_dir)
            return _predictor_cache
        # Legacy fallback: data/output/stress/
        legacy_dir = Path(config.get_output_dir()) / 'stress'
        if legacy_dir.exists() and list(legacy_dir.glob('GAUGE-*.joblib')):
            _predictor_cache = FloodPredictor(legacy_dir)
            logger.info("FloodPredictor loaded from legacy stress dir (%s)", legacy_dir)
            return _predictor_cache
        logger.warning("No flood classifier models found in stressm or stress directories")
    return _predictor_cache


def _invalidate_predictor_cache():
    """Reset the predictor cache so the next request loads fresh models.

    Called after on-demand classifier training completes — the new .joblib
    file needs to be picked up by the predictor.
    """
    global _predictor_cache
    _predictor_cache = None

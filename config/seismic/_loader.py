# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Loader for the seismic model configuration.

Hydrates the typed dataclasses from the two seed-matrices JSON files, stripping
documentation keys (_doc, _meta) on the way in. No numeric value is embedded in
code; everything is read from config/seismicmatrices.json and
config/seismic_zones.json (which sit one level up, beside this package).
"""

import json
from pathlib import Path
from typing import Optional

from config.seismic._schema import (
    FragilityConfig,
    GroundMotionConfig,
    OccurrenceConfig,
    ResponseConfig,
    SeismicModelConfig,
    SeismicRunConfig,
)

# The JSON seed files live in config/, one level above this package.
_CONFIG_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MATRICES_PATH = _CONFIG_DIR / "seismicmatrices.json"
DEFAULT_ZONES_PATH = _CONFIG_DIR / "seismic_zones.json"


def _strip_docs(obj):
    """Recursively drop documentation keys (_doc, _meta, leading underscore)."""
    if isinstance(obj, dict):
        return {k: _strip_docs(v) for k, v in obj.items()
                if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(obj, list):
        return [_strip_docs(v) for v in obj]
    return obj


def load_seismic_config(
    matrices_path: Path = DEFAULT_MATRICES_PATH,
    zones_path: Path = DEFAULT_ZONES_PATH,
    run: Optional[SeismicRunConfig] = None,
) -> SeismicModelConfig:
    """Load the seismic model config from the two seed-matrices JSON files.

    Args:
        matrices_path: path to seismicmatrices.json (defaults beside config/).
        zones_path: path to seismic_zones.json (defaults beside config/).
        run: optional run-config override; defaults to SeismicRunConfig().

    Returns:
        A hydrated SeismicModelConfig.
    """
    matrices = _strip_docs(json.loads(Path(matrices_path).read_text()))
    zones = _strip_docs(json.loads(Path(zones_path).read_text()))

    gm_raw = zones["ground_motion"]
    site_raw = zones["site_class"]
    occ_raw = matrices["occurrence"]
    frag_raw = matrices["fragility"]
    resp_raw = matrices["response"]

    occurrence = OccurrenceConfig(
        zones=zones["zones"],
        hazard_class_to_zone=zones["hazard_class_to_zone"],
        default_zone=zones.get("default_zone", "Moderate"),
        soil_recurrence_m_soil=site_raw["soil_recurrence_m_soil"],
        fault_proximity=occ_raw["fault_proximity"],
        wells_coppersmith=occ_raw["wells_coppersmith"],
    )

    ground_motion = GroundMotionConfig(
        gmpe_by_regime=gm_raw["gmpe_by_regime"],
        default_regime=gm_raw.get("default_regime", "active_shallow_crust"),
        default_sigma_total=gm_raw.get("default_sigma_total", 0.65),
        vs30_proxy_by_class=site_raw["vs30_proxy_by_class"],
        vs30_bands=site_raw["vs30_bands"],
        default_site_class=site_raw.get("default_class", "B"),
        soil_amplification=site_raw["soil_amplification"],
    )

    response = ResponseConfig(
        measure_modifiers=resp_raw["measure_modifiers"],
        governance=resp_raw["governance"],
        gs02_soil_gate=resp_raw["gs02_soil_gate"],
        post_earthquake_fire=resp_raw["post_earthquake_fire"],
        recovery_acceleration=resp_raw["recovery_acceleration"],
        grade_code_sets=resp_raw["grade_code_sets"],
    )

    fragility = FragilityConfig(
        medians_by_construction=frag_raw["medians_by_construction"],
        default_beta=frag_raw.get("default_beta", 0.60),
        loss_given_damage_state=frag_raw["loss_given_damage_state"],
        recovery=frag_raw["recovery"],
    )

    return SeismicModelConfig(
        run=run or SeismicRunConfig(),
        occurrence=occurrence,
        ground_motion=ground_motion,
        response=response,
        fragility=fragility,
    )

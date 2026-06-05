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

"""
Model C — response effectiveness for the fire model.

Turns the static CDM resilience levels of one asset into the dynamic quantities
the fire progression consumes: how fast the fire is detected, how long until
active suppression bites, how quickly intensity grows, the critical intensity
threshold, the aggregate passive and response effectiveness, the vertical
(height) penalty, and an overall controllability score.

The result is a ResponseProfile, computed once per asset and reused for every
fire that asset instantiates. All numbers come from ProgressionConfig (loaded
from fire_matrices.json); this module embeds none. The resilience-level
vocabulary is imported from the CDM so the level->fraction mapping is
single-source.
"""

from typing import Optional

from config.fire import ProgressionConfig
from models.fire.data_structures import AssetFireFeatures, ResponseProfile
from port.cdm.asset.resilience import RESILIENCE_LEVELS

__all__ = [
    "level_index",
    "level_fraction",
    "height_penalty",
    "passive_effectiveness",
    "response_effectiveness",
    "controllability_score",
    "derive_response_profile",
]


# Map the JSON effectiveness-range keys (CDM field names) to the AssetFireFeatures
# attribute that carries that field's resilience level.
_PASSIVE_FIELD_TO_ATTR = {
    "StructuralFireResistanceAdequate": "structural_fire_resistance_level",
    "CompartmentsProvided": "compartments_level",
    "FireStoppingAtPenetrations": "fire_stopping_level",
    "ExternalMaterialsFireResistant": "external_materials_level",
}

_RESPONSE_FIELD_TO_ATTR = {
    "AccessRouteResilient": "access_route_level",
    "EmergencyProceduresTested": "emergency_procedures_level",
    "BusinessContinuityPlanInPlace": "business_continuity_level",
}

_WORST_LEVEL = RESILIENCE_LEVELS[0]   # "Not assessed"


# ===========================================================================
# Level helpers
# ===========================================================================


def level_index(level: Optional[str]) -> int:
    """Index of a resilience level in RESILIENCE_LEVELS.

    Unknown or missing levels map to the worst level (index 0) — an unassessed
    field is treated as offering no resilience benefit.
    """
    if level in RESILIENCE_LEVELS:
        return RESILIENCE_LEVELS.index(level)
    return 0


def level_fraction(level: Optional[str]) -> float:
    """Resilience level as a fraction in [0, 1] (worst 0.0 -> best 1.0)."""
    return level_index(level) / (len(RESILIENCE_LEVELS) - 1)


def _interpolate(low: float, high: float, frac: float) -> float:
    """Linear interpolation low + frac*(high-low), frac clamped to [0,1]."""
    frac = min(max(frac, 0.0), 1.0)
    return low + frac * (high - low)


# ===========================================================================
# Component derivations
# ===========================================================================


def height_penalty(features: AssetFireFeatures, cfg: ProgressionConfig) -> float:
    """Vertical suppression penalty (>= 1) from NumberOfStoreys.

    Interpolates the configured range from 1 storey -> range[0] to
    max_storeys -> range[1]. Missing storey count is treated as a single storey.
    """
    block = cfg.upper_floor_penalty_per_storey
    low, high = block["range"]
    max_storeys = block["max_storeys"]
    storeys = features.number_of_storeys or 1
    frac = (storeys - 1) / (max_storeys - 1) if max_storeys > 1 else 0.0
    return _interpolate(low, high, frac)


def _aggregate_effectiveness(features, field_map, ranges) -> float:
    """Mean over fields of each field's range interpolated by its level fraction."""
    values = []
    for field_name, attr in field_map.items():
        rng = ranges.get(field_name)
        if rng is None:
            continue
        frac = level_fraction(getattr(features, attr))
        values.append(_interpolate(rng[0], rng[1], frac))
    return sum(values) / len(values) if values else 0.0


def passive_effectiveness(features: AssetFireFeatures, cfg: ProgressionConfig) -> float:
    """Aggregate passive (structural) defence effectiveness in [0, 1]."""
    return _aggregate_effectiveness(
        features, _PASSIVE_FIELD_TO_ATTR, cfg.passive_effectiveness_ranges,
    )


def response_effectiveness(features: AssetFireFeatures, cfg: ProgressionConfig) -> float:
    """Aggregate active response effectiveness in [0, 1]."""
    return _aggregate_effectiveness(
        features, _RESPONSE_FIELD_TO_ATTR, cfg.response_effectiveness_ranges,
    )


def controllability_score(
    passive: float,
    response: float,
    suppression_fraction: float,
    cfg: ProgressionConfig,
) -> float:
    """Weighted controllability score in [0, 1] used to select the pre-PNR matrix.

    Combines passive defence, active response and suppression-system strength
    using the configured weights (renormalised defensively).
    """
    weights = cfg.controllability["weights"]
    wp, wr, ws = weights["passive"], weights["response"], weights["suppression"]
    total = wp + wr + ws
    if total <= 0.0:
        return 0.0
    return (wp * passive + wr * response + ws * suppression_fraction) / total


# ===========================================================================
# Profile assembly
# ===========================================================================


def derive_response_profile(
    features: AssetFireFeatures,
    cfg: ProgressionConfig,
) -> ResponseProfile:
    """Derive the per-asset ResponseProfile from its resilience levels.

    Deterministic — no randomness. Computed once per asset and reused across
    all of that asset's fires.
    """
    timing = cfg.timing
    dynamics = cfg.intensity_dynamics

    # Detection: faster (fewer steps) the better the detection level.
    detect_mult = cfg.detection_time_multiplier_by_level.get(
        features.automatic_detection_level or _WORST_LEVEL, 1.0,
    )
    detection_steps = timing["detection_base_steps"] * detect_mult

    # Suppression bite: slower the taller the building (height penalty).
    penalty = height_penalty(features, cfg)
    suppression_bite_steps = timing["suppression_bite_base_steps"] * penalty

    # Intensity growth: compartmentation quality (mean of compartments +
    # fire-stopping level indices) selects the well/poorly-compartmented rate.
    compartmentation_idx = 0.5 * (
        level_index(features.compartments_level)
        + level_index(features.fire_stopping_level)
    )
    growth_key = (
        "well_compartmented"
        if compartmentation_idx >= dynamics["compartmentation_well_threshold"]
        else "poorly_compartmented"
    )
    growth_per_step = cfg.growth_per_step_intensity[growth_key]

    # Suppression effectiveness: scales growth once suppression is active.
    suppression_growth_multiplier = cfg.suppression_growth_multiplier_by_level.get(
        features.suppression_systems_level or _WORST_LEVEL, 1.0,
    )

    # Critical intensity threshold: strong vs weak suppression by level index.
    suppression_idx = level_index(features.suppression_systems_level)
    i_crit_key = (
        "strong_suppression"
        if suppression_idx >= dynamics["strong_suppression_threshold"]
        else "weak_suppression"
    )
    i_crit = cfg.i_crit_by_suppression[i_crit_key]

    passive = passive_effectiveness(features, cfg)
    response = response_effectiveness(features, cfg)
    controllability = controllability_score(
        passive, response, level_fraction(features.suppression_systems_level), cfg,
    )

    return ResponseProfile(
        detection_steps=detection_steps,
        suppression_bite_steps=suppression_bite_steps,
        growth_per_step=growth_per_step,
        suppression_growth_multiplier=suppression_growth_multiplier,
        i_crit=i_crit,
        passive_effectiveness=passive,
        response_effectiveness=response,
        height_penalty=penalty,
        controllability=controllability,
    )

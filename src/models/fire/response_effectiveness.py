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
    "combustibility",
    "intensity_ceiling",
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


def combustibility(features: AssetFireFeatures, cfg: ProgressionConfig) -> float:
    """Structural-frame combustibility in [0, 1] from ConstructionType.

    0 = non-combustible (reinforced concrete); 1 = combustible (timber frame).
    An unknown / missing construction type returns the configured default (kept
    on the combustible side so an unassessed building is treated cautiously).
    """
    block = cfg.construction
    table = block["combustibility_by_type"]
    default = block["default_combustibility"]
    ctype = features.construction_type
    if ctype is None:
        return default
    return table.get(ctype, default)


def intensity_ceiling(combustibility_fraction: float, cfg: ProgressionConfig) -> float:
    """Cap on the latent intensity track implied by structural combustibility.

    The band is anchored on the combustible threshold so that EVERY
    non-combustible frame (combustibility at or below the threshold) shares the
    low plateau ``intensity_ceiling[0]`` — which sits below even the worst i_crit,
    so the intensity race can never cross the point of no return. Above the
    threshold the ceiling grades linearly up to ``intensity_ceiling[1]`` (above
    any i_crit) as the structure becomes fully combustible. This keeps the
    plateau flat across concrete/steel/brick (they should not conflagrate at all)
    while still grading modern-methods/mixed/timber by how much fuel they add.
    """
    low, high = cfg.construction["intensity_ceiling"]
    threshold = cfg.construction["combustible_threshold"]
    if combustibility_fraction <= threshold or threshold >= 1.0:
        return low
    frac = (combustibility_fraction - threshold) / (1.0 - threshold)
    return _interpolate(low, high, frac)


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
    suppression_idx = level_index(features.suppression_systems_level)

    # Detection: faster (fewer steps) the better the detection level.
    detect_mult = cfg.detection_time_multiplier_by_level.get(
        features.automatic_detection_level or _WORST_LEVEL, 1.0,
    )
    detection_steps = timing["detection_base_steps"] * detect_mult

    # Suppression bite. The fire service can only mount an effective external
    # attack up to the fire-truck reach height; above it, suppression must come
    # from internal sprinklers. A building taller than the reach with no
    # adequate internal suppression never achieves effective suppression — the
    # bite time is pushed beyond the step budget, so the fire runs to the point
    # of no return. Otherwise the bite time scales by both the per-storey height
    # penalty and the suppression-system level: a better system engages sooner
    # (smaller multiplier), which is how it wins the controllability race.
    penalty = height_penalty(features, cfg)
    bite_mult = cfg.suppression_bite_multiplier_by_level.get(
        features.suppression_systems_level or _WORST_LEVEL, 1.0,
    )
    reach = cfg.fire_service_reach
    internal_ok = suppression_idx >= reach["internal_suppression_threshold"]
    within_reach = (features.number_of_storeys or 1) <= reach["reach_storeys"]
    suppression_reachable = internal_ok or within_reach
    if suppression_reachable:
        suppression_bite_steps = (
            timing["suppression_bite_base_steps"] * penalty * bite_mult
        )
    else:
        suppression_bite_steps = reach["no_reach_bite_steps"]

    # Structural-frame combustibility drives the conflagration leg: it scales the
    # growth rate (the timing leg — combustible catches faster, giving suppression
    # less time to win the race), caps the intensity track (intensity_ceiling) and
    # gates the unreachable-suppression auto-PNR latch.
    combustibility_fraction = combustibility(features, cfg)

    # Intensity growth: compartmentation quality (mean of compartments +
    # fire-stopping level indices) selects the well/poorly-compartmented rate,
    # then combustibility scales it (a non-combustible frame grows slower).
    compartmentation_idx = 0.5 * (
        level_index(features.compartments_level)
        + level_index(features.fire_stopping_level)
    )
    growth_key = (
        "well_compartmented"
        if compartmentation_idx >= dynamics["compartmentation_well_threshold"]
        else "poorly_compartmented"
    )
    growth_scale_lo, growth_scale_hi = cfg.construction["growth_combustibility_scale"]
    growth_scale = _interpolate(growth_scale_lo, growth_scale_hi, combustibility_fraction)
    growth_per_step = cfg.growth_per_step_intensity[growth_key] * growth_scale

    # Suppression effectiveness: scales growth once suppression is active.
    suppression_growth_multiplier = cfg.suppression_growth_multiplier_by_level.get(
        features.suppression_systems_level or _WORST_LEVEL, 1.0,
    )

    # Critical intensity threshold: graded by suppression level so every level
    # shifts the controllability race (not a binary strong/weak step).
    i_crit = cfg.i_crit_by_level.get(
        features.suppression_systems_level or _WORST_LEVEL,
        cfg.i_crit_by_level[_WORST_LEVEL],
    )

    passive = passive_effectiveness(features, cfg)
    response = response_effectiveness(features, cfg)
    controllability = controllability_score(
        passive, response, level_fraction(features.suppression_systems_level), cfg,
    )

    # Intensity ceiling (fuel cap) + the unreachable-suppression auto-PNR gate,
    # both from the same combustibility fraction computed above.
    ceiling = intensity_ceiling(combustibility_fraction, cfg)
    structure_combustible = (
        combustibility_fraction >= cfg.construction["combustible_threshold"]
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
        suppression_reachable=suppression_reachable,
        combustibility=combustibility_fraction,
        intensity_ceiling=ceiling,
        structure_combustible=structure_combustible,
    )

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
Model A — Poisson initiation for the fire model.

Computes the per-asset annual ignition rate

    lambda_i = lambda_0,c * m_occ * m_proc * m_cond * m_protection * m_history

from CDM-derived AssetFireFeatures, then for each of n_sim draws samples a
Poisson count and instantiates a fire when the count >= 1 (the analog of
storm-event generation: only a subset of draws produce an event). Each
instantiated fire is tagged with an InitiationClass drawn from the
per-CommercialType categorical prior.

All numeric inputs arrive via config.fire (loaded from fire_matrices.json);
this module embeds no numbers. The resilience-level vocabulary is imported
from the CDM so m_protection stays single-source.

All randomness flows through a single numpy.random.Generator passed in by the
caller, matching the typhoon model convention.
"""

from typing import Dict, List, Optional

import numpy as np

from config.fire import FireModelConfig, InitiationClass, InitiationConfig
from models.fire.data_structures import (
    AssetFireFeatures,
    AssetInitiationResult,
    IgnitionDraw,
)
from port.cdm.asset.resilience import RESILIENCE_LEVELS

__all__ = [
    "m_occ",
    "m_proc",
    "m_cond",
    "m_protection",
    "m_history",
    "asset_lambda",
    "sample_initiation_class",
    "simulate_asset_initiation",
    "simulate_portfolio_initiation",
]


# ===========================================================================
# Frequency modifiers
# ===========================================================================
#
# Each modifier maps a CDM option (or a derived quantity) to a multiplier from
# the InitiationConfig seed tables. Unknown / missing options fall back to a
# neutral 1.0 so a partial CDM record still yields a usable lambda_i.


def m_occ(features: AssetFireFeatures, cfg: InitiationConfig) -> float:
    """Occupancy multiplier from OccupancyStatus (neutral 1.0 if unknown)."""
    if features.occupancy_status is None:
        return 1.0
    return cfg.m_occ_by_status.get(features.occupancy_status, 1.0)


def m_proc(features: AssetFireFeatures, cfg: InitiationConfig) -> float:
    """Process-load multiplier from CommercialType, raised by a business-rates
    override when that category implies a higher-process use (e.g. Restaurant).

    The override only ever raises m_proc — it never lowers the type-based value.
    """
    base = cfg.m_proc_by_type.get(features.commercial_type, 1.0)
    if features.business_rates_category is not None:
        override = cfg.m_proc_business_rates_override.get(
            features.business_rates_category
        )
        if override is not None:
            base = max(base, override)
    return base


def m_cond(features: AssetFireFeatures, cfg: InitiationConfig) -> float:
    """Condition multiplier from PropertyCondition (neutral 1.0 if unknown)."""
    if features.property_condition is None:
        return 1.0
    return cfg.m_cond_by_condition.get(features.property_condition, 1.0)


def _mean_protection_level(protection_levels: List[str]) -> Optional[str]:
    """Reduce the protection-field resilience levels to a single level label.

    Each level is mapped to its index in RESILIENCE_LEVELS, averaged, and
    rounded to the nearest level. Unknown labels are skipped. Returns None when
    no recognised level is present (caller then uses a neutral multiplier).
    """
    indices = [
        RESILIENCE_LEVELS.index(lv)
        for lv in protection_levels
        if lv in RESILIENCE_LEVELS
    ]
    if not indices:
        return None
    mean_idx = int(round(sum(indices) / len(indices)))
    mean_idx = max(0, min(len(RESILIENCE_LEVELS) - 1, mean_idx))
    return RESILIENCE_LEVELS[mean_idx]


def m_protection(features: AssetFireFeatures, cfg: InitiationConfig) -> float:
    """Protection multiplier from the mean resilience level across the
    protection fields (neutral 1.0 when no level is recognised)."""
    level = _mean_protection_level(features.protection_levels)
    if level is None:
        return 1.0
    return cfg.m_protection_by_level.get(level, 1.0)


def m_history(features: AssetFireFeatures, cfg: InitiationConfig) -> float:
    """History multiplier from FireDamageSeverity + recency of LastFireDate.

    A recent moderate/severe fire signals latent unaddressed risk (highest
    multiplier); an old or minor fire much less so; no prior fire is neutral.
    """
    severity = features.fire_damage_severity
    if severity is None or severity == "None":
        return cfg.m_history.get("no_prior", 1.0)

    recent_years = cfg.m_history.get("recent_years", 5)
    years = features.years_since_last_fire
    is_recent = years is not None and years <= recent_years

    severe = severity in ("Moderate", "Severe", "Total loss")

    if is_recent and severe:
        key = "recent_moderate_or_severe"
    elif is_recent:
        key = "recent_minor"
    else:
        key = "old_minor"
    return cfg.m_history.get(key, 1.0)


def asset_lambda(features: AssetFireFeatures, cfg: InitiationConfig) -> float:
    """Effective annual ignition rate lambda_i for one asset.

        lambda_i = lambda_0,c * m_occ * m_proc * m_cond * m_protection * m_history
    """
    lambda_0 = cfg.base_annual_frequency_by_type.get(features.commercial_type, 0.0)
    return (
        lambda_0
        * m_occ(features, cfg)
        * m_proc(features, cfg)
        * m_cond(features, cfg)
        * m_protection(features, cfg)
        * m_history(features, cfg)
    )


# ===========================================================================
# Initiation-class sampling
# ===========================================================================


def sample_initiation_class(
    commercial_type: str,
    cfg: InitiationConfig,
    rng: np.random.Generator,
) -> InitiationClass:
    """Draw an InitiationClass from the per-CommercialType categorical prior.

    Falls back to the "Other" type row when the asset's type has no prior.
    Probabilities are renormalised defensively (calibration drift tolerant).
    """
    priors = cfg.initiation_class_priors_by_type
    weights = priors.get(commercial_type) or priors.get("Other")
    if not weights:
        raise ValueError(
            f"No initiation-class prior for type {commercial_type!r} or 'Other'"
        )
    probs = np.array(weights, dtype=float)
    total = probs.sum()
    if total <= 0.0:
        raise ValueError("Initiation-class prior must sum to a positive value")
    probs = probs / total
    idx = int(rng.choice(len(cfg.initiation_classes), p=probs))
    return InitiationClass(cfg.initiation_classes[idx])


# ===========================================================================
# Simulation
# ===========================================================================


def simulate_asset_initiation(
    features: AssetFireFeatures,
    config: FireModelConfig,
    rng: np.random.Generator,
) -> AssetInitiationResult:
    """Run Stage-1 initiation for one asset.

    Draws config.run.n_sim Poisson counts at rate lambda_effective (the annual
    rate scaled to the run horizon), flags fire when count >= 1, and tags each
    instantiated fire with an initiation class.

    Returns:
        AssetInitiationResult with per-draw records and aggregate summaries.
    """
    cfg = config.initiation
    lambda_annual = asset_lambda(features, cfg)
    lambda_effective = lambda_annual * config.run.horizon_years
    n_sim = config.run.n_sim

    counts = rng.poisson(lambda_effective, size=n_sim)

    draws: List[IgnitionDraw] = []
    class_counts: Dict[InitiationClass, int] = {}
    n_fires = 0
    for i in range(n_sim):
        count = int(counts[i])
        fire = count >= 1
        klass: Optional[InitiationClass] = None
        if fire:
            n_fires += 1
            klass = sample_initiation_class(features.commercial_type, cfg, rng)
            class_counts[klass] = class_counts.get(klass, 0) + 1
        draws.append(IgnitionDraw(
            draw_index=i, count=count, fire=fire, initiation_class=klass,
        ))

    return AssetInitiationResult(
        asset_id=features.asset_id,
        lambda_annual=lambda_annual,
        lambda_effective=lambda_effective,
        n_sim=n_sim,
        n_fires=n_fires,
        fire_probability=n_fires / n_sim if n_sim else 0.0,
        class_counts=class_counts,
        draws=draws,
    )


def simulate_portfolio_initiation(
    features: List[AssetFireFeatures],
    config: FireModelConfig,
    rng: np.random.Generator,
) -> List[AssetInitiationResult]:
    """Run Stage-1 initiation for every asset in a portfolio.

    Assets share the single caller-owned Generator, so the whole portfolio run
    is reproducible from one seed.
    """
    return [
        simulate_asset_initiation(f, config, rng) for f in features
    ]

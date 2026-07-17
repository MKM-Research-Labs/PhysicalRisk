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
Model D — Damage State, Loss and Resilience Credit (MKM-SEIS-001).

For each instantiated earthquake the single-step lognormal fragility chain
assigns one of four damage states from the site PGA and the Model-C-adjusted
medians, draws a structural loss, optionally cascades a post-earthquake fire,
and reads a functionality-recovery index. Aggregated over n_sim draws the model
emits the resilience-credit leg the Commercial PRS Pricer consumes:

    loss frequency       = Sum L_s / n_sim
    no-collapse rate     = (n_DS0 + n_DS1 + n_DS2) / n_events
    seismic spread (bps) = (n_DS3 / n_sim) x LGE x 10,000

``simulate_asset_seismic`` runs the full A -> B -> C -> D pipeline for one asset
and ``simulate_portfolio_seismic`` runs the portfolio, both from a single
caller-owned generator so the run is reproducible from one seed.
"""

import math
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from config.seismic import FragilityConfig, SeismicModelConfig
from models.seismic.datastructures import (
    AssetSeismicFeatures,
    AssetSeismicResult,
    DamageOutcome,
)
from models.seismic.groundmotion import simulate_asset_ground_motion
from models.seismic.occurrence import Coord, simulate_asset_occurrence
from models.seismic.responseeffectiveness import derive_response_profile

__all__ = [
    "fragility_exceedance",
    "adjusted_medians",
    "assign_damage_state",
    "sample_loss_ratio",
    "functionality_index",
    "simulate_asset_seismic",
    "simulate_portfolio_seismic",
]

# A callable mapping a generator to a post-earthquake-fire loss ratio L_fire,
# the seam where the real MKM-FIRE-001 cascade is plugged in (SEIS-R1).
FireLossFn = Callable[[np.random.Generator], float]

_DS_THRESHOLDS = ("DS1", "DS2", "DS3")


def _phi(x: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def fragility_exceedance(pga: float, theta: float, beta: float) -> float:
    """P(DS >= threshold | PGA) = Phi((ln PGA - ln theta) / beta)."""
    if pga <= 0.0 or theta <= 0.0:
        return 0.0
    return _phi((math.log(pga) - math.log(theta)) / beta)


def adjusted_medians(
    construction_type: Optional[str],
    theta_mult: Dict[str, float],
    frag_cfg: FragilityConfig,
) -> Tuple[Dict[str, float], float]:
    """Model-C-adjusted fragility medians and beta for a construction class.

    ``theta_i_adj = theta_i_base * theta_mult[DS_i]`` (Section 3.5).
    """
    base = (frag_cfg.medians_by_construction.get(construction_type)
            or frag_cfg.medians_by_construction["Default"])
    beta = base.get("beta", frag_cfg.default_beta)
    medians = {ds: base[ds] * theta_mult.get(ds, 1.0) for ds in _DS_THRESHOLDS}
    return medians, beta


def assign_damage_state(
    pga: float, medians_adj: Dict[str, float], beta: float, u: float,
) -> int:
    """Assign the highest damage state whose exceedance probability exceeds *u*."""
    p1 = fragility_exceedance(pga, medians_adj["DS1"], beta)
    p2 = fragility_exceedance(pga, medians_adj["DS2"], beta)
    p3 = fragility_exceedance(pga, medians_adj["DS3"], beta)
    if u <= p3:
        return 3
    if u <= p2:
        return 2
    if u <= p1:
        return 1
    return 0


def sample_loss_ratio(
    damage_state: int, frag_cfg: FragilityConfig, rng: np.random.Generator,
) -> float:
    """Structural loss ratio L_s for a damage state (Appendix E2).

    DS3 is the fixed total loss; the others are truncated-lognormal draws (the
    seed mean is used as the lognormal median) clipped to [0, 1].
    """
    block = frag_cfg.loss_given_damage_state[f"DS{damage_state}"]
    if "fixed" in block:
        return block["fixed"]
    value = block["mean"] * math.exp(block["logstd"] * float(rng.standard_normal()))
    return min(1.0, max(0.0, value))


def functionality_index(
    damage_state: int, r_acc: float, frag_cfg: FragilityConfig,
) -> float:
    """Normalised area under the functionality curve Q(t) over the horizon.

    Q(t) ramps linearly from Q(t0) to 1.0 over the effective recovery time
    ``T_rec / r_acc`` (Section 3.5); the index is the mean of Q over the control
    horizon T_LC, in [0, 1].
    """
    rec = frag_cfg.recovery
    key = f"DS{damage_state}"
    q0 = rec["q_t0_by_ds"][key]
    t_rec = rec["t_rec_months_by_ds"][key]
    t_lc = rec["control_horizon_months"]
    if t_rec <= 0 or q0 >= 1.0 or r_acc <= 0.0 or t_lc <= 0:
        return 1.0
    t_eff = t_rec / r_acc
    if t_eff >= t_lc:
        # Never fully recovers within the horizon.
        return q0 + (1.0 - q0) * t_lc / (2.0 * t_eff)
    area = q0 * t_eff + (1.0 - q0) * t_eff / 2.0 + (t_lc - t_eff)
    return area / t_lc


def _cascade_fire_loss(
    pef_cfg: dict, rng: np.random.Generator, fire_loss_fn: Optional[FireLossFn],
) -> float:
    """Loss-given-cascade L_fire — the hook, else the seed conditional draw."""
    if fire_loss_fn is not None:
        return fire_loss_fn(rng)
    cfl = pef_cfg.get("conditional_fire_loss")
    if not cfl:
        return 1.0
    value = cfl["mean"] * math.exp(cfl["logstd"] * float(rng.standard_normal()))
    return min(1.0, max(0.0, value))


def simulate_asset_seismic(
    features: AssetSeismicFeatures,
    config: SeismicModelConfig,
    fault: Optional[List[Coord]],
    rng: np.random.Generator,
    n_sim: Optional[int] = None,
    fire_loss_fn: Optional[FireLossFn] = None,
) -> AssetSeismicResult:
    """Run the full seismic model (Models A-D) for one asset.

    Args:
        features: the asset's CDM-derived feature bundle.
        config: the hydrated seismic model config.
        fault: the catchment fault trace as ``(lat, lon)`` vertices, or None.
        rng: caller-owned random generator (threaded for reproducibility).
        n_sim: optional draw-count override; defaults to ``config.run.n_sim``.
        fire_loss_fn: optional post-earthquake-fire loss hook; defaults to the
            seed conditional-loss draw.

    Returns:
        An :class:`AssetSeismicResult` carrying the seismic spread leg.
    """
    occurrence = simulate_asset_occurrence(features, config, fault, rng, n_sim)
    ground = simulate_asset_ground_motion(occurrence, features, config, rng)
    profile = derive_response_profile(features, config)

    frag = config.fragility
    pef_cfg = config.response.post_earthquake_fire
    medians_adj, beta = adjusted_medians(
        features.construction_type, profile.theta_mult, frag)

    n = occurrence.n_sim
    loss_array = np.zeros(n)
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    n_cascade = 0
    resilience_sum = 0.0
    outcomes: List[DamageOutcome] = []

    for event, sample in zip(occurrence.events, ground.samples):
        pga = sample.pga_g
        damage_state = assign_damage_state(pga, medians_adj, beta, float(rng.random()))
        structural = sample_loss_ratio(damage_state, frag, rng)

        combined = structural
        cascade = False
        if damage_state >= 2:
            p_pef = profile.p_pef_by_ds.get(f"DS{damage_state}", 0.0)
            if float(rng.random()) < p_pef:
                cascade = True
                combined = max(structural, _cascade_fire_loss(pef_cfg, rng, fire_loss_fn))

        resilience = functionality_index(damage_state, profile.r_acc, frag)
        counts[damage_state] += 1
        n_cascade += int(cascade)
        resilience_sum += resilience
        loss_array[event.draw_index] = combined
        outcomes.append(DamageOutcome(
            draw_index=event.draw_index,
            pga_g=pga,
            damage_state=damage_state,
            structural_loss=structural,
            cascade_fire=cascade,
            combined_loss=combined,
            resilience_index=resilience,
        ))

    n_events = occurrence.n_events
    lge = config.run.loss_given_event_collapse
    no_collapse = (counts[0] + counts[1] + counts[2]) / n_events if n_events else 1.0
    spread = (counts[3] / n) * lge * 10_000.0 if n else 0.0

    return AssetSeismicResult(
        asset_id=features.asset_id,
        zone=occurrence.zone,
        site_class=occurrence.site_class,
        construction_type=features.construction_type or "Default",
        rating=profile.rating,
        lambda_annual=occurrence.lambda_annual,
        n_sim=n,
        n_events=n_events,
        damage_state_counts=counts,
        n_cascade_fire=n_cascade,
        loss_frequency=float(loss_array.mean()) if n else 0.0,
        no_collapse_rate=no_collapse,
        seismic_spread_bps=spread,
        mean_resilience_index=resilience_sum / n_events if n_events else 1.0,
        pml_475=float(np.quantile(loss_array, 1.0 - 1.0 / 475.0)) if n else 0.0,
        pml_2475=float(np.quantile(loss_array, 1.0 - 1.0 / 2475.0)) if n else 0.0,
        outcomes=outcomes,
    )


def simulate_portfolio_seismic(
    features: List[AssetSeismicFeatures],
    config: SeismicModelConfig,
    fault: Optional[List[Coord]],
    rng: np.random.Generator,
    n_sim: Optional[int] = None,
    fire_loss_fn: Optional[FireLossFn] = None,
) -> List[AssetSeismicResult]:
    """Run the full seismic model for every asset in a portfolio.

    Assets share the single caller-owned generator, so the whole portfolio run
    is reproducible from one seed.
    """
    return [
        simulate_asset_seismic(f, config, fault, rng, n_sim, fire_loss_fn)
        for f in features
    ]

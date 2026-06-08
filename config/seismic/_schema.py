# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Typed configuration dataclasses for the seismic model (MKM-SEIS-001).

These describe the *shape* of the seed parameters; the loader (_loader.py)
hydrates them from config/seismicmatrices.json and config/seismic_zones.json.
No numeric value is embedded here.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SeismicRunConfig:
    """Top-level simulation knobs.

    Attributes:
        n_sim: number of Monte Carlo draws per asset (Poisson occurrence).
        horizon_years: exposure horizon for the Poisson rate (1.0 = annual).
        loss_given_event_collapse: fixed loss-given-event for the DS3 leg the
            PRS pricer charges (1.0 = 100%), mirroring the fire conflagration
            leg's fixed quantum.
    """
    n_sim: int = 10000
    horizon_years: float = 1.0
    loss_given_event_collapse: float = 1.0


@dataclass
class OccurrenceConfig:
    """Model A seed parameters — Poisson occurrence and fault spatial draw.

    lambda_i = lambda_zone * m_fault * m_soil

    Attributes:
        zones: per-zone {lambda_zone, b, m_min, m_max, tectonic_regime} block.
        hazard_class_to_zone: CDM SeismicHazardClass -> zone label.
        default_zone: zone used when the hazard class is missing/unmapped.
        soil_recurrence_m_soil: m_soil multiplier per Eurocode site class.
        fault_proximity: {delta_gs01, threshold_km} for the near-fault uplift.
        wells_coppersmith: {a, b} for log10(L_r_km) = a + b*M rupture scaling.
    """
    zones: Dict[str, dict] = field(default_factory=dict)
    hazard_class_to_zone: Dict[str, str] = field(default_factory=dict)
    default_zone: str = "Moderate"
    soil_recurrence_m_soil: Dict[str, float] = field(default_factory=dict)
    fault_proximity: Dict[str, float] = field(default_factory=dict)
    wells_coppersmith: Dict[str, float] = field(default_factory=dict)


@dataclass
class GroundMotionConfig:
    """Model B seed parameters — GMPE and site amplification (Appendix C).

    Attributes:
        gmpe_by_regime: per tectonic-regime parametric GMPE coefficient block.
        default_regime: regime used when a zone does not name one.
        default_sigma_total: fallback total log-sigma when a GMPE omits it.
        vs30_proxy_by_class: V_S30 (m/s) proxy per site class.
        vs30_bands: lower V_S30 bound (m/s) per site class (classification).
        default_site_class: site class used when V_S30 is unavailable.
        soil_amplification: {fa, applies_classes} for the GS02 soft-soil gate.
    """
    gmpe_by_regime: Dict[str, dict] = field(default_factory=dict)
    default_regime: str = "active_shallow_crust"
    default_sigma_total: float = 0.65
    vs30_proxy_by_class: Dict[str, float] = field(default_factory=dict)
    vs30_bands: Dict[str, float] = field(default_factory=dict)
    default_site_class: str = "B"
    soil_amplification: Dict[str, object] = field(default_factory=dict)


@dataclass
class ResponseConfig:
    """Model C seed parameters — BRI geoseismic measure -> modifier mapping
    (Appendix D).

    Attributes:
        measure_modifiers: per GS code {applies, delta} fragility-median shift.
        governance: GS16-18 {codes, delta_each, combined_cap, applies} block.
        gs02_soil_gate: {code, removes_fa} soft-soil amplification gate.
        post_earthquake_fire: {gs15_code, gs15_reduction, p_pef_by_ds} cascade.
        recovery_acceleration: {r_acc_by_rating, gs18_multiplier, gs18_code}.
        grade_code_sets: {B, A_extra, AA_extra} BRI rating tiers for r_acc.
    """
    measure_modifiers: Dict[str, dict] = field(default_factory=dict)
    governance: Dict[str, object] = field(default_factory=dict)
    gs02_soil_gate: Dict[str, object] = field(default_factory=dict)
    post_earthquake_fire: Dict[str, object] = field(default_factory=dict)
    recovery_acceleration: Dict[str, object] = field(default_factory=dict)
    grade_code_sets: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class FragilityConfig:
    """Model D seed parameters — fragility, loss and recovery (Appendix E).

    Attributes:
        medians_by_construction: per fragility-class {DS1, DS2, DS3, beta}.
        default_beta: log-standard deviation when a class omits beta.
        loss_given_damage_state: per-DS {mean, logstd} (DS3 -> {fixed}).
        recovery: {q_t0_by_ds, t_rec_months_by_ds, control_horizon_months}.
    """
    medians_by_construction: Dict[str, dict] = field(default_factory=dict)
    default_beta: float = 0.60
    loss_given_damage_state: Dict[str, dict] = field(default_factory=dict)
    recovery: Dict[str, object] = field(default_factory=dict)


@dataclass
class SeismicModelConfig:
    """Aggregate seismic-model configuration (run knobs + all seed parameters)."""
    run: SeismicRunConfig
    occurrence: OccurrenceConfig
    ground_motion: GroundMotionConfig
    response: ResponseConfig
    fragility: FragilityConfig

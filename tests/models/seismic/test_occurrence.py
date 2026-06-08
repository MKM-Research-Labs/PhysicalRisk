# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Tests for Model A — occurrence and fault-geometry spatial draw (occurrence.py).

Covers: fault-trace parsing ([lon,lat] -> (lat,lon)); cumulative arc-length;
zone and site-class resolution; truncated Gutenberg-Richter magnitude bounds;
the lambda_i multiplier chain (zone / soil / near-fault uplift); Joyner-Boore
distance monotonicity with source-to-site distance; and portfolio
reproducibility from a single seed.
"""

from dataclasses import replace

import numpy as np
import pytest

from config.seismic import load_seismic_config
from models.seismic.datastructures import AssetSeismicFeatures
from models.seismic.occurrence import (
    asset_fault_distance_km,
    asset_lambda,
    cumulative_arclengths,
    joyner_boore_distance_km,
    parse_fault_trace,
    resolve_site_class,
    resolve_zone,
    sample_magnitude,
    simulate_asset_occurrence,
    simulate_portfolio_occurrence,
)

# A simple ~constant-latitude fault running east at lat 21.0 from lon 105 to 107
# (~208 km). [lon, lat] on disk, per Appendix B.
_FAULT_RAW = [[105.0, 21.0], [105.5, 21.0], [106.0, 21.0], [106.5, 21.0], [107.0, 21.0]]


@pytest.fixture
def config():
    return load_seismic_config()


@pytest.fixture
def fault():
    return parse_fault_trace(_FAULT_RAW)


def _asset(**overrides):
    base = dict(
        asset_id="SEIS-1",
        commercial_type="Office",
        construction_type="RC_PreCode",
        number_of_storeys=4,
        latitude=20.90,            # ~11 km south of the lat-21.0 fault
        longitude=106.0,
        soil_vs30_mps=450.0,       # site class B
        seismic_hazard_class="Medium",  # Moderate zone
        measures=frozenset(),
    )
    base.update(overrides)
    return AssetSeismicFeatures(**base)


def _rng(seed=20260608):
    return np.random.default_rng(seed)


# ===========================================================================
# Fault trace parsing & geometry
# ===========================================================================


def test_parse_flips_lon_lat_order(fault):
    # On disk [105.0, 21.0] is [lon, lat]; parsed as (lat, lon).
    assert fault[0] == (21.0, 105.0)


def test_parse_rejects_short_trace():
    with pytest.raises(ValueError):
        parse_fault_trace([[105.0, 21.0]])


def test_cumulative_arclengths_monotone(fault):
    cum = cumulative_arclengths(fault)
    assert cum[0] == 0.0
    assert cum == sorted(cum)
    assert cum[-1] == pytest.approx(208.0, rel=0.02)  # ~208 km total


# ===========================================================================
# Zone & site-class resolution
# ===========================================================================


def test_resolve_zone_from_hazard_class(config):
    occ = config.occurrence
    assert resolve_zone(_asset(seismic_hazard_class="Medium"), occ) == "Moderate"
    assert resolve_zone(_asset(seismic_hazard_class="Extreme"), occ) == "Very high"


def test_resolve_zone_defaults_when_unknown(config):
    occ = config.occurrence
    assert resolve_zone(_asset(seismic_hazard_class=None), occ) == occ.default_zone


def test_resolve_site_class_from_vs30(config):
    gm = config.ground_motion
    assert resolve_site_class(800.0, gm) == "A"
    assert resolve_site_class(450.0, gm) == "B"
    assert resolve_site_class(270.0, gm) == "C"
    assert resolve_site_class(150.0, gm) == "D"
    assert resolve_site_class(100.0, gm) == "E"
    assert resolve_site_class(None, gm) == gm.default_site_class


# ===========================================================================
# Magnitude — truncated Gutenberg-Richter
# ===========================================================================


def test_magnitude_within_bounds(config):
    rng = _rng()
    draws = [sample_magnitude(1.0, 5.0, 7.5, rng) for _ in range(5000)]
    assert min(draws) >= 5.0
    assert max(draws) <= 7.5
    # G-R is bottom-heavy: the mean sits well below the midpoint.
    assert np.mean(draws) < 6.0


def test_magnitude_degenerate_bounds_return_min(config):
    assert sample_magnitude(1.0, 6.0, 6.0, _rng()) == 6.0


# ===========================================================================
# lambda_i multiplier chain
# ===========================================================================


def test_lambda_increases_with_hazard_zone(config):
    low = _asset(seismic_hazard_class="Low")
    high = _asset(seismic_hazard_class="Extreme")
    lam_low = asset_lambda(low, None, "B", config)
    lam_high = asset_lambda(high, None, "B", config)
    assert lam_high > lam_low


def test_soil_recurrence_modifier_applied(config):
    a = _asset()
    lam_rock = asset_lambda(a, None, "A", config)
    lam_soft = asset_lambda(a, None, "E", config)
    assert lam_soft == pytest.approx(lam_rock * 1.20)


def test_near_fault_uplift_only_without_gs01(config):
    near = _asset()
    lam_plain = asset_lambda(near, fault_distance_km=0.5, site_class="B", config=config)
    lam_base = asset_lambda(near, fault_distance_km=5.0, site_class="B", config=config)
    assert lam_plain == pytest.approx(lam_base * 1.15)
    # GS01 (seismic design at the fault) removes the uplift.
    protected = _asset(measures=frozenset({"GS01"}))
    lam_protected = asset_lambda(protected, 0.5, "B", config)
    assert lam_protected == pytest.approx(lam_base)


# ===========================================================================
# Joyner-Boore distance
# ===========================================================================


def test_rjb_grows_with_source_to_site_distance(fault):
    # Whole-fault distance as a proxy rupture: nearer asset -> smaller R_JB.
    near = joyner_boore_distance_km(20.95, 106.0, fault)   # ~5.5 km south
    far = joyner_boore_distance_km(20.50, 106.0, fault)    # ~55 km south
    assert near < far
    assert near == pytest.approx(5.5, rel=0.1)


def test_asset_fault_distance_prefers_explicit(fault):
    a = _asset(fault_proximity_km=3.3)
    assert asset_fault_distance_km(a, fault) == 3.3


# ===========================================================================
# Orchestrators
# ===========================================================================


def test_occurrence_instantiates_events(config, fault):
    # High-hazard, near-fault asset over many draws produces events with
    # in-range magnitudes and finite R_JB.
    asset = _asset(seismic_hazard_class="Extreme")
    result = simulate_asset_occurrence(asset, config, fault, _rng(), n_sim=20000)
    assert result.zone == "Very high"
    assert result.site_class == "B"
    assert result.n_events > 0
    assert result.n_events == len(result.events)
    for ev in result.events:
        assert 5.0 <= ev.magnitude <= 8.5
        assert ev.r_jb_km > 0.0
        assert ev.rupture_length_km > 0.0


def test_event_rate_scales_with_zone(config, fault):
    low = simulate_asset_occurrence(
        _asset(seismic_hazard_class="Low"), config, fault, _rng(), n_sim=20000)
    high = simulate_asset_occurrence(
        _asset(seismic_hazard_class="Extreme"), config, fault, _rng(), n_sim=20000)
    assert high.event_rate > low.event_rate


def test_occurrence_without_fault_has_zero_rjb(config):
    result = simulate_asset_occurrence(
        _asset(seismic_hazard_class="Extreme"), config, None, _rng(), n_sim=5000)
    assert result.fault_distance_km is None
    assert all(ev.r_jb_km == 0.0 for ev in result.events)


def test_occurrence_is_reproducible(config, fault):
    asset = _asset(seismic_hazard_class="High")
    r1 = simulate_asset_occurrence(asset, config, fault, _rng(), n_sim=10000)
    r2 = simulate_asset_occurrence(asset, config, fault, _rng(), n_sim=10000)
    assert r1.n_events == r2.n_events
    assert [e.magnitude for e in r1.events] == [e.magnitude for e in r2.events]
    assert [e.r_jb_km for e in r1.events] == [e.r_jb_km for e in r2.events]


def test_portfolio_runs_every_asset(config, fault):
    feats = [_asset(asset_id="A"), _asset(asset_id="B", seismic_hazard_class="High")]
    results = simulate_portfolio_occurrence(feats, config, fault, _rng(), n_sim=2000)
    assert [r.asset_id for r in results] == ["A", "B"]

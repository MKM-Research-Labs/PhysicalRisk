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

"""Tests for Stage 1 of the fire model — config loading + Poisson initiation.

Verifies that:
- config/fire_matrices.json loads into a complete FireModelConfig
- the seed parameter tables cover every CommercialType / option vocabulary
- frequency modifiers map options to multipliers with neutral fallbacks
- lambda_i composes the multiplier chain correctly
- the Poisson simulation produces reproducible fire/no-fire draws whose
  empirical rate tracks the configured lambda, and tags fires with classes
"""

import numpy as np
import pytest

from config.fire import (
    FireModelConfig,
    FireRunConfig,
    InitiationClass,
    load_fire_config,
)
from models.fire.data_structures import AssetFireFeatures
from models.fire.initiation import (
    asset_lambda,
    m_cond,
    m_history,
    m_occ,
    m_proc,
    m_protection,
    sample_initiation_class,
    simulate_asset_initiation,
    simulate_portfolio_initiation,
)
from port.cdm.asset.commercial.schema import COMMERCIAL_TYPE_OPTIONS
from port.cdm.asset.resilience import RESILIENCE_LEVELS


def _rng(seed=20260605):
    return np.random.default_rng(seed)


@pytest.fixture
def config():
    return load_fire_config()


@pytest.fixture
def office():
    return AssetFireFeatures(
        asset_id="ASSET-001",
        commercial_type="Office",
        occupancy_status="Fully occupied",
        business_rates_category="Office",
        property_condition="Good",
        automatic_detection_level="Enhanced",
        suppression_systems_level="Enhanced",
        emergency_procedures_level="Meets minimum",
        fire_damage_severity="None",
        years_since_last_fire=None,
        number_of_storeys=4,
    )


# ===========================================================================
# Config loading
# ===========================================================================


def test_load_returns_complete_config(config):
    assert isinstance(config, FireModelConfig)
    assert config.run.n_sim == 1000
    assert config.run.step_minutes == 15
    assert config.run.max_steps == 200
    assert config.run.horizon_hours == pytest.approx(50.0)


def test_doc_keys_are_stripped(config):
    # No "_doc"/"_meta" helper keys leak into the loaded mappings.
    assert "_doc" not in config.initiation.base_annual_frequency_by_type
    assert "classes" not in config.initiation.initiation_class_priors_by_type


def test_every_commercial_type_has_seed_params(config):
    init = config.initiation
    for ct in COMMERCIAL_TYPE_OPTIONS:
        assert ct in init.base_annual_frequency_by_type
        assert ct in init.m_proc_by_type
        assert ct in init.initiation_class_priors_by_type


def test_initiation_class_priors_sum_to_one(config):
    init = config.initiation
    for ct, weights in init.initiation_class_priors_by_type.items():
        assert len(weights) == len(init.initiation_classes)
        assert sum(weights) == pytest.approx(1.0)


def test_protection_table_covers_all_levels(config):
    for level in RESILIENCE_LEVELS:
        assert level in config.initiation.m_protection_by_level


def test_transition_matrices_are_row_stochastic(config):
    for name, matrix in config.progression.transition_matrices.items():
        assert len(matrix) == 8, name
        for row in matrix:
            assert len(row) == 8, name
            assert sum(row) == pytest.approx(1.0), name


def test_point_of_no_return_zeroes_contained_column(config):
    # S5_Contained is column index 5. Under the PNR matrix no transient state
    # can reach Contained — only the Contained self-loop remains.
    matrix = config.progression.transition_matrices["point_of_no_return"]
    for i, row in enumerate(matrix):
        if i == 5:
            assert row[5] == pytest.approx(1.0)
        else:
            assert row[5] == pytest.approx(0.0)


# ===========================================================================
# Frequency modifiers
# ===========================================================================


def test_modifiers_are_neutral_when_options_missing(config):
    bare = AssetFireFeatures(asset_id="X", commercial_type="Office")
    cfg = config.initiation
    assert m_occ(bare, cfg) == 1.0
    assert m_cond(bare, cfg) == 1.0
    assert m_protection(bare, cfg) == 1.0
    assert m_history(bare, cfg) == 1.0


def test_business_rates_override_only_raises_m_proc(config):
    cfg = config.initiation
    # Office base m_proc is 1.00; a Restaurant rates category raises it.
    restaurant_office = AssetFireFeatures(
        asset_id="X", commercial_type="Office",
        business_rates_category="Restaurant",
    )
    assert m_proc(restaurant_office, cfg) == pytest.approx(1.25)
    # A Hotel (base 1.25) is not lowered by an Office rates category.
    hotel = AssetFireFeatures(
        asset_id="Y", commercial_type="Hotel",
        business_rates_category="Office",
    )
    assert m_proc(hotel, cfg) == pytest.approx(1.25)


def test_m_protection_uses_mean_level(config):
    cfg = config.initiation
    # Mean of [Verified(4), Verified(4), Enhanced(3)] -> round(3.67)=4 -> Verified.
    feats = AssetFireFeatures(
        asset_id="X", commercial_type="Office",
        automatic_detection_level="Verified",
        suppression_systems_level="Verified",
        emergency_procedures_level="Enhanced",
    )
    assert m_protection(feats, cfg) == pytest.approx(
        cfg.m_protection_by_level["Verified"]
    )


def test_m_history_recent_severe_is_highest(config):
    cfg = config.initiation
    recent_severe = AssetFireFeatures(
        asset_id="X", commercial_type="Office",
        fire_damage_severity="Severe", years_since_last_fire=2.0,
    )
    old_severe = AssetFireFeatures(
        asset_id="Y", commercial_type="Office",
        fire_damage_severity="Severe", years_since_last_fire=20.0,
    )
    assert m_history(recent_severe, cfg) > m_history(old_severe, cfg)
    assert m_history(recent_severe, cfg) == pytest.approx(
        cfg.m_history["recent_moderate_or_severe"]
    )


def test_asset_lambda_composes_multiplier_chain(config, office):
    cfg = config.initiation
    expected = (
        cfg.base_annual_frequency_by_type["Office"]
        * m_occ(office, cfg)
        * m_proc(office, cfg)
        * m_cond(office, cfg)
        * m_protection(office, cfg)
        * m_history(office, cfg)
    )
    assert asset_lambda(office, cfg) == pytest.approx(expected)
    assert asset_lambda(office, cfg) > 0.0


# ===========================================================================
# Initiation-class sampling
# ===========================================================================


def test_sample_initiation_class_returns_valid_enum(config):
    rng = _rng()
    klass = sample_initiation_class("Office", config.initiation, rng)
    assert isinstance(klass, InitiationClass)


def test_unknown_type_falls_back_to_other_prior(config):
    rng = _rng()
    # A type with no prior row should still sample via the "Other" row.
    klass = sample_initiation_class("Spaceport", config.initiation, rng)
    assert isinstance(klass, InitiationClass)


# ===========================================================================
# Simulation
# ===========================================================================


def test_simulate_asset_initiation_shape(config, office):
    result = simulate_asset_initiation(office, config, _rng())
    assert result.asset_id == "ASSET-001"
    assert result.n_sim == config.run.n_sim
    assert len(result.draws) == config.run.n_sim
    assert 0 <= result.n_fires <= config.run.n_sim
    assert result.fire_probability == pytest.approx(
        result.n_fires / config.run.n_sim
    )
    # Every fire draw carries a class; every non-fire draw does not.
    for draw in result.draws:
        if draw.fire:
            assert draw.count >= 1
            assert draw.initiation_class is not None
        else:
            assert draw.count == 0
            assert draw.initiation_class is None
    assert sum(result.class_counts.values()) == result.n_fires


def test_simulation_is_reproducible(config, office):
    a = simulate_asset_initiation(office, config, _rng(42))
    b = simulate_asset_initiation(office, config, _rng(42))
    assert a.n_fires == b.n_fires
    assert [d.count for d in a.draws] == [d.count for d in b.draws]


def test_empirical_rate_tracks_lambda(config, office):
    # For small lambda, P(>=1 ignition) ~= 1 - exp(-lambda). Use many draws.
    run = FireRunConfig(n_sim=200_000)
    big = FireModelConfig(run=run, initiation=config.initiation,
                          progression=config.progression)
    result = simulate_asset_initiation(office, big, _rng(7))
    lam = result.lambda_effective
    expected_p = 1.0 - np.exp(-lam)
    assert result.fire_probability == pytest.approx(expected_p, abs=0.01)


def test_higher_risk_asset_has_higher_lambda(config, office):
    high_risk = AssetFireFeatures(
        asset_id="HR", commercial_type="MixedUse",
        occupancy_status="Vacant", property_condition="Very poor",
        automatic_detection_level="Not assessed",
        fire_damage_severity="Severe", years_since_last_fire=1.0,
    )
    assert asset_lambda(high_risk, config.initiation) > asset_lambda(
        office, config.initiation
    )


def test_simulate_portfolio_initiation(config, office):
    portfolio = [office, AssetFireFeatures(asset_id="ASSET-002",
                                           commercial_type="Hotel")]
    results = simulate_portfolio_initiation(portfolio, config, _rng())
    assert len(results) == 2
    assert [r.asset_id for r in results] == ["ASSET-001", "ASSET-002"]


# ---------------------------------------------------------------------------
# Guards that stop a mis-calibrated prior sampling silently
# ---------------------------------------------------------------------------

def test_a_recent_minor_fire_uses_its_own_multiplier(config):
    """Three history bands, not two.

    'Recent and severe' and 'old' were both covered; the middle band — a
    recent fire that was only minor — was not, so a mis-keyed lookup there
    would have gone unnoticed.
    """
    recent_minor = AssetFireFeatures(
        asset_id="ASSET-RM",
        commercial_type="Office",
        fire_damage_severity="Minor",
        years_since_last_fire=1,
    )
    expected = config.initiation.m_history.get("recent_minor", 1.0)
    assert m_history(recent_minor, config.initiation) == expected


def test_an_unknown_type_with_no_fallback_row_raises(config, monkeypatch):
    """Sampling must fail loudly when neither the type nor 'Other' has a prior.

    The alternative is a KeyError or an empty draw much further downstream,
    where the cause is no longer visible.
    """
    cfg = config.initiation
    monkeypatch.setattr(cfg, "initiation_class_priors_by_type", {}, raising=False)
    with pytest.raises(ValueError, match="No initiation-class prior"):
        sample_initiation_class("Spaceport", cfg, _rng())


def test_a_prior_summing_to_zero_raises(config, monkeypatch):
    """A calibration that zeroes every class is not a uniform draw.

    The renormalisation divides by the sum, so a zero row would otherwise
    produce NaN probabilities and an opaque failure inside the RNG.
    """
    cfg = config.initiation
    monkeypatch.setattr(
        cfg, "initiation_class_priors_by_type",
        {"Office": [0.0] * len(cfg.initiation_classes)}, raising=False)
    with pytest.raises(ValueError, match="must sum to a positive value"):
        sample_initiation_class("Office", cfg, _rng())

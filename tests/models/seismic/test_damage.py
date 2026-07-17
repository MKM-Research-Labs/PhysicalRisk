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

"""Tests for Model D — damage, loss and resilience credit (damage.py).

Covers: the lognormal fragility exceedance and damage-state assignment; the
loss draw (DS3 fixed total); the functionality-recovery index; the end-to-end
orchestrator's tally consistency and reproducibility; and the three primary
sensitivity directions in miniature — construction, intensity, resilience and
distance all move the seismic spread the right way.
"""

import numpy as np
import pytest

from config.seismic import load_seismic_config
from models.seismic.datastructures import AssetSeismicFeatures
from models.seismic.damage import (
    adjusted_medians,
    assign_damage_state,
    fragility_exceedance,
    functionality_index,
    sample_loss_ratio,
    simulate_asset_seismic,
    simulate_portfolio_seismic,
)
from models.seismic.occurrence import parse_fault_trace

# Lat-21.0 fault from lon 105 to 107 (~208 km), [lon, lat] on disk.
_FAULT = parse_fault_trace(
    [[105.0, 21.0], [105.5, 21.0], [106.0, 21.0], [106.5, 21.0], [107.0, 21.0]])

# Table 5 measure positions.
_B = ["GS01", "GS05", "GS07", "GS10", "GS11", "GS14"]
_A = _B + ["GS02", "GS08", "GS09", "GS15", "GS16"]
_AA = _A + ["GS03", "GS12", "GS13", "GS17", "GS18"]


@pytest.fixture
def config():
    return load_seismic_config()


def _asset(**overrides):
    base = dict(
        asset_id="SEIS-1",
        commercial_type="Office",
        construction_type="RC_PreCode",
        number_of_storeys=4,
        latitude=20.95,                 # ~5.5 km south of the fault
        longitude=106.0,
        soil_vs30_mps=450.0,            # site class B
        seismic_hazard_class="High",
        measures=frozenset(),
    )
    base.update(overrides)
    return AssetSeismicFeatures(**base)


def _rng(seed=20260608):
    return np.random.default_rng(seed)


# ===========================================================================
# Fragility primitives
# ===========================================================================


def test_exceedance_is_half_at_the_median():
    assert fragility_exceedance(0.22, 0.22, 0.60) == pytest.approx(0.5)


def test_exceedance_monotone_in_pga():
    ps = [fragility_exceedance(p, 0.22, 0.60) for p in (0.02, 0.1, 0.22, 0.5, 1.0)]
    assert ps == sorted(ps)
    assert fragility_exceedance(0.0, 0.22, 0.60) == 0.0


def test_adjusted_medians_apply_theta_mult(config):
    base = config.fragility.medians_by_construction["RC_PreCode"]
    medians, beta = adjusted_medians(
        "RC_PreCode", {"DS1": 1.0, "DS2": 1.0, "DS3": 1.40}, config.fragility)
    assert medians["DS3"] == pytest.approx(base["DS3"] * 1.40)
    assert beta == pytest.approx(base["beta"])


def test_unknown_construction_falls_back_to_default(config):
    medians, _ = adjusted_medians(
        "Adobe", {"DS1": 1.0, "DS2": 1.0, "DS3": 1.0}, config.fragility)
    default = config.fragility.medians_by_construction["Default"]
    assert medians["DS3"] == pytest.approx(default["DS3"])


def test_damage_state_assignment_extremes(config):
    medians, beta = adjusted_medians(
        "RC_PreCode", {"DS1": 1.0, "DS2": 1.0, "DS3": 1.0}, config.fragility)
    assert assign_damage_state(3.0, medians, beta, 0.001) == 3   # huge PGA
    assert assign_damage_state(0.001, medians, beta, 0.999) == 0  # tiny PGA


# ===========================================================================
# Loss & functionality
# ===========================================================================


def test_loss_ratio_ds3_is_fixed_total(config):
    assert sample_loss_ratio(3, config.fragility, _rng()) == 1.0


def test_loss_ratio_in_unit_interval(config):
    rng = _rng()
    draws = [sample_loss_ratio(2, config.fragility, rng) for _ in range(2000)]
    assert all(0.0 <= x <= 1.0 for x in draws)
    assert np.mean(draws) < 1.0


def test_functionality_index_ordered_by_damage(config):
    r_acc = 0.40
    q = [functionality_index(ds, r_acc, config.fragility) for ds in range(4)]
    assert q[0] == 1.0
    assert q[0] > q[1] > q[2] > q[3]


def test_faster_recovery_raises_functionality(config):
    slow = functionality_index(2, 0.25, config.fragility)
    fast = functionality_index(2, 1.00, config.fragility)
    assert fast > slow


# ===========================================================================
# Orchestrator — structural consistency & reproducibility
# ===========================================================================


def test_tally_consistency_and_spread_formula(config):
    result = simulate_asset_seismic(_asset(), config, _FAULT, _rng(), n_sim=20000)
    counts = result.damage_state_counts
    assert sum(counts.values()) == result.n_events
    assert result.seismic_spread_bps == pytest.approx(counts[3] / 20000 * 10_000.0)
    assert result.no_collapse_rate == pytest.approx(
        (counts[0] + counts[1] + counts[2]) / result.n_events)
    assert 0.0 <= result.mean_resilience_index <= 1.0
    assert result.pml_2475 >= result.pml_475


def test_is_reproducible_from_seed(config):
    r1 = simulate_asset_seismic(_asset(), config, _FAULT, _rng(), n_sim=10000)
    r2 = simulate_asset_seismic(_asset(), config, _FAULT, _rng(), n_sim=10000)
    assert r1.seismic_spread_bps == r2.seismic_spread_bps
    assert r1.damage_state_counts == r2.damage_state_counts
    assert r1.loss_frequency == r2.loss_frequency


def test_to_dict_is_json_friendly(config):
    d = simulate_asset_seismic(_asset(), config, _FAULT, _rng(), n_sim=5000).to_dict()
    assert d["seismic_spread_bps"] >= 0.0
    assert set(d["damage_state_counts"]) == {"0", "1", "2", "3"}
    assert "outcomes" not in d


# ===========================================================================
# The three primary sensitivity directions (miniature)
# ===========================================================================


def test_intensity_axis_higher_zone_higher_spread(config):
    low = simulate_asset_seismic(
        _asset(seismic_hazard_class="Low"), config, _FAULT, _rng(), n_sim=20000)
    high = simulate_asset_seismic(
        _asset(seismic_hazard_class="Extreme"), config, _FAULT, _rng(), n_sim=20000)
    assert high.seismic_spread_bps > low.seismic_spread_bps


def test_construction_axis_urm_worse_than_modern_rc(config):
    urm = simulate_asset_seismic(
        _asset(construction_type="Masonry_URM"), config, _FAULT, _rng(), n_sim=20000)
    modern = simulate_asset_seismic(
        _asset(construction_type="RC_Modern"), config, _FAULT, _rng(), n_sim=20000)
    assert urm.seismic_spread_bps > modern.seismic_spread_bps


def test_resilience_axis_aa_lower_spread_than_nr(config):
    nr = simulate_asset_seismic(
        _asset(measures=frozenset()), config, _FAULT, _rng(), n_sim=20000)
    aa = simulate_asset_seismic(
        _asset(measures=frozenset(_AA)), config, _FAULT, _rng(), n_sim=20000)
    assert aa.seismic_spread_bps < nr.seismic_spread_bps
    assert aa.no_collapse_rate >= nr.no_collapse_rate


def test_distance_axis_near_fault_higher_spread(config):
    near = simulate_asset_seismic(
        _asset(latitude=20.99, seismic_hazard_class="Extreme"),  # ~1 km
        config, _FAULT, _rng(), n_sim=20000)
    far = simulate_asset_seismic(
        _asset(latitude=20.40, seismic_hazard_class="Extreme"),  # ~67 km
        config, _FAULT, _rng(), n_sim=20000)
    assert near.seismic_spread_bps > far.seismic_spread_bps


def test_portfolio_runs_every_asset_reproducibly(config):
    feats = [_asset(asset_id="A"), _asset(asset_id="B", construction_type="Masonry_URM")]
    r1 = simulate_portfolio_seismic(feats, config, _FAULT, _rng(), n_sim=5000)
    r2 = simulate_portfolio_seismic(feats, config, _FAULT, _rng(), n_sim=5000)
    assert [r.asset_id for r in r1] == ["A", "B"]
    assert [r.seismic_spread_bps for r in r1] == [r.seismic_spread_bps for r in r2]

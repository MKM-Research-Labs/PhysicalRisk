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

"""Tests for Model C — seismic response effectiveness (responseeffectiveness.py).

Covers: per-damage-state fragility median multipliers (incl. the GS16-18
governance cap); the BRI geoseismic rating derivation at the Section 7.4 Table 5
positions; recovery acceleration ordering; the GS15 post-earthquake-fire
reduction; and the directional resilience requirement that an AA asset is more
resilient (higher theta_mult) than an NR asset.
"""

import pytest

from config.seismic import load_seismic_config
from models.seismic.datastructures import AssetSeismicFeatures
from models.seismic.responseeffectiveness import (
    DAMAGE_STATE_KEYS,
    derive_response_profile,
    fragility_multipliers,
    geoseismic_rating,
    pef_probabilities,
    recovery_acceleration,
)

# Section 7.4 Table 5 BRI positions (cumulative).
_B = ["GS01", "GS05", "GS07", "GS10", "GS11", "GS14"]
_A = _B + ["GS02", "GS08", "GS09", "GS15", "GS16"]
_AA = _A + ["GS03", "GS12", "GS13", "GS17", "GS18"]


@pytest.fixture
def config():
    return load_seismic_config()


@pytest.fixture
def resp(config):
    return config.response


def _asset(measures=(), **overrides):
    base = dict(
        asset_id="SEIS-1",
        commercial_type="Office",
        construction_type="RC_PreCode",
        measures=frozenset(measures),
    )
    base.update(overrides)
    return AssetSeismicFeatures(**base)


# ===========================================================================
# Fragility median multipliers
# ===========================================================================


def test_no_measures_gives_unit_multipliers(resp):
    mult = fragility_multipliers(_asset(), resp)
    assert mult == {"DS1": 1.0, "DS2": 1.0, "DS3": 1.0}


def test_base_isolation_shifts_all_damage_states(resp):
    # GS12 applies to all DS at +0.40.
    mult = fragility_multipliers(_asset(["GS12"]), resp)
    assert mult == {ds: pytest.approx(1.40) for ds in DAMAGE_STATE_KEYS}


def test_lateral_force_targets_ds2_ds3_only(resp):
    # GS08 (+0.20) applies to DS2/DS3 but not DS1.
    mult = fragility_multipliers(_asset(["GS08"]), resp)
    assert mult["DS1"] == 1.0
    assert mult["DS2"] == pytest.approx(1.20)
    assert mult["DS3"] == pytest.approx(1.20)


def test_governance_block_is_capped(resp):
    # GS16+GS17+GS18 = 3 x 0.03 = 0.09, capped at 0.05 -> x1.05 on all DS.
    mult = fragility_multipliers(_asset(["GS16", "GS17", "GS18"]), resp)
    assert mult["DS1"] == pytest.approx(1.05)
    # A single governance measure is below the cap.
    one = fragility_multipliers(_asset(["GS16"]), resp)
    assert one["DS1"] == pytest.approx(1.03)


def test_measures_compound_multiplicatively(resp):
    # GS08 (DS3 +0.20) and GS14 (DS3 +0.15) compound on DS3.
    mult = fragility_multipliers(_asset(["GS08", "GS14"]), resp)
    assert mult["DS3"] == pytest.approx(1.20 * 1.15)


# ===========================================================================
# Geoseismic rating
# ===========================================================================


def test_rating_at_table5_positions(resp):
    assert geoseismic_rating(_asset(), resp) == "NR"
    assert geoseismic_rating(_asset(_B), resp) == "B"
    assert geoseismic_rating(_asset(_A), resp) == "A"
    assert geoseismic_rating(_asset(_AA), resp) == "AA"


def test_single_measure_does_not_reach_b(resp):
    # One AA-tier measure is not a broad enough stack to earn a recovery rating.
    assert geoseismic_rating(_asset(["GS12"]), resp) == "NR"


# ===========================================================================
# Recovery acceleration
# ===========================================================================


def test_recovery_acceleration_increases_with_rating(resp):
    nr = recovery_acceleration(_asset(), resp)
    b = recovery_acceleration(_asset(_B), resp)
    a = recovery_acceleration(_asset(_A), resp)
    aa = recovery_acceleration(_asset(_AA), resp)
    assert nr < b < a < aa
    assert nr == pytest.approx(0.25)
    # AA position carries GS18 -> r_acc gets the 1.30 EGGAR uplift.
    assert aa == pytest.approx(1.00 * 1.30)


# ===========================================================================
# Post-earthquake fire
# ===========================================================================


def test_pef_probabilities_and_gs15_reduction(resp):
    base = pef_probabilities(_asset(), resp)
    assert base["DS0"] == 0.0 and base["DS1"] == 0.0
    assert base["DS2"] == pytest.approx(0.08)
    assert base["DS3"] == pytest.approx(0.18)
    # GS15 cuts PEF by 80%.
    shielded = pef_probabilities(_asset(["GS15"]), resp)
    assert shielded["DS2"] == pytest.approx(0.08 * 0.20)
    assert shielded["DS3"] == pytest.approx(0.18 * 0.20)


# ===========================================================================
# Profile assembly & directional resilience
# ===========================================================================


def test_derive_profile_assembles_all_fields(config):
    profile = derive_response_profile(_asset(_A), config)
    assert profile.asset_id == "SEIS-1"
    assert profile.rating == "A"
    assert profile.gs02_present is True       # GS02 is in the A stack
    assert set(profile.theta_mult) == set(DAMAGE_STATE_KEYS)
    assert set(profile.p_pef_by_ds) == {"DS0", "DS1", "DS2", "DS3"}


def test_aa_asset_is_more_resilient_than_nr(config):
    nr = derive_response_profile(_asset(), config)
    aa = derive_response_profile(_asset(_AA), config)
    # Higher DS3 median multiplier -> rarer collapse: the resilience credit.
    assert aa.theta_mult["DS3"] > nr.theta_mult["DS3"]
    assert aa.r_acc > nr.r_acc

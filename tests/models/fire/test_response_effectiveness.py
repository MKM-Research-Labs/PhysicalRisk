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

"""Tests for Model C — response effectiveness (response_effectiveness.py).

Verifies the deterministic mapping from an asset's CDM resilience levels to the
ResponseProfile the intensity track and chain march consume:
- level helpers map the RESILIENCE_LEVELS vocabulary to indices/fractions
- the height penalty interpolates with storeys and is >= 1
- passive/response aggregates sit in [0,1] and rise with better levels
- detection is faster, suppression bites sooner, and controllability is higher
  for a well-protected asset than for a bare one
- a strong asset selects the strong i_crit / well-compartmented growth branch
"""

import pytest

from config.fire import load_fire_config
from models.fire.data_structures import AssetFireFeatures
from models.fire.response_effectiveness import (
    combustibility,
    controllability_score,
    derive_response_profile,
    height_penalty,
    intensity_ceiling,
    level_fraction,
    level_index,
    passive_effectiveness,
    response_effectiveness,
)
from port.cdm.asset.resilience import RESILIENCE_LEVELS


@pytest.fixture
def config():
    return load_fire_config()


@pytest.fixture
def prog(config):
    return config.progression


def _strong(**overrides):
    base = dict(
        asset_id="STRONG",
        commercial_type="Office",
        automatic_detection_level="Verified",
        suppression_systems_level="Verified",
        emergency_procedures_level="Verified",
        structural_fire_resistance_level="Verified",
        compartments_level="Verified",
        fire_stopping_level="Verified",
        external_materials_level="Verified",
        access_route_level="Verified",
        business_continuity_level="Verified",
        number_of_storeys=2,
    )
    base.update(overrides)
    return AssetFireFeatures(**base)


def _weak(**overrides):
    base = dict(
        asset_id="WEAK",
        commercial_type="Office",
        number_of_storeys=20,
    )
    base.update(overrides)
    return AssetFireFeatures(**base)


# ===========================================================================
# Level helpers
# ===========================================================================


def test_level_index_known_and_unknown():
    assert level_index(RESILIENCE_LEVELS[0]) == 0
    assert level_index(RESILIENCE_LEVELS[-1]) == len(RESILIENCE_LEVELS) - 1
    # Unknown / missing levels fall back to the worst index (0).
    assert level_index(None) == 0
    assert level_index("Nonsense") == 0


def test_level_fraction_spans_zero_to_one():
    assert level_fraction(RESILIENCE_LEVELS[0]) == pytest.approx(0.0)
    assert level_fraction(RESILIENCE_LEVELS[-1]) == pytest.approx(1.0)
    assert 0.0 <= level_fraction("Meets minimum") <= 1.0


# ===========================================================================
# Height penalty
# ===========================================================================


def test_height_penalty_endpoints(prog):
    block = prog.upper_floor_penalty_per_storey
    low, high = block["range"]
    max_storeys = block["max_storeys"]
    assert height_penalty(_weak(number_of_storeys=1), prog) == pytest.approx(low)
    assert height_penalty(
        _weak(number_of_storeys=max_storeys), prog
    ) == pytest.approx(high)


def test_height_penalty_monotonic_and_at_least_one(prog):
    p1 = height_penalty(_weak(number_of_storeys=1), prog)
    p10 = height_penalty(_weak(number_of_storeys=10), prog)
    p20 = height_penalty(_weak(number_of_storeys=20), prog)
    assert 1.0 <= p1 < p10 < p20


def test_height_penalty_missing_storeys_treated_as_single(prog):
    block = prog.upper_floor_penalty_per_storey
    low, _ = block["range"]
    assert height_penalty(_weak(number_of_storeys=None), prog) == pytest.approx(low)


# ===========================================================================
# Aggregate effectiveness
# ===========================================================================


def test_effectiveness_in_unit_interval_and_ordered(prog):
    strong_p = passive_effectiveness(_strong(), prog)
    weak_p = passive_effectiveness(_weak(), prog)
    strong_r = response_effectiveness(_strong(), prog)
    weak_r = response_effectiveness(_weak(), prog)
    for v in (strong_p, weak_p, strong_r, weak_r):
        assert 0.0 <= v <= 1.0
    assert strong_p > weak_p
    assert strong_r > weak_r


def test_controllability_score_weighted_and_bounded(prog):
    # All components at 1 -> score 1; all at 0 -> score 0.
    assert controllability_score(1.0, 1.0, 1.0, prog) == pytest.approx(1.0)
    assert controllability_score(0.0, 0.0, 0.0, prog) == pytest.approx(0.0)
    mid = controllability_score(0.5, 0.5, 0.5, prog)
    assert 0.0 < mid < 1.0


# ===========================================================================
# Profile assembly
# ===========================================================================


def test_strong_profile_beats_weak_profile(prog):
    strong = derive_response_profile(_strong(), prog)
    weak = derive_response_profile(_weak(), prog)

    # Faster detection and sooner suppression for the strong asset.
    assert strong.detection_steps < weak.detection_steps
    assert strong.suppression_active_step < weak.suppression_active_step
    # Stronger suppression damps growth more once active (lower multiplier).
    assert strong.suppression_growth_multiplier < weak.suppression_growth_multiplier
    # Higher controllability => selects the AA_controllable branch.
    assert strong.controllability > weak.controllability


def test_strong_asset_uses_strong_i_crit_and_well_compartmented(prog):
    strong = derive_response_profile(_strong(), prog)
    # i_crit is graded by suppression level; a Verified asset gets the top value.
    assert strong.i_crit == pytest.approx(prog.i_crit_by_level["Verified"])
    assert strong.growth_per_step == pytest.approx(
        prog.growth_per_step_intensity["well_compartmented"]
    )


def test_weak_asset_uses_weak_i_crit_and_poorly_compartmented(prog):
    weak = derive_response_profile(_weak(), prog)
    # The weak asset has no assessed suppression -> the worst (lowest) i_crit.
    assert weak.i_crit == pytest.approx(prog.i_crit_by_level["Not assessed"])
    assert weak.growth_per_step == pytest.approx(
        prog.growth_per_step_intensity["poorly_compartmented"]
    )


def test_i_crit_grades_monotonically_with_suppression_level(prog):
    # Every suppression level shifts the point-of-no-return threshold, so the
    # controllability race is graded rather than a binary strong/weak step.
    levels = ["Not assessed", "Partial", "Meets minimum", "Enhanced", "Verified"]
    crits = [
        derive_response_profile(_strong(suppression_systems_level=lv), prog).i_crit
        for lv in levels
    ]
    assert crits == sorted(crits)
    assert crits[0] < crits[-1]


def test_better_suppression_bites_sooner(prog):
    # A better suppression system engages sooner (smaller bite time), within the
    # fire-service reach so the height/reach path does not dominate.
    enhanced = derive_response_profile(
        _strong(number_of_storeys=2, suppression_systems_level="Enhanced"), prog)
    partial = derive_response_profile(
        _strong(number_of_storeys=2, suppression_systems_level="Partial"), prog)
    assert enhanced.suppression_bite_steps < partial.suppression_bite_steps


# ===========================================================================
# Fire-service reach (fire-truck height) x internal sprinklers
# ===========================================================================


def _office(storeys, suppression=None):
    return AssetFireFeatures(
        asset_id="O", commercial_type="Office",
        number_of_storeys=storeys, suppression_systems_level=suppression,
    )


def test_lowrise_unsprinklered_suppression_engages_within_reach(prog):
    # At/below the fire-truck reach the external service engages even with no
    # internal sprinklers, so suppression bites within the step budget.
    reach = prog.fire_service_reach
    asset = _office(reach["reach_storeys"], suppression=None)
    profile = derive_response_profile(asset, prog)
    assert profile.suppression_active_step < prog.fire_service_reach["no_reach_bite_steps"]


def test_tall_unsprinklered_suppression_never_engages(prog):
    # Above the reach with no internal sprinklers the suppression flag never
    # bites — the bite time is the configured no-reach (beyond-budget) value.
    reach = prog.fire_service_reach
    asset = _office(reach["reach_storeys"] + 1, suppression=None)
    profile = derive_response_profile(asset, prog)
    assert profile.suppression_bite_steps == pytest.approx(reach["no_reach_bite_steps"])


def test_tall_sprinklered_suppression_engages(prog):
    # Internal sprinklers restore suppression at any height — a tall building
    # with adequate sprinklers bites within the step budget.
    reach = prog.fire_service_reach
    asset = _office(reach["reach_storeys"] + 10, suppression="Verified")
    profile = derive_response_profile(asset, prog)
    assert profile.suppression_bite_steps < reach["no_reach_bite_steps"]


def test_tall_unsprinklered_asset_reaches_pnr(config, prog):
    # End-to-end: a tall, unsprinklered asset whose suppression never engages
    # must actually cross the point of no return.
    from models.fire.intensity_track import (
        advance_intensity,
        initial_intensity_track,
    )

    asset = _office(prog.fire_service_reach["reach_storeys"] + 1, suppression=None)
    profile = derive_response_profile(asset, prog)
    track = initial_intensity_track()
    for _ in range(config.run.max_steps):
        track = advance_intensity(track, profile, prog)
        if track.point_of_no_return:
            break
    assert track.point_of_no_return


def test_tall_sprinklered_asset_avoids_pnr(config, prog):
    # The same tall asset with adequate sprinklers suppresses and never crosses
    # the point of no return.
    from models.fire.intensity_track import (
        advance_intensity,
        initial_intensity_track,
    )

    asset = _office(prog.fire_service_reach["reach_storeys"] + 1, suppression="Verified")
    profile = derive_response_profile(asset, prog)
    track = initial_intensity_track()
    for _ in range(config.run.max_steps):
        track = advance_intensity(track, profile, prog)
    assert not track.point_of_no_return


# ===========================================================================
# Construction type — structural-frame combustibility
# ===========================================================================


def test_combustibility_maps_construction_type(prog):
    # Non-combustible frames sit near 0; timber at 1; the gap is monotone.
    c_concrete = combustibility(_weak(construction_type="Reinforced concrete"), prog)
    c_steel = combustibility(_weak(construction_type="Steel frame"), prog)
    c_timber = combustibility(_weak(construction_type="Timber frame"), prog)
    assert c_concrete == pytest.approx(0.0)
    assert c_concrete < c_steel < c_timber
    assert c_timber == pytest.approx(1.0)


def test_combustibility_unknown_uses_default(prog):
    # A missing / unrecognised construction type falls back to the configured
    # default (kept on the combustible side so an unassessed building is cautious).
    default = prog.construction["default_combustibility"]
    assert combustibility(_weak(construction_type=None), prog) == pytest.approx(default)
    assert combustibility(
        _weak(construction_type="Adobe"), prog) == pytest.approx(default)


def test_intensity_ceiling_noncombustible_below_worst_i_crit(prog):
    # Every non-combustible frame shares the low plateau, which must sit below
    # even the worst i_crit so the intensity race can never cross it.
    worst_i_crit = min(prog.i_crit_by_level.values())
    plateau = prog.construction["intensity_ceiling"][0]
    for ctype in ("Reinforced concrete", "Steel frame", "Brick and block"):
        c = combustibility(_weak(construction_type=ctype), prog)
        assert intensity_ceiling(c, prog) == pytest.approx(plateau)
    assert plateau < worst_i_crit


def test_intensity_ceiling_grades_above_threshold(prog):
    # Above the combustible threshold the ceiling grades up to the configured top.
    lo, hi = prog.construction["intensity_ceiling"]
    mixed = intensity_ceiling(
        combustibility(_weak(construction_type="Mixed construction"), prog), prog)
    timber = intensity_ceiling(
        combustibility(_weak(construction_type="Timber frame"), prog), prog)
    assert lo < mixed < timber
    assert timber == pytest.approx(hi)


def test_combustibility_scales_growth_rate(prog):
    # The timing leg: a combustible frame catches and grows faster than a
    # non-combustible one (same compartmentation), giving suppression less time.
    concrete = derive_response_profile(
        _weak(construction_type="Reinforced concrete"), prog)
    timber = derive_response_profile(_weak(construction_type="Timber frame"), prog)
    assert timber.growth_per_step > concrete.growth_per_step


def test_unknown_construction_growth_is_neutral(prog):
    # An unknown construction type (default combustibility at the scale midpoint)
    # leaves the growth rate at the un-scaled compartmentation value, preserving
    # the pre-construction behaviour for records without a construction type.
    weak = derive_response_profile(_weak(construction_type=None), prog)
    poorly = prog.growth_per_step_intensity["poorly_compartmented"]
    assert weak.growth_per_step == pytest.approx(poorly)


def test_profile_carries_construction_fields(prog):
    concrete = derive_response_profile(
        _weak(construction_type="Reinforced concrete"), prog)
    timber = derive_response_profile(_weak(construction_type="Timber frame"), prog)
    # Non-combustible: low ceiling, not flagged combustible.
    assert not concrete.structure_combustible
    assert concrete.intensity_ceiling < timber.intensity_ceiling
    # Combustible: flagged, high ceiling.
    assert timber.structure_combustible
    assert timber.combustibility > concrete.combustibility

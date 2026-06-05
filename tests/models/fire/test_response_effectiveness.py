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
    controllability_score,
    derive_response_profile,
    height_penalty,
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
    assert strong.i_crit == pytest.approx(prog.i_crit_by_suppression["strong_suppression"])
    assert strong.growth_per_step == pytest.approx(
        prog.growth_per_step_intensity["well_compartmented"]
    )


def test_weak_asset_uses_weak_i_crit_and_poorly_compartmented(prog):
    weak = derive_response_profile(_weak(), prog)
    assert weak.i_crit == pytest.approx(prog.i_crit_by_suppression["weak_suppression"])
    assert weak.growth_per_step == pytest.approx(
        prog.growth_per_step_intensity["poorly_compartmented"]
    )

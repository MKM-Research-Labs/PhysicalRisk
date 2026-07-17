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

"""Tests for Model B — intensity track (intensity_track.py).

Verifies the deterministic 15-minute intensity dynamics:
- the track starts at zero intensity with nothing active
- per-step growth is damped by passive effectiveness and cut by suppression
- suppression activates once the step reaches suppression_active_step
- the point of no return latches when intensity crosses i_crit *before*
  suppression bites, and once latched stays latched
- a strong asset suppresses before i_crit and never reaches the PNR; a weak
  asset loses the controllability race and does reach it
"""

import pytest

from config.fire import load_fire_config
from models.fire.data_structures import AssetFireFeatures, ResponseProfile
from models.fire.intensity_track import (
    advance_intensity,
    effective_growth,
    initial_intensity_track,
)
from models.fire.response_effectiveness import derive_response_profile


@pytest.fixture
def config():
    return load_fire_config()


@pytest.fixture
def prog(config):
    return config.progression


def _profile(prog, **overrides):
    base = dict(
        detection_steps=2.0,
        suppression_bite_steps=3.0,
        growth_per_step=4.0,
        suppression_growth_multiplier=0.5,
        i_crit=12.0,
        passive_effectiveness=0.0,
        response_effectiveness=0.0,
        height_penalty=1.0,
        controllability=0.5,
    )
    base.update(overrides)
    return ResponseProfile(**base)


def _strong():
    return AssetFireFeatures(
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


def _weak():
    return AssetFireFeatures(
        asset_id="WEAK", commercial_type="Office", number_of_storeys=20,
    )


# ===========================================================================
# Initial state
# ===========================================================================


def test_initial_track_is_empty():
    track = initial_intensity_track()
    assert track.step == 0
    assert track.intensity == pytest.approx(0.0)
    assert not track.suppression_active
    assert not track.point_of_no_return
    assert track.point_of_no_return_step is None


# ===========================================================================
# Growth
# ===========================================================================


def test_passive_effectiveness_damps_growth(prog):
    bare = _profile(prog, passive_effectiveness=0.0)
    defended = _profile(prog, passive_effectiveness=0.9)
    g_bare = effective_growth(bare, prog, suppression_active=False)
    g_def = effective_growth(defended, prog, suppression_active=False)
    assert g_bare > g_def
    assert g_def >= 0.0


def test_suppression_cuts_growth(prog):
    profile = _profile(prog, suppression_growth_multiplier=0.5)
    g_pre = effective_growth(profile, prog, suppression_active=False)
    g_post = effective_growth(profile, prog, suppression_active=True)
    assert g_post == pytest.approx(g_pre * 0.5)


# ===========================================================================
# Stepping & suppression activation
# ===========================================================================


def test_suppression_activates_at_active_step(prog):
    # active_step = detection(2) + bite(3) = 5; suppression bites from step 5.
    profile = _profile(prog, detection_steps=2.0, suppression_bite_steps=3.0)
    track = initial_intensity_track()
    seen_active = []
    for _ in range(6):
        track = advance_intensity(track, profile, prog)
        seen_active.append((track.step, track.suppression_active))
    assert (4, False) in seen_active
    assert (5, True) in seen_active


# ===========================================================================
# Point of no return
# ===========================================================================


def test_pnr_latches_when_intensity_beats_suppression(prog):
    # Fast growth, low i_crit, late suppression => PNR fires pre-suppression.
    profile = _profile(
        prog, growth_per_step=4.0, passive_effectiveness=0.0,
        i_crit=10.0, detection_steps=2.0, suppression_bite_steps=4.0,
    )
    track = initial_intensity_track()
    for _ in range(10):
        track = advance_intensity(track, profile, prog)
        if track.point_of_no_return:
            break
    assert track.point_of_no_return
    assert track.point_of_no_return_step is not None
    # PNR must have latched before suppression became active.
    assert track.point_of_no_return_step < profile.suppression_active_step


def test_pnr_does_not_fire_when_suppression_wins(prog):
    # High i_crit, early suppression => intensity never crosses pre-suppression.
    profile = _profile(
        prog, growth_per_step=1.5, passive_effectiveness=0.9,
        i_crit=75.0, detection_steps=1.0, suppression_bite_steps=2.0,
    )
    track = initial_intensity_track()
    for _ in range(50):
        track = advance_intensity(track, profile, prog)
    assert not track.point_of_no_return
    assert track.point_of_no_return_step is None


def test_pnr_latch_is_sticky(prog):
    profile = _profile(
        prog, growth_per_step=4.0, passive_effectiveness=0.0,
        i_crit=10.0, detection_steps=2.0, suppression_bite_steps=4.0,
    )
    track = initial_intensity_track()
    for _ in range(10):
        track = advance_intensity(track, profile, prog)
    latched_step = track.point_of_no_return_step
    assert track.point_of_no_return
    # Marching further must not clear or move the latch.
    for _ in range(10):
        track = advance_intensity(track, profile, prog)
        assert track.point_of_no_return
        assert track.point_of_no_return_step == latched_step


# ===========================================================================
# Seed-level reachability (regression: PNR must not be dead code)
# ===========================================================================


def test_weak_asset_reaches_pnr_under_seed_config(prog):
    profile = derive_response_profile(_weak(), prog)
    track = initial_intensity_track()
    for _ in range(int(profile.suppression_active_step) + 1):
        track = advance_intensity(track, profile, prog)
        if track.point_of_no_return:
            break
    assert track.point_of_no_return, (
        "A poorly-compartmented, weakly-suppressed asset must be able to lose "
        "the controllability race under the seed config."
    )


def test_strong_asset_never_reaches_pnr_under_seed_config(prog):
    profile = derive_response_profile(_strong(), prog)
    track = initial_intensity_track()
    for _ in range(200):
        track = advance_intensity(track, profile, prog)
    assert not track.point_of_no_return


# ===========================================================================
# Construction material — the building-material conflagration sensitivity
# ===========================================================================


def _tall_unsprinklered(construction_type):
    # Above the fire-service reach with no internal sprinklers: suppression can
    # never engage, so material is the only thing that can prevent a whole-
    # building conflagration.
    return AssetFireFeatures(
        asset_id="C", commercial_type="Office", number_of_storeys=20,
        construction_type=construction_type,
    )


def test_noncombustible_frame_avoids_pnr_when_suppression_unreachable(prog):
    # A reinforced-concrete tall, unsprinklered building is contained by its own
    # structure: the intensity ceiling sits below i_crit and the unreachable
    # auto-latch does not fire, so it never reaches the point of no return.
    profile = derive_response_profile(
        _tall_unsprinklered("Reinforced concrete"), prog)
    assert not profile.suppression_reachable
    assert not profile.structure_combustible
    track = initial_intensity_track()
    for _ in range(200):
        track = advance_intensity(track, profile, prog)
    assert not track.point_of_no_return
    # And the intensity is held at the non-combustible plateau.
    assert track.intensity == pytest.approx(profile.intensity_ceiling)


def test_combustible_frame_reaches_pnr_when_suppression_unreachable(prog):
    # The same tall, unsprinklered building in timber runs to the point of no
    # return — material, not height, now decides the conflagration outcome.
    profile = derive_response_profile(_tall_unsprinklered("Timber frame"), prog)
    assert not profile.suppression_reachable
    assert profile.structure_combustible
    track = initial_intensity_track()
    for _ in range(200):
        track = advance_intensity(track, profile, prog)
        if track.point_of_no_return:
            break
    assert track.point_of_no_return


def test_intensity_capped_at_ceiling(prog):
    # The latent intensity never exceeds the structure's combustibility ceiling.
    profile = derive_response_profile(_tall_unsprinklered("Steel frame"), prog)
    track = initial_intensity_track()
    for _ in range(200):
        track = advance_intensity(track, profile, prog)
        assert track.intensity <= profile.intensity_ceiling + 1e-9

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

"""Tests for the instant single-asset PRS re-depth shortcut (recompute.py).

Covers the threshold-from-data derivation, the re-thresholded severe count, the
per-mode floor-shift mapping (floor vs BRI vs unsupported field), and the
``recompute_decomposition`` driver including every fall-back-to-oracle branch
(unsupported field, zero storms, missing timeseries file, compound events).
"""


def _ts(events, **extra):
    return {"flood_events": events, **extra}


# --- _threshold -------------------------------------------------------------
def test_threshold_from_first_flooded_event(recompute_mod):
    # threshold = attenuated_wse_m - flood_depth_m on the first flooded event
    ts = _ts([{"flood_depth_m": 0, "attenuated_wse_m": 5.0},
              {"flood_depth_m": 1.5, "attenuated_wse_m": 6.0}])
    assert recompute_mod._threshold(ts) == 4.5


def test_threshold_falls_back_to_geometry_when_dry(recompute_mod):
    ts = _ts([{"flood_depth_m": 0, "attenuated_wse_m": 5.0}],
             elevation_m=3.0, floor_level_m=0.5)
    assert recompute_mod._threshold(ts) == 3.5


# --- severe_count -----------------------------------------------------------
def test_severe_count_requires_depth_and_severe(recompute_mod):
    # threshold derives to 4.0 (5.0 wse - 1.0 depth on the flooded seed event).
    events = [
        {"attenuated_wse_m": 5.0, "flood_depth_m": 1.0, "exceeded_severe": True},
        {"attenuated_wse_m": 4.5, "flood_depth_m": 0.5, "exceeded_severe": False},
        {"attenuated_wse_m": 3.0, "flood_depth_m": 0.0, "exceeded_severe": True},
    ]
    ts = _ts(events)
    # delta 0: event0 floods+severe (count), event1 floods but not severe,
    # event2 severe but dry -> count == 1
    assert recompute_mod.severe_count(ts, 0.0) == 1


def test_severe_count_raising_floor_drops_events(recompute_mod):
    events = [{"attenuated_wse_m": 5.0, "flood_depth_m": 1.0,
               "exceeded_severe": True}]
    ts = _ts(events)
    assert recompute_mod.severe_count(ts, 0.0) == 1
    # raise the floor by 2 m -> 5.0 - (4.0 + 2.0) = -1 -> dry -> 0
    assert recompute_mod.severe_count(ts, 2.0) == 0


# --- mode_deltas ------------------------------------------------------------
def test_mode_deltas_none_when_value_missing(recompute_mod):
    assert recompute_mod.mode_deltas("X.FloorLevelMeters", None, 1.0) is None
    assert recompute_mod.mode_deltas("X.FloorLevelMeters", 1.0, None) is None


def test_mode_deltas_floor_applies_to_every_mode(recompute_mod):
    d = recompute_mod.mode_deltas(
        "PropertyHeader.Construction.FloorLevelMeters", 0.5, 1.5)
    assert d == {m: 1.0 for m in recompute_mod.MODES}


def test_mode_deltas_bri_only_moves_bri(recompute_mod):
    d = recompute_mod.mode_deltas("PropertyHeader.RiskAssessment.BRIFloodScore",
                                  0.0, 1.0)
    assert set(d) == {"bri"} and d["bri"] >= 0


def test_mode_deltas_unsupported_field_is_none(recompute_mod):
    # ground-level / non-floor edits cannot be done by the shortcut
    assert recompute_mod.mode_deltas(
        "PropertyHeader.RiskAssessment.GroundLevelMeters", 0.0, 1.0) is None
    # a BRIAdjusted floor field is explicitly excluded
    assert recompute_mod.mode_deltas(
        "X.BRIAdjustedFloorLevelMeters", 0.0, 1.0) is None


# --- recompute_decomposition (reads per-mode timeseries via the database seam) ---
def test_recompute_decomposition_unsupported_field_returns_none(recompute_mod):
    out = recompute_mod.recompute_decomposition(
        "P1", "X.GroundLevelMeters", 0.0, 1.0,
        asset="property", catchment="thames", before_decomp={}, num_storms=100)
    assert out is None


def test_recompute_decomposition_zero_storms_returns_none(recompute_mod):
    out = recompute_mod.recompute_decomposition(
        "P1", "X.FloorLevelMeters", 0.0, 1.0,
        asset="property", catchment="thames", before_decomp={}, num_storms=0)
    assert out is None


def test_recompute_decomposition_compound_falls_back(recompute_mod, seam):
    seam.save_property_timeseries("thames", "P1", _ts(
        [{"attenuated_wse_m": 5.0, "flood_depth_m": 1.0,
          "exceeded_severe": True, "compound": True}]), mode="flood")
    out = recompute_mod.recompute_decomposition(
        "P1", "X.FloorLevelMeters", 0.0, 1.0,
        asset="property", catchment="thames",
        before_decomp={"gauge_spread_bps": 5.0}, num_storms=100)
    assert out is None


def test_recompute_decomposition_missing_ts_is_skipped(recompute_mod, seam):
    # No timeseries in the seam -> every mode skipped -> seeds returned unchanged.
    before = {"gauge_spread_bps": 7.0, "property_spread_bps": 50.0}
    out = recompute_mod.recompute_decomposition(
        "P1", "X.FloorLevelMeters", 0.0, 1.0,
        asset="property", catchment="thames", before_decomp=before, num_storms=100)
    assert out == before and out is not before  # copied, not mutated


def test_recompute_decomposition_recomputes_present_modes(recompute_mod, seam):
    # property/flood mode has one severe-flooding event; raising the floor by 10 m
    # makes it dry -> 0 severe -> 0 bps.
    events = [{"attenuated_wse_m": 5.0, "flood_depth_m": 1.0, "exceeded_severe": True}]
    seam.save_property_timeseries("thames", "P1", _ts(events), mode="flood")
    out = recompute_mod.recompute_decomposition(
        "P1", "X.FloorLevelMeters", 0.0, 10.0,
        asset="property", catchment="thames",
        before_decomp={"gauge_spread_bps": 5.0, "property_spread_bps": 100.0},
        num_storms=100)
    assert out["property_spread_bps"] == 0.0
    assert out["gauge_spread_bps"] == 5.0  # untouched stage preserved


def test_recompute_decomposition_commercial(recompute_mod, seam):
    events = [{"attenuated_wse_m": 5.0, "flood_depth_m": 1.0, "exceeded_severe": True}]
    seam.save_commercial_timeseries("thames", "C1", _ts(events), mode="flood")
    out = recompute_mod.recompute_decomposition(
        "C1", "X.FloorLevelMeters", 0.0, 0.0,
        asset="commercial", catchment="thames", before_decomp={}, num_storms=200)
    # 1 severe / 200 storms * 10000 = 50.0 bps
    assert out["property_spread_bps"] == 50.0

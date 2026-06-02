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

"""Tests for the BRI-adjusted floor level model.

``bri_floor_uplift`` maps a BRIFloodScore to an additive floor-level credit
(metres), and ``bri_adjusted_floor_level`` adds that credit to the surveyed
floor level. A highly-resilient (AA) building floods at a higher water level,
suppressing PRS flood counts; a poor (NR) building gets no credit.
"""

import pytest

from config.damage import (
    BRI_FLOOR_UPLIFT_MAX_M,
    BRI_FLOOR_UPLIFT_SCORE_HI,
    BRI_FLOOR_UPLIFT_SCORE_LO,
)
from models.floodrisk.depth_damage import (
    bri_adjusted_floor_level,
    bri_floor_uplift,
    flood_rating_to_score,
)


class TestBriFloorUplift:

    def test_nr_band_gets_no_uplift(self):
        # At / below the low anchor (NR / B boundary) there is no credit.
        assert bri_floor_uplift(BRI_FLOOR_UPLIFT_SCORE_LO) == 0.0
        assert bri_floor_uplift(0.2) == 0.0
        assert bri_floor_uplift(0.0) == 0.0

    def test_aa_band_gets_full_uplift(self):
        # At / above the high anchor (AA) the full uplift is awarded.
        assert bri_floor_uplift(BRI_FLOOR_UPLIFT_SCORE_HI) == BRI_FLOOR_UPLIFT_MAX_M
        assert bri_floor_uplift(0.95) == BRI_FLOOR_UPLIFT_MAX_M
        assert bri_floor_uplift(1.0) == BRI_FLOOR_UPLIFT_MAX_M

    def test_aa_anchor_is_about_three_metres(self):
        # Spec anchor: an AA property earns ~3 m of effective floor.
        assert bri_floor_uplift(0.87) == pytest.approx(3.0)

    def test_midpoint_interpolates_linearly(self):
        mid = (BRI_FLOOR_UPLIFT_SCORE_LO + BRI_FLOOR_UPLIFT_SCORE_HI) / 2.0
        assert bri_floor_uplift(mid) == pytest.approx(BRI_FLOOR_UPLIFT_MAX_M / 2.0)

    def test_linear_in_between_anchors(self):
        lo, hi = BRI_FLOOR_UPLIFT_SCORE_LO, BRI_FLOOR_UPLIFT_SCORE_HI
        score = 0.62  # A / B boundary
        expected = (score - lo) / (hi - lo) * BRI_FLOOR_UPLIFT_MAX_M
        assert bri_floor_uplift(score) == pytest.approx(expected)

    def test_monotonically_increasing(self):
        scores = [0.0, 0.2, 0.38, 0.5, 0.62, 0.75, 0.87, 1.0]
        uplifts = [bri_floor_uplift(s) for s in scores]
        assert all(uplifts[i] <= uplifts[i + 1] for i in range(len(uplifts) - 1))

    def test_never_negative(self):
        for s in [-1.0, 0.0, 0.1, 0.38, 0.5, 0.87, 1.0, 2.0]:
            assert bri_floor_uplift(s) >= 0.0

    def test_clamps_out_of_range_scores(self):
        # Scores outside [0, 1] are clamped, not extrapolated.
        assert bri_floor_uplift(5.0) == BRI_FLOOR_UPLIFT_MAX_M
        assert bri_floor_uplift(-3.0) == 0.0

    def test_returns_float(self):
        assert isinstance(bri_floor_uplift(0.5), float)


class TestBriAdjustedFloorLevel:

    def test_adds_uplift_to_floor(self):
        # 0.3 m surveyed floor + full AA uplift.
        assert bri_adjusted_floor_level(0.3, 0.87) == pytest.approx(0.3 + 3.0)

    def test_nr_property_unchanged(self):
        # No credit for a poor BRI score: adjusted == surveyed.
        assert bri_adjusted_floor_level(0.5, 0.2) == pytest.approx(0.5)

    def test_always_at_least_surveyed_floor(self):
        for score in [0.0, 0.2, 0.38, 0.5, 0.87, 1.0]:
            assert bri_adjusted_floor_level(0.4, score) >= 0.4

    def test_monotone_in_score(self):
        floor = 0.5
        adj = [bri_adjusted_floor_level(floor, s) for s in [0.2, 0.5, 0.7, 0.9]]
        assert all(adj[i] <= adj[i + 1] for i in range(len(adj) - 1))


class TestFloodRatingToScore:
    """Letter-grade bridge for assets without a numeric BRIFloodScore."""

    def test_known_grades_map_to_band_midpoints(self):
        assert flood_rating_to_score("AA") == pytest.approx(0.935)
        assert flood_rating_to_score("A") == pytest.approx(0.745)
        assert flood_rating_to_score("B") == pytest.approx(0.500)
        assert flood_rating_to_score("NR") == pytest.approx(0.190)

    def test_plus_modifier_stripped(self):
        assert flood_rating_to_score("A+") == flood_rating_to_score("A")
        assert flood_rating_to_score("B+") == flood_rating_to_score("B")

    def test_grade_ordering_is_monotone(self):
        order = ["NR", "B", "A", "AA"]
        scores = [flood_rating_to_score(g) for g in order]
        assert all(scores[i] < scores[i + 1] for i in range(len(scores) - 1))

    def test_unmappable_returns_none(self):
        assert flood_rating_to_score(None) is None
        assert flood_rating_to_score("") is None
        assert flood_rating_to_score("N/A") is None
        assert flood_rating_to_score("ZZ") is None

    def test_bridges_into_uplift(self):
        # An AA-graded commercial asset (no numeric score) earns the full uplift.
        aa_score = flood_rating_to_score("AA")
        assert bri_floor_uplift(aa_score) == pytest.approx(3.0)
        # An NR-graded asset earns none.
        nr_score = flood_rating_to_score("NR")
        assert bri_floor_uplift(nr_score) == 0.0

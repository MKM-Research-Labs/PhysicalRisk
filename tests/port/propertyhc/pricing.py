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

"""Tests for event count PRS spread computation."""

import json

import pytest

from port.src.property.propertyhc import (
    PropertyHazardCurveGenerator,
)


class TestEventCountSpread:
    """Test the event count spread formula: spread = flood_count / num_storms * 10000."""

    def test_zero_floods_zero_spread(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        # All properties should have spread proportional to flood_count
        for prop_id, pc in data["property_hazard_curves"].items():
            flood_count = pc["flood_count"]
            spreads = pc["term_structure"]["severe"]["prs_spread_bps"]
            expected = round((flood_count / 100) * 10000, 2)  # num_storms=100
            assert spreads[0] == expected, (
                f"{prop_id}: expected {expected}, got {spreads[0]}")

    def test_spread_proportional_to_floods(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        curves = data["property_hazard_curves"]
        # PROP-001 has 5 floods, PROP-002 has 2, PROP-003 has 10
        spread1 = curves["PROP-001"]["term_structure"]["severe"]["prs_spread_bps"][0]
        spread2 = curves["PROP-002"]["term_structure"]["severe"]["prs_spread_bps"][0]
        spread3 = curves["PROP-003"]["term_structure"]["severe"]["prs_spread_bps"][0]

        assert spread3 > spread1 > spread2

    def test_spread_is_flat_term_structure(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        spreads = data["property_hazard_curves"]["PROP-001"]["term_structure"]["severe"]["prs_spread_bps"]
        # All tenors should have the same spread (storms are independent)
        assert all(s == spreads[0] for s in spreads)


class TestGetGaugeSevereCount:
    """Test _get_gauge_severe_count static method."""

    def test_returns_severe_event_count(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hc = {"severe_event_count": 7}
        assert gen._get_gauge_severe_count(gauge_hc) == 7

    def test_returns_zero_when_missing(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hc = {"annual_hazard_rate_severe": 0.005}
        assert gen._get_gauge_severe_count(gauge_hc) == 0

    def test_returns_zero_for_empty_dict(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        assert gen._get_gauge_severe_count({}) == 0

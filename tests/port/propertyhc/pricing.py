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

"""Tests for PRS spread computation and recovery rates."""

import json

import pytest

from port.src.property.propertyhc import (
    DEPTH_THRESHOLDS,
    PropertyHazardCurveGenerator,
)


class TestPRSSpreadComputation:
    """Test the analytical PRS spread calculation."""

    def test_zero_hazard_rate(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        spread = gen._compute_prs_spread(0.0, 5, None)
        assert spread == 0.0

    def test_positive_spread(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        spread = gen._compute_prs_spread(0.02, 5, None)
        assert spread > 0
        assert 50 < spread < 500

    def test_spread_increases_with_hazard(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        spread_low = gen._compute_prs_spread(0.01, 5, None)
        spread_high = gen._compute_prs_spread(0.05, 5, None)
        assert spread_high > spread_low

    def test_spread_values_at_different_tenors(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        spreads = [gen._compute_prs_spread(0.02, t, None) for t in [1, 5, 10, 30]]
        for s in spreads:
            assert s > 0


class TestRecoveryRates:
    """Test trigger-dependent recovery rates in PRS spread computation."""

    def test_recovery_reduces_spread(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        spread_no_recovery = gen._compute_prs_spread(0.03, 5, None, recovery=0.0)
        spread_with_recovery = gen._compute_prs_spread(0.03, 5, None, recovery=0.70)
        assert spread_with_recovery < spread_no_recovery

    def test_recovery_rates_by_trigger(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        ts = data["property_hazard_curves"]["PROP-001"]["term_structure"]
        for name in DEPTH_THRESHOLDS:
            spreads = ts[name]["prs_spread_bps"]
            assert len(spreads) > 0

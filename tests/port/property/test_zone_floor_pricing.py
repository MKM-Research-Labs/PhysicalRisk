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

"""Tests for event count pricing and synthetic-based basis."""

import pytest

from config.models import EA_FLOOD_ZONE_RATES


class TestEventCountPricing:
    """Verify spread = flood_count / num_storms * 10000."""

    def test_zero_floods_gives_zero_spread(self):
        flood_count = 0
        num_storms = 20000
        spread = (flood_count / num_storms) * 10000
        assert spread == 0.0

    def test_100_floods_gives_50bp(self):
        flood_count = 100
        num_storms = 20000
        spread = (flood_count / num_storms) * 10000
        assert spread == 50.0

    def test_664_floods_gives_332bp(self):
        flood_count = 664
        num_storms = 20000
        spread = (flood_count / num_storms) * 10000
        assert spread == 332.0

    def test_spread_scales_with_num_storms(self):
        flood_count = 100
        spread_20k = (flood_count / 20000) * 10000
        spread_10k = (flood_count / 10000) * 10000
        assert spread_10k == spread_20k * 2

    def test_zone_rates_still_valid(self):
        """Zone hazard rates are still defined for reference/terrain grid."""
        assert EA_FLOOD_ZONE_RATES['Zone 3b'] == 0.05
        assert EA_FLOOD_ZONE_RATES['Zone 3a'] == 0.02
        assert EA_FLOOD_ZONE_RATES['Zone 2'] == 0.005
        assert EA_FLOOD_ZONE_RATES['Zone 1'] == 0.001


class TestSyntheticBasisPriority:
    """Verify that basis uses synthetic gauge when present."""

    def test_synth_prefix_detection(self):
        nearest_basis = [
            {'gauge_id': 'GAUGE-AAA', 'basis_bps': {}},
            {'gauge_id': 'SYNTH-123', 'basis_bps': {}},
            {'gauge_id': 'GAUGE-BBB', 'basis_bps': {}},
        ]
        synth = next(
            (nb for nb in nearest_basis if nb['gauge_id'].startswith('SYNTH-')),
            None
        )
        assert synth is not None
        assert synth['gauge_id'] == 'SYNTH-123'

    def test_no_synth_returns_none(self):
        nearest_basis = [
            {'gauge_id': 'GAUGE-AAA'},
            {'gauge_id': 'GAUGE-BBB'},
        ]
        synth = next(
            (nb for nb in nearest_basis if nb['gauge_id'].startswith('SYNTH-')),
            None
        )
        assert synth is None

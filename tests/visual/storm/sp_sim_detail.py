# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Regression tests for sp_sim.py (Storm Simulation sub-module).

Snag 5 regression: scrubber range must cover the full storm simulation
window.  The window length is controlled by config.models.STORM_SIMULATION_HOURS
(currently 168).  The old code had a hardcoded scrubber.max = '59' (60 hours),
cutting off 108 hours of the simulation.

These tests derive expected values from config so that changing the window
length in config automatically updates the expected scrubber bounds.
"""

import pytest


@pytest.fixture(scope='module')
def sim_js():
    from visual.interactivity.storm import sp_sim
    return sp_sim.get_js()


# ---------------------------------------------------------------------------
# Scrubber range (Snag 5 regression)
# ---------------------------------------------------------------------------

class TestScrubberRange:
    """Storm sim scrubber must span the full STORM_SIMULATION_HOURS window."""

    def test_scrubber_max_from_config(self, sim_js):
        """scrubber.max must equal STORM_SIMULATION_HOURS - 1 (0-indexed).

        The value is driven by config.models.STORM_SIMULATION_HOURS so that
        changing the simulation window in one place updates every consumer.
        Regression guard: old hardcoded value was '59' (60 hours only).
        """
        from config.models import STORM_SIMULATION_HOURS
        expected = str(STORM_SIMULATION_HOURS - 1)
        assert f"scrubber.max = '{expected}'" in sim_js, (
            f"scrubber.max must be '{expected}' "
            f"(STORM_SIMULATION_HOURS={STORM_SIMULATION_HOURS}, 0-indexed)"
        )

    def test_scrubber_max_not_59(self, sim_js):
        """Regression guard: the old wrong value '59' must not be present."""
        assert "scrubber.max = '59'" not in sim_js, (
            "scrubber.max = '59' is the Snag-5 bug value — it limited "
            "the storm simulation to 60 hours instead of 168"
        )

    def test_scrubber_min_is_zero(self, sim_js):
        """scrubber.min must be '0' so the timeline starts at hour 0."""
        assert "scrubber.min = '0'" in sim_js

    def test_scrubber_type_is_range(self, sim_js):
        """Scrubber element must be an input[type=range]."""
        assert "scrubber.type = 'range'" in sim_js

    def test_scrubber_id_present(self, sim_js):
        """Scrubber element must have the expected DOM ID."""
        assert 'sp-sim-scrubber' in sim_js

    def test_hour_label_present(self, sim_js):
        """Hour label element must be present to display current hour."""
        assert 'sp-sim-hour-label' in sim_js


# ---------------------------------------------------------------------------
# Seek and animation functions
# ---------------------------------------------------------------------------

class TestSimFunctions:
    """Core simulation control functions must be defined."""

    def test_spSeekTo_defined(self, sim_js):
        """spSeekTo() must be defined — called by scrubber oninput."""
        assert 'spSeekTo' in sim_js

    def test_spSetSpeed_defined(self, sim_js):
        """spSetSpeed() must be defined — called by speed buttons."""
        assert 'spSetSpeed' in sim_js

    def test_spStopAnim_defined(self, sim_js):
        """spStopAnim() must be defined — cleans up animation interval."""
        assert 'spStopAnim' in sim_js

    def test_get_js_returns_nonempty(self, sim_js):
        """sp_sim.get_js() must return a non-empty string."""
        assert len(sim_js) > 100

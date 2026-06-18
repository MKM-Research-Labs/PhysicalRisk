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

"""Tests for Basis Explorer — SHE (elevation) sub-tab JS output."""

import pytest

from visual.interactivity.property import phc_basis_she


class TestBasisSHEJS:
    """Verify the SHE sub-tab JS contains required elements."""

    @pytest.fixture
    def js(self):
        return phc_basis_she.get_js()

    def test_render_function_defined(self, js):
        assert "function renderBasisSHE()" in js

    def test_elevation_section_function_defined(self, js):
        assert "function _drawElevationSection(" in js

    def test_reads_storm_details(self, js):
        assert "phcData.storm_details" in js

    def test_reads_property_elevation(self, js):
        assert "phcData.elevation_m" in js

    def test_reads_floor_level(self, js):
        assert "phcData.floor_level_m" in js

    def test_reads_gauge_elevation(self, js):
        assert "gauge_elevation_m" in js

    def test_height_diff_calculated(self, js):
        assert "heightDiff" in js

    def test_flood_threshold_calculated(self, js):
        assert "floodThreshold" in js

    def test_bankfull_offset(self, js):
        """Bankfull level uses 0.5m offset from severe."""
        assert "severeLevel - 0.5" in js

    def test_reaches_property_classification(self, js):
        assert "reachesProperty" in js

    def test_two_canvas_layout(self, js):
        assert "basis-she-section" in js
        assert "basis-she-waterfall" in js

    def test_waterfall_render_call(self, js):
        assert "_renderSpreadWaterfall" in js

    def test_storm_classification(self, js):
        """Storm data classifies by reach and severity."""
        assert "reachesProperty" in js
        assert "reachCount" in js

    def test_summary_shows_elevation_effect(self, js):
        assert "Elevation Effect" in js

    def test_cross_section_draws_ground(self, js):
        assert "gaugeElev" in js
        assert "propElev" in js
        assert "ctx.fill()" in js

    def test_cross_section_draws_water(self, js):
        assert "rgba(33, 150, 243" in js  # blue water fill

    def test_cross_section_severe_line(self, js):
        assert "'Severe'" in js

    def test_floor_level_drawn(self, js):
        assert "'Floor +" in js

    def test_click_sets_selected_storm(self, js):
        assert "basisSelectedStorm" in js

    def test_she_spread_in_stats(self, js):
        assert "she_spread_bps" in js

    def test_chart_variable_declared(self, js):
        assert "var basisSHEChart" in js

    def test_summary_shows_counts(self, js):
        assert "reachCount" in js
        assert "severeCount" in js

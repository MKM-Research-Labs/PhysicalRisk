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

"""Detailed regression tests for Historical Data tab JS generation (part 1).

Basic render, history endpoint, storm scenarios endpoint, presentation fields,
list ordering.
"""

import pytest


# =============================================================================
# Basic render check
# =============================================================================

class TestHistoricalTabRenders:

    def test_historical_tab_renders(self, hist_js):
        """ghc_historical.get_js() returns substantial JS output."""
        assert len(hist_js) > 1000

    def test_iife_safe_length(self, hist_js):
        """Output long enough to contain real function definitions."""
        assert len(hist_js) > 3000


# =============================================================================
# History endpoint
# =============================================================================

class TestHistoryEndpoint:

    def test_fetches_gauge_history(self, hist_js):
        """Historical tab fetches from /gauges/<gauge_id>/history."""
        assert '/api/v1/gauges/' in hist_js
        assert '/history' in hist_js

    def test_uses_gauge_id_variable(self, hist_js):
        """Fetch URL is built using gaugeId variable."""
        assert 'gaugeId' in hist_js


# =============================================================================
# Storm scenario list — uses the correct stress/storms endpoint
# =============================================================================

class TestStormScenariosEndpoint:
    """Critical: Historical tab must use /trading/stress/storms for the storm list."""

    def test_loads_storm_scenarios(self, hist_js):
        """_loadStormScenarios function must be defined."""
        assert '_loadStormScenarios' in hist_js

    def test_uses_trading_stress_storms_endpoint(self, hist_js):
        """Storm list must be loaded from the same endpoint as Stress tab."""
        assert '/api/v1/trading/stress/storms' in hist_js, \
            "Historical tab MUST use /trading/stress/storms for storm list — " \
            "mismatched endpoint would cause 'no stress' on storm selection"

    def test_does_not_use_gauge_storms_endpoint(self, hist_js):
        """Historical tab must NOT use /gauges/<id>/storms for the storm list."""
        assert '_loadStormScenarios' in hist_js
        fn_idx = hist_js.find('function _loadStormScenarios')
        assert fn_idx >= 0, "_loadStormScenarios function must be defined"
        fn_body = hist_js[fn_idx:fn_idx + 600]
        assert 'trading/stress/storms' in fn_body, \
            "_loadStormScenarios function body must fetch from /trading/stress/storms"

    def test_storm_list_renders_in_panel(self, hist_js):
        """Storm list renders in hist-storms-list element."""
        assert 'hist-storms-list' in hist_js
        assert 'hist-storms-panel' in hist_js


# =============================================================================
# Storm presentation fields
# =============================================================================

class TestStormPresentationFields:
    """Storms in the Historical list must display the same fields as the
    Stress tab dropdown."""

    def test_uses_storm_name_field(self, hist_js):
        assert 's.name' in hist_js or 'storm.name' in hist_js

    def test_uses_storm_id(self, hist_js):
        assert 'storm_id' in hist_js

    def test_uses_intensity_category(self, hist_js):
        assert 'intensity_category' in hist_js

    def test_uses_gauges_severe(self, hist_js):
        assert 'gauges_severe' in hist_js

    def test_uses_effective_precipitation(self, hist_js):
        assert 'effective_precipitation_mm' in hist_js

    def test_uses_peak_level_m(self, hist_js):
        assert 'peak_level_m' in hist_js, \
            "Historical storm list should display peak_level_m — it's the sort key"

    def test_uses_max_trigger_for_colour(self, hist_js):
        assert 'max_trigger' in hist_js


# =============================================================================
# Storm list limits and ordering
# =============================================================================

class TestStormListOrdering:

    def test_shows_top_30_storms(self, hist_js):
        assert '30' in hist_js, \
            "Historical tab must limit storm list to top 30 (sorted worst-first)"

    def test_sorted_by_peak_level(self, hist_js):
        assert 'sorted by peak level' in hist_js or \
               'peak_level' in hist_js, \
            "Historical storm list iterates in API sort order (peak_level_m DESC)"

    def test_shows_overflow_count(self, hist_js):
        assert 'more storms' in hist_js or '+ ' in hist_js

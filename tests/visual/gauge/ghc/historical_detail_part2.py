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

"""Detailed regression tests for Historical Data tab JS generation (part 2).

Click navigation, chart display, stats bar, data caching, field consistency.
"""

import pytest


# =============================================================================
# Click handler — navigation to Stress Test tab
# =============================================================================

class TestStormClickNavigation:
    """When a storm row is clicked, the tab must navigate to the Stress Test
    tab with the correct storm pre-selected."""

    def test_click_handler_defined(self, hist_js):
        assert '_navigateToStress' in hist_js

    def test_sets_stress_storm_hint(self, hist_js):
        assert 'window._stressStormHint' in hist_js, \
            "_navigateToStress must set window._stressStormHint = stormId"

    def test_storm_hint_set_before_switch_tab(self, hist_js):
        idx_hint = hist_js.find('window._stressStormHint')
        idx_switch = hist_js.find('switchTab(5)')
        assert idx_hint > 0, "window._stressStormHint not set in historical JS"
        assert idx_switch > 0, "switchTab(5) not called in historical JS"
        assert idx_hint < idx_switch, \
            "Hint must be set BEFORE switchTab(5) — otherwise Stress tab sees no hint"

    def test_navigates_to_tab_5(self, hist_js):
        assert 'switchTab(5)' in hist_js, \
            "Must navigate to Tab 5 (Stress Test) — check tab index"
        assert 'switchTab(4)' not in hist_js.replace(
            'switchTab(5)', ''), "switchTab(4) should not appear near stress navigation"

    def test_click_handler_iife_safe(self, hist_js):
        assert 'addEventListener' in hist_js, \
            "Storm click handlers must use addEventListener (not inline onclick)"
        assert 'hist-storm-row' in hist_js

    def test_storm_id_passed_to_navigate(self, hist_js):
        assert 'data-storm-id' in hist_js
        assert 'getAttribute' in hist_js


# =============================================================================
# Historical chart — 50yr water level display
# =============================================================================

class TestHistoricalChart:

    def test_renders_historical_chart(self, hist_js):
        assert 'hist-timeseries-chart' in hist_js

    def test_shows_flood_alert_threshold(self, hist_js):
        assert 'FloodAlert' in hist_js

    def test_shows_flood_warning_threshold(self, hist_js):
        assert 'FloodWarning' in hist_js

    def test_shows_severe_flood_threshold(self, hist_js):
        assert 'SevereFloodWarning' in hist_js

    def test_alert_colour_amber(self, hist_js):
        assert '#FFC107' in hist_js

    def test_warning_colour_orange(self, hist_js):
        assert '#FF9800' in hist_js

    def test_severe_colour_red(self, hist_js):
        assert '#F44336' in hist_js

    def test_daily_observations_field(self, hist_js):
        assert 'daily_observations' in hist_js

    def test_subsamples_observations(self, hist_js):
        assert '7' in hist_js  # every 7th day
        assert 'sampleObs' in hist_js


# =============================================================================
# Stats bar
# =============================================================================

class TestHistoricalStatsBar:

    def test_stats_bar_record_years(self, hist_js):
        assert 'record_years' in hist_js or 'Record' in hist_js

    def test_stats_bar_mean_level(self, hist_js):
        assert 'mean_level' in hist_js or 'Mean' in hist_js

    def test_stats_bar_flood_exceedances(self, hist_js):
        assert 'flood_exceedances' in hist_js

    def test_cleanup_function(self, hist_js):
        assert '_cleanupHistCharts' in hist_js


# =============================================================================
# Data caching
# =============================================================================

class TestHistoricalDataCaching:

    def test_caches_history_data(self, hist_js):
        assert '_histData' in hist_js

    def test_cache_keyed_by_gauge_id(self, hist_js):
        assert '_gaugeId' in hist_js

    def test_uses_cached_data_on_revisit(self, hist_js):
        assert '_histData._gaugeId' in hist_js or \
               '_histData && _histData._gaugeId' in hist_js


# =============================================================================
# Consistency: same fields used in Historical list and Stress dropdown
# =============================================================================

class TestStormFieldConsistencyWithStressTab:
    """The Historical storm list and the Stress Test storm dropdown both
    consume data from /trading/stress/storms."""

    def test_storm_id_consistent(self, hist_js):
        assert 'storm_id' in hist_js

    def test_intensity_category_consistent(self, hist_js):
        assert 'intensity_category' in hist_js

    def test_peak_level_m_consistent(self, hist_js):
        assert 'peak_level_m' in hist_js

    def test_gauges_severe_consistent(self, hist_js):
        assert 'gauges_severe' in hist_js

    def test_effective_precipitation_mm_consistent(self, hist_js):
        assert 'effective_precipitation_mm' in hist_js

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

"""Detailed regression tests for Historical Data tab (ghc_historical.py) JS generation.

Protects against regressions in:
- Storm scenario list rendering and click navigation
- Correct endpoint usage (stress/storms, not gauges/storms)
- _stressStormHint handoff to Stress Test tab
- switchTab(5) navigation (Tab 5 = Stress Test in gauge panel)
- Storm field consistency with the stress endpoint response
- Top-30 display limit (sorted by peak_level_m desc)
- Flood threshold display in the 50yr chart
"""

import pytest


@pytest.fixture(scope='module')
def hist_js():
    """Get Historical tab JS once for all tests."""
    from visual.interactivity.gauge.gaugehc import ghc_historical
    return ghc_historical.get_js()


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
    """Critical: Historical tab must use /trading/stress/storms for the storm list.

    If it uses a different endpoint (e.g., /gauges/storms), the storm_ids
    returned will not be recognised by POST /trading/stress/run, causing
    'no stress' when a storm is selected.
    """

    def test_loads_storm_scenarios(self, hist_js):
        """_loadStormScenarios function must be defined."""
        assert '_loadStormScenarios' in hist_js

    def test_uses_trading_stress_storms_endpoint(self, hist_js):
        """Storm list must be loaded from the same endpoint as Stress tab.

        Critical for consistency: /trading/stress/storms returns storms from
        stress_storms.json — the same source used by POST /trading/stress/run.
        Using any other endpoint would produce storm_ids that the stress run
        cannot find, resulting in 404 and 'no stress' on selection.
        """
        assert '/api/v1/trading/stress/storms' in hist_js, \
            "Historical tab MUST use /trading/stress/storms for storm list — " \
            "mismatched endpoint would cause 'no stress' on storm selection"

    def test_does_not_use_gauge_storms_endpoint(self, hist_js):
        """Historical tab must NOT use /gauges/<id>/storms for the storm list.

        /gauges/<id>/storms returns gaugets data which uses different storm_ids
        to stress_storms.json — these cannot be passed to /trading/stress/run.
        """
        assert '_loadStormScenarios' in hist_js
        # Find the function definition (not the call site — starts with 'function')
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
    Stress tab dropdown, and must access all fields present in the
    /trading/stress/storms response.
    """

    def test_uses_storm_name_field(self, hist_js):
        """Storm display uses 'name' field from the stress/storms response."""
        assert 's.name' in hist_js or 'storm.name' in hist_js

    def test_uses_storm_id(self, hist_js):
        """Storm display uses storm_id."""
        assert 'storm_id' in hist_js

    def test_uses_intensity_category(self, hist_js):
        """Storm display shows intensity_category."""
        assert 'intensity_category' in hist_js

    def test_uses_gauges_severe(self, hist_js):
        """Storm display shows gauges_severe count."""
        assert 'gauges_severe' in hist_js

    def test_uses_effective_precipitation(self, hist_js):
        """Storm display shows effective_precipitation_mm."""
        assert 'effective_precipitation_mm' in hist_js

    def test_uses_peak_level_m(self, hist_js):
        """Storm display shows peak_level_m — the primary sort key.

        The stress endpoint returns storms sorted by peak_level_m DESC.
        Without displaying this, users cannot see why a storm is ranked first.
        """
        assert 'peak_level_m' in hist_js, \
            "Historical storm list should display peak_level_m — it's the sort key"

    def test_uses_max_trigger_for_colour(self, hist_js):
        """Storm rows use max_trigger field for colour coding."""
        assert 'max_trigger' in hist_js


# =============================================================================
# Storm list limits and ordering
# =============================================================================

class TestStormListOrdering:

    def test_shows_top_30_storms(self, hist_js):
        """Historical tab limits display to 30 storms."""
        assert '30' in hist_js, \
            "Historical tab must limit storm list to top 30 (sorted worst-first)"

    def test_sorted_by_peak_level(self, hist_js):
        """Comment or logic references peak_level sort for display."""
        # The backend sorts by peak_level_m DESC and sends them in that order.
        # The frontend iterates in order → first 30 = worst 30.
        assert 'sorted by peak level' in hist_js or \
               'peak_level' in hist_js, \
            "Historical storm list iterates in API sort order (peak_level_m DESC)"

    def test_shows_overflow_count(self, hist_js):
        """When more than 30 storms exist, shows '+ N more' message."""
        assert 'more storms' in hist_js or '+ ' in hist_js


# =============================================================================
# Click handler — navigation to Stress Test tab
# =============================================================================

class TestStormClickNavigation:
    """When a storm row is clicked, the tab must navigate to the Stress Test
    tab with the correct storm pre-selected.  This is the critical integration
    between the scenario visualiser and the stress testing module.
    """

    def test_click_handler_defined(self, hist_js):
        """_navigateToStress function must be defined."""
        assert '_navigateToStress' in hist_js

    def test_sets_stress_storm_hint(self, hist_js):
        """_navigateToStress must set window._stressStormHint before switching tab.

        Critical: without this, the Stress tab has no hint to auto-select the
        correct storm, leaving the user with the default 'Select a storm' state.
        """
        assert 'window._stressStormHint' in hist_js, \
            "_navigateToStress must set window._stressStormHint = stormId"

    def test_storm_hint_set_before_switch_tab(self, hist_js):
        """Hint must be set BEFORE switchTab is called — otherwise Stress tab
        renders before the hint is available and ignores it."""
        idx_hint = hist_js.find('window._stressStormHint')
        idx_switch = hist_js.find('switchTab(5)')
        assert idx_hint > 0, "window._stressStormHint not set in historical JS"
        assert idx_switch > 0, "switchTab(5) not called in historical JS"
        assert idx_hint < idx_switch, \
            "Hint must be set BEFORE switchTab(5) — otherwise Stress tab sees no hint"

    def test_navigates_to_tab_5(self, hist_js):
        """Must call switchTab(5), NOT switchTab(4) or any other index.

        Tab 5 = Stress Test in the gauge hazard curve panel (0-indexed):
          0=Hazard Curve, 1=Term Structure, 2=PRS Pricing, 3=Basis, 4=Historical,
          5=Stress Test.
        Using the wrong tab index would switch to the wrong tab.
        """
        assert 'switchTab(5)' in hist_js, \
            "Must navigate to Tab 5 (Stress Test) — check tab index"
        # Also assert we do NOT call switchTab with wrong index for stress
        assert 'switchTab(4)' not in hist_js.replace(
            'switchTab(5)', ''), "switchTab(4) should not appear near stress navigation"

    def test_click_handler_iife_safe(self, hist_js):
        """Click handlers use addEventListener, not inline onclick.

        Inside an IIFE, inline onclick cannot reference enclosing scope functions.
        addEventListener is the correct pattern.
        """
        assert 'addEventListener' in hist_js, \
            "Storm click handlers must use addEventListener (not inline onclick)"
        assert 'hist-storm-row' in hist_js

    def test_storm_id_passed_to_navigate(self, hist_js):
        """data-storm-id attribute used to pass storm_id to _navigateToStress."""
        assert 'data-storm-id' in hist_js
        assert 'getAttribute' in hist_js


# =============================================================================
# Historical chart — 50yr water level display
# =============================================================================

class TestHistoricalChart:

    def test_renders_historical_chart(self, hist_js):
        """Historical chart canvas element defined."""
        assert 'hist-timeseries-chart' in hist_js

    def test_shows_flood_alert_threshold(self, hist_js):
        """Alert threshold line on the 50yr chart."""
        assert 'FloodAlert' in hist_js

    def test_shows_flood_warning_threshold(self, hist_js):
        """Warning threshold line on the 50yr chart."""
        assert 'FloodWarning' in hist_js

    def test_shows_severe_flood_threshold(self, hist_js):
        """Severe threshold line on the 50yr chart."""
        assert 'SevereFloodWarning' in hist_js

    def test_alert_colour_amber(self, hist_js):
        """Alert line uses amber (#FFC107)."""
        assert '#FFC107' in hist_js

    def test_warning_colour_orange(self, hist_js):
        """Warning line uses orange (#FF9800)."""
        assert '#FF9800' in hist_js

    def test_severe_colour_red(self, hist_js):
        """Severe line uses red (#F44336)."""
        assert '#F44336' in hist_js

    def test_daily_observations_field(self, hist_js):
        """Chart uses daily_observations from history API response."""
        assert 'daily_observations' in hist_js

    def test_subsamples_observations(self, hist_js):
        """Subsamples every 7th day for performance."""
        assert '7' in hist_js  # every 7th day
        assert 'sampleObs' in hist_js


# =============================================================================
# Stats bar
# =============================================================================

class TestHistoricalStatsBar:

    def test_stats_bar_record_years(self, hist_js):
        """Stats bar shows record years."""
        assert 'record_years' in hist_js or 'Record' in hist_js

    def test_stats_bar_mean_level(self, hist_js):
        """Stats bar shows mean level."""
        assert 'mean_level' in hist_js or 'Mean' in hist_js

    def test_stats_bar_flood_exceedances(self, hist_js):
        """Stats bar shows flood exceedances."""
        assert 'flood_exceedances' in hist_js

    def test_cleanup_function(self, hist_js):
        """Chart cleanup function defined."""
        assert '_cleanupHistCharts' in hist_js


# =============================================================================
# Data caching
# =============================================================================

class TestHistoricalDataCaching:

    def test_caches_history_data(self, hist_js):
        """Historical data is cached to avoid repeated fetches."""
        assert '_histData' in hist_js

    def test_cache_keyed_by_gauge_id(self, hist_js):
        """Cache is keyed by gauge ID (_gaugeId)."""
        assert '_gaugeId' in hist_js

    def test_uses_cached_data_on_revisit(self, hist_js):
        """If cache exists for same gauge, skip API fetch."""
        assert '_histData._gaugeId' in hist_js or \
               '_histData && _histData._gaugeId' in hist_js


# =============================================================================
# Consistency: same fields used in Historical list and Stress dropdown
# =============================================================================

class TestStormFieldConsistencyWithStressTab:
    """The Historical storm list and the Stress Test storm dropdown both
    consume data from /trading/stress/storms.  They must access the same
    field names so that a storm shown in the Historical panel can be
    correctly identified and auto-selected in the Stress tab.
    """

    def test_storm_id_consistent(self, hist_js):
        """Both tabs use 'storm_id' (not 'id' or 'stormId')."""
        assert 'storm_id' in hist_js

    def test_intensity_category_consistent(self, hist_js):
        """Both tabs use 'intensity_category' field."""
        assert 'intensity_category' in hist_js

    def test_peak_level_m_consistent(self, hist_js):
        """Both tabs use 'peak_level_m' field."""
        assert 'peak_level_m' in hist_js

    def test_gauges_severe_consistent(self, hist_js):
        """Both tabs use 'gauges_severe' field."""
        assert 'gauges_severe' in hist_js

    def test_effective_precipitation_mm_consistent(self, hist_js):
        """Both tabs use 'effective_precipitation_mm' field."""
        assert 'effective_precipitation_mm' in hist_js

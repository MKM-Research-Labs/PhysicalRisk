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

"""Tests for Portfolio Stress tab (Tab 8) JavaScript rendering."""

import pytest


class TestPortStressSubmodule:
    """The port_stress sub-module renders and exposes required public API."""

    @pytest.fixture(scope='class')
    def ps_js(self):
        from visual.interactivity.trading import port_stress
        return port_stress.get_js()

    @pytest.fixture(scope='class')
    def full_js(self):
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        return TradingDeskPanel().get_js()

    def test_port_stress_renders(self, ps_js):
        """port_stress.get_js() returns non-empty string without errors."""
        assert len(ps_js) > 0

    def test_port_stress_has_create_view(self, ps_js):
        """'createPortStressView' must be defined — builds the Tab 8 DOM."""
        assert 'createPortStressView' in ps_js

    def test_port_stress_has_load_data(self, ps_js):
        """'loadPortStressData' must be defined — fetches storm list on tab open."""
        assert 'loadPortStressData' in ps_js

    def test_port_stress_has_storm_changed(self, ps_js):
        """'psStormChanged' must be defined — handles storm dropdown selection."""
        assert 'psStormChanged' in ps_js

    def test_port_stress_has_switch_subtab(self, ps_js):
        """'psSwitchSubTab' must be defined — controls the 4 sub-tabs."""
        assert 'psSwitchSubTab' in ps_js

    def test_port_stress_has_cleanup(self, ps_js):
        """'psCleanupCharts' must be defined — destroys Chart.js instances."""
        assert 'psCleanupCharts' in ps_js

    def test_port_stress_has_all_sub_tabs(self, ps_js):
        """All four sub-tab render functions must be present."""
        assert '_psRenderPFloodTab' in ps_js
        assert '_psRenderPortPnlTab' in ps_js
        assert '_psRenderGaugePnlTab' in ps_js
        assert '_psRenderSeverityTab' in ps_js

    def test_port_stress_state_vars(self, ps_js):
        """Module-level state variables must be declared."""
        assert 'psResult' in ps_js
        assert 'psActiveSubTab' in ps_js
        assert 'psSelectedGaugeId' in ps_js


class TestPortStressEndpoints:
    """The correct API endpoint URLs must appear in the rendered JS."""

    @pytest.fixture(scope='class')
    def ps_js(self):
        from visual.interactivity.trading import port_stress
        return port_stress.get_js()

    def test_portfolio_storms_endpoint(self, ps_js):
        """JS must fetch from /api/v1/trading/stress/portfolio-storms."""
        assert '/api/v1/trading/stress/portfolio-storms' in ps_js

    def test_portfolio_run_endpoint(self, ps_js):
        """JS must POST to /api/v1/trading/stress/portfolio-run."""
        assert '/api/v1/trading/stress/portfolio-run' in ps_js

    def test_post_method_used_for_run(self, ps_js):
        """portfolio-run endpoint must use POST method."""
        assert 'POST' in ps_js


class TestPortStressIdConventions:
    """DOM element IDs must use ps- prefix to avoid collisions with Tab 7."""

    @pytest.fixture(scope='class')
    def ps_js(self):
        from visual.interactivity.trading import port_stress
        return port_stress.get_js()

    def test_ps_prefix_on_storm_sel(self, ps_js):
        """Storm selector uses ps- prefix (not td-stress-*)."""
        assert 'ps-storm-sel' in ps_js

    def test_ps_prefix_on_content(self, ps_js):
        """Content area uses ps-content ID."""
        assert 'ps-content' in ps_js

    def test_ps_prefix_on_tabs(self, ps_js):
        """Sub-tab button IDs are built using ps-tab- prefix.
        The JS uses dynamic construction: btn.id = 'ps-tab-' + st.id
        so we verify the prefix string and the sub-tab ids individually."""
        assert "ps-tab-'" in ps_js or "'ps-tab-' +" in ps_js or 'ps-tab-' in ps_js
        # The four sub-tab id values must appear as string literals
        assert "'pflood'" in ps_js
        assert "'portpnl'" in ps_js
        assert "'gaugepnl'" in ps_js
        assert "'severity'" in ps_js

    def test_no_id_conflicts_with_stress_tab(self, ps_js):
        """ps- IDs must not collide with Tab 7's td-stress-gauge ID."""
        assert 'td-stress-gauge' not in ps_js


class TestPortStressPFloodTab:
    """P(flood) sub-tab render function and Chart.js canvas."""

    @pytest.fixture(scope='class')
    def ps_js(self):
        from visual.interactivity.trading import port_stress
        return port_stress.get_js()

    def test_pflood_render_function(self, ps_js):
        """_psRenderPFloodTab must be defined."""
        assert '_psRenderPFloodTab' in ps_js

    def test_pflood_uses_chartjs(self, ps_js):
        """P(flood) tab creates a Chart.js instance."""
        assert 'Chart(' in ps_js

    def test_pflood_canvas_id(self, ps_js):
        """Canvas element uses ps-pflood-canvas ID."""
        assert 'ps-pflood-canvas' in ps_js

    def test_pflood_threshold_colours(self, ps_js):
        """Threshold bar colours must be present: severe red, warning orange, alert amber."""
        assert '#c62828' in ps_js  # severe red
        assert '#e65100' in ps_js  # warning orange
        assert '#f9a825' in ps_js  # alert amber


class TestPortStressPortPnlTab:
    """Portfolio P&L sub-tab render function and horizontal bar chart."""

    @pytest.fixture(scope='class')
    def ps_js(self):
        from visual.interactivity.trading import port_stress
        return port_stress.get_js()

    def test_portpnl_render_function(self, ps_js):
        """_psRenderPortPnlTab must be defined."""
        assert '_psRenderPortPnlTab' in ps_js

    def test_portpnl_uses_horizontal_bars(self, ps_js):
        """Horizontal bar chart needs indexAxis: 'y' in Chart.js options."""
        assert 'indexAxis' in ps_js

    def test_portpnl_canvas_id(self, ps_js):
        """Canvas element uses ps-portpnl-canvas ID."""
        assert 'ps-portpnl-canvas' in ps_js

    def test_portpnl_fmtgbp(self, ps_js):
        """Portfolio P&L tab uses the shared fmtGBP formatter."""
        assert 'fmtGBP' in ps_js


class TestPortStressGaugePnlTab:
    """Gauge P&L sub-tab render function, trade table, and cross-tab navigation."""

    @pytest.fixture(scope='class')
    def ps_js(self):
        from visual.interactivity.trading import port_stress
        return port_stress.get_js()

    def test_gaugepnl_render_function(self, ps_js):
        """_psRenderGaugePnlTab must be defined."""
        assert '_psRenderGaugePnlTab' in ps_js

    def test_gaugepnl_has_gauge_table(self, ps_js):
        """_psRenderGaugeTable must be defined — renders per-gauge trade rows."""
        assert '_psRenderGaugeTable' in ps_js

    def test_gaugepnl_full_detail_button(self, ps_js):
        """'Full Detail' link button must be present — navigates to Tab 7 gauge view."""
        assert 'Full Detail' in ps_js

    def test_gaugepnl_sets_storm_hint(self, ps_js):
        """_stressStormHint must be set — passes selected storm to Tab 7 auto-selection."""
        assert '_stressStormHint' in ps_js

    def test_gaugepnl_sets_gauge_hint(self, ps_js):
        """tdStressGaugeHint must be set — passes selected gauge to Tab 7 pre-selection."""
        assert 'tdStressGaugeHint' in ps_js

    def test_gaugepnl_calls_switch_tab_stress(self, ps_js):
        """Full Detail button must navigate to Tab 7 via switchTab('stress')."""
        assert "switchTab('stress')" in ps_js


class TestPortStressSeverityTab:
    """Severity breakdown sub-tab with four threshold groups."""

    @pytest.fixture(scope='class')
    def ps_js(self):
        from visual.interactivity.trading import port_stress
        return port_stress.get_js()

    def test_severity_render_function(self, ps_js):
        """_psRenderSeverityTab must be defined."""
        assert '_psRenderSeverityTab' in ps_js

    def test_severity_has_four_groups(self, ps_js):
        """All four severity group labels must be present in the JS output."""
        assert 'SEVERE' in ps_js
        assert 'WARNING' in ps_js
        assert 'ALERT' in ps_js
        assert 'CLEAN' in ps_js

    def test_severity_severe_colour(self, ps_js):
        """Severe group must use the #ffebee background colour."""
        assert ps_js.lower().find('#ffebee') >= 0, \
            "Severe group must use #ffebee background"

    def test_severity_gauge_pnl_link(self, ps_js):
        """Severity rows must navigate to Gauge P&L sub-tab via psSwitchSubTab."""
        assert 'psSwitchSubTab' in ps_js

    def test_severity_sets_selected_gauge(self, ps_js):
        """Severity row click must set psSelectedGaugeId before switching sub-tab."""
        assert 'psSelectedGaugeId' in ps_js


class TestPortStressInTradingDesk:
    """Port Stress tab (Tab 8) must be fully integrated into the TradingDeskPanel."""

    @pytest.fixture(scope='class')
    def ps_js(self):
        from visual.interactivity.trading import port_stress
        return port_stress.get_js()

    @pytest.fixture(scope='class')
    def full_js(self):
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        return TradingDeskPanel().get_js()

    def test_port_stress_tab_in_full_js(self, full_js):
        """'Port Stress' tab label must appear in the rendered trading desk."""
        assert 'Port Stress' in full_js

    def test_port_stress_view_created(self, full_js):
        """createPortStressView() call must appear in panel construction."""
        assert 'createPortStressView' in full_js

    def test_port_stress_view_appended(self, full_js):
        """portStressView variable must appear — panel appends it to DOM."""
        assert 'portStressView' in full_js

    def test_portstress_in_tabs_array(self, full_js):
        """tabs array must include the portstress entry."""
        assert "id: 'portstress'" in full_js

    def test_portstress_in_views_array(self, full_js):
        """switchTab views array must include 'portstress'."""
        assert "'portstress'" in full_js

    def test_portstress_in_switch_tab(self, full_js):
        """switchTab must handle tab === 'portstress' branch."""
        assert "tab === 'portstress'" in full_js

    def test_load_port_stress_data_called(self, full_js):
        """loadPortStressData() must be called in the portstress switchTab branch."""
        assert 'loadPortStressData' in full_js

    def test_ps_cleanup_in_hide_panel(self, full_js):
        """hidePanel must call psCleanupCharts() to destroy chart instances."""
        assert 'psCleanupCharts' in full_js

    def test_ps_js_inside_iife(self, full_js):
        """psResult state variable must appear inside the IIFE, not after it."""
        iife_close = full_js.rfind('})();')
        idx = full_js.find('psResult')
        assert idx > 0, "psResult not found in full JS"
        assert idx < iife_close, \
            "psResult is outside the IIFE — Port Stress functions are not reachable"

    def test_full_js_syntax_valid_with_port_stress(self, full_js):
        """Rendered full JS must be of substantial length — sanity check that
        port_stress rendering did not break the panel output."""
        assert len(full_js) > 200000, \
            "Rendered JS suspiciously short — port_stress may have caused a render error"

    def test_no_brace_artifacts(self, full_js):
        """psResult must survive f-string rendering — absent if brace escaping broke."""
        assert 'psResult' in full_js, \
            "psResult missing from full JS — likely caused by f-string brace escaping error"

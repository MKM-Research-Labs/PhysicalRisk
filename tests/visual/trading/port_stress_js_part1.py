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

"""Tests for Portfolio Stress tab (Tab 8) JavaScript rendering — part 1.

Sub-module API, endpoints, ID conventions, P(flood) tab, and Port P&L tab.
"""

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
        """P(flood) tab contains the heatmap canvas and chart area container."""
        assert 'ps-heatmap-canvas' in ps_js
        assert 'ps-pflood-chart-area' in ps_js

    def test_pflood_threshold_colours(self, ps_js):
        """Threshold bar colours must be present: severe red, warning orange, alert amber."""
        assert 'var(--red-dark)' in ps_js  # severe red
        assert 'var(--amber-deep)' in ps_js  # warning orange
        assert 'var(--gold-deep)' in ps_js  # alert amber


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

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

"""Tests for Portfolio Stress tab (Tab 8) JavaScript rendering — part 2.

Gauge P&L tab, Severity tab, and TradingDesk integration.
"""

import pytest


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
        """Severe group must use the danger background tint."""
        assert 'var(--danger-bg-soft)' in ps_js, \
            "Severe group must use the danger background tint"

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

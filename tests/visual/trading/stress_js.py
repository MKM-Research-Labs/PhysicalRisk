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

"""Tests for Stress tab JavaScript rendering and gauge hint pre-selection."""

import pytest


class TestStressKnockOut:
    """Regression: Stress test knock-out behaviour."""

    def test_stress_ko_status_in_table(self):
        """Stress table must show KO status per trade."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'triggered_hour' in js, \
            "Stress table must reference triggered_hour"
        assert 'KO H' in js, "Must show 'KO H{n}' label for triggered trades"

    def test_stress_ko_annotation_on_charts(self):
        """Both stress charts must show KO vertical annotation line."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'koLine' in js, "Charts must have KO annotation line"
        assert 'first_trigger_hour' in js, \
            "Charts must reference first_trigger_hour for KO line"

    def test_stress_stats_bar_ko_info(self):
        """Stats bar must show knock-out count."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'num_triggered' in js, "Stats bar must show num_triggered"
        assert 'Knocked Out' in js, "Stats bar must show 'Knocked Out' label"


class TestStressGaugeFunctions:
    """All stress gauge/storm functions must be defined and reachable.

    'None of the gauge functions are available' means these must all exist
    in the rendered JS output.
    """

    @pytest.fixture(scope='class')
    def stress_js(self):
        from visual.interactivity.trading import stress
        return stress.get_js()

    @pytest.fixture(scope='class')
    def full_js(self):
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        return TradingDeskPanel().get_js()

    def test_populate_gauge_dropdown_function_defined(self, stress_js):
        """_tdPopulateGaugeDropdown must exist — builds gauge selector."""
        assert '_tdPopulateGaugeDropdown' in stress_js, \
            "_tdPopulateGaugeDropdown missing — gauge list cannot be built"

    def test_stress_gauge_changed_function_defined(self, stress_js):
        """tdStressGaugeChanged must exist — called when gauge is selected."""
        assert 'function tdStressGaugeChanged' in stress_js, \
            "tdStressGaugeChanged missing — gauge selection has no handler"

    def test_populate_storm_dropdown_function_defined(self, stress_js):
        """_tdPopulateStormDropdown must exist — builds storm list for selected gauge."""
        assert '_tdPopulateStormDropdown' in stress_js, \
            "_tdPopulateStormDropdown missing — storm list cannot be populated"

    def test_stress_storm_changed_function_defined(self, stress_js):
        """tdStressStormChanged must exist — called when storm is selected."""
        assert 'function tdStressStormChanged' in stress_js, \
            "tdStressStormChanged missing — storm selection has no handler"

    def test_stress_gauge_changed_binds_to_dropdown(self, stress_js):
        """gauge onchange must call tdStressGaugeChanged."""
        assert 'tdStressGaugeChanged()' in stress_js, \
            "gauge dropdown onchange must invoke tdStressGaugeChanged()"

    def test_stress_storm_changed_binds_to_dropdown(self, stress_js):
        """storm onchange must call tdStressStormChanged."""
        assert 'tdStressStormChanged()' in stress_js, \
            "storm dropdown onchange must invoke tdStressStormChanged()"

    def test_gauge_selector_element_id_present(self, stress_js):
        """td-stress-gauge element must be present for JS to find it."""
        assert "getElementById('td-stress-gauge')" in stress_js, \
            "JS must look up td-stress-gauge element by ID"

    def test_storm_selector_element_id_present(self, stress_js):
        """td-stress-storm element must be present for JS to find it."""
        assert "getElementById('td-stress-storm')" in stress_js, \
            "JS must look up td-stress-storm element by ID"

    def test_full_js_contains_stress_gauge_changed(self, full_js):
        """tdStressGaugeChanged must survive f-string rendering in tradingdesk.py."""
        assert 'tdStressGaugeChanged' in full_js, \
            "tdStressGaugeChanged lost during f-string rendering — check brace escaping"

    def test_full_js_contains_populate_gauge_dropdown(self, full_js):
        """_tdPopulateGaugeDropdown must survive f-string rendering."""
        assert '_tdPopulateGaugeDropdown' in full_js, \
            "_tdPopulateGaugeDropdown lost during f-string rendering"

    def test_full_js_no_unclosed_template_literal(self, full_js):
        """Rendered JS must not have unescaped f-string brace artifacts."""
        # A NameError during render produces empty/short output
        assert len(full_js) > 10000, \
            "Rendered JS suspiciously short — likely f-string brace error"

    def test_stress_functions_not_before_iife_close(self, full_js):
        """Stress functions must be INSIDE the IIFE, not after it."""
        iife_close = full_js.rfind('})();')
        idx_gauge_changed = full_js.find('tdStressGaugeChanged')
        assert idx_gauge_changed > 0, "tdStressGaugeChanged not found in full JS"
        assert idx_gauge_changed < iife_close, \
            "tdStressGaugeChanged is outside the IIFE — functions not reachable"


class TestStressTabSubmodule:
    """Test the Stress tab (Tab 7) sub-module."""

    def test_stress_renders(self):
        """Stress sub-module should render without errors."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert len(js) > 0

    def test_stress_has_create_and_load(self):
        """Stress tab must have createStressView and loadStressData."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'createStressView' in js
        assert 'loadStressData' in js

    def test_stress_gauge_dropdown(self):
        """Stress tab must have gauge selector dropdown."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'td-stress-gauge' in js
        assert 'tdStressGaugeChanged' in js

    def test_stress_storm_dropdown(self):
        """Stress tab must have storm selector dropdown."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'td-stress-storm' in js
        assert 'tdStressStormChanged' in js

    def test_stress_charts(self):
        """Stress tab must have both chart renderers."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert '_tdRenderProbabilityChart' in js
        assert '_tdRenderStressPnlChart' in js

    def test_stress_trade_table(self):
        """Stress tab must have trade table renderer."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert '_tdRenderStressTable' in js
        assert 'td-stress-table-wrap' in js

    def test_stress_stats_bar(self):
        """Stress tab must have stats bar with KO info."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert '_tdRenderStressStats' in js
        assert 'td-stress-stats-bar' in js
        assert 'Knocked Out' in js

    def test_stress_link_storm_simulation(self):
        """Stress tab must have Storm Simulation link."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'tdStressOpenGauge' in js
        assert 'Storm Simulation' in js

    def test_stress_link_property_damage(self):
        """Stress tab must have Property Damage link."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'tdStressOpenDamage' in js
        assert 'Property Damage' in js

    def test_stress_cleanup(self):
        """Stress tab must have cleanup function."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'tdCleanupStressCharts' in js

    def test_stress_ko_annotation(self):
        """Charts must have KO annotation line."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'koLine' in js
        assert 'first_trigger_hour' in js

    def test_stress_gauges_endpoint(self):
        """Stress tab must fetch from stress/gauges endpoint."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert '/api/v1/trading/stress/gauges' in js

    def test_stress_chart_canvas(self):
        """Chart canvas element must use td- prefixed ID."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'td-stress-chart-canvas' in js

    def test_stress_chart_tabs(self):
        """Chart sub-tabs must exist for Flood Probability, Stress P&L, and Surface."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'td-stress-ctab-0' in js
        assert 'td-stress-ctab-1' in js
        assert 'td-stress-ctab-2' in js
        assert 'Flood Probability' in js
        assert 'Surface' in js

    def test_surface_table_scrollable(self):
        """Surface table must be horizontally scrollable for 168h of columns."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'overflow:auto' in js, \
            "Surface wrap must have overflow:auto for horizontal scroll"
        idx = js.find('td-stress-surface-wrap')
        table_idx = js.find('<table style=', idx)
        if table_idx > 0:
            snippet = js[table_idx:table_idx+120]
            assert 'width:100%' not in snippet, \
                "Surface table must NOT have width:100% — prevents horizontal scroll"

    def test_stress_surface_table(self):
        """Stress tab must render probability surface table."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'probability_surface' in js
        assert 'td-stress-surface-wrap' in js
        assert '#FFEBEE' in js  # severe band
        assert '#FFF8E1' in js  # alert band


class TestStressGaugeHint:
    """Tests for stress tab gauge pre-selection via hint from blotter/market."""

    def test_stress_gauge_hint_state_variable(self):
        """tdStressGaugeHint state variable must exist in stress JS."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'tdStressGaugeHint' in js, \
            "tdStressGaugeHint state variable missing — gauge hint cannot be stored"

    def test_load_stress_data_accepts_gauge_hint(self):
        """loadStressData must accept a gaugeHint parameter."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'function loadStressData(gaugeHint)' in js, \
            "loadStressData must accept gaugeHint parameter"

    def test_load_stress_data_stores_hint(self):
        """loadStressData must store gaugeHint in tdStressGaugeHint."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'if (gaugeHint) tdStressGaugeHint = gaugeHint' in js, \
            "loadStressData must save gaugeHint to tdStressGaugeHint"

    def test_populate_gauge_dropdown_reads_hint(self):
        """_tdPopulateGaugeDropdown must use tdStressGaugeHint for pre-selection."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'tdStressGaugeHint' in js
        idx_populate = js.find('_tdPopulateGaugeDropdown')
        idx_hint_use = js.find('tdStressGaugeHint', idx_populate)
        assert idx_hint_use > idx_populate, \
            "tdStressGaugeHint must be read inside _tdPopulateGaugeDropdown"

    def test_hint_consumed_after_use(self):
        """tdStressGaugeHint must be set to null after use to prevent stale hint."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'tdStressGaugeHint = null' in js, \
            "tdStressGaugeHint must be cleared after use"

    def test_hint_fallback_to_blotter_filter(self):
        """When no market hint, tdBlotterFilters.gauge_id must be the fallback."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert 'tdBlotterFilters' in js, \
            "stress setup must reference tdBlotterFilters as fallback hint"
        assert 'tdBlotterFilters.gauge_id' in js, \
            "stress must fall back to tdBlotterFilters.gauge_id when no market hint"

    def test_switch_tab_stress_passes_gauge_hint(self):
        """switchTab('stress') in tradingdesk must pass gauge hint to loadStressData."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        js = TradingDeskPanel().get_js()
        assert "loadStressData(stressHint)" in js, \
            "switchTab must call loadStressData(stressHint) not bare loadStressData()"
        assert "tdSelectedGauge" in js, \
            "switchTab stress block must reference tdSelectedGauge"
        assert "tdBlotterFilters.gauge_id" in js, \
            "switchTab must include tdBlotterFilters.gauge_id as fallback hint"

    def test_switch_tab_stress_blotter_filter_first(self):
        """switchTab('stress') must use blotter filter as primary hint.

        Blotter filter reflects the most recent explicit gauge selection by the user.
        Market gauge (tdSelectedGauge) is secondary — it can be stale from a prior
        Market tab visit. Priority: blotter filter > market gauge > first blotter trade.
        """
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        js = TradingDeskPanel().get_js()
        idx_blotter = js.find("tdBlotterFilters.gauge_id")
        idx_market = js.find("tdSelectedGauge")
        assert idx_blotter > 0, "tdBlotterFilters.gauge_id missing from stress hint"
        assert idx_market > 0, "tdSelectedGauge missing from stress hint"
        stress_start = js.find("tab === 'stress'")
        assert stress_start > 0, "stress tab block not found in rendered JS"
        stress_block = js[stress_start:stress_start + 600]
        bi = stress_block.find("tdBlotterFilters.gauge_id")
        mi = stress_block.find("tdSelectedGauge")
        assert bi > 0, "tdBlotterFilters.gauge_id not found in stress block"
        assert mi > 0, "tdSelectedGauge not found in stress block"
        assert bi < mi, \
            "In stress switchTab block, blotter filter must come before tdSelectedGauge"

    def test_switch_tab_stress_uses_blotter_data_fallback(self):
        """switchTab('stress') must fall back to first blotter trade gauge when no filter set."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        js = TradingDeskPanel().get_js()
        assert "tdBlotterData" in js, \
            "stress tab switch must use tdBlotterData as last-resort gauge hint"
        assert "tdBlotterData[0].gauge_id" in js, \
            "stress tab must use first blotter trade gauge when filter and market gauge are absent"

    def test_hint_applied_before_fallback(self):
        """Hint selection must happen before the 'first with trades' fallback."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        idx_hint = js.find('sel.value = hint')
        idx_fallback = js.find('withTrades')
        assert idx_hint > 0, "sel.value = hint assignment must exist"
        assert idx_fallback > idx_hint, \
            "'withTrades' fallback must come AFTER hint selection, not before"

    def test_fallback_only_when_hint_not_matched(self):
        """'First with trades' fallback must only run when sel.value is still empty."""
        from visual.interactivity.trading import stress
        js = stress.get_js()
        assert "if (!sel.value && tdStressGauges.length > 0)" in js, \
            "Fallback must be guarded by !sel.value — must not override a valid hint"

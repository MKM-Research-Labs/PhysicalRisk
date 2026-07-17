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

"""Tests for Classifiers tab (Tab 9) JavaScript rendering."""

import pytest


class TestClassifiersSubmodule:
    """The classifiers sub-module renders and exposes required public API."""

    @pytest.fixture(scope='class')
    def cl_js(self):
        from visual.interactivity.trading import classifiers
        return classifiers.get_js()

    @pytest.fixture(scope='class')
    def full_js(self):
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        return TradingDeskPanel().get_js()

    def test_classifiers_renders(self, cl_js):
        """classifiers.get_js() returns non-empty string."""
        assert len(cl_js) > 0

    def test_has_create_view(self, cl_js):
        """'createClassifiersView' builds the Tab 9 DOM."""
        assert 'createClassifiersView' in cl_js

    def test_has_load_data(self, cl_js):
        """'loadClassifiersData' fetches summary on tab open."""
        assert 'loadClassifiersData' in cl_js

    def test_has_render_summary_table(self, cl_js):
        """'_clRenderSummaryTable' renders the all-gauge table."""
        assert '_clRenderSummaryTable' in cl_js

    def test_has_render_detail(self, cl_js):
        """'_clRenderDetail' renders single-gauge detail panel."""
        assert '_clRenderDetail' in cl_js

    def test_has_metric_card(self, cl_js):
        """'_clMetricCard' builds metric display cards."""
        assert '_clMetricCard' in cl_js

    def test_has_feature_chart(self, cl_js):
        """'_clRenderFeatureChart' renders feature importance bar chart."""
        assert '_clRenderFeatureChart' in cl_js

    def test_has_cleanup(self, cl_js):
        """'clCleanupCharts' destroys Chart.js instances."""
        assert 'clCleanupCharts' in cl_js

    def test_has_single_training(self, cl_js):
        """'_clStartSingleTraining' triggers per-gauge training."""
        assert '_clStartSingleTraining' in cl_js

    def test_has_batch_training(self, cl_js):
        """'_clStartBatchTraining' triggers train-all."""
        assert '_clStartBatchTraining' in cl_js

    def test_has_progress_bar(self, cl_js):
        """'_clUpdateProgress' updates the batch progress bar."""
        assert '_clUpdateProgress' in cl_js

    def test_state_vars(self, cl_js):
        """Module-level state variables must be declared."""
        assert 'clSummary' in cl_js
        assert 'clSelectedGaugeId' in cl_js
        assert 'clFeatureChart' in cl_js
        assert 'clBatchPollTimer' in cl_js


class TestClassifiersEndpoints:
    """Correct API endpoint URLs appear in the rendered JS."""

    @pytest.fixture(scope='class')
    def cl_js(self):
        from visual.interactivity.trading import classifiers
        return classifiers.get_js()

    def test_summary_endpoint(self, cl_js):
        assert '/api/v1/trading/classifiers/summary' in cl_js

    def test_train_endpoint(self, cl_js):
        assert '/api/v1/trading/stress/train/' in cl_js

    def test_status_endpoint(self, cl_js):
        assert '/api/v1/trading/stress/classifier-status/' in cl_js

    def test_train_all_endpoint(self, cl_js):
        assert '/api/v1/trading/classifiers/train-all' in cl_js


class TestClassifiersInPanel:
    """Tab 9 is correctly wired into the Trading Desk panel."""

    @pytest.fixture(scope='class')
    def full_js(self):
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel
        return TradingDeskPanel().get_js()

    def test_classifiers_tab_in_array(self, full_js):
        """Tab button array includes classifiers."""
        assert "'classifiers'" in full_js or '"classifiers"' in full_js

    def test_classifiers_view_created(self, full_js):
        """createClassifiersView() called in panel setup."""
        assert 'createClassifiersView()' in full_js

    def test_classifiers_in_views_array(self, full_js):
        """'classifiers' included in switchTab views array."""
        assert "'classifiers'" in full_js

    def test_classifiers_switch_handler(self, full_js):
        """switchTab calls loadClassifiersData."""
        assert 'loadClassifiersData()' in full_js

    def test_classifiers_cleanup(self, full_js):
        """hidePanel calls clCleanupCharts."""
        assert 'clCleanupCharts' in full_js

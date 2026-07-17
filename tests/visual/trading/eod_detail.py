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

"""Detailed regression tests for EOD tab (td_eod.py) JS generation.

Protects against regressions in EOD submit, history display,
chart rendering, and P&L attribution.
"""

import pytest


@pytest.fixture(scope='module')
def eod_js():
    """Get EOD tab JS once for all tests."""
    from visual.interactivity.trading import eod
    return eod.get_js()


class TestEODEndpoints:
    """EOD tab must fetch from correct endpoints."""

    def test_eod_submit_endpoint(self, eod_js):
        """Hits /api/v1/trading/eod for submit."""
        assert '/api/v1/trading/eod' in eod_js

    def test_eod_history_fetch(self, eod_js):
        """Fetches /api/v1/trading/eod/history."""
        assert '/api/v1/trading/eod/history' in eod_js

    def test_eod_pnl_series_fetch(self, eod_js):
        """Fetches /api/v1/trading/pnl-series."""
        assert '/api/v1/trading/pnl-series' in eod_js

    def test_eod_blotter_fetch(self, eod_js):
        """Also fetches blotter for live summary."""
        assert '/api/v1/trading/blotter' in eod_js


class TestEODFunctions:
    """Core EOD functions must exist."""

    def test_submit_function(self, eod_js):
        """tdSubmitEod function exists."""
        assert 'tdSubmitEod' in eod_js

    def test_download_pdf_function(self, eod_js):
        """tdDownloadEodPdf function exists."""
        assert 'tdDownloadEodPdf' in eod_js

    def test_chart_rendering(self, eod_js):
        """renderEodChart function exists."""
        assert 'renderEodChart' in eod_js

    def test_attribution_section(self, eod_js):
        """renderEodAttribution function exists."""
        assert 'renderEodAttribution' in eod_js

    def test_cleanup_function(self, eod_js):
        """tdCleanupEodCharts exists for chart cleanup."""
        assert 'tdCleanupEodCharts' in eod_js


class TestEODUIStructure:
    """EOD tab UI elements must be present."""

    def test_submit_button(self, eod_js):
        """Submit EOD button present."""
        assert 'td-eod-submit-btn' in eod_js
        assert 'EOD Submit' in eod_js

    def test_date_input(self, eod_js):
        """Date picker for EOD date."""
        assert 'td-eod-date' in eod_js

    def test_cards_container(self, eod_js):
        """P&L summary cards container present."""
        assert 'td-eod-cards' in eod_js

    def test_history_wrap(self, eod_js):
        """EOD History section present."""
        assert 'td-eod-history-wrap' in eod_js
        assert 'EOD History' in eod_js

    def test_attribution_wrap(self, eod_js):
        """Attribution section container present."""
        assert 'td-eod-attribution' in eod_js

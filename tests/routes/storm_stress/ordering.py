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

"""Tests that the worst-case storm (highest peak_level_m) is first in the list."""

import json


class TestPeakOrdering:
    """The worst-case storm (highest peak_level_m) must be first in the list.
    Both the Historical tab (top of list = most prominent) and the Stress tab
    (auto-selects storms[0]) depend on this ordering.
    """

    def test_storms_sorted_worst_first(self, integration_env):
        """GET /trading/stress/storms returns storms sorted by peak_level_m DESC."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        assert len(storms) >= 2
        peaks = [s['peak_level_m'] for s in storms]
        assert peaks == sorted(peaks, reverse=True), \
            "Storms must be sorted by peak_level_m DESC — " \
            "first storm is auto-selected in Stress tab and shown first in Historical list"

    def test_worst_storm_is_first(self, integration_env):
        """storms[0] must have the highest peak_level_m."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        if len(storms) >= 2:
            assert storms[0]['peak_level_m'] >= storms[-1]['peak_level_m']

    def test_severe_storm_alpha_is_first(self, integration_env):
        """STORM-SEVERE-001 (peak 6.5m) should come before STORM-MODERATE-002 (4.8m)."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        storm_ids = [s['storm_id'] for s in storms]
        severe_idx = storm_ids.index('STORM-SEVERE-001')
        moderate_idx = storm_ids.index('STORM-MODERATE-002')
        assert severe_idx < moderate_idx, \
            "Severe storm (peak 6.5m) must appear before moderate storm (peak 4.8m)"

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

"""Tests that all fields needed to render the Historical tab storm list are present."""

import json


class TestScenarioVisuiserFields:
    """All fields needed to render the Historical tab storm list must be
    present in the GET /trading/stress/storms response.
    """

    def test_storm_list_has_name(self, integration_env):
        """'name' field — shown in storm row title."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'name' in s, f"Storm {s.get('storm_id')} missing 'name' field"

    def test_storm_list_has_intensity_category(self, integration_env):
        """'intensity_category' field — colour-coded in storm row."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'intensity_category' in s

    def test_storm_list_has_gauges_severe(self, integration_env):
        """'gauges_severe' field — severity indicator in storm row."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'gauges_severe' in s

    def test_storm_list_has_effective_precipitation_mm(self, integration_env):
        """'effective_precipitation_mm' field — shown in storm row."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'effective_precipitation_mm' in s

    def test_storm_list_has_peak_level_m(self, integration_env):
        """'peak_level_m' field — primary sort key and shown in Trading Desk label."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'peak_level_m' in s

    def test_storm_list_has_max_trigger(self, integration_env):
        """'max_trigger' field — used for trigger colour coding in Historical list."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'max_trigger' in s

    def test_storm_list_has_base_level_m(self, integration_env):
        """'base_level_m' field — used in Stress tab storm info bar."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'base_level_m' in s

    def test_storm_list_has_level_change_m(self, integration_env):
        """'level_change_m' field — used in Stress tab storm info bar."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'level_change_m' in s

    def test_storm_list_has_duration_hours(self, integration_env):
        """'duration_hours' field — used in Stress tab storm info bar."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'duration_hours' in s

    def test_storm_list_has_peak_position(self, integration_env):
        """'peak_position' field — used in hydrograph synthesis."""
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        storms = json.loads(resp.data)['storms']
        for s in storms:
            assert 'peak_position' in s

# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for hydrograph data sourcing (gaugets) and the production synthesis function."""

import json
from unittest.mock import MagicMock, patch


class TestGaugetsHydrographIntegration:
    """The stress run builds the hydrograph from gaugets data when available.
    gaugets files may use either 'waterLevel' or 'level' as the reading field.
    Both must be handled correctly to avoid zero-amplitude hydrographs.
    """

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_gaugets_waterlevel_field(self, mock_pred, integration_env):
        """gaugets readings using 'waterLevel' key are correctly extracted."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {'gauges': []}
        mock_pred.return_value = pred

        readings = [{'timestamp': f'2024-01-01T{h:02d}:00:00', 'waterLevel': 3.0 + h * 0.1}
                    for h in range(48)]
        gaugets_file = integration_env['gaugets_dir'] / 'GAUGE-001.json'
        gaugets_file.write_text(json.dumps({
            'gauge_id': 'GAUGE-001',
            'flood_simulation': {'readings': readings},
        }))

        client = integration_env['client']
        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001',
                                 'storm_id': 'STORM-SEVERE-001'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        water_levels = [h['water_level'] for h in data['hourly']]
        assert max(water_levels) > min(water_levels), \
            "Hydrograph from gaugets (waterLevel field) must show water level variation"
        assert data['hydrograph_source'].startswith('Gauge response'), \
            "hydrograph_source must indicate gaugets data was used"

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_gaugets_level_field_fallback(self, mock_pred, integration_env):
        """gaugets readings using 'level' key (alternate field name) are extracted."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {'gauges': []}
        mock_pred.return_value = pred

        readings = [{'timestamp': f'2024-01-01T{h:02d}:00:00', 'level': 3.0 + h * 0.12}
                    for h in range(48)]
        gaugets_file = integration_env['gaugets_dir'] / 'GAUGE-001.json'
        gaugets_file.write_text(json.dumps({
            'gauge_id': 'GAUGE-001',
            'flood_simulation': {'readings': readings},
        }))

        client = integration_env['client']
        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001',
                                 'storm_id': 'STORM-SEVERE-001'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        water_levels = [h['water_level'] for h in data['hourly']]
        assert max(water_levels) > min(water_levels), \
            "Hydrograph from gaugets (level field) must show variation — " \
            "'level' field fallback not working"

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_missing_gaugets_returns_404(self, mock_pred, integration_env):
        """When no gaugets file exists, stress run returns 404.

        Stress scenarios are tail events requiring real timeseries data.
        """
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {'gauges': []}
        mock_pred.return_value = pred

        gaugets_file = integration_env['gaugets_dir'] / 'GAUGE-001.json'
        if gaugets_file.exists():
            gaugets_file.unlink()

        client = integration_env['client']
        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001',
                                 'storm_id': 'STORM-SEVERE-001'})
        data = json.loads(resp.data)
        assert resp.status_code == 404, \
            "Stress run must fail when gaugets data is missing"
        assert "No gaugets data" in data.get('message', '')


class TestActualHydrographFunction:
    """Tests against the actual production function in routes.trading.stress,
    not a local copy.  This catches discrepancies like the default num_hours
    being 60 in tests vs 168 in production.
    """

    def test_actual_function_returns_168_hours(self):
        """_synthesize_hydrograph default returns 168 hours (STORM_HOURS constant)."""
        from routes.trading.stress._helpers import _synthesize_hydrograph, STORM_HOURS
        assert STORM_HOURS == 168, \
            "STORM_HOURS constant must be 168 (7-day industry standard storm window)"
        levels = _synthesize_hydrograph(
            base_level=3.0, level_change=2.0,
            duration_hours=24, peak_position=0.4
        )
        assert len(levels) == 168, \
            f"Production _synthesize_hydrograph must return 168 hours, got {len(levels)}"

    def test_actual_function_starts_at_base(self):
        """Production function: hour 0 = base_level."""
        from routes.trading.stress._helpers import _synthesize_hydrograph
        levels = _synthesize_hydrograph(3.0, 2.0, 24, 0.4)
        assert abs(levels[0] - 3.0) < 0.01

    def test_actual_function_reaches_peak(self):
        """Production function: peak ≈ base + level_change."""
        from routes.trading.stress._helpers import _synthesize_hydrograph
        base, change = 3.0, 2.0
        levels = _synthesize_hydrograph(base, change, 24, 0.4)
        assert max(levels) >= base + change * 0.9, \
            "Peak must reach ≥ 90% of expected base + level_change"

    def test_actual_function_decays_after_peak(self):
        """Production function: levels decay back toward base after peak."""
        from routes.trading.stress._helpers import _synthesize_hydrograph
        levels = _synthesize_hydrograph(3.0, 2.0, 24, 0.3)
        peak_idx = levels.index(max(levels))
        if peak_idx < 150:
            assert levels[-1] < max(levels), \
                "Levels must decay after peak — check exp(-3t) decay formula"

    def test_peak_hour_matches_peak_position(self):
        """Peak occurs near duration_hours * peak_position."""
        from routes.trading.stress._helpers import _synthesize_hydrograph
        duration, pos = 48, 0.4
        levels = _synthesize_hydrograph(3.0, 2.0, duration, pos)
        expected_peak_hour = int(duration * pos)
        actual_peak_hour = levels.index(max(levels))
        assert abs(actual_peak_hour - expected_peak_hour) <= 2, \
            f"Peak at H{actual_peak_hour} but expected near H{expected_peak_hour}"

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

"""
Unit tests for port.src.gauge.gaugets — part 2.

Covers convenience function, DateTimeEncoder, and __main__ block.
"""

import json

import pytest

import database


# ===========================================================================
# Convenience function  (lines 236-237)
# ===========================================================================

class TestGenerateGaugetsConvenience:

    def test_generate_gaugets_calls_generator(self, tmp_path):
        """Lines 236-237: generate_gaugets() instantiates generator and calls generate()."""
        from unittest.mock import MagicMock, patch
        from port.src.gauge.gaugets import generate_gaugets

        mock_gen = MagicMock()
        mock_gen.generate.return_value = {
            'data': {'time_series': [], 'num_gauges': 5, 'num_timesteps': 168},
            'catchment': 'thames',
            'simulation_parameters': {},
        }
        with patch('port.src.gauge.gaugets.GaugeTimeSeriesGenerator', return_value=mock_gen):
            result = generate_gaugets(simulation_hours=48)
        mock_gen.generate.assert_called_once_with(48)
        assert result['data']['num_gauges'] == 5


# ===========================================================================
# DateTimeEncoder in gaugets module  (lines 71-79)
# ===========================================================================

class TestGaugetsDateTimeEncoder:

    def test_encodes_datetime(self):
        """Line 72: datetime -> isoformat string."""
        from port.src.gauge.gaugets import DateTimeEncoder
        from datetime import datetime
        result = json.dumps({"d": datetime(2026, 1, 1)}, cls=DateTimeEncoder)
        assert "2026-01-01" in result

    def test_encodes_numpy_integer(self):
        """Lines 73-74: np.integer -> int."""
        import numpy as np
        from port.src.gauge.gaugets import DateTimeEncoder
        result = json.dumps({"n": np.int64(42)}, cls=DateTimeEncoder)
        assert "42" in result

    def test_encodes_numpy_float32(self):
        """Lines 75-76: np.float32 is np.floating but not Python float -> default() called."""
        import numpy as np
        from port.src.gauge.gaugets import DateTimeEncoder
        result = json.dumps({"f": np.float32(2.5)}, cls=DateTimeEncoder)
        assert "2.5" in result

    def test_encodes_numpy_ndarray(self):
        """Lines 77-78: np.ndarray -> list via tolist()."""
        import numpy as np
        from port.src.gauge.gaugets import DateTimeEncoder
        result = json.dumps({"a": np.array([1.0, 2.0])}, cls=DateTimeEncoder)
        assert "1.0" in result

    def test_fallback_raises_for_unknown(self):
        """Line 79: unknown type -> super().default() -> TypeError."""
        from port.src.gauge.gaugets import DateTimeEncoder
        with pytest.raises(TypeError):
            json.dumps({"x": object()}, cls=DateTimeEncoder)


# ===========================================================================
# __main__ block  (lines 241-244)
# ===========================================================================

class TestGaugetsMain:

    def test_main_block(self, tmp_path):
        """The __main__ block runs generate_gaugets(168) and writes per-gauge timeseries.

        The tmp_catchment backend (rooted at tmp_path) supplies the gauge read and
        receives the per-gauge timeseries writes through ``database``.
        """
        import runpy
        from db_helpers import test_backend, tmp_catchment

        gauge_portfolio = {
            'flood_gauges': [{
                'FloodGauge': {
                    'Header': {'GaugeID': 'GAUGE-test0001', 'GaugeName': 'Test'},
                    'SensorDetails': {'GaugeInformation': {
                        'GaugeLatitude': 51.5, 'GaugeLongitude': -0.1,
                    }},
                    'FloodStage': {'UK': {'FloodAlert': 4.5}},
                }
            }]
        }

        with tmp_catchment(tmp_path):
            database.save_gauges(database.active_catchment(), gauge_portfolio)
            try:
                runpy.run_module('port.src.gauge.gaugets', run_name='__main__')
            except SystemExit:
                pass
            # Per-gauge timeseries were written -> __main__ block executed
            assert list(database.iter_gauge_timeseries_ids(database.active_catchment()))
        # On the file backend the per-gauge timeseries land physically under
        # tmp_path/gaugets; on pg they are rows, so the seam assertion above is
        # the cross-backend proof and this file check is file-only.
        if test_backend() != "pg":
            assert (tmp_path / 'gaugets').exists()

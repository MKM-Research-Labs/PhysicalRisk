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
Unit tests for port.src.gauge.gaugets — GaugeTimeSeriesGenerator.

Covers default simulation duration (168 hours), parameter defaults,
generate() output structure, and the gaugets_random fallback defaults.
"""

import json

import pytest


# ===========================================================================
# Default parameter values
# ===========================================================================

class TestGaugeTimeSeriesDefaults:

    def test_default_simulation_hours_is_168(self):
        """DEFAULT_PARAMS and generate() default must both be 168 hours (7 days).
        Regression: was hardcoded to 60 / 72, showing only ~63 readings."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        assert GaugeTimeSeriesGenerator.DEFAULT_PARAMS["simulation_hours"] == 168

    def test_generate_default_argument_is_168(self):
        """generate(simulation_hours) default parameter must be 168."""
        import inspect
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        sig = inspect.signature(GaugeTimeSeriesGenerator.generate)
        default = sig.parameters["simulation_hours"].default
        assert default == 168, f"Expected 168, got {default}"

    def test_generate_gaugets_function_default_is_168(self):
        """Convenience function generate_gaugets() default must be 168."""
        import inspect
        from port.src.gauge.gaugets import generate_gaugets
        sig = inspect.signature(generate_gaugets)
        default = sig.parameters["simulation_hours"].default
        assert default == 168, f"Expected 168, got {default}"

    def test_peak_hour_max_within_simulation_window(self):
        """peak_hour_max must be strictly less than simulation_hours."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        p = GaugeTimeSeriesGenerator.DEFAULT_PARAMS
        assert p["peak_hour_max"] < p["simulation_hours"], (
            f"peak_hour_max ({p['peak_hour_max']}) must be < "
            f"simulation_hours ({p['simulation_hours']})"
        )

    def test_peak_hour_min_less_than_max(self):
        """peak_hour_min must be less than peak_hour_max."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        p = GaugeTimeSeriesGenerator.DEFAULT_PARAMS
        assert p["peak_hour_min"] < p["peak_hour_max"]


# ===========================================================================
# gaugets_random DEFAULT_PARAMS
# ===========================================================================

class TestGaugetsRandomDefaults:

    def test_random_default_simulation_hours_is_168(self):
        """gaugets_random.DEFAULT_PARAMS simulation_hours must be 168."""
        from port.rand.thames.gauge.gaugets_random import DEFAULT_PARAMS
        assert DEFAULT_PARAMS["simulation_hours"] == 168, (
            f"Expected 168, got {DEFAULT_PARAMS['simulation_hours']}"
        )

    def test_random_default_peak_hour_max_within_window(self):
        """Random module peak_hour_max must be < simulation_hours."""
        from port.rand.thames.gauge.gaugets_random import DEFAULT_PARAMS
        assert DEFAULT_PARAMS["peak_hour_max"] < DEFAULT_PARAMS["simulation_hours"]


# ===========================================================================
# Generated output has correct reading count
# ===========================================================================

class TestGaugeTimeSeriesGenerate:

    def test_explicit_168_hours_produces_168_readings(self, tmp_path):
        """generate(168) should produce ~168 readings per gauge."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(simulation_hours=168)

        gaugets_dir = tmp_path / "gaugets"
        files = list(gaugets_dir.glob("GAUGE-*.json"))
        assert len(files) > 0, "No gaugets files generated"

        for f in files:
            data = json.loads(f.read_text())
            sim = data.get("flood_simulation", {})
            assert sim.get("simulation_hours") == 168, (
                f"{f.name}: simulation_hours is {sim.get('simulation_hours')}, expected 168"
            )
            readings = sim.get("readings", [])
            # Should have approximately 168 readings (one per hour)
            assert len(readings) >= 160, (
                f"{f.name}: only {len(readings)} readings for 168h simulation"
            )

    def test_explicit_60_hours_stores_60_in_metadata(self, tmp_path):
        """Explicit override stores the passed value in simulation_hours metadata."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(output_dir=tmp_path, verbose=False)
        gen.generate(simulation_hours=60)

        gaugets_dir = tmp_path / "gaugets"
        for f in gaugets_dir.glob("GAUGE-*.json"):
            data = json.loads(f.read_text())
            sim = data.get("flood_simulation", {})
            assert sim.get("simulation_hours") == 60

    def test_168_produces_more_readings_than_60(self, tmp_path):
        """168-hour simulation produces significantly more readings than 60-hour."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        import shutil

        gen60 = GaugeTimeSeriesGenerator(output_dir=tmp_path / "t60", verbose=False)
        gen60.generate(simulation_hours=60)

        gen168 = GaugeTimeSeriesGenerator(output_dir=tmp_path / "t168", verbose=False)
        gen168.generate(simulation_hours=168)

        files60 = list((tmp_path / "t60" / "gaugets").glob("GAUGE-*.json"))
        files168 = list((tmp_path / "t168" / "gaugets").glob("GAUGE-*.json"))

        assert files60 and files168
        count60 = len(json.loads(files60[0].read_text())["flood_simulation"]["readings"])
        count168 = len(json.loads(files168[0].read_text())["flood_simulation"]["readings"])
        assert count168 > count60, (
            f"168h ({count168} readings) should exceed 60h ({count60} readings)"
        )

    def test_simulation_hours_stored_in_output(self, tmp_path):
        """simulation_hours is written into each gaugets JSON."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(output_dir=tmp_path, verbose=False)
        gen.generate(simulation_hours=168)

        for f in (tmp_path / "gaugets").glob("GAUGE-*.json"):
            data = json.loads(f.read_text())
            assert "simulation_hours" in data["flood_simulation"]

    def test_configure_known_param(self, tmp_path):
        """Lines 127-130: configure() updates a known sim_param key."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(output_dir=tmp_path, verbose=False)
        gen.configure(simulation_hours=48)
        assert gen.sim_params['simulation_hours'] == 48

    def test_configure_unknown_param_ignored(self, tmp_path):
        """Lines 127-129: unknown key is silently ignored (if branch is False)."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(output_dir=tmp_path, verbose=False)
        gen.configure(nonexistent_param=999)
        assert 'nonexistent_param' not in gen.sim_params

    def test_missing_gauge_file_raises(self, tmp_path):
        """Lines 157-159: gauge.json absent → FileNotFoundError re-raised."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        from unittest.mock import patch
        from config import config as cfg
        gen = GaugeTimeSeriesGenerator(output_dir=tmp_path, verbose=False)
        # Point get_input_path to a non-existent file
        with patch.object(cfg, 'get_input_path', return_value=tmp_path / 'no_gauge.json'):
            with pytest.raises(FileNotFoundError):
                gen.generate(simulation_hours=10)

    def test_stale_gauge_files_removed(self, tmp_path):
        """Line 175: stale GAUGE-*.json files in gaugets/ are deleted before writing."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        # Pre-create a stale file in the gaugets directory
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir(parents=True)
        stale = gaugets_dir / "GAUGE-stale1234.json"
        stale.write_text('{"stale": true}')
        assert stale.exists()

        gen = GaugeTimeSeriesGenerator(output_dir=tmp_path, verbose=False)
        gen.generate(simulation_hours=10)

        # Stale file must have been removed (line 175 executed)
        assert not stale.exists()


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
            'file_path': tmp_path / 'gaugets',
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
        """Line 72: datetime → isoformat string."""
        from port.src.gauge.gaugets import DateTimeEncoder
        from datetime import datetime
        result = json.dumps({"d": datetime(2026, 1, 1)}, cls=DateTimeEncoder)
        assert "2026-01-01" in result

    def test_encodes_numpy_integer(self):
        """Lines 73-74: np.integer → int."""
        import numpy as np
        from port.src.gauge.gaugets import DateTimeEncoder
        result = json.dumps({"n": np.int64(42)}, cls=DateTimeEncoder)
        assert "42" in result

    def test_encodes_numpy_float32(self):
        """Lines 75-76: np.float32 is np.floating but not Python float → default() called."""
        import numpy as np
        from port.src.gauge.gaugets import DateTimeEncoder
        result = json.dumps({"f": np.float32(2.5)}, cls=DateTimeEncoder)
        assert "2.5" in result

    def test_encodes_numpy_ndarray(self):
        """Lines 77-78: np.ndarray → list via tolist()."""
        import numpy as np
        from port.src.gauge.gaugets import DateTimeEncoder
        result = json.dumps({"a": np.array([1.0, 2.0])}, cls=DateTimeEncoder)
        assert "1.0" in result

    def test_fallback_raises_for_unknown(self):
        """Line 79: unknown type → super().default() → TypeError."""
        from port.src.gauge.gaugets import DateTimeEncoder
        with pytest.raises(TypeError):
            json.dumps({"x": object()}, cls=DateTimeEncoder)


# ===========================================================================
# __main__ block  (lines 241-244)
# ===========================================================================

class TestGaugetsMain:

    def test_main_block(self, tmp_path):
        """Lines 241-244: __main__ block runs generate_gaugets(168) and logs results.

        GaugeTimeSeriesGenerator is redefined in runpy's fresh namespace, so it cannot
        be patched via sys.modules.  Instead patch the config singleton methods that the
        generator uses: get_input_dir (for output) and get_input_path (for reading
        gauge.json).  A minimal gauge.json is written to tmp_path first.
        """
        import runpy
        from unittest.mock import patch
        from config import config as cfg

        gauge_json = tmp_path / 'gauge.json'
        gauge_json.write_text(json.dumps({
            'flood_gauges': [{
                'FloodGauge': {
                    'Header': {'GaugeID': 'GAUGE-test0001', 'GaugeName': 'Test'},
                    'SensorDetails': {'GaugeInformation': {
                        'GaugeLatitude': 51.5, 'GaugeLongitude': -0.1,
                    }},
                    'FloodStage': {'UK': {'FloodAlert': 4.5}},
                }
            }]
        }))

        with patch.object(cfg, 'get_input_dir', return_value=tmp_path), \
             patch.object(cfg, 'get_input_path', return_value=gauge_json):
            try:
                runpy.run_module('port.src.gauge.gaugets', run_name='__main__')
            except SystemExit:
                pass
        # Per-gauge files were written → __main__ block executed
        assert (tmp_path / 'gaugets').exists()

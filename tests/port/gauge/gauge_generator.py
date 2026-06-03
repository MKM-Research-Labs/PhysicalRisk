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
Unit tests for GaugePortfolioGenerator end-to-end.
"""

import json
import re

import pytest

from port.cdm import FloodGaugeCDM
from port.src.gauge import GaugePortfolioGenerator


class TestDateTimeEncoder:
    """Lines 56-64: DateTimeEncoder branches."""

    def test_encodes_datetime(self):
        from port.src.gauge.gauge import DateTimeEncoder
        import json
        from datetime import datetime
        result = json.dumps({"d": datetime(2026, 1, 1)}, cls=DateTimeEncoder)
        assert "2026-01-01" in result

    def test_encodes_numpy_integer(self):
        from port.src.gauge.gauge import DateTimeEncoder
        import json, numpy as np
        result = json.dumps({"n": np.int64(42)}, cls=DateTimeEncoder)
        assert "42" in result

    def test_encodes_numpy_floating(self):
        from port.src.gauge.gauge import DateTimeEncoder
        import json, numpy as np
        result = json.dumps({"f": np.float64(3.14)}, cls=DateTimeEncoder)
        assert "3.14" in result

    def test_encodes_numpy_float32(self):
        """Line 80: np.float32 is np.floating but NOT a Python float subclass in NumPy 2.x,
        so the JSON encoder cannot handle it natively and must call default()."""
        from port.src.gauge.gauge import DateTimeEncoder
        import json, numpy as np
        result = json.dumps({"f": np.float32(2.5)}, cls=DateTimeEncoder)
        assert "2.5" in result

    def test_encodes_numpy_ndarray(self):
        from port.src.gauge.gauge import DateTimeEncoder
        import json, numpy as np
        result = json.dumps({"a": np.array([1.0, 2.0])}, cls=DateTimeEncoder)
        assert "1.0" in result

    def test_fallback_raises_for_unknown(self):
        from port.src.gauge.gauge import DateTimeEncoder
        import json
        with pytest.raises(TypeError):
            json.dumps({"x": object()}, cls=DateTimeEncoder)


@pytest.mark.generator
class TestGaugeGeneratorOutput:

    def test_generate_returns_expected_keys(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        assert "data" in result
        assert "file_path" in result
        assert "processing_stats" in result

    def test_generate_correct_count(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        # Catchment-agnostic: count is capped to the catchment's available
        # gauge points (thames has 52, halong only 3).
        expected = min(5, len(gen.params.GAUGE_POINTS))
        result = gen.generate(count=5)
        assert len(result["data"]["flood_gauges"]) == expected

    def test_gauge_ids_unique(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=10)
        ids = result["data"]["gauge_ids"]
        assert len(ids) == len(set(ids))

    def test_gauge_id_format(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        for gid in result["data"]["gauge_ids"]:
            assert re.match(r"^GAUGE-[a-f0-9]{8}$", gid)

    def test_locations_have_coordinates(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        for loc in result["data"]["locations"]:
            assert "lat" in loc
            assert "lon" in loc
            assert "elevation" in loc


@pytest.mark.generator
class TestGaugeGeneratorFile:

    def test_output_file_exists(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        assert result["file_path"].exists()

    def test_output_file_is_valid_json(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        with open(result["file_path"]) as f:
            data = json.load(f)
        assert "flood_gauges" in data

    def test_output_json_has_correct_count(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        expected = min(5, len(gen.params.GAUGE_POINTS))
        result = gen.generate(count=5)
        with open(result["file_path"]) as f:
            data = json.load(f)
        assert len(data["flood_gauges"]) == expected


@pytest.mark.generator
class TestGaugeGeneratorEdgeCases:

    def test_count_zero_raises_value_error(self, tmp_path):
        """Line 155-156: count < 1 raises ValueError."""
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        with pytest.raises(ValueError):
            gen.generate(count=0)

    def test_count_exceeds_available_points_capped(self, tmp_path):
        """Lines 159-162: count > max_gauges → capped to max_gauges."""
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        max_available = len(gen.params.GAUGE_POINTS)
        result = gen.generate(count=max_available + 100)
        assert len(result["data"]["flood_gauges"]) == max_available

    def test_generate_gauges_convenience_function(self, tmp_path):
        """Lines 354-355: generate_gauges() convenience function."""
        from port.src.gauge.gauge import generate_gauges
        result = generate_gauges(count=3, output_dir=tmp_path)
        assert "data" in result
        assert len(result["data"]["flood_gauges"]) == 3

    def test_verbose_false_sets_warning_level(self, tmp_path):
        """Lines 99-100: verbose=False sets logger to WARNING."""
        import logging
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        assert logging.getLogger("port.src.gauge.gauge").level == logging.WARNING

    def test_log_method_works(self, tmp_path):
        """Lines 122-125: log() dispatches to correct logger method."""
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        gen.log("test message", "WARNING")   # should not raise

    def test_build_section_non_dict_schema_returns_empty(self, tmp_path):
        """Line 290: non-dict section_schema returns {}."""
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen._build_section("not_a_dict", 0, {})
        assert result == {}

    def test_build_section_skips_metadata_keys(self, tmp_path):
        """Line 294: 'type', 'options', 'description', 'values' keys are skipped."""
        from unittest.mock import patch
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        schema = {
            "type": "object",
            "options": ["A", "B"],
            "description": "A gauge field",
            "values": [1, 2, 3],
        }
        # Only skip-keys: _build_section should produce empty dict
        with patch.object(gen, 'random') as mock_random:
            mock_random.generate_field_value.return_value = "x"
            result = gen._build_section(schema, 0, {})
        for skip in ("type", "options", "description", "values"):
            assert skip not in result

    def test_generate_single_gauge_failure_counted(self, tmp_path):
        """Lines 212-215: exception in _generate_single_gauge increments failed_gauges."""
        from unittest.mock import patch, MagicMock
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        # Patch random to raise on generate_gauge_metadata
        original_random = gen.random
        mock_random = MagicMock()
        mock_random.generate_gauge_metadata.side_effect = RuntimeError("test error")
        gen.random = mock_random
        # generate with count=1, expect the failure to be logged not raised
        result = gen.generate(count=1)
        assert result["processing_stats"]["failed_gauges"] == 1
        gen.random = original_random

    def test_set_specific_values_creates_missing_sections(self, tmp_path):
        """Lines 309-327: missing FloodGauge/Header/Location/FloodStages are created."""
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        gauge_data = {}  # all sections missing
        metadata = {
            "location": {"lat": 51.5, "lon": -0.1, "elevation": 7.0},
            "flood_alert": 3.5,
            "flood_warning": 4.5,
            "severe_flood_warning": 5.5,
            "historical_high_level": 6.0,
            "historical_high_date": "2014-02-10",
        }
        gen._set_specific_gauge_values(gauge_data, "GAUGE-test0001", 0, metadata)
        assert gauge_data["FloodGauge"]["Header"]["GaugeID"] == "GAUGE-test0001"
        assert gauge_data["FloodGauge"]["Location"]["GaugeLatitude"] == 51.5


@pytest.mark.generator
class TestGaugeGeneratorDataQuality:

    def test_flood_stages_ordering(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=10)
        cdm = FloodGaugeCDM()
        for gauge in result["data"]["flood_gauges"]:
            mapping = cdm.create_mapping(gauge)
            alert = mapping.get("flood_alert", 0)
            warning = mapping.get("flood_warning", 0)
            severe = mapping.get("severe_flood_warning", 0)
            if alert and warning and severe:
                assert alert < warning < severe

    def test_processing_stats(self, tmp_path):
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        expected = min(5, len(gen.params.GAUGE_POINTS))
        result = gen.generate(count=5)
        stats = result["processing_stats"]
        assert stats["successful_gauges"] == expected
        assert stats["failed_gauges"] == 0

    def test_second_generate_hits_end_time_branch(self, tmp_path):
        """Line 245: end_time is set by the first generate(); the second generate() call
        finds it truthy and serialises it (line 245 executed)."""
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        gen.generate(count=1)          # sets processing_stats['end_time']
        gen.generate(count=1)          # second call: end_time truthy → line 245

    def test_save_exception_propagates(self, tmp_path):
        """Lines 264-266: exception during json.dump is logged and re-raised."""
        from unittest.mock import patch
        gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
        with patch('port.src.gauge.gauge.json.dump', side_effect=IOError('disk full')):
            with pytest.raises(IOError):
                gen.generate(count=1)


@pytest.mark.generator
class TestGaugeGeneratorMain:

    def test_main_block(self, tmp_path):
        """Lines 378-381: __main__ block calls generate_gauges and logs results.
        config.get_input_dir is patched to redirect output to tmp_path."""
        import runpy
        import sys
        from unittest.mock import patch
        from config import config as cfg

        with patch.object(cfg, 'get_input_dir', return_value=tmp_path):
            try:
                runpy.run_module('port.src.gauge.gauge', run_name='__main__')
            except SystemExit:
                pass
        # gauge.json written to tmp_path by the __main__ block
        assert (tmp_path / 'gauge.json').exists()

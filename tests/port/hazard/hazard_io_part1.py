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
Tests for models.hazard.io — load_storms, load_gauges.
"""

import json

import pytest

from tests.port.hazard.conftest import _make_gauge_json, _make_storms_json


# ===========================================================================
# load_storms
# ===========================================================================

class TestLoadStorms:

    def test_loads_list(self, tmp_path):
        from models.hazard.io import load_storms
        p = tmp_path / "storms.json"
        p.write_text(json.dumps(_make_storms_json(5)))
        result = load_storms(p)
        assert isinstance(result, list)
        assert len(result) == 5

    def test_storm_has_id(self, tmp_path):
        from models.hazard.io import load_storms
        p = tmp_path / "storms.json"
        p.write_text(json.dumps(_make_storms_json(2)))
        result = load_storms(p)
        assert result[0]["storm_id"] == "STORM-0000"

    def test_file_not_found_raises(self, tmp_path):
        from models.hazard.io import load_storms
        with pytest.raises((FileNotFoundError, OSError)):
            load_storms(tmp_path / "missing.json")


# ===========================================================================
# load_gauges
# ===========================================================================

class TestLoadGauges:

    def test_loads_gauges(self, tmp_path):
        from models.hazard.io import load_gauges
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps(_make_gauge_json()))
        result = load_gauges(p)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_gauge_has_id(self, tmp_path):
        from models.hazard.io import load_gauges
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps(_make_gauge_json("GAUGE-999")))
        result = load_gauges(p)
        assert result[0]["gauge_id"] == "GAUGE-999"

    def test_empty_gauge_list_raises(self, tmp_path):
        from models.hazard.io import load_gauges
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps({"flood_gauges": []}))
        with pytest.raises(ValueError, match="No gauges found"):
            load_gauges(p)

    def test_file_not_found_raises(self, tmp_path):
        from models.hazard.io import load_gauges
        with pytest.raises((FileNotFoundError, OSError)):
            load_gauges(tmp_path / "missing.json")

    def test_gauge_without_gauge_id_raises(self, tmp_path):
        """Gauge that maps to no gauge_id raises ValueError."""
        from models.hazard.io import load_gauges
        # A gauge record with no Header/GaugeID -> CDM maps gauge_id to None
        bad_gauge = {
            "flood_gauges": [
                {
                    "FloodGauge": {
                        "Header": {},  # No GaugeID
                        "Location": {},
                        "SensorDetails": {"GaugeInformation": {}},
                        "SensorStats": {},
                        "NRFAMetadata": {},
                        "FloodStage": {},
                    }
                }
            ]
        }
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps(bad_gauge))
        with pytest.raises(ValueError, match="gauge_id"):
            load_gauges(p)

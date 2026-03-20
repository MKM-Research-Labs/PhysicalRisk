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

"""Tests for _extract_gauges, _parse_gauge, and _build_summary helpers."""

import pytest

from port.src.stressm.gauge_parser import _extract_gauges, _parse_gauge
from port.src.stressm.gaugets_writer import build_summary as _build_summary
from port.src.storm_multi.generators.batch_generator import generate_event_set

from .conftest import _G1, _G2


# ---------------------------------------------------------------------------
# _extract_gauges
# ---------------------------------------------------------------------------

class TestExtractGauges:

    def test_list_format(self):
        d = {"flood_gauges": [_G1, _G2]}
        result = _extract_gauges(d)
        assert result == [_G1, _G2]

    def test_dict_format(self):
        d = {"flood_gauges": {"g1": _G1, "g2": _G2}}
        result = _extract_gauges(d)
        assert len(result) == 2

    def test_empty_list(self):
        assert _extract_gauges({"flood_gauges": []}) == []

    def test_missing_key_returns_empty(self):
        assert _extract_gauges({}) == []


# ---------------------------------------------------------------------------
# _parse_gauge
# ---------------------------------------------------------------------------

class TestParseGauge:

    def test_valid_record_returns_dict(self):
        result = _parse_gauge(_G1)
        assert result is not None

    def test_gauge_id(self):
        assert _parse_gauge(_G1)["gauge_id"] == "GAUGE-test001"

    def test_lat_lon(self):
        r = _parse_gauge(_G1)
        assert r["lat"] == pytest.approx(51.46)
        assert r["lon"] == pytest.approx(-0.30)

    def test_flood_alert(self):
        assert _parse_gauge(_G1)["flood_alert"] == pytest.approx(3.5)

    def test_flood_warning(self):
        assert _parse_gauge(_G1)["flood_warning"] == pytest.approx(4.6)

    def test_severe_warning(self):
        assert _parse_gauge(_G1)["severe_warning"] == pytest.approx(5.5)

    def test_base_level_derived_from_alert(self):
        r = _parse_gauge(_G1)
        assert r["base_level"] == pytest.approx(3.5 * 0.35)

    def test_missing_gauge_id_returns_none(self):
        bad = {"FloodGauge": {
            "Header": {},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0},
        }}
        assert _parse_gauge(bad) is None

    def test_missing_lat_returns_none(self):
        bad = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-x"},
            "Location": {},
            "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0},
        }}
        assert _parse_gauge(bad) is None

    def test_missing_alert_returns_none(self):
        bad = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-x"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStages": {},
        }}
        assert _parse_gauge(bad) is None

    def test_warning_defaults_when_absent(self):
        rec = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-x"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStages": {"FloodAlert": 4.0},
        }}
        r = _parse_gauge(rec)
        assert r is not None
        assert r["flood_warning"] == pytest.approx(4.0 * 1.33)
        assert r["severe_warning"] == pytest.approx(4.0 * 1.58)


# ---------------------------------------------------------------------------
# _build_summary
# ---------------------------------------------------------------------------

class TestBuildSummary:

    def test_returns_required_keys(self):
        seqs = generate_event_set(count=5, seed=0)
        tc = {"isolated": 5}
        s = _build_summary(seqs, tc, gauge_params_list=[{"id": "x"}])
        for key in ("num_sequences", "num_gauges", "type_counts",
                    "alert_sequences", "warning_sequences", "severe_sequences",
                    "elapsed_seconds"):
            assert key in s

    def test_num_sequences(self):
        seqs = generate_event_set(count=7, seed=0)
        s = _build_summary(seqs, {}, gauge_params_list=[])
        assert s["num_sequences"] == 7

    def test_num_gauges(self):
        seqs = generate_event_set(count=3, seed=0)
        s = _build_summary(seqs, {}, gauge_params_list=[1, 2, 3, 4])
        assert s["num_gauges"] == 4

    def test_counts_default_to_zero(self):
        seqs = generate_event_set(count=3, seed=0)
        s = _build_summary(seqs, {}, gauge_params_list=[])
        assert s["alert_sequences"] == 0
        assert s["warning_sequences"] == 0
        assert s["severe_sequences"] == 0

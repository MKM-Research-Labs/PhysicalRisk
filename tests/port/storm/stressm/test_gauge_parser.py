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
Unit tests for gauge_parser.py — gauge JSON parsing and baseline loading.

Covers _load_gaugehd_baselines, _seasonal_base_level, and _parse_gauge
with historical baselines (gaugehd) and monthly seasonality.
"""

import pytest
from db_helpers import tmp_catchment

import database

_CATCHMENT = "thames"


@pytest.fixture
def seam_tmp(tmp_path):
    """Bind a scratch seam backend for gauge-history (gaugehd) reads."""
    with tmp_catchment(tmp_path, _CATCHMENT):
        yield


def _seed_gaugehd(key, gauge_id, mean=None, monthly=None):
    """Seed one gaugehd record into the seam (keyed on the gauge_{key}_hd id)."""
    stats = {}
    if mean is not None:
        stats["mean_level"] = mean
    if monthly is not None:
        stats["monthly_means"] = monthly
    database.save_gauge_history(_CATCHMENT, key, {
        "gauge_metadata": {"gauge_id": gauge_id},
        "statistics": stats,
    })


# ---------------------------------------------------------------------------
# _load_gaugehd_baselines
# ---------------------------------------------------------------------------

class TestLoadGaugehdBaselines:
    """Load historical water level baselines through the gauge-history seam."""

    def test_no_history(self, seam_tmp):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        assert _load_gaugehd_baselines() == {}

    def test_valid_gaugehd(self, seam_tmp):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        _seed_gaugehd("001", "GAUGE-001", mean=1.25,
                      monthly={"01": 1.4, "07": 0.9})
        baselines = _load_gaugehd_baselines()
        assert "GAUGE-001" in baselines
        assert baselines["GAUGE-001"]["mean_level"] == 1.25
        assert baselines["GAUGE-001"]["monthly_means"]["01"] == 1.4

    def test_multiple_gauges(self, seam_tmp):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        for i in range(3):
            _seed_gaugehd(f"{i:03d}", f"GAUGE-{i:03d}", mean=1.0 + i * 0.1)
        baselines = _load_gaugehd_baselines()
        assert len(baselines) == 3

    def test_corrupt_record_skipped(self, seam_tmp, monkeypatch):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        _seed_gaugehd("ok", "GAUGE-OK", mean=2.0)
        _seed_gaugehd("bad", "GAUGE-BAD", mean=3.0)
        real_get = database.get_gauge_history

        def flaky(catchment, key):
            if key == "bad":
                raise ValueError("corrupt record")
            return real_get(catchment, key)

        monkeypatch.setattr(database, "get_gauge_history", flaky)
        baselines = _load_gaugehd_baselines()
        assert len(baselines) == 1
        assert "GAUGE-OK" in baselines

    def test_missing_mean_level_skipped(self, seam_tmp):
        from port.src.stressm.gauge_parser import _load_gaugehd_baselines
        _seed_gaugehd("nolevel", "GAUGE-NOLEVEL")  # no mean_level
        assert _load_gaugehd_baselines() == {}


# ---------------------------------------------------------------------------
# _seasonal_base_level
# ---------------------------------------------------------------------------

class TestSeasonalBaseLevel:
    """Monthly base level selection with fallback to annual mean."""

    def test_with_monthly_means(self):
        from port.src.stressm.gauge_parser import _seasonal_base_level
        monthly = {"01": 1.5, "07": 0.8}
        assert _seasonal_base_level(monthly, mean_level=1.0, month=1) == 1.5
        assert _seasonal_base_level(monthly, mean_level=1.0, month=7) == 0.8

    def test_missing_month_falls_back(self):
        from port.src.stressm.gauge_parser import _seasonal_base_level
        monthly = {"01": 1.5}
        # March not in monthly_means → fall back to mean_level
        assert _seasonal_base_level(monthly, mean_level=1.0, month=3) == 1.0

    def test_no_monthly_means(self):
        from port.src.stressm.gauge_parser import _seasonal_base_level
        assert _seasonal_base_level(None, mean_level=1.0, month=6) == 1.0

    def test_empty_monthly_means(self):
        from port.src.stressm.gauge_parser import _seasonal_base_level
        assert _seasonal_base_level({}, mean_level=1.0, month=6) == 1.0


# ---------------------------------------------------------------------------
# _parse_gauge with baselines
# ---------------------------------------------------------------------------

class TestParseGaugeWithBaselines:
    """_parse_gauge using gaugehd historical baselines and monthly means."""

    def _make_gauge(self, gauge_id="GAUGE-001"):
        return {
            "FloodGauge": {
                "Header": {"GaugeID": gauge_id},
                "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
                "FloodStages": {
                    "FloodAlert": 3.5,
                    "FloodWarning": 4.6,
                    "SevereFloodWarning": 5.5,
                },
            }
        }

    def test_with_baseline(self):
        from port.src.stressm.gauge_parser import _parse_gauge
        baselines = {
            "GAUGE-001": {"mean_level": 1.25, "monthly_means": {"01": 1.4}},
        }
        result = _parse_gauge(self._make_gauge(), baselines)
        assert result["base_level"] == 1.25
        assert result["monthly_means"] == {"01": 1.4}

    def test_without_baseline_uses_heuristic(self):
        from port.src.stressm.gauge_parser import _parse_gauge
        result = _parse_gauge(self._make_gauge(), baselines={})
        assert result["base_level"] == pytest.approx(3.5 * 0.35)
        assert result["monthly_means"] is None

    def test_baseline_without_monthly_means(self):
        from port.src.stressm.gauge_parser import _parse_gauge
        baselines = {"GAUGE-001": {"mean_level": 1.5}}
        result = _parse_gauge(self._make_gauge(), baselines)
        assert result["base_level"] == 1.5
        assert result["monthly_means"] is None

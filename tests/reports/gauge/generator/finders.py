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

"""Tests for _find_gauge_by_id — flood_gauges, FloodGauge, list, not-found,
invalid type, and malformed entries."""

import pytest


class TestFindGaugeByIdAdditional:
    """Additional _find_gauge_by_id tests covering malformed entries
    and the 'FloodGauge' single-gauge path.
    """

    def test_flood_gauges_key_first_gauge(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "G-A"}}},
            {"FloodGauge": {"Header": {"GaugeID": "G-B"}}},
        ]}
        result = _find_gauge_by_id(data, "G-A")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-A"

    def test_flood_gauges_key_last_gauge(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "G-A"}}},
            {"FloodGauge": {"Header": {"GaugeID": "G-C"}}},
        ]}
        result = _find_gauge_by_id(data, "G-C")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-C"

    def test_malformed_entry_with_none_skipped(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            None,
            {"FloodGauge": {"Header": {"GaugeID": "G-OK"}}},
        ]}
        result = _find_gauge_by_id(data, "G-OK")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-OK"

    def test_malformed_entry_missing_flood_gauge_key_skipped(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            {"some_other_key": {}},
            {"FloodGauge": {"Header": {"GaugeID": "G-REAL"}}},
        ]}
        result = _find_gauge_by_id(data, "G-REAL")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-REAL"

    def test_single_flood_gauge_dict_returns_itself(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"FloodGauge": {"Header": {"GaugeID": "G-SINGLE"}}}
        result = _find_gauge_by_id(data, "G-SINGLE")
        assert result is data

    def test_integer_input_raises(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        with pytest.raises(ValueError):
            _find_gauge_by_id(123, "G-001")

    def test_string_input_raises(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        with pytest.raises(ValueError):
            _find_gauge_by_id("not-a-valid-input", "G-001")

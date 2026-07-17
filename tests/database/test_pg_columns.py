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

"""Unit tests for promoted-column extraction (WP1.6) — pure, no database."""

from database._pg._columns import promoted_columns


def test_extracts_nested_value():
    rec = {"FloodGauge": {"Location": {"GaugeLatitude": 51.5}}}
    assert promoted_columns("gauge", rec)["latitude"] == 51.5


def test_flat_path_for_dict_container_record():
    cols = promoted_columns("gauge_hazard_curve", {"gev_scale": 0.5, "gauge_name": "A"})
    assert cols["gev_scale"] == 0.5
    assert cols["gauge_name"] == "A"


def test_missing_key_yields_none():
    assert promoted_columns("gauge", {"FloodGauge": {}})["latitude"] is None


def test_non_dict_mid_path_yields_none():
    # 'latitude' = FloodGauge.Location.GaugeLatitude; here Location is not a dict.
    assert promoted_columns("gauge", {"FloodGauge": {"Location": "oops"}})["latitude"] is None


def test_unmapped_artifact_returns_empty_dict():
    assert promoted_columns("market_state", {"anything": 1}) == {}

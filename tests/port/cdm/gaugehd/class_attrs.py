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

"""Tests for GaugeHistoricalDaily class attributes and module flags."""

import port.cdm.gaugehd as mod
from port.cdm.gaugehd import GaugeHistoricalDaily


class TestGaugeHistoricalDailyInit:

    def test_cdm_available_flag_is_bool(self):
        assert hasattr(mod, "CDM_AVAILABLE")
        assert isinstance(mod.CDM_AVAILABLE, bool)


class TestClassAttributes:

    def test_schema_version_is_string(self):
        assert isinstance(GaugeHistoricalDaily.SCHEMA_VERSION, str)
        assert len(GaugeHistoricalDaily.SCHEMA_VERSION) > 0

    def test_metadata_categories_contains_expected_keys(self):
        cats = GaugeHistoricalDaily.METADATA_CATEGORIES
        for key in ("station", "dataType", "data", "file", "database"):
            assert key in cats

    def test_metadata_categories_station_has_required_subkeys(self):
        station_keys = GaugeHistoricalDaily.METADATA_CATEGORIES["station"]
        for key in ("id", "name", "gridReference"):
            assert key in station_keys

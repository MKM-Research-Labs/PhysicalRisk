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

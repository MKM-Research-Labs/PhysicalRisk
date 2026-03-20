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

"""Tests for DataLoader.load_all_data."""

import json

from .conftest import (write_gauge, write_property, write_mortgage,
                       write_hazard, write_property_hazard,
                       write_storms, write_counterparty)


class TestDataLoaderLoadAll:

    def test_empty_dir_returns_loaded_data(self, tmp_path):
        from visual.core.data_loader import DataLoader, LoadedData
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert isinstance(result, LoadedData)

    def test_with_gauge_data_loaded(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.gauge_data is not None

    def test_gauge_data_has_items_key(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert "items" in result.gauge_data

    def test_gauge_data_count_matches_records(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.gauge_data["count"] == len(result.gauge_data["items"])

    def test_with_property_data_loaded(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path); write_property(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.property_data is not None

    def test_with_mortgage_data_loaded(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path); write_mortgage(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.mortgage_data is not None

    def test_hazard_curves_loaded(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path); write_hazard(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.hazard_data is not None

    def test_property_hazard_curves_loaded(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path); write_property_hazard(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.property_hazard_data is not None

    def test_property_hazard_summary_fields_accessible(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path); write_property_hazard(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert "summary" in result.property_hazard_data

    def test_storm_data_loaded_dict_format(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path); write_storms(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.storm_data is not None

    def test_storm_data_list_format(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        (tmp_path / "storm_sequences.json").write_text(
            json.dumps([{"sequence_id": "STORM-seq001"}])
        )
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.storm_data is not None

    def test_storm_data_with_items_key(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        (tmp_path / "storm_sequences.json").write_text(
            json.dumps({"items": [{"sequence_id": "STORM-seq002"}]})
        )
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.storm_data is not None

    def test_storm_data_unknown_format(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        (tmp_path / "storm_sequences.json").write_text(json.dumps("not a dict or list"))
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.storm_data is not None

    def test_counterparty_data_loaded(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path); write_counterparty(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.counterparty_data is not None

    def test_gaugets_dir_counted(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        (gaugets / "GAUGE-001.json").write_text(json.dumps({"gauge_id": "GAUGE-001"}))
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.gaugets_count == 1

    def test_gaugets_dir_multiple_files_counted(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        for i in range(3):
            (gaugets / f"GAUGE-{i:03d}.json").write_text("{}")
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.gaugets_count == 3

    def test_gaugehd_dir_counted(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        hd = tmp_path / "gaugehd"
        hd.mkdir()
        (hd / "GAUGE-001.json").write_text("{}")
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.gaugehd_count == 1

    def test_propertyts_dir_counted(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        pts = tmp_path / "propertyts"
        pts.mkdir()
        (pts / "PROP-001.json").write_text("{}")
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.propertyts_count >= 1

    def test_lookups_built_after_load(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.mortgage_lookup is not None
        assert result.gauge_flood_info is not None

    def test_no_gaugets_dir_count_stays_zero(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.gaugets_count == 0

    def test_no_gaugehd_dir_count_stays_zero(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.gaugehd_count == 0

    def test_no_propertyts_dir_count_stays_zero(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        result = DataLoader(input_dir=tmp_path).load_all_data()
        assert result.propertyts_count == 0
